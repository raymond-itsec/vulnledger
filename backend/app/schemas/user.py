from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, model_validator

from app.services.password_policy import validate_password_strength

# Canonical role values used across the app. Matches the runtime checks
# in app/api/deps.py (client_user) and the require_role calls in the
# routers (admin, reviewer). Pydantic rejects anything else with a
# 422 instead of letting it land in the DB as a soft-locked account.
Role = Literal["admin", "reviewer", "client_user"]


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str | None = None
    company_name: str | None = None
    email: EmailStr
    role: Role = "reviewer"
    linked_client_id: UUID | None = None

    @model_validator(mode="after")
    def _check_password_strength(self):
        validate_password_strength(
            self.password,
            user_inputs=[self.username, self.email, self.full_name, self.company_name],
        )
        return self


class UserUpdate(BaseModel):
    full_name: str | None = None
    company_name: str | None = None
    email: EmailStr | None = None
    role: Role | None = None
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
