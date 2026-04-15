"""Optional OIDC/SSO authentication flow.

Only loaded when FINDINGS_OIDC_ENABLED=true. Provides:
  GET  /api/auth/oidc/login    — redirects to the IdP
  GET  /api/auth/oidc/callback — handles the IdP callback, creates/logs in user
"""

import logging

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Response
from starlette.requests import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.auth import create_access_token, create_refresh_token, hash_password

logger = logging.getLogger(__name__)

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
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    try:
        token = await oauth.oidc.authorize_access_token(request)
    except Exception as e:
        logger.error("OIDC token exchange failed: %s", e)
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
    access_token = create_access_token(user.user_id, user.role, user.linked_client_id)
    refresh = create_refresh_token(user.user_id)
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=7 * 24 * 3600,
        path="/api/auth",
    )

    # Redirect to frontend with token
    base = settings.app_base_url.rstrip("/")
    return Response(
        status_code=302,
        headers={"Location": f"{base}/?oidc_token={access_token}"},
    )
