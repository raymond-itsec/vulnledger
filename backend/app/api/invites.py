import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import paginate, require_role
from app.database import get_db
from app.models.invite import Invite
from app.models.user import User
from app.schemas.invite import InviteCreateRequest, InviteResponse, InviteRevokeResponse
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/invites", tags=["invites"])

admin_only = require_role("admin")


def _generate_invite_code() -> str:
    return secrets.token_urlsafe(18)


@router.get("", response_model=PaginatedResponse[InviteResponse])
async def list_invites(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    query = select(Invite).order_by(Invite.created_at.desc())
    return await paginate(db, query, page, per_page)


@router.post("", response_model=InviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    body: InviteCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    result = await db.execute(
        select(Invite).where(
            Invite.email == body.email,
            Invite.claimed_at.is_(None),
            Invite.revoked_at.is_(None),
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active invite already exists for this email address",
        )

    invite = Invite(
        code=_generate_invite_code(),
        email=body.email,
        source="admin",
        expires_at=body.expires_at,
    )
    db.add(invite)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Could not create invite")

    await db.refresh(invite)
    return invite


@router.post("/{invite_id}/revoke", response_model=InviteRevokeResponse)
async def revoke_invite(
    invite_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_only),
):
    result = await db.execute(select(Invite).where(Invite.invite_id == invite_id))
    invite = result.scalar_one_or_none()
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found")
    if invite.claimed_at is not None:
        raise HTTPException(status_code=409, detail="Claimed invites cannot be revoked")
    if invite.revoked_at is None:
        invite.revoked_at = datetime.now(timezone.utc)
        await db.commit()
    return InviteRevokeResponse(invite_id=invite.invite_id)
