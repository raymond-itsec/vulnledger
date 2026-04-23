from uuid import UUID
import ipaddress

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.error import make_error_payload
from app.schemas.auth import (
    LoginRequest,
    SecurityEventInfo,
    SecurityEventListResponse,
    SessionInfo,
    SessionListResponse,
    SessionRevokeAllResponse,
    SessionRevokeResponse,
    TokenResponse,
)
from app.services.auth import (
    create_access_token,
    verify_password,
)
from app.services.refresh_sessions import (
    describe_refresh_session,
    exchange_refresh_token,
    issue_refresh_session,
    list_active_refresh_sessions_for_user,
    list_security_events_for_user,
    refresh_cookie_max_age_seconds,
    resolve_refresh_session,
    revoke_all_refresh_sessions_for_user,
    revoke_refresh_session_by_id,
    revoke_refresh_session_family,
)

router = APIRouter(prefix="/auth", tags=["auth"])

limiter = Limiter(key_func=get_remote_address)
COOKIE_SECURE = settings.app_base_url.startswith("https://")


def _parse_ip_candidate(value: str | None) -> str | None:
    if not value:
        return None
    candidate = value.strip()
    if not candidate:
        return None
    # Handle potential "IP:port" form from some proxies.
    if candidate.count(":") == 1 and "." in candidate:
        host, _, _ = candidate.partition(":")
        candidate = host.strip()
    try:
        return str(ipaddress.ip_address(candidate))
    except ValueError:
        return None


def _is_public_ip(value: str | None) -> bool:
    parsed_value = _parse_ip_candidate(value)
    if not parsed_value:
        return False
    parsed = ipaddress.ip_address(parsed_value)
    return not (
        parsed.is_private
        or parsed.is_loopback
        or parsed.is_link_local
        or parsed.is_reserved
        or parsed.is_unspecified
        or parsed.is_multicast
    )


def _extract_forwarded_ips(request: Request) -> list[str]:
    forwarded_for = request.headers.get("x-forwarded-for", "")
    if not forwarded_for:
        return []
    values = []
    for part in forwarded_for.split(","):
        normalized = _parse_ip_candidate(part)
        if normalized:
            values.append(normalized)
    return values


def _request_ip(request: Request) -> str | None:
    direct_ip = _parse_ip_candidate(request.client.host if request.client else None)
    if not settings.trust_proxy_headers:
        return direct_ip

    x_real_ip = _parse_ip_candidate(request.headers.get("x-real-ip"))
    forwarded_ips = _extract_forwarded_ips(request)
    candidates = [x_real_ip, *forwarded_ips, direct_ip]
    for candidate in candidates:
        if _is_public_ip(candidate):
            return candidate
    for candidate in candidates:
        if candidate:
            return candidate
    return None


def _request_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=refresh_cookie_max_age_seconds(),
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key="refresh_token",
        path="/api/auth",
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )


def _refresh_failure_response(detail: str) -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=make_error_payload(
            code="session_expired",
            detail=detail,
        ),
    )
    _clear_refresh_cookie(response)
    return response


async def _current_refresh_identity(
    db: AsyncSession,
    raw_token: str | None,
) -> tuple[UUID | None, UUID | None]:
    if not raw_token:
        return None, None
    session = await resolve_refresh_session(db, raw_token=raw_token)
    if not session:
        return None, None
    return session.refresh_session_id, session.family_id


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_login)
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    client_ip = _request_ip(request)
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    access_token = create_access_token(
        user.user_id,
        user.role,
        user.linked_client_id,
        token_version=user.token_version,
    )
    refresh_token = await issue_refresh_session(
        db,
        user_id=user.user_id,
        created_ip=client_ip,
        created_user_agent=_request_user_agent(request),
    )
    _set_refresh_cookie(response, refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(None),
):
    client_ip = _request_ip(request)
    if not refresh_token:
        return _refresh_failure_response("Session expired. Please sign in again.")

    exchange_result = await exchange_refresh_token(
        db,
        raw_token=refresh_token,
        current_ip=client_ip,
        current_user_agent=_request_user_agent(request),
    )
    if exchange_result.status != "success" or not exchange_result.user or not exchange_result.refresh_token:
        return _refresh_failure_response("Session expired. Please sign in again.")

    access_token = create_access_token(
        exchange_result.user.user_id,
        exchange_result.user.role,
        exchange_result.user.linked_client_id,
        token_version=exchange_result.user.token_version,
    )
    _set_refresh_cookie(response, exchange_result.refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(None),
):
    client_ip = _request_ip(request)
    if refresh_token:
        await revoke_refresh_session_family(
            db,
            raw_token=refresh_token,
            reason="logout",
            actor_ip=client_ip,
            actor_user_agent=_request_user_agent(request),
        )
    _clear_refresh_cookie(response)
    return {"detail": "Logged out"}


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    refresh_token: str | None = Cookie(None),
):
    sessions = await list_active_refresh_sessions_for_user(
        db,
        user_id=user.user_id,
    )
    current_session_id, current_family_id = await _current_refresh_identity(db, refresh_token)

    items: list[SessionInfo] = []
    for session in sessions:
        payload = describe_refresh_session(session)
        payload["is_current"] = (
            current_session_id == session.refresh_session_id
            or (current_family_id is not None and current_family_id == session.family_id)
        )
        items.append(SessionInfo(**payload))

    return SessionListResponse(items=items)


@router.post("/sessions/revoke-all", response_model=SessionRevokeAllResponse)
async def revoke_all_sessions(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    client_ip = _request_ip(request)
    revoked_count = await revoke_all_refresh_sessions_for_user(
        db,
        user_id=user.user_id,
        reason="logout_all_sessions",
        actor_ip=client_ip,
        actor_user_agent=_request_user_agent(request),
    )
    _clear_refresh_cookie(response)
    return SessionRevokeAllResponse(revoked_count=revoked_count)


@router.post("/sessions/{refresh_session_id}/revoke", response_model=SessionRevokeResponse)
async def revoke_session(
    request: Request,
    refresh_session_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    client_ip = _request_ip(request)
    revoked = await revoke_refresh_session_by_id(
        db,
        user_id=user.user_id,
        refresh_session_id=refresh_session_id,
        reason="user_revoked_session",
        actor_ip=client_ip,
        actor_user_agent=_request_user_agent(request),
    )
    if not revoked:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionRevokeResponse(
        revoked=True,
        refresh_session_id=refresh_session_id,
    )


@router.get("/security-events", response_model=SecurityEventListResponse)
async def list_security_events(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    events = await list_security_events_for_user(
        db,
        user_id=user.user_id,
        limit=limit,
    )
    items = [
        SecurityEventInfo(
            security_event_id=event.security_event_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            family_id=event.family_id,
            refresh_session_id=event.refresh_session_id,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            details=event.details,
        )
        for event in events
    ]
    return SecurityEventListResponse(items=items, limit=limit)
