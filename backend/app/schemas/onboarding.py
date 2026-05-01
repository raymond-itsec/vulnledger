from pydantic import BaseModel, EmailStr, Field, model_validator

from app.services.password_policy import validate_password_strength


class InviteVerifyRequest(BaseModel):
    invite_code: str = Field(min_length=1, max_length=128)


class InviteVerifyResponse(BaseModel):
    email: EmailStr


class OnboardingStateResponse(BaseModel):
    email: EmailStr


class OnboardingCompleteRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str
    full_name: str | None = Field(default=None, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)

    @model_validator(mode="after")
    def _check_password_strength(self):
        validate_password_strength(
            self.password,
            user_inputs=[self.username, self.full_name, self.company_name],
        )
        return self


class OnboardingCompleteResponse(BaseModel):
    username: str
    email: EmailStr
