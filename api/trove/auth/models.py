import re
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


LINKEDIN_PROFILE = re.compile(r"^https://(?:www\.)?linkedin\.com/in/[A-Za-z0-9%_\-]{2,100}/?$")
PHONE_CHARACTERS = re.compile(r"^\+?[0-9 ()\-.]+$")


class ContactDetailsUpdate(RequestBody):
    """What a member shares once an author says yes.

    The sign-in email is always shared. LinkedIn and phone are optional: send null or leave one out
    to stop sharing it. Both are replaced together, so the settings form sends the whole picture.
    """

    linkedin_url: Annotated[str, Field(max_length=200)] | None = None
    phone: Annotated[str, Field(max_length=30)] | None = None

    @field_validator("linkedin_url", "phone", mode="before")
    @classmethod
    def blank_means_unset(cls, value: object) -> object:
        # An emptied form field clears the detail instead of failing validation.
        if isinstance(value, str):
            return value.strip() or None
        return value

    @field_validator("linkedin_url")
    @classmethod
    def check_linkedin(cls, value: str | None) -> str | None:
        if value is not None and not LINKEDIN_PROFILE.match(value):
            raise ValueError(
                "Use the link to your LinkedIn profile, like https://www.linkedin.com/in/your-name."
            )
        return value

    @field_validator("phone")
    @classmethod
    def check_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digits = sum(character.isdigit() for character in value)
        if not PHONE_CHARACTERS.match(value) or not 7 <= digits <= 15:
            raise ValueError("Enter a phone number with 7 to 15 digits. Spaces, dashes and + are fine.")
        return value


class ContactDetailsResponse(BaseModel):
    email: EmailStr
    linkedin_url: str | None
    phone: str | None


class NotificationSettingsUpdate(RequestBody):
    """The one email switch. Account emails, like the welcome message, are sent either way."""

    email_notifications: bool


class DeleteAccountRequest(RequestBody):
    """Deleting an account cannot be undone, so the member types their email to confirm."""

    email: EmailStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.casefold()


class UserResponse(BaseModel):
    id: str
    first_name: str
    # Null for accounts made before last names were collected, until the member sets one.
    last_name: str | None
    # What books show (trove.md §3): first and last name, or the first name alone.
    full_name: str
    email: EmailStr
    email_notifications: bool
    created_at: datetime


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
