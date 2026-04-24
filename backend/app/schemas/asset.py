from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.schemas._metadata import validate_metadata


VALID_ASSET_TYPES = [
    "repository", "browser_extension", "web_application",
    "api", "mobile_app", "other",
]


class AssetCreate(BaseModel):
    client_id: UUID
    asset_name: str
    asset_type: str
    description: str | None = None
    metadata_: dict | None = None

    @field_validator("metadata_")
    @classmethod
    def _check_metadata(cls, value):
        return validate_metadata(value)


class AssetUpdate(BaseModel):
    asset_name: str | None = None
    asset_type: str | None = None
    description: str | None = None
    metadata_: dict | None = None

    @field_validator("metadata_")
    @classmethod
    def _check_metadata(cls, value):
        return validate_metadata(value)


class AssetResponse(BaseModel):
    asset_id: UUID
    client_id: UUID
    asset_name: str
    asset_type: str
    description: str | None
    metadata_: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
