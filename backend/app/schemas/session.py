from datetime import date, datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field


VALID_STATUSES = ["planned", "in_progress", "completed", "cancelled"]

SessionName = Annotated[str, Field(min_length=1, max_length=255)]
SessionNotes = Annotated[str, Field(max_length=20000)]


class SessionCreate(BaseModel):
    asset_id: UUID
    review_name: SessionName
    review_date: date
    reviewer_id: UUID
    status: str = "planned"
    notes: SessionNotes | None = None


class SessionUpdate(BaseModel):
    review_name: SessionName | None = None
    review_date: date | None = None
    reviewer_id: UUID | None = None
    status: str | None = None
    notes: SessionNotes | None = None


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
