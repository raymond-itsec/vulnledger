from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


VALID_RISK_LEVELS = ["critical", "high", "medium", "low", "informational"]
VALID_REMEDIATION_STATUSES = [
    "open", "in_progress", "resolved", "accepted_risk", "false_positive",
]


class FindingCreate(BaseModel):
    session_id: UUID
    title: str
    description: str
    risk_level: str
    impact: str | None = None
    recommendation: str | None = None
    remediation_status: str = "open"
    references: list[str] | None = None


class FindingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    risk_level: str | None = None
    impact: str | None = None
    recommendation: str | None = None
    remediation_status: str | None = None
    references: list[str] | None = None


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
