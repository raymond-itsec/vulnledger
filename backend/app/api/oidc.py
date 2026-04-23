"""Optional OIDC/SSO authentication flow.

Only loaded when FINDINGS_OIDC_ENABLED=true. Provides:
  GET  /api/auth/oidc/login    -- redirects to the IdP
  GET  /api/auth/oidc/callback -- handles the IdP callback, creates/logs in user
"""

import logging

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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

router = APIRouter(prefix="/auth/oidc", tags=["oidc"])

oauth = OAuth()
oauth.register(
    name="oidc",
    client_id=settings.oidc_client_id,
    client_secret=settings.oidc_client_secret,
    server_metadata_url=settings.oidc_discovery_url,
    client_kwargs={"scope": "openid email profile"},
)


@router.get("/login")
async def oidc_login(request: Request):
    redirect_uri = settings.oidc_redirect_uri or str(
        request.url_for("oidc_callback")
    )
    return await oauth.oidc.authorize_redirect(request, redirect_uri)


@router.get("/callback")
async def oidc_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        token = await oauth.oidc.authorize_access_token(request)
    except Exception as exc:
        # Do not log raw exception text from token flows; some providers may include
        # sensitive auth details in error payloads.
        logger.warning("OIDC token exchange failed (%s)", exc.__class__.__name__)
        raise HTTPException(status_code=401, detail="OIDC authentication failed")

    userinfo = token.get("userinfo")
    if not userinfo:
        raise HTTPException(status_code=401, detail="No user info from IdP")

    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Email not provided by IdP")

    # Find or create user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # Auto-provision new user from OIDC
        username = email.split("@")[0]
        # Ensure unique username
        existing = await db.execute(select(User).where(User.username == username))
        if existing.scalar_one_or_none():
            username = email  # Fall back to full email as username

        user = User(
            username=username,
            email=email,
            full_name=userinfo.get("name") or userinfo.get("preferred_username") or username,
            password_hash=hash_password(f"oidc-{email}-nologin"),  # Not used for OIDC login
            role=settings.oidc_default_role,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("Auto-provisioned OIDC user: %s (%s)", user.username, email)

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
    redirect.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=refresh_cookie_max_age_seconds(),
        path="/api/auth",
    )
    return redirect
