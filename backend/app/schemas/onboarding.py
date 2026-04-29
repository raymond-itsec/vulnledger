from pydantic import BaseModel, EmailStr, Field


class InviteVerifyRequest(BaseModel):
    invite_code: str = Field(min_length=1, max_length=128)


class InviteVerifyResponse(BaseModel):
    email: EmailStr


class OnboardingStateResponse(BaseModel):
    email: EmailStr


class OnboardingCompleteRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=12, max_length=512)
    full_name: str | None = Field(default=None, max_length=255)
    company_name: str | None = Field(default=None, max_length=255)


class OnboardingCompleteResponse(BaseModel):
    username: str
    email: EmailStr
