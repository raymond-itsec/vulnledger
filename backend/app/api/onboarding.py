from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.invite import Invite
from app.models.user import User
from app.schemas.onboarding import (
    InviteVerifyRequest,
    InviteVerifyResponse,
    OnboardingCompleteRequest,
    OnboardingCompleteResponse,
    OnboardingStateResponse,
)
from app.services.auth import hash_password
from app.services.onboarding import (
    ONBOARDING_COOKIE_NAME,
    ONBOARDING_TOKEN_TTL_MINUTES,
    create_onboarding_token,
    decode_onboarding_token,
)
from app.versioning import CURRENT_API_PREFIX, LEGACY_UNVERSIONED_API_PREFIX

router = APIRouter(tags=["onboarding"])
COOKIE_SECURE = settings.cookie_secure  # see settings.cookie_secure docstring

# VL-2026-018: cookie paths derive from app.versioning so they cannot
# drift from the actual mounted router prefix. Hardcoding "/api/onboarding"
# (as this module did before the fix) breaks browsers under RFC 6265
# strict path-matching: a cookie at "/api/onboarding" is NOT sent on
# requests to "/api/v1/onboarding/...", so the verify-invite -> state
# -> complete flow returns 401 on every call after the first.
# Same fix shape as auth.py / oidc.py.
_ONBOARDING_COOKIE_PATH = f"{CURRENT_API_PREFIX}/onboarding"
_LEGACY_ONBOARDING_COOKIE_PATH = f"{LEGACY_UNVERSIONED_API_PREFIX}/onboarding"


def _set_onboarding_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=ONBOARDING_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="strict",
        max_age=ONBOARDING_TOKEN_TTL_MINUTES * 60,
        path=_ONBOARDING_COOKIE_PATH,
    )


def _clear_onboarding_cookie(response: Response) -> None:
    # Clear at both the current versioned path AND the legacy unversioned
    # path so users carrying a phantom cookie from before the VL-2026-018
    # fix (or from before the /api/v1 URL migration) get cleaned up.
    # Browsers do not auto-evict cookies just because the server stopped
    # using a path; the legacy delete is replay-safe for users who never
    # had one there.
    response.delete_cookie(
        key=ONBOARDING_COOKIE_NAME,
        path=_ONBOARDING_COOKIE_PATH,
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )
    response.delete_cookie(
        key=ONBOARDING_COOKIE_NAME,
        path=_LEGACY_ONBOARDING_COOKIE_PATH,
        secure=COOKIE_SECURE,
        httponly=True,
        samesite="strict",
    )


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


async def _resolve_active_invite(
    db: AsyncSession,
    raw_token: str | None,
) -> Invite:
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invite verification required",
        )

    payload = decode_onboarding_token(raw_token)
    invite_id = payload.get("sub")
    email = payload.get("email")
    code = payload.get("code")
    if not invite_id or not isinstance(email, str) or not isinstance(code, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invite verification required",
        )

    try:
        invite_uuid = UUID(invite_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invite verification required",
        ) from exc

    result = await db.execute(select(Invite).where(Invite.invite_id == invite_uuid))
    invite = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if (
        not invite
        or invite.code != code
        or invite.email != email
        or invite.claimed_at is not None
        or invite.revoked_at is not None
        or (invite.expires_at is not None and invite.expires_at <= now)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invite verification required",
        )
    return invite


@router.post("/invites/verify", response_model=InviteVerifyResponse)
async def verify_invite(
    body: InviteVerifyRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    invite_code = body.invite_code.strip()
    if not invite_code:
        raise HTTPException(status_code=400, detail="Invite code is required")

    result = await db.execute(select(Invite).where(Invite.code == invite_code))
    invite = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if (
        not invite
        or invite.claimed_at is not None
        or invite.revoked_at is not None
        or (invite.expires_at is not None and invite.expires_at <= now)
    ):
        # 401, not 404. The URL `/api/v1/invites/verify` exists; what
        # failed is credential validation (the invite code is the
        # bootstrapping credential for an unauthenticated user). 404
        # would imply the route is missing, which it isn't, and
        # confuses both clients and security tooling.
        #
        # The single uniform message ("invalid or expired") covers
        # all four cases (never existed / claimed / revoked / expired)
        # so attackers cannot enumerate valid codes by classifying
        # responses. Same shape as the login endpoint's uniform 401.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invite code is invalid or expired",
        )

    existing_user = await db.execute(select(User).where(User.email == invite.email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this invited email address",
        )

    token = create_onboarding_token(invite.invite_id, invite.email, invite.code)
    _set_onboarding_cookie(response, token)
    return InviteVerifyResponse(email=invite.email)


@router.get("/onboarding/state", response_model=OnboardingStateResponse)
async def onboarding_state(
    response: Response,
    db: AsyncSession = Depends(get_db),
    onboarding_token: str | None = Cookie(default=None, alias=ONBOARDING_COOKIE_NAME),
):
    try:
        invite = await _resolve_active_invite(db, onboarding_token)
    except HTTPException:
        _clear_onboarding_cookie(response)
        raise
    return OnboardingStateResponse(email=invite.email)


@router.post(
    "/onboarding/complete",
    response_model=OnboardingCompleteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def complete_onboarding(
    body: OnboardingCompleteRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    onboarding_token: str | None = Cookie(default=None, alias=ONBOARDING_COOKIE_NAME),
):
    try:
        invite = await _resolve_active_invite(db, onboarding_token)
    except HTTPException:
        _clear_onboarding_cookie(response)
        raise
    username = body.username.strip()
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters")

    existing_email = await db.execute(select(User).where(User.email == invite.email))
    if existing_email.scalar_one_or_none():
        _clear_onboarding_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account already exists for this invited email address",
        )

    user = User(
        username=username,
        password_hash=hash_password(body.password),
        full_name=_normalize_optional_text(body.full_name),
        company_name=_normalize_optional_text(body.company_name),
        email=invite.email,
        role="reviewer",
    )
    invite.claimed_at = datetime.now(timezone.utc)
    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already in use",
        )

    _clear_onboarding_cookie(response)
    return OnboardingCompleteResponse(username=user.username, email=user.email)
