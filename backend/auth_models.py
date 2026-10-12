"""Separate account credentials from public network profiles."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", json_schema_extra={"examples": [{
        "email": "you@example.com", "password": "choose-your-own-password",
    }]})

    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        # Our platform treats email addresses as case-insensitive account names.
        return value.casefold()


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class LinkedInExchangeRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    code: str = Field(min_length=1, max_length=256)


class LinkedInLoginResponse(LoginResponse):
    # New members are sent to finish their profile; returning members go to the directory.
    is_new: bool
