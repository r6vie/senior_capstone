from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, EmailStr, Field, SecretStr, field_validator, model_validator

from trove.core.models import NonEmptyText, RequestBody


class LoginRequest(RequestBody):
    email: EmailStr
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        # Email addresses are case-insensitive account names.
        return value.casefold()


Name = Annotated[NonEmptyText, Field(max_length=60)]


class SignupRequest(LoginRequest):
    first_name: Name
    last_name: Name
    password: SecretStr = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def reject_blank_password(cls, value: SecretStr) -> SecretStr:
        if value.get_secret_value().isspace():
            raise ValueError("Password cannot consist only of spaces.")
        return value


class NameUpdate(RequestBody):
    """Change the name on the account. Leave out a field to keep it."""

    first_name: Name | None = None
    last_name: Name | None = None

    @model_validator(mode="after")
    def require_a_change(self) -> "NameUpdate":
        if self.first_name is None and self.last_name is None:
            raise ValueError("Send a first_name, a last_name or both.")
        return self


class UserResponse(BaseModel):
    id: str
    first_name: str
    # Null for accounts made before last names were collected, until the member sets one.
    last_name: str | None
    # What books show (trove.md §3): first and last name, or the first name alone.
    full_name: str
    email: EmailStr
    created_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
