from datetime import UTC, datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field

from trove.core.models import NonEmptyText, RequestBody

MAX_MESSAGE = 2000

# "checkout_note": the reader's note from checking out, always first. "note": a line the app posted,
# such as a confirmed meeting time. "message": something one of the two people wrote.
MessageKind = Literal["checkout_note", "message", "note"]


class MessageRequest(RequestBody):
    text: NonEmptyText = Field(max_length=MAX_MESSAGE)


def _with_zone(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("Include a time zone.")
    return value.astimezone(UTC)


class ReadRequest(RequestBody):
    # The `sent_at` of the newest message the page showed. Messages that arrive after it stay new, even
    # if the page is marked read a moment later. Request bodies are strict, which would reject the ISO
    # text a browser sends for a time, so this one field isn't.
    seen_up_to: Annotated[datetime, Field(strict=False), AfterValidator(_with_zone)]


class Message(BaseModel):
    id: str
    kind: MessageKind
    # True if you wrote it. Notes are from the app, so they're never yours.
    from_me: bool
    # Who wrote it; empty for app notes.
    sender_name: str
    text: str
    sent_at: datetime


class Thread(BaseModel):
    checkout_id: str
    book_title: str
    # The other person on the checkout.
    other_name: str
    # False once the thread is read-only history.
    can_write: bool
    messages: list[Message]
