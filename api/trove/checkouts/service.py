"""The checkout rules (docs/trove.md §6) and the contract functions other features call."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pymongo import DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from trove.books.service import get_book_of, get_public_book

OPEN_LIMIT = 3  # open checkouts per reader
ANSWER_DAYS = 7  # an unanswered checkout closes quietly after this
RETRY_DAYS = 30  # after a decline or expiry, the same reader can try the same book again after this

REQUESTED = "requested"
ACCEPTED = "accepted"
DECLINED = "declined"
CANCELLED = "cancelled"
EXPIRED = "expired"

# Shown for every refusal that would otherwise tell the reader about copies, declines or expiries.
UNAVAILABLE = "This book isn't available right now."
NEWEST_FIRST = [("created_at", DESCENDING), ("_id", DESCENDING)]
LIST_LIMIT = 100


class CheckoutRefused(Exception):
    """A rule stops this action. The router turns it into an HTTP error with this status and message."""

    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


async def ensure_indexes(database: AsyncDatabase) -> None:
    # `open` is true while a checkout is requested or accepted. One open checkout per reader and book,
    # even if two arrive at the same moment.
    await database.checkouts.create_index(
        [("reader_id", 1), ("book_id", 1)],
        unique=True,
        partialFilterExpression={"open": True},
        name="checkouts_one_open_per_reader_and_book",
    )
    await database.checkouts.create_index([("reader_id", 1), *NEWEST_FIRST], name="checkouts_reader")
    await database.checkouts.create_index([("author_id", 1), *NEWEST_FIRST], name="checkouts_author")
    await database.checkouts.create_index([("book_id", 1), ("open", 1)], name="checkouts_book_open")
    await database.checkouts.create_index([("status", 1), ("expires_at", 1)], name="checkouts_expiry")


async def close_expired(database: AsyncDatabase) -> None:
    """Close unanswered checkouts past their time. Run before every read, so nobody needs a background job."""
    await database.checkouts.update_many(
        {"status": REQUESTED, "expires_at": {"$lte": datetime.now(UTC)}},
        # Closed when it expired, not when someone next looked, so the 30-day wait starts on time.
        [
            {
                "$set": {
                    "status": EXPIRED,
                    "open": False,
                    "closed_at": "$expires_at",
                    "updated_at": "$expires_at",
                }
            }
        ],
    )


async def _open_count(database: AsyncDatabase, field: str, value: str) -> int:
    return await database.checkouts.count_documents({field: value, "open": True})


async def check_out(database: AsyncDatabase, *, reader_id: str, book_id: str, message: str) -> dict:
    """Check out a book with a message. Raises CheckoutRefused if a rule stops it."""
    await close_expired(database)
    # A draft doesn't count: readers share their own book before borrowing someone else's.
    if await reader_book_of(database, reader_id) is None:
        raise CheckoutRefused(403, "Put your own book on the shelf before you check one out.")
    book = await get_public_book(database, book_id)
    if book is None:
        raise CheckoutRefused(404, UNAVAILABLE)
    if book["author_id"] == reader_id:
        raise CheckoutRefused(409, "This is your own book.")
    if await database.checkouts.find_one(
        {"reader_id": reader_id, "book_id": book_id, "open": True}, {"_id": 1}
    ):
        raise CheckoutRefused(409, "You've already checked out this book.")

    now = datetime.now(UTC)
    turned_away = await database.checkouts.find_one(
        {
            "reader_id": reader_id,
            "book_id": book_id,
            "status": {"$in": [DECLINED, EXPIRED]},
            "closed_at": {"$gt": now - timedelta(days=RETRY_DAYS)},
        },
        {"_id": 1},
    )
    if turned_away:
        raise CheckoutRefused(409, UNAVAILABLE)
    if await _open_count(database, "reader_id", reader_id) >= OPEN_LIMIT:
        raise CheckoutRefused(409, too_many_message())
    if await _open_count(database, "book_id", book_id) >= book["copies"]:
        raise CheckoutRefused(409, UNAVAILABLE)

    checkout = {
        "_id": str(uuid4()),
        "book_id": book_id,
        "author_id": book["author_id"],
        "reader_id": reader_id,
        # Kept so the checkout still reads well if the book changes or leaves the shelf.
        "book_title": book["title"],
        "author_name": book["author_name"],
        "message": message,
        "status": REQUESTED,
        "open": True,
        "created_at": now,
        "updated_at": now,
        "expires_at": now + timedelta(days=ANSWER_DAYS),
    }
    try:
        await database.checkouts.insert_one(checkout)
    except DuplicateKeyError:
        raise CheckoutRefused(409, "You've already checked out this book.") from None

    # Check the limits again now that it's saved, so two checkouts at the same moment can't both slip
    # past them. If both lose, the reader just tries again.
    over_reader = await _open_count(database, "reader_id", reader_id) > OPEN_LIMIT
    over_copies = await _open_count(database, "book_id", book_id) > book["copies"]
    if over_reader or over_copies:
        await database.checkouts.delete_one({"_id": checkout["_id"]})
        raise CheckoutRefused(409, too_many_message() if over_reader else UNAVAILABLE)
    return checkout


def too_many_message() -> str:
    return (
        f"You can have {OPEN_LIMIT} open checkouts at a time. "
        "Cancel one that hasn't been answered, or wait until one is returned."
    )


async def get_checkout_for(database: AsyncDatabase, checkout_id: str, user_id: str) -> dict | None:
    """The checkout if this user is its reader or author, else None. For messaging and meetings."""
    await close_expired(database)
    return await database.checkouts.find_one(
        {"_id": checkout_id, "$or": [{"reader_id": user_id}, {"author_id": user_id}]}
    )


async def _close_requested(
    database: AsyncDatabase, checkout_id: str, owner: dict, changes: dict
) -> dict | None:
    """Move a still-unanswered checkout on. Raises CheckoutRefused if it's missing or already answered."""
    await close_expired(database)
    now = datetime.now(UTC)
    updated = await database.checkouts.find_one_and_update(
        {"_id": checkout_id, "status": REQUESTED, **owner},
        {"$set": {**changes, "updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is not None:
        return updated
    if await database.checkouts.find_one({"_id": checkout_id, **owner}, {"_id": 1}) is None:
        raise CheckoutRefused(404, "We couldn't find that checkout.")
    raise CheckoutRefused(409, "This checkout has already been answered or closed.")


async def accept(database: AsyncDatabase, checkout_id: str, author_id: str) -> dict:
    # The copy was taken when the reader checked out, so accepting never goes over the author's copies.
    now = datetime.now(UTC)
    return await _close_requested(
        database,
        checkout_id,
        {"author_id": author_id},
        {"status": ACCEPTED, "answered_at": now, "expires_at": None},
    )


async def decline(database: AsyncDatabase, checkout_id: str, author_id: str) -> dict:
    now = datetime.now(UTC)
    return await _close_requested(
        database,
        checkout_id,
        {"author_id": author_id},
        {"status": DECLINED, "open": False, "answered_at": now, "closed_at": now, "expires_at": None},
    )


async def cancel(database: AsyncDatabase, checkout_id: str, reader_id: str) -> dict:
    """The reader withdraws an unanswered checkout. Unlike a decline, they can check it out again right away."""
    now = datetime.now(UTC)
    return await _close_requested(
        database,
        checkout_id,
        {"reader_id": reader_id},
        {"status": CANCELLED, "open": False, "closed_at": now, "expires_at": None},
    )


async def checkouts_of_reader(database: AsyncDatabase, reader_id: str) -> list[dict]:
    """Every checkout this member made, newest first."""
    await close_expired(database)
    cursor = database.checkouts.find({"reader_id": reader_id}).sort(NEWEST_FIRST).limit(LIST_LIMIT)
    return await cursor.to_list()


async def open_checkouts_of_author(database: AsyncDatabase, author_id: str) -> list[dict]:
    """Open checkouts of this member's book, newest first."""
    await close_expired(database)
    cursor = database.checkouts.find({"author_id": author_id, "open": True}).sort(NEWEST_FIRST)
    return await cursor.limit(LIST_LIMIT).to_list()


async def fully_checked_out(database: AsyncDatabase, books: list[dict]) -> set[str]:
    """The ids of the books whose copies are all out. Each book needs its `_id` and `copies`.

    For the shelf: a book with no copies left quietly leaves it (docs/trove.md §6). Never show the
    result to a reader as a label or a count.
    """
    await close_expired(database)
    counts = {
        row["_id"]: row["open"]
        async for row in await database.checkouts.aggregate(
            [
                {"$match": {"book_id": {"$in": [book["_id"] for book in books]}, "open": True}},
                {"$group": {"_id": "$book_id", "open": {"$sum": 1}}},
            ]
        )
    }
    return {book["_id"] for book in books if counts.get(book["_id"], 0) >= book["copies"]}


async def reader_book_of(database: AsyncDatabase, reader_id: str) -> dict | None:
    """The reader's own book, if it's on the shelf, for the author to look at."""
    book = await get_book_of(database, reader_id)
    return await get_public_book(database, book["_id"]) if book else None
