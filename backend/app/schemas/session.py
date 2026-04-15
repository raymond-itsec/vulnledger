from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


VALID_STATUSES = ["planned", "in_progress", "completed", "cancelled"]


class SessionCreate(BaseModel):
    asset_id: UUID
    review_name: str
    review_date: date
    reviewer_id: UUID
    status: str = "planned"
    notes: str | None = None


class SessionUpdate(BaseModel):
    review_name: str | None = None
    review_date: date | None = None
    reviewer_id: UUID | None = None
    status: str | None = None
    notes: str | None = None


class SessionResponse(BaseModel):
    session_id: UUID
    asset_id: UUID
    review_name: str
    review_date: date
    reviewer_id: UUID
    reviewer_name: str | None = None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
