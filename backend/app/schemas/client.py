from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ClientCreate(BaseModel):
    company_name: str
    primary_contact_name: str | None = None
    primary_contact_email: EmailStr | None = None
    metadata_: dict | None = None


class ClientUpdate(BaseModel):
    company_name: str | None = None
    primary_contact_name: str | None = None
    primary_contact_email: EmailStr | None = None
    metadata_: dict | None = None


class ClientResponse(BaseModel):
    client_id: UUID
    company_name: str
    primary_contact_name: str | None
    primary_contact_email: str | None
    metadata_: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
