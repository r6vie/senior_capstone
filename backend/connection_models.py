"""Request and response shapes for connection requests (mentorship, advice, introductions...)."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from models import NonEmptyText, SavedProfile

RequestType = Literal["mentorship", "career_advice", "introduction", "collaboration", "other"]
# What the app shows in its dropdown, in this order. email_templates.py words each type too.
REQUEST_TYPE_LABELS: dict[str, str] = {
    "mentorship": "Mentorship",
    "career_advice": "Career advice",
    "introduction": "Introduction",
    "collaboration": "Collaboration",
    "other": "Something else",
}

# The message the requester writes to the person they are asking.
Message = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]


class ConnectionCreate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", json_schema_extra={"examples": [{
        "profile_id": "sample-taylor", "type": "mentorship",
        "message": "Hi Taylor, I'm a junior interested in medical devices. Could you mentor me this semester?",
    }]})

    profile_id: NonEmptyText
    type: RequestType
    message: Message


class ConnectionUpdate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", json_schema_extra={"examples": [{"status": "accepted"}]})

    status: Literal["accepted", "declined"]


class MessageCreate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", json_schema_extra={"examples": [{
        "body": "Thanks for reaching out! What are you hoping to get out of mentorship?",
    }]})

    body: Message


class MessageResponse(BaseModel):
    id: str  # the first message of every thread is the original request, with the id "request"
    from_me: bool
    body: str
    created_at: datetime


class RequestTypeOption(BaseModel):
    value: RequestType
    label: str


class ConnectionResponse(BaseModel):
    id: str
    status: Literal["pending", "accepted", "declined"]
    type: RequestType
    direction: Literal["incoming", "outgoing"]  # incoming = someone asked you
    message: str | None = None
    created_at: datetime
    responded_at: datetime | None = None
    profile: SavedProfile | None = None  # the other person's public profile
    # The other person's email address. Shared only once the request is accepted, otherwise null.
    contact_email: str | None = None
