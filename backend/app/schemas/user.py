from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str | None = None
    company_name: str | None = None
    email: EmailStr
    role: str = "reviewer"
    linked_client_id: UUID | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    company_name: str | None = None
    email: EmailStr | None = None
    role: str | None = None
    linked_client_id: UUID | None = None
    is_active: bool | None = None


class UserSelfUpdate(BaseModel):
    full_name: str | None = None
    company_name: str | None = None
    email: EmailStr | None = None


class UserResponse(BaseModel):
    user_id: UUID
    username: str
    full_name: str | None
    company_name: str | None
    email: str
    role: str
    linked_client_id: UUID | None
    is_active: bool
    oidc_issuer: str | None = None
    oidc_subject: str | None = None

    model_config = {"from_attributes": True}
