from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TemplateCreate(BaseModel):
    stable_id: str
    name: str
    category: str | None = None
    title: str | None = None
    description: str | None = None
    risk_level: str | None = None
    impact: str | None = None
    recommendation: str | None = None
    references: list[str] | None = None


class TemplateUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    title: str | None = None
    description: str | None = None
    risk_level: str | None = None
    impact: str | None = None
    recommendation: str | None = None
    references: list[str] | None = None


class TemplateResponse(BaseModel):
    template_id: UUID
    stable_id: str
    name: str
    category: str | None
    is_builtin: bool
    title: str | None
    description: str | None
    risk_level: str | None
    impact: str | None
    recommendation: str | None
    references: list[str] | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
