from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TaxonomyEntryResponse(BaseModel):
    taxonomy_entry_id: UUID
    domain: str
    value: str
    label: str
    sort_order: int
    color: str | None = None
    is_active: bool

    model_config = {"from_attributes": True}


class TaxonomyVersionResponse(BaseModel):
    taxonomy_version_id: UUID
    version_number: int
    description: str | None = None
    is_current: bool
    created_at: datetime
    updated_at: datetime
    domains: dict[str, list[TaxonomyEntryResponse]]


class TaxonomyEntryCreate(BaseModel):
    value: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(ge=0)
    color: str | None = Field(default=None, max_length=32)
    is_active: bool = True


class TaxonomyVersionCreate(BaseModel):
    description: str | None = Field(default=None, max_length=2000)
    domains: dict[str, list[TaxonomyEntryCreate]]


class TaxonomyVersionActivate(BaseModel):
    taxonomy_version_id: UUID
