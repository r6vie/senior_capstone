from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from trove.core.models import NonEmptyText, RequestBody

# What a reader sees. Declined and expired both show as "unavailable", so a reader can't tell a no
# from no answer (docs/trove.md §6).
ReaderStatus = Literal["waiting", "accepted", "cancelled", "unavailable", "returned"]
# Authors see only their open checkouts.
AuthorStatus = Literal["waiting", "accepted"]


# "Did you meet?" (docs/trove.md §8): "met" and "no" end the reading; "not_yet" keeps it open.
MeetAnswer = Literal["met", "not_yet", "no"]


class DidYouMeet(BaseModel):
    """This member's own side of "Did you meet?". Never includes the other person's answer."""

    # True once it's being asked and this member can (still) answer.
    can_answer: bool
    my_answer: MeetAnswer | None


class MeetAnswerRequest(RequestBody):
    answer: MeetAnswer


class CheckoutRequest(RequestBody):
    book_id: NonEmptyText = Field(max_length=100)
    message: NonEmptyText = Field(max_length=1000)


class Contact(BaseModel):
    """What the other member chose to share once the author said yes (docs/trove.md §9.1)."""

    email: str
    linkedin_url: str | None
    phone: str | None


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
    # The author's contact details, only once they've accepted.
    author_contact: Contact | None = None
    # True when the conversation has something you haven't read. Private to you; never a count.
    new_messages: bool = False
    # Set once "Did you meet?" is being asked (after the meeting time), and after the reading.
    did_you_meet: DidYouMeet | None = None


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
    # The reader's contact details, only once you've accepted.
    reader_contact: Contact | None = None
    # True when the conversation has something you haven't read. Private to you; never a count.
    new_messages: bool = False
    # Set once "Did you meet?" is being asked (after the meeting time).
    did_you_meet: DidYouMeet | None = None


class MyCheckouts(BaseModel):
    # Books you've checked out, newest first.
    reading: list[ReadingCheckout]
    # Open checkouts of your book, newest first.
    lending: list[LendingCheckout]


class PastMeet(BaseModel):
    """Someone you met through a checkout (docs/trove.md §8). Both people get one."""

    checkout_id: str
    # The book that was checked out.
    book_title: str
    # Whether you were the one who checked out the book, or its author.
    you_were: Literal["reader", "author"]
    other_name: str
    # The other person's own book, if it's on the shelf.
    other_book: ReaderBook | None
    # Their contact details stay available after a meeting.
    contact: Contact | None
    met_on: datetime
    # You can still give your own answer if you haven't (for example, "no" if you didn't meet).
    did_you_meet: DidYouMeet
