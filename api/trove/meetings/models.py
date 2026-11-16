from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, field_validator

from trove.core.models import RequestBody

SLOT_MINUTES = 30
MAX_TIMES = 5


def _as_slot(value: datetime) -> datetime:
    """A start time to the minute, in UTC. The screen offers half-hour steps, so people's times line up."""
    if value.tzinfo is None:
        raise ValueError("Include a time zone.")
    if value.minute not in (0, 30) or value.second or value.microsecond:
        raise ValueError("Start on the hour or the half hour.")
    return value.astimezone(UTC)


# Request bodies are strict, which would reject the ISO text a browser sends for a time.
Slot = Annotated[datetime, Field(strict=False), AfterValidator(_as_slot)]


def _link(value: str | None) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    if " " in value or not value.lower().startswith("https://") or len(value) < 12:
        raise ValueError("Enter a full link that starts with https://")
    return value


class TimesUpdate(RequestBody):
    times: list[Slot] = Field(max_length=MAX_TIMES)

    @field_validator("times")
    @classmethod
    def no_duplicates(cls, times: list[datetime]) -> list[datetime]:
        return sorted(set(times))


class ConfirmRequest(RequestBody):
    start: Slot


class DetailsUpdate(RequestBody):
    video_link: str | None = Field(default=None, max_length=300)
    place_note: str | None = Field(default=None, max_length=200)

    @field_validator("video_link")
    @classmethod
    def https_link(cls, value: str | None) -> str | None:
        return _link(value)

    @field_validator("place_note")
    @classmethod
    def blank_is_none(cls, value: str | None) -> str | None:
        return (value or "").strip() or None


class MeetingView(BaseModel):
    checkout_id: str
    book_title: str
    other_name: str
    minutes: int = SLOT_MINUTES
    my_times: list[datetime]
    their_times: list[datetime]
    # Times both people offered, still ahead of us.
    shared_times: list[datetime]
    start: datetime | None
    video_link: str | None
    place_note: str | None
