from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class InviteCreateRequest(BaseModel):
    email: EmailStr
    expires_at: datetime | None = None


class InviteResponse(BaseModel):
    invite_id: UUID
    code: str
    email: EmailStr
    source: str
    expires_at: datetime | None
    claimed_at: datetime | None
    revoked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class InviteRevokeResponse(BaseModel):
    revoked: bool = True
    invite_id: UUID
