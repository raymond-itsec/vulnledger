from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field


VALID_RISK_LEVELS = ["critical", "high", "medium", "low", "informational"]
VALID_REMEDIATION_STATUSES = [
    "open", "in_progress", "resolved", "accepted_risk", "false_positive",
]

FindingTitle = Annotated[str, Field(min_length=1, max_length=500)]
FindingDescription = Annotated[str, Field(min_length=1, max_length=20000)]
FindingDetail = Annotated[str, Field(max_length=10000)]
FindingReference = Annotated[str, Field(min_length=1, max_length=2048)]


class FindingCreate(BaseModel):
    session_id: UUID
    title: FindingTitle
    description: FindingDescription
    risk_level: str
    impact: FindingDetail | None = None
    recommendation: FindingDetail | None = None
    remediation_status: str = "open"
    references: list[FindingReference] | None = Field(default=None, max_length=50)


class FindingUpdate(BaseModel):
    title: FindingTitle | None = None
    description: FindingDescription | None = None
    risk_level: str | None = None
    impact: FindingDetail | None = None
    recommendation: FindingDetail | None = None
    remediation_status: str | None = None
    references: list[FindingReference] | None = Field(default=None, max_length=50)


class FindingResponse(BaseModel):
    finding_id: UUID
    session_id: UUID
    title: str
    description: str
    risk_level: str
    impact: str | None
    recommendation: str | None
    remediation_status: str
    references: list[str] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FindingHistoryResponse(BaseModel):
    history_id: UUID
    finding_id: UUID
    changed_by: UUID
    changed_by_name: str | None = None
    changed_at: datetime
    field_name: str
    old_value: str | None
    new_value: str | None

    model_config = {"from_attributes": True}
