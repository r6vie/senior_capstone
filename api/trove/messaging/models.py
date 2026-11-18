from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from trove.core.models import NonEmptyText, RequestBody

MAX_MESSAGE = 2000

# "checkout_note": the reader's note from checking out, always first. "note": a line the app posted,
# such as a confirmed meeting time. "message": something one of the two people wrote.
MessageKind = Literal["checkout_note", "message", "note"]


class MessageRequest(RequestBody):
    text: NonEmptyText = Field(max_length=MAX_MESSAGE)


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
