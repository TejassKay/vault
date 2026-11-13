from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSignup(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8)
    consent: bool = Field(
        ...,
        description="FR-1: Mandatory user consent to personal finance & document data processing",
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    email: str
    notification_pref: str
    consent_given_at: datetime
    created_at: datetime
