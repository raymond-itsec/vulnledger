"""Optional OIDC/SSO authentication flow.

Only loaded when FINDINGS_OIDC_ENABLED=true. Provides:
  GET  /api/auth/oidc/login    -- redirects to the IdP
  GET  /api/auth/oidc/callback -- handles the IdP callback, creates/logs in user
"""

import hmac
import logging
import secrets

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.auth import hash_password
from app.services.refresh_sessions import (
    issue_refresh_session,
    refresh_cookie_max_age_seconds,
)

logger = logging.getLogger(__name__)
COOKIE_SECURE = settings.app_base_url.startswith("https://")
OIDC_TEMP_COOKIE_MAX_AGE = 600
SESSION_HINT_COOKIE_NAME = settings.session_hint_cookie_name

router = APIRouter(prefix="/auth/oidc", tags=["oidc"])

oauth = OAuth()
oauth.register(
    name="oidc",
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret,
    server_metadata_url=settings.oidc_discovery_url,
    client_kwargs={"scope": "openid email profile"},
)


def _normalize_identity_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def _default_oidc_issuer() -> str | None:
    discovery = settings.oidc_discovery_url.strip()
    if not discovery:
        return None
    marker = "/.well-known/openid-configuration"
    if discovery.endswith(marker):
        return discovery[: -len(marker)]
    return discovery


def _extract_identity(token: dict, userinfo: dict) -> tuple[str | None, str | None]:
    claims = token.get("userinfo") if isinstance(token.get("userinfo"), dict) else {}
    id_token_claims = token.get("id_token_claims") if isinstance(token.get("id_token_claims"), dict) else {}
    subject = (
        _normalize_identity_value(userinfo.get("sub"))
        or _normalize_identity_value(claims.get("sub"))
        or _normalize_identity_value(id_token_claims.get("sub"))
    )
    issuer = (
        _normalize_identity_value(userinfo.get("iss"))
        or _normalize_identity_value(claims.get("iss"))
        or _normalize_identity_value(id_token_claims.get("iss"))
        or _default_oidc_issuer()
    )
    return issuer, subject


def _redirect_uri_allowed(redirect_uri: str) -> bool:
    allowlist = [entry.strip() for entry in settings.oidc_redirect_uri_allowlist if entry.strip()]
    if allowlist:
        return redirect_uri in allowlist
    configured = settings.oidc_redirect_uri.strip()
    if configured:
        return redirect_uri == configured
    return True


def _seed_username_from_subject(subject: str) -> str:
    filtered = "".join(ch for ch in subject.lower() if ch.isalnum())
    if not filtered:
        filtered = secrets.token_hex(6)
    return f"oidc_{filtered[:24]}"


async def _resolve_or_create_user(
    db: AsyncSession,
    *,
    issuer: str,
    subject: str,
    email: str,
    userinfo: dict,
) -> User:
    # Canonical identity: provider issuer + subject
    result = await db.execute(
        select(User).where(
            User.oidc_issuer == issuer,
            User.oidc_subject == subject,
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # Email-based auto-linking intentionally removed: we do not trust the
    # email claim from arbitrary customer IdPs, and linking on email enables
    # the nOAuth class of attacks where an attacker who controls an email
    # claim can take over a local account. Unknown (issuer, subject) pairs
    # always auto-provision a fresh user. Existing local accounts that want
    # SSO must be linked via an authenticated self-service flow (not part of
    # this sweep).
    username = _seed_username_from_subject(subject)
    suffix = 0
    while True:
        candidate = username if suffix == 0 else f"{username}_{suffix}"
        existing_username = await db.execute(select(User.user_id).where(User.username == candidate))
        if existing_username.scalar_one_or_none() is None:
            username = candidate
            break
        suffix += 1

    user = User(
        username=username,
        email=email,
        full_name=userinfo.get("name") or userinfo.get("preferred_username") or username,
        password_hash=hash_password(f"oidc-{subject}-nologin"),
        role=settings.oidc_default_role,
        is_active=True,
        oidc_issuer=issuer,
        oidc_subject=subject,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("Auto-provisioned OIDC user: %s (%s)", user.username, email)
    return user


def _set_oidc_temp_cookies(response, *, state_value: str, nonce_value: str) -> None:
    response.set_cookie(
        key="oidc_state",
        value=state_value,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=OIDC_TEMP_COOKIE_MAX_AGE,
        path="/api/auth/oidc",
    )
    response.set_cookie(
        key="oidc_nonce",
        value=nonce_value,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=OIDC_TEMP_COOKIE_MAX_AGE,
        path="/api/auth/oidc",
    )


def _clear_oidc_temp_cookies(response) -> None:
    response.delete_cookie("oidc_state", path="/api/auth/oidc")
    response.delete_cookie("oidc_nonce", path="/api/auth/oidc")


def _set_session_hint_cookie(response) -> None:
    response.set_cookie(
        key=SESSION_HINT_COOKIE_NAME,
        value="1",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=refresh_cookie_max_age_seconds(),
        path="/",
    )


@router.get("/login")
async def oidc_login(request: Request):
    redirect_uri = settings.oidc_redirect_uri or str(request.url_for("oidc_callback"))
    if not _redirect_uri_allowed(redirect_uri):
        raise HTTPException(
            status_code=500,
            detail="OIDC redirect URI is not in the configured allowlist.",
        )

    state_value = secrets.token_urlsafe(32)
    nonce_value = secrets.token_urlsafe(32)
    response = await oauth.oidc.authorize_redirect(
        request,
        redirect_uri,
        state=state_value,
        nonce=nonce_value if settings.oidc_require_nonce else None,
    )
    _set_oidc_temp_cookies(
        response,
        state_value=state_value,
        nonce_value=nonce_value,
    )
    return response


@router.get("/callback")
async def oidc_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    oidc_state_cookie: str | None = Cookie(None, alias="oidc_state"),
    oidc_nonce_cookie: str | None = Cookie(None, alias="oidc_nonce"),
):
    state_param = request.query_params.get("state")
    if not state_param or not oidc_state_cookie or not hmac.compare_digest(state_param, oidc_state_cookie):
        raise HTTPException(status_code=401, detail="OIDC state validation failed")

    try:
        token = await oauth.oidc.authorize_access_token(request)
    except Exception:
        # Do not log raw exception text from token flows; some providers may include
        # sensitive auth details in error payloads.
        logger.warning("OIDC authentication exchange failed")
        raise HTTPException(status_code=401, detail="OIDC authentication failed")

    userinfo = token.get("userinfo")
    if not isinstance(userinfo, dict):
        raise HTTPException(status_code=401, detail="No user info from IdP")

    email = _normalize_identity_value(userinfo.get("email"))
    if not email:
        raise HTTPException(status_code=401, detail="Email not provided by IdP")

    issuer, subject = _extract_identity(token, userinfo)
    if not issuer or not subject:
        raise HTTPException(status_code=401, detail="OIDC identity is missing issuer or subject")

    if settings.oidc_require_nonce:
        nonce_claim = _normalize_identity_value(
            (token.get("id_token_claims") or {}).get("nonce")
            if isinstance(token.get("id_token_claims"), dict)
            else None
        )
        if not nonce_claim or not oidc_nonce_cookie or not hmac.compare_digest(nonce_claim, oidc_nonce_cookie):
            raise HTTPException(status_code=401, detail="OIDC nonce validation failed")

    user = await _resolve_or_create_user(
        db,
        issuer=issuer,
        subject=subject,
        email=email,
        userinfo=userinfo,
    )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    # Issue tokens
    refresh_token = await issue_refresh_session(
        db,
        user_id=user.user_id,
        created_ip=request.client.host if request.client else None,
        created_user_agent=request.headers.get("user-agent"),
    )
    # Redirect to frontend and let the SPA bootstrap from the refresh cookie.
    base = settings.app_base_url.rstrip("/")
    redirect = RedirectResponse(url=f"{base}/", status_code=302)
    _clear_oidc_temp_cookies(redirect)
    redirect.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=refresh_cookie_max_age_seconds(),
        path="/api/auth",
    )
    _set_session_hint_cookie(redirect)
    return redirect
