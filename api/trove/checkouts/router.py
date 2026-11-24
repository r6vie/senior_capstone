import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import (
    ContactDetailsResponse,
    contact_details_of_many,
    full_names_of,
    get_current_user,
)
from trove.books.service import shelf_books_of
from trove.checkouts import service
from trove.checkouts.models import (
    CheckoutRequest,
    Contact,
    DidYouMeet,
    LendingCheckout,
    MeetAnswerRequest,
    MyCheckouts,
    PastMeet,
    ReaderBook,
    ReadingCheckout,
)
from trove.checkouts.service import CheckoutRefused
from trove.core.database import get_database
from trove.interview.service import ask_after_reading
from trove.messaging.service import checkouts_with_new_messages
from trove.notifications.service import notify_checkout_accepted, notify_checkout_requested

router = APIRouter(prefix="/checkouts", tags=["Checkouts"])

READER_STATUS = {
    service.REQUESTED: "waiting",
    service.ACCEPTED: "accepted",
    service.CANCELLED: "cancelled",
    service.DECLINED: "unavailable",
    service.EXPIRED: "unavailable",
    service.RETURNED: "returned",
}


def refused(error: CheckoutRefused) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


def reveals(checkout: dict) -> bool:
    """Whether contact details show on this checkout: accepted, or a Past meet afterwards (C2, C4).

    Read fresh each time, so a change in Settings shows up, and nothing is copied onto the checkout.
    After the reading they stay for a Past meet (docs/trove.md §8), and go if the two didn't meet.
    """
    return checkout["status"] == service.ACCEPTED or service.is_past_meet(checkout)


def meet_view(checkout: dict, user_id: str, due: datetime | None) -> DidYouMeet | None:
    """This member's side of "Did you meet?": None until it's asked (after the meeting time, `due`)."""
    mine = service.my_answer(checkout, user_id)
    if checkout["status"] == service.RETURNED:
        return DidYouMeet(can_answer=mine not in service.FINAL_ANSWERS, my_answer=mine)
    if checkout["status"] != service.ACCEPTED or due is None or datetime.now(UTC) < due:
        return None
    return DidYouMeet(can_answer=True, my_answer=mine)


@dataclass
class Lookups:
    """Everything a list of checkouts shows about the other people in them, read in one go: each kind of
    data is one database trip, and the trips run at the same time, however many checkouts there are."""

    names: dict[str, str] = field(default_factory=dict)
    contacts: dict[str, ContactDetailsResponse] = field(default_factory=dict)
    books: dict[str, dict] = field(default_factory=dict)
    due: dict[str, datetime] = field(default_factory=dict)
    starts: dict[str, datetime] = field(default_factory=dict)

    @classmethod
    async def load(
        cls, database: AsyncDatabase, checkouts: list[dict], others: list[str], *, books: bool = False
    ) -> "Lookups":
        if not checkouts:
            # An empty list shows nobody, so there's nothing to look up.
            return cls()
        revealed = list(
            {other for checkout, other in zip(checkouts, others, strict=True) if reveals(checkout)}
        )

        async def nothing() -> dict:
            return {}

        names, contacts, shelf, meetings = await asyncio.gather(
            full_names_of(database, list(set(others))),
            contact_details_of_many(database, revealed) if revealed else nothing(),
            shelf_books_of(database, list(set(others))) if books else nothing(),
            service.meetings_of(database, checkouts),
        )
        starts = {
            checkout_id: service.as_utc(meeting["start"])
            for checkout_id, meeting in meetings.items()
            if meeting.get("start")
        }
        return cls(
            names=names,
            contacts=contacts,
            books=shelf,
            due=service.due_times(checkouts, meetings),
            starts=starts,
        )

    def meeting_start(self, checkout: dict) -> datetime | None:
        """The confirmed time, only while the checkout is accepted: after the reading it's history."""
        return self.starts.get(checkout["_id"]) if checkout["status"] == service.ACCEPTED else None

    def contact(self, checkout: dict, other_id: str) -> Contact | None:
        details = self.contacts.get(other_id) if reveals(checkout) else None
        return Contact.model_validate(details.model_dump()) if details else None

    def book(self, other_id: str) -> ReaderBook | None:
        book = self.books.get(other_id)
        return ReaderBook(id=book["_id"], title=book["title"]) if book else None


async def reading_views(database: AsyncDatabase, checkouts: list[dict]) -> list[ReadingCheckout]:
    authors = [checkout["author_id"] for checkout in checkouts]
    found = await Lookups.load(database, checkouts, authors)
    return [
        ReadingCheckout(
            id=checkout["_id"],
            book_id=checkout["book_id"],
            book_title=checkout["book_title"],
            # Authors' current names; the name saved on the checkout covers sample books with no account.
            author_name=found.names.get(checkout["author_id"]) or checkout["author_name"],
            message=checkout["message"],
            status=READER_STATUS[checkout["status"]],
            created_at=checkout["created_at"],
            expires_at=checkout["expires_at"] if checkout["status"] == service.REQUESTED else None,
            author_contact=found.contact(checkout, checkout["author_id"]),
            did_you_meet=meet_view(checkout, checkout["reader_id"], found.due.get(checkout["_id"])),
            meeting_start=found.meeting_start(checkout),
        )
        for checkout in checkouts
    ]


async def lending_views(database: AsyncDatabase, checkouts: list[dict]) -> list[LendingCheckout]:
    readers = [checkout["reader_id"] for checkout in checkouts]
    found = await Lookups.load(database, checkouts, readers, books=True)
    return [
        LendingCheckout(
            id=checkout["_id"],
            book_id=checkout["book_id"],
            book_title=checkout["book_title"],
            reader_name=found.names.get(checkout["reader_id"], ""),
            reader_book=found.book(checkout["reader_id"]),
            message=checkout["message"],
            status="accepted" if checkout["status"] == service.ACCEPTED else "waiting",
            created_at=checkout["created_at"],
            expires_at=checkout["expires_at"] if checkout["status"] == service.REQUESTED else None,
            reader_contact=found.contact(checkout, checkout["reader_id"]),
            did_you_meet=meet_view(checkout, checkout["author_id"], found.due.get(checkout["_id"])),
            meeting_start=found.meeting_start(checkout),
        )
        for checkout in checkouts
    ]


@router.post("", response_model=ReadingCheckout, status_code=201)
async def check_out(
    data: CheckoutRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> ReadingCheckout:
    """Check out a book with a short message to its author."""
    try:
        checkout = await service.check_out(
            database, reader_id=user["_id"], book_id=data.book_id, message=data.message
        )
    except CheckoutRefused as error:
        raise refused(error) from None
    reader_name = (await full_names_of(database, [user["_id"]])).get(user["_id"], user["first_name"])
    background_tasks.add_task(
        notify_checkout_requested,
        database,
        checkout_id=checkout["_id"],
        author_id=checkout["author_id"],
        reader_name=reader_name,
        book_title=checkout["book_title"],
        message=checkout["message"],
        # From the checkout rules, so the email can't drift from them.
        answer_days=service.ANSWER_DAYS,
    )
    return (await reading_views(database, [checkout]))[0]


@router.get("", response_model=MyCheckouts)
async def my_checkouts(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyCheckouts:
    """Books you've checked out, and open checkouts of your book."""
    reading, lending = await service.checkouts_page_of(database, user["_id"])
    ids = [checkout["_id"] for checkout in [*reading, *lending]]
    reading_list, lending_list, unread = await asyncio.gather(
        reading_views(database, reading),
        lending_views(database, lending),
        checkouts_with_new_messages(database, user["_id"], ids),
    )
    mine = MyCheckouts(reading=reading_list, lending=lending_list)
    items = [*mine.reading, *mine.lending]
    for item in items:
        item.new_messages = item.id in unread
    return mine


@router.post("/{checkout_id}/cancel", response_model=ReadingCheckout)
async def cancel(
    checkout_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> ReadingCheckout:
    """Withdraw a checkout the author hasn't answered yet."""
    try:
        checkout = await service.cancel(database, checkout_id, user["_id"])
    except CheckoutRefused as error:
        raise refused(error) from None
    return (await reading_views(database, [checkout]))[0]


@router.post("/{checkout_id}/accept", response_model=LendingCheckout)
async def accept(
    checkout_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> LendingCheckout:
    """Say yes to a checkout of your book. Both of you now see each other's contact details."""
    try:
        checkout = await service.accept(database, checkout_id, user["_id"])
    except CheckoutRefused as error:
        raise refused(error) from None
    names = await full_names_of(database, [checkout["reader_id"], checkout["author_id"]])
    background_tasks.add_task(
        notify_checkout_accepted,
        database,
        checkout_id=checkout["_id"],
        reader_id=checkout["reader_id"],
        author_id=checkout["author_id"],
        # Fallbacks so a subject line never starts with an empty name.
        reader_name=names.get(checkout["reader_id"]) or "A reader",
        author_name=names.get(checkout["author_id"]) or checkout["author_name"] or "The author",
        book_title=checkout["book_title"],
    )
    return (await lending_views(database, [checkout]))[0]


@router.post("/{checkout_id}/decline", status_code=204, response_class=Response)
async def decline(
    checkout_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> Response:
    """Say no to a checkout of your book. The reader sees "this book isn't available right now"."""
    try:
        await service.decline(database, checkout_id, user["_id"])
    except CheckoutRefused as error:
        raise refused(error) from None
    return Response(status_code=204)


@router.post("/{checkout_id}/met", response_model=DidYouMeet)
async def did_you_meet(
    checkout_id: str,
    data: MeetAnswerRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> DidYouMeet:
    """Answer "Did you meet?" for yourself. Your answer is never shown to the other person."""
    try:
        checkout = await service.answer_did_you_meet(database, checkout_id, user["_id"], data.answer)
    except CheckoutRefused as error:
        raise refused(error) from None
    if service.is_past_meet(checkout):
        # Each reading grows the book (I6): the author gets one quick question. Safe to call again.
        await ask_after_reading(database, checkout["author_id"], checkout["_id"])
    due = (await service.question_due_times(database, [checkout])).get(checkout["_id"])
    view = meet_view(checkout, user["_id"], due)
    return view or DidYouMeet(can_answer=False, my_answer=service.my_answer(checkout, user["_id"]))


@router.get("/past-meets", response_model=list[PastMeet])
async def past_meets(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> list[PastMeet]:
    """The people you've met through checkouts, newest first, with their contact details."""
    checkouts = await service.past_meet_checkouts(database, user["_id"])
    others = [c["author_id"] if c["reader_id"] == user["_id"] else c["reader_id"] for c in checkouts]
    found = await Lookups.load(database, checkouts, others, books=True)
    meets = [
        PastMeet(
            checkout_id=checkout["_id"],
            book_title=checkout["book_title"],
            you_were="reader" if checkout["reader_id"] == user["_id"] else "author",
            other_name=found.names.get(other)
            or (checkout["author_name"] if other == checkout["author_id"] else ""),
            other_book=found.book(other),
            contact=found.contact(checkout, other),
            met_on=service.as_utc(checkout["returned_at"]),
            did_you_meet=meet_view(checkout, user["_id"], found.due.get(checkout["_id"])),
        )
        for checkout, other in zip(checkouts, others, strict=True)
    ]
    return meets
