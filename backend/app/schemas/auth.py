from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    role: str
    client_id: str | None = None


class SessionInfo(BaseModel):
    refresh_session_id: UUID
    family_id: UUID
    issued_at: datetime
    last_seen_at: datetime
    ip_address: str | None
    user_agent: str | None
    is_current: bool


class SessionListResponse(BaseModel):
    items: list[SessionInfo]


class SessionRevokeResponse(BaseModel):
    revoked: bool
    refresh_session_id: UUID


class SessionRevokeAllResponse(BaseModel):
    revoked_count: int


class SecurityEventInfo(BaseModel):
    security_event_id: UUID
    event_type: str
    occurred_at: datetime
    family_id: UUID | None
    refresh_session_id: UUID | None
    ip_address: str | None
    user_agent: str | None
    details: dict | None = None


class SecurityEventListResponse(BaseModel):
    items: list[SecurityEventInfo]
    limit: int = Field(ge=1, le=200)
