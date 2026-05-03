from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
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
    SessionInfo,
    SessionRevokeAllResponse,
    SessionRevokeResponse,
    TokenResponse,
)
from app.schemas.pagination import PaginatedResponse
from app.services.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.services.ip_utils import (
    extract_forwarded_ips,
    is_public_ip,
    parse_ip_candidate,
    rate_limit_ip_key,
    resolve_request_ip,
)
from app.services.login_throttle import check_login_allowed
from app.versioning import CURRENT_API_PREFIX, LEGACY_UNVERSIONED_API_PREFIX
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

# Pre-computed dummy hash used to keep login timing constant when the supplied
# username doesn't exist. Without this, verify_password() is short-circuited by
# Python's `or` semantics in the "no user" branch (~2ms response) while a real
# username forces a full bcrypt verify (~150-220ms). The timing differential is
# sufficient to enumerate valid usernames remotely. Hashing a sentinel string
# at import time means we use the SAME hashing function and cost factor as
# real passwords, so the dummy verify takes equivalent CPU time.
# The sentinel string is never accepted as a real password because no real
# user will ever have THIS hash stored against them (it's local to this file).
_DUMMY_PASSWORD_HASH = hash_password(
    "vl::timing-oracle-defense::never-matches-any-real-input"
)

limiter = Limiter(key_func=lambda request: rate_limit_ip_key(request, settings.trust_proxy_headers))
COOKIE_SECURE = settings.app_base_url.startswith("https://")
# VL-2026-014: hardcoded (was settings.session_hint_cookie_name). Caddy's
# protected-route gate also looks for this exact name; the env var was
# the drift source between the two layers and had no real-world use case.
SESSION_HINT_COOKIE_NAME = "vl_session"


def _request_ip(request: Request) -> str | None:
    resolved = resolve_request_ip(request, settings.trust_proxy_headers)
    if resolved:
        return resolved

    direct_ip = parse_ip_candidate(request.client.host if request.client else None)
    if direct_ip and is_public_ip(direct_ip):
        return direct_ip
    if direct_ip:
        return direct_ip

    forwarded_ips = extract_forwarded_ips(request)
    for candidate in forwarded_ips:
        if is_public_ip(candidate):
            return candidate
    return forwarded_ips[0] if forwarded_ips else None


def _request_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


# Cookie paths are derived from app.versioning so that a v2 cutover
# only requires updating CURRENT_API_VERSION there; cookie paths and
# router mounts then move together. See `app/versioning.py` for the
# rationale and the startup sanity-check in app/main.py.
_REFRESH_COOKIE_PATH = f"{CURRENT_API_PREFIX}/auth"
_LEGACY_REFRESH_COOKIE_PATH = f"{LEGACY_UNVERSIONED_API_PREFIX}/auth"


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=refresh_cookie_max_age_seconds(),
        path=_REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    # Clear at both the current versioned path AND the legacy
    # unversioned path so that users who logged in before Phase 1.4
    # (when the cookie was scoped to /api/auth) don't end up with a
    # phantom cookie sitting in their jar. Browsers do not auto-evict
    # cookies just because the server stopped using a path; the legacy
    # delete is idempotent for users who never had one there.
    response.delete_cookie(
        key="refresh_token",
        path=_REFRESH_COOKIE_PATH,
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )
    response.delete_cookie(
        key="refresh_token",
        path=_LEGACY_REFRESH_COOKIE_PATH,
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )


def _set_session_hint_cookie(response: Response) -> None:
    response.set_cookie(
        key=SESSION_HINT_COOKIE_NAME,
        value="1",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=refresh_cookie_max_age_seconds(),
        path="/",
    )


def _clear_session_hint_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_HINT_COOKIE_NAME,
        path="/",
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
    _clear_session_hint_cookie(response)
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
    if not await check_login_allowed(body.username):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts for this account. Please try again later.",
        )
    result = await db.execute(select(User).where(User.username == body.username))
    user = result.scalar_one_or_none()
    # Always run verify_password — even for missing users — against a sentinel
    # hash so timing is identical for "user exists, wrong password" and "user
    # does not exist". Closes the username-enumeration timing oracle.
    target_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    password_ok = verify_password(body.password, target_hash)
    if user is None or not password_ok:
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
    _set_session_hint_cookie(response)
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
    _set_session_hint_cookie(response)
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
    _clear_session_hint_cookie(response)
    return {"detail": "Logged out"}


@router.get("/sessions", response_model=PaginatedResponse[SessionInfo])
async def list_sessions(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    refresh_token: str | None = Cookie(None),
):
    sessions = await list_active_refresh_sessions_for_user(
        db,
        user_id=user.user_id,
    )
    current_session_id, current_family_id = await _current_refresh_identity(db, refresh_token)

    all_items: list[SessionInfo] = []
    for session in sessions:
        payload = describe_refresh_session(session)
        payload["is_current"] = (
            current_session_id == session.refresh_session_id
            or (current_family_id is not None and current_family_id == session.family_id)
        )
        all_items.append(SessionInfo(**payload))

    total = len(all_items)
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    start = (page - 1) * per_page
    items = all_items[start : start + per_page]

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }


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
    _clear_session_hint_cookie(response)
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


@router.get("/security-events", response_model=PaginatedResponse[SecurityEventInfo])
async def list_security_events(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Service caps internally; pull (page * per_page) so we can window the page slice.
    fetch_cap = min(page * per_page, 200)
    events = await list_security_events_for_user(
        db,
        user_id=user.user_id,
        limit=fetch_cap,
    )
    all_items = [
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
    total = len(all_items)
    pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    start = (page - 1) * per_page
    items = all_items[start : start + per_page]

    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
    }
