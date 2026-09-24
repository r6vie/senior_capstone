"""Separate account credentials from public network profiles."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator

from models import NonEmptyText


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


class SignupRequest(LoginRequest):
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "name": "Your Name", "email": "you@example.com", "password": "choose-your-own-password",
    }]})

    name: NonEmptyText
    password: SecretStr = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def reject_blank_password(cls, value: SecretStr) -> SecretStr:
        if value.get_secret_value().isspace():
            raise ValueError("Password cannot consist only of spaces.")
        return value


class UserResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
