from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from trove.core.models import NonEmptyText, RequestBody

# What a reader sees. Declined and expired both show as "unavailable", so a reader can't tell a no
# from no answer (docs/trove.md §6).
ReaderStatus = Literal["waiting", "accepted", "cancelled", "unavailable"]
# Authors see only their open checkouts.
AuthorStatus = Literal["waiting", "accepted"]


class CheckoutRequest(RequestBody):
    book_id: NonEmptyText = Field(max_length=100)
    message: NonEmptyText = Field(max_length=1000)


class ReadingCheckout(BaseModel):
    """A checkout as its reader sees it."""

    id: str
    book_id: str
    book_title: str
    author_name: str
    message: str
    status: ReaderStatus
    created_at: datetime
    # When an unanswered checkout closes on its own; null once it's answered or closed.
    expires_at: datetime | None


class ReaderBook(BaseModel):
    id: str
    title: str


class LendingCheckout(BaseModel):
    """A checkout of your book, as its author sees it."""

    id: str
    book_id: str
    book_title: str
    reader_name: str
    # The reader's own book, if it's on the shelf, so the author can see who's asking.
    reader_book: ReaderBook | None
    message: str
    status: AuthorStatus
    created_at: datetime
    expires_at: datetime | None


class MyCheckouts(BaseModel):
    # Books you've checked out, newest first.
    reading: list[ReadingCheckout]
    # Open checkouts of your book, newest first.
    lending: list[LendingCheckout]
