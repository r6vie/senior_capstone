"""Request and response shapes for connection requests."""

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints

from models import NonEmptyText, SavedProfile

# An optional personal note, shown to the person you ask to connect with.
Note = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]


class ConnectionCreate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", json_schema_extra={"examples": [{
        "profile_id": "sample-taylor", "message": "Hi! I'd love to hear how you got into medical devices.",
    }]})

    profile_id: NonEmptyText
    message: Note | None = None


class ConnectionUpdate(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", json_schema_extra={"examples": [{"status": "accepted"}]})

    status: Literal["accepted", "declined"]


class ConnectionResponse(BaseModel):
    id: str
    status: Literal["pending", "accepted", "declined"]
    direction: Literal["incoming", "outgoing"]  # incoming = someone asked you
    message: str | None = None
    created_at: datetime
    responded_at: datetime | None = None
    profile: SavedProfile | None = None  # the other person's public profile
