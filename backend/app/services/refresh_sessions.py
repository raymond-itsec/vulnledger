import hashlib
import hmac
import ipaddress
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.auth_security_event import AuthSecurityEvent
from app.models.refresh_session import RefreshSession
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class RefreshExchangeResult:
    status: str
    user: User | None = None
    refresh_token: str | None = None


def refresh_cookie_max_age_seconds() -> int:
    return settings.refresh_token_expire_days * 24 * 3600


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _normalize_ip(ip_address: str | None) -> str | None:
    if not ip_address:
        return None
    return ip_address[:64]


def _normalize_user_agent(user_agent: str | None) -> str | None:
    if not user_agent:
        return None
    trimmed = user_agent.strip()
    return trimmed[:512] if trimmed else None


def _build_refresh_token(session_id: uuid.UUID, secret: str) -> str:
    return f"{session_id}.{secret}"


def _parse_refresh_token(raw_token: str | None) -> tuple[uuid.UUID, str] | None:
    if not raw_token:
        return None
    session_id_raw, separator, secret = raw_token.partition(".")
    if not separator or not secret:
        return None
    try:
        session_id = uuid.UUID(session_id_raw)
    except ValueError:
        return None
    return session_id, secret


def parse_refresh_session_id(raw_token: str | None) -> uuid.UUID | None:
    parsed = _parse_refresh_token(raw_token)
    if not parsed:
        return None
    return parsed[0]


async def _load_refresh_session(
    db: AsyncSession,
    raw_token: str | None,
    *,
    for_update: bool = False,
) -> RefreshSession | None:
    parsed = _parse_refresh_token(raw_token)
    if not parsed:
        return None

    session_id, _ = parsed
    stmt = select(RefreshSession).where(RefreshSession.refresh_session_id == session_id)
    if for_update:
        stmt = stmt.with_for_update()

    result = await db.execute(stmt)
    session = result.scalar_one_or_none()
    if not session:
        return None

    if not hmac.compare_digest(session.token_hash, _hash_refresh_token(raw_token)):
        return None
    return session


def _ip_country_hint(ip_address: str | None) -> str:
    # TODO: Replace this heuristic with trusted GeoIP enrichment if/when we add it server-side.
    normalized = _normalize_ip(ip_address)
    if not normalized:
        return "Unknown"
    try:
        parsed = ipaddress.ip_address(normalized)
    except ValueError:
        return "Unknown"
    if (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_reserved
        or parsed.is_unspecified
    ):
        return "Private/Local"
    return "Unknown"


async def _create_refresh_session(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    family_id: uuid.UUID | None,
    parent_session_id: uuid.UUID | None,
    created_ip: str | None,
    created_user_agent: str | None,
) -> tuple[RefreshSession, str]:
    refresh_session_id = uuid.uuid4()
    secret = secrets.token_urlsafe(48)
    raw_token = _build_refresh_token(refresh_session_id, secret)
    issued_at = _now()

    session = RefreshSession(
        refresh_session_id=refresh_session_id,
        user_id=user_id,
        family_id=family_id or uuid.uuid4(),
        parent_session_id=parent_session_id,
        token_hash=_hash_refresh_token(raw_token),
        issued_at=issued_at,
        # FIXME: Add an absolute family lifetime cap. Current policy extends lifetime on each rotation.
        expires_at=issued_at + timedelta(days=settings.refresh_token_expire_days),
        created_ip=_normalize_ip(created_ip),
        created_user_agent=_normalize_user_agent(created_user_agent),
    )
    db.add(session)
    await db.flush()
    return session, raw_token


async def _record_security_event(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    event_type: str,
    family_id: uuid.UUID | None = None,
    refresh_session_id: uuid.UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: dict | None = None,
) -> None:
    db.add(
        AuthSecurityEvent(
            user_id=user_id,
            event_type=event_type,
            occurred_at=_now(),
            family_id=family_id,
            refresh_session_id=refresh_session_id,
            ip_address=_normalize_ip(ip_address),
            user_agent=_normalize_user_agent(user_agent),
            details=details,
        )
    )
    await db.flush()


async def _revoke_family(
    db: AsyncSession,
    family_id: uuid.UUID,
    *,
    reason: str,
) -> None:
    revoked_at = _now()
    await db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.family_id == family_id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(
            revoked_at=revoked_at,
            revoke_reason=reason,
        )
    )


async def _bump_user_token_version(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> None:
    await db.execute(
        update(User)
        .where(User.user_id == user_id)
        .values(token_version=User.token_version + 1)
    )


async def _prune_stale_refresh_sessions(db: AsyncSession) -> None:
    if settings.refresh_session_retention_days <= 0:
        return

    cutoff = _now() - timedelta(days=settings.refresh_session_retention_days)
    await db.execute(
        delete(RefreshSession).where(
            or_(
                RefreshSession.expires_at < cutoff,
                and_(
                    RefreshSession.revoked_at.is_not(None),
                    RefreshSession.revoked_at < cutoff,
                ),
            )
        )
    )


async def resolve_refresh_session(
    db: AsyncSession,
    *,
    raw_token: str | None,
) -> RefreshSession | None:
    return await _load_refresh_session(db, raw_token)


async def list_active_refresh_sessions_for_user(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
) -> list[RefreshSession]:
    now = _now()
    result = await db.execute(
        select(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
            RefreshSession.expires_at > now,
        )
        .order_by(RefreshSession.last_used_at.desc(), RefreshSession.issued_at.desc())
    )
    return result.scalars().all()


async def list_security_events_for_user(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[AuthSecurityEvent]:
    safe_limit = min(max(limit, 1), 200)
    result = await db.execute(
        select(AuthSecurityEvent)
        .where(AuthSecurityEvent.user_id == user_id)
        .order_by(AuthSecurityEvent.occurred_at.desc())
        .limit(safe_limit)
    )
    return result.scalars().all()


async def revoke_refresh_session_by_id(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    refresh_session_id: uuid.UUID,
    reason: str,
) -> bool:
    result = await db.execute(
        select(RefreshSession)
        .where(
            RefreshSession.refresh_session_id == refresh_session_id,
            RefreshSession.user_id == user_id,
        )
        .with_for_update()
    )
    session = result.scalar_one_or_none()
    if not session:
        return False

    await _revoke_family(db, session.family_id, reason=reason)
    await _record_security_event(
        db,
        user_id=user_id,
        event_type="refresh_session_revoked",
        family_id=session.family_id,
        refresh_session_id=session.refresh_session_id,
        details={"reason": reason},
    )
    await _bump_user_token_version(db, user_id)
    await _prune_stale_refresh_sessions(db)
    await db.commit()
    return True


async def revoke_all_refresh_sessions_for_user(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    reason: str,
) -> int:
    now = _now()
    result = await db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user_id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(
            revoked_at=now,
            revoke_reason=reason,
        )
    )
    revoked_count = result.rowcount or 0
    await _record_security_event(
        db,
        user_id=user_id,
        event_type="all_refresh_sessions_revoked",
        details={"reason": reason, "revoked_count": revoked_count},
    )
    await _bump_user_token_version(db, user_id)
    await _prune_stale_refresh_sessions(db)
    await db.commit()
    return revoked_count


async def issue_refresh_session(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    created_ip: str | None = None,
    created_user_agent: str | None = None,
) -> str:
    _, raw_token = await _create_refresh_session(
        db,
        user_id=user_id,
        family_id=None,
        parent_session_id=None,
        created_ip=created_ip,
        created_user_agent=created_user_agent,
    )
    await _prune_stale_refresh_sessions(db)
    await db.commit()
    return raw_token


async def exchange_refresh_token(
    db: AsyncSession,
    *,
    raw_token: str | None,
    current_ip: str | None = None,
    current_user_agent: str | None = None,
) -> RefreshExchangeResult:
    session = await _load_refresh_session(db, raw_token, for_update=True)
    if not session:
        return RefreshExchangeResult(status="invalid")

    if session.replaced_by_session_id is not None or session.revoke_reason == "rotated":
        await _record_security_event(
            db,
            user_id=session.user_id,
            event_type="refresh_token_reuse_detected",
            family_id=session.family_id,
            refresh_session_id=session.refresh_session_id,
            ip_address=current_ip,
            user_agent=current_user_agent,
            details={"reason": "rotated_token_reused"},
        )
        await _revoke_family(db, session.family_id, reason="reused_refresh_token")
        await _bump_user_token_version(db, session.user_id)
        await _prune_stale_refresh_sessions(db)
        await db.commit()
        return RefreshExchangeResult(status="reused")

    if session.revoked_at is not None:
        return RefreshExchangeResult(status="invalid")

    now = _now()
    if session.expires_at <= now:
        session.revoked_at = now
        session.revoke_reason = session.revoke_reason or "expired"
        await _prune_stale_refresh_sessions(db)
        await db.commit()
        return RefreshExchangeResult(status="invalid")

    user_result = await db.execute(select(User).where(User.user_id == session.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        await _revoke_family(db, session.family_id, reason="user_inactive")
        await _bump_user_token_version(db, session.user_id)
        await _prune_stale_refresh_sessions(db)
        await db.commit()
        return RefreshExchangeResult(status="invalid")

    session.last_used_at = now
    session.last_used_ip = _normalize_ip(current_ip)
    session.last_used_user_agent = _normalize_user_agent(current_user_agent)

    replacement, new_raw_token = await _create_refresh_session(
        db,
        user_id=session.user_id,
        family_id=session.family_id,
        parent_session_id=session.refresh_session_id,
        created_ip=current_ip,
        created_user_agent=current_user_agent,
    )
    session.replaced_by_session_id = replacement.refresh_session_id
    session.revoked_at = now
    session.revoke_reason = "rotated"

    await _prune_stale_refresh_sessions(db)
    await db.commit()
    return RefreshExchangeResult(
        status="success",
        user=user,
        refresh_token=new_raw_token,
    )


async def revoke_refresh_session_family(
    db: AsyncSession,
    *,
    raw_token: str | None,
    reason: str,
) -> None:
    parsed = _parse_refresh_token(raw_token)
    if not parsed:
        if raw_token:
            # TODO: Persist structured security audit events for malformed refresh-token revoke attempts.
            logger.warning("Malformed refresh token supplied for revoke operation")
        return

    session = await _load_refresh_session(db, raw_token, for_update=True)
    if not session:
        # TODO: Persist structured security audit events for unknown session-id revoke attempts.
        logger.warning(
            "Refresh session revoke requested for unknown session_id=%s",
            parsed[0],
        )
        return
    await _revoke_family(db, session.family_id, reason=reason)
    await _record_security_event(
        db,
        user_id=session.user_id,
        event_type="refresh_session_family_revoked",
        family_id=session.family_id,
        refresh_session_id=session.refresh_session_id,
        details={"reason": reason},
    )
    await _bump_user_token_version(db, session.user_id)
    await _prune_stale_refresh_sessions(db)
    await db.commit()


def describe_refresh_session(session: RefreshSession) -> dict:
    last_seen_at = session.last_used_at or session.issued_at
    ip_address = session.last_used_ip or session.created_ip
    user_agent = session.last_used_user_agent or session.created_user_agent
    return {
        "refresh_session_id": session.refresh_session_id,
        "family_id": session.family_id,
        "issued_at": session.issued_at,
        "last_seen_at": last_seen_at,
        "ip_address": ip_address,
        "user_agent": user_agent,
        "country": _ip_country_hint(ip_address),
    }
