"""The checkout rules (docs/trove.md §6) and the contract functions other features call."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pymongo import DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from trove.auth.service import full_names_of, on_account_deleted
from trove.books.service import get_book_of, get_public_book

OPEN_LIMIT = 3  # open checkouts per reader
ANSWER_DAYS = 7  # an unanswered checkout closes quietly after this
RETRY_DAYS = 30  # after a decline or expiry, the same reader can try the same book again after this
ASK_DAYS_WITHOUT_TIME = 14  # "Did you meet?" is asked this long after the yes if no time was confirmed
RETURN_DAYS = 14  # an unanswered "Did you meet?" returns the copy this long after it was asked

REQUESTED = "requested"
ACCEPTED = "accepted"
DECLINED = "declined"
CANCELLED = "cancelled"
EXPIRED = "expired"
RETURNED = "returned"  # the reading is over: "Did you meet?" was answered, or nobody answered (C4)

# "Did you meet?" answers (docs/trove.md §8). Private: nobody is ever shown another person's answer.
MET = "met"
NOT_YET = "not_yet"
DIDNT = "no"
FINAL_ANSWERS = (MET, DIDNT)

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
    await database.checkouts.create_index([("status", 1), ("answered_at", 1)], name="checkouts_readings")


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


def as_utc(value: datetime) -> datetime:
    # MongoDB hands back naive datetimes; they are always UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _key(user_id: str) -> str:
    # Member ids become field names under `answers`. They are UUIDs; refuse anything MongoDB would read
    # as a path or an operator.
    if not user_id or "." in user_id or "$" in user_id:
        raise ValueError("Unexpected member id.")
    return user_id


def _due(checkout: dict, meeting: dict | None) -> datetime:
    # Imported here because meetings imports this module; a top-level import would be circular.
    from trove.meetings.models import SLOT_MINUTES

    if meeting and meeting.get("start"):
        return as_utc(meeting["start"]) + timedelta(minutes=SLOT_MINUTES)
    return as_utc(checkout["answered_at"]) + timedelta(days=ASK_DAYS_WITHOUT_TIME)


async def question_due_at(database: AsyncDatabase, checkout: dict) -> datetime:
    """When "Did you meet?" is asked: once the confirmed meeting is over, or 14 days after the yes."""
    from trove.meetings.service import get_meeting

    return _due(checkout, await get_meeting(database, checkout["_id"]))


async def question_due_times(database: AsyncDatabase, checkouts: list[dict]) -> dict[str, datetime]:
    """`question_due_at` for each accepted or returned checkout, by id, in at most one database trip."""
    answered = [checkout for checkout in checkouts if checkout.get("answered_at")]
    if not answered:
        return {}
    meetings = {
        meeting["_id"]: meeting
        async for meeting in database.meetings.find(
            {"_id": {"$in": [checkout["_id"] for checkout in answered]}}, {"start": 1}
        )
    }
    return {checkout["_id"]: _due(checkout, meetings.get(checkout["_id"])) for checkout in answered}


def is_past_meet(checkout: dict) -> bool:
    """Someone said they met and nobody said they didn't (docs/trove.md §8)."""
    answers = [entry["answer"] for entry in (checkout.get("answers") or {}).values()]
    return checkout["status"] == RETURNED and MET in answers and DIDNT not in answers


async def return_overdue(database: AsyncDatabase, scope: dict) -> None:
    """Return the copy of accepted checkouts in `scope` whose "Did you meet?" went unanswered for 14 days.

    Run before reads, like `close_expired`, so nobody needs a background job. Not a Past meet.
    """
    now = datetime.now(UTC)
    # The question is never asked before the yes, so only yeses at least 14 days old can be overdue.
    candidates = await database.checkouts.find(
        {**scope, "status": ACCEPTED, "answered_at": {"$lte": now - timedelta(days=RETURN_DAYS)}}
    ).to_list()
    due = await question_due_times(database, candidates)
    for checkout in candidates:
        returned_at = due[checkout["_id"]] + timedelta(days=RETURN_DAYS)
        if returned_at <= now:
            await database.checkouts.update_one(
                {"_id": checkout["_id"], "status": ACCEPTED},
                {
                    "$set": {
                        "status": RETURNED,
                        "open": False,
                        "met": False,
                        "returned_by": "no_answer",
                        "returned_at": returned_at,
                        "updated_at": now,
                    }
                },
            )


async def _refresh(database: AsyncDatabase, scope: dict) -> None:
    """Bring checkouts in `scope` up to date before reading them: expiries and overdue returns."""
    # Independent (unanswered vs accepted checkouts), so both go to the database at once.
    await asyncio.gather(close_expired(database), return_overdue(database, scope))


async def _open_count(database: AsyncDatabase, field: str, value: str) -> int:
    return await database.checkouts.count_documents({field: value, "open": True})


async def check_out(database: AsyncDatabase, *, reader_id: str, book_id: str, message: str) -> dict:
    """Check out a book with a message. Raises CheckoutRefused if a rule stops it."""
    await _refresh(database, {"$or": [{"reader_id": reader_id}, {"book_id": book_id}]})
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


async def get_checkout(database: AsyncDatabase, checkout_id: str) -> dict | None:
    """The checkout by id, whoever is asking. Only for the app acting on its own, like messaging's notes;
    anything done for a member goes through `get_checkout_for`."""
    await _refresh(database, {"_id": checkout_id})
    return await database.checkouts.find_one({"_id": checkout_id})


async def get_checkout_for(database: AsyncDatabase, checkout_id: str, user_id: str) -> dict | None:
    """The checkout if this user is its reader or author, else None. For messaging and meetings."""
    await _refresh(database, {"_id": checkout_id})
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
    await _refresh(database, {"reader_id": reader_id})
    cursor = database.checkouts.find({"reader_id": reader_id}).sort(NEWEST_FIRST).limit(LIST_LIMIT)
    return await cursor.to_list()


async def open_checkouts_of_author(database: AsyncDatabase, author_id: str) -> list[dict]:
    """Open checkouts of this member's book, newest first."""
    await _refresh(database, {"author_id": author_id})
    cursor = database.checkouts.find({"author_id": author_id, "open": True}).sort(NEWEST_FIRST)
    return await cursor.limit(LIST_LIMIT).to_list()


async def checkouts_page_of(database: AsyncDatabase, user_id: str) -> tuple[list[dict], list[dict]]:
    """`checkouts_of_reader` and `open_checkouts_of_author` together, for the Checkouts page: one refresh,
    then both lists read at once."""
    await _refresh(database, {"$or": [{"reader_id": user_id}, {"author_id": user_id}]})
    reading = database.checkouts.find({"reader_id": user_id}).sort(NEWEST_FIRST).limit(LIST_LIMIT)
    lending = (
        database.checkouts.find({"author_id": user_id, "open": True}).sort(NEWEST_FIRST).limit(LIST_LIMIT)
    )
    reading_list, lending_list = await asyncio.gather(reading.to_list(), lending.to_list())
    return reading_list, lending_list


async def fully_checked_out(database: AsyncDatabase, books: list[dict]) -> set[str]:
    """The ids of the books whose copies are all out. Each book needs its `_id` and `copies`.

    For the shelf: a book with no copies left quietly leaves it (docs/trove.md §6). Never show the
    result to a reader as a label or a count.
    """
    await _refresh(database, {"book_id": {"$in": [book["_id"] for book in books]}})
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


async def answer_did_you_meet(database: AsyncDatabase, checkout_id: str, user_id: str, answer: str) -> dict:
    """Record this member's private answer to "Did you meet?" (docs/trove.md §8).

    The first "met" or "no" from either person returns the copy. "Not yet" keeps the checkout open to
    reschedule. After the return, the other person can still give their own final answer once.
    Raises CheckoutRefused if it can't be answered (yet). Returns the updated checkout.
    """
    checkout = await get_checkout_for(database, checkout_id, user_id)
    if checkout is None or checkout["status"] not in (ACCEPTED, RETURNED):
        raise CheckoutRefused(404, "We couldn't find that checkout.")
    now = datetime.now(UTC)
    if checkout["status"] == ACCEPTED and now < await question_due_at(database, checkout):
        raise CheckoutRefused(409, "You can answer once the meeting time has passed.")
    key = f"answers.{_key(user_id)}"
    entry = {"answer": answer, "at": now}

    if checkout["status"] == ACCEPTED:
        changes: dict = {key: entry, "updated_at": now}
        if answer in FINAL_ANSWERS:
            changes |= {"status": RETURNED, "open": False, "returned_by": "answer", "returned_at": now}
        # Only while still accepted, so two first answers at the same moment can't both return it.
        updated = await database.checkouts.find_one_and_update(
            {"_id": checkout_id, "status": ACCEPTED},
            {"$set": changes},
            return_document=ReturnDocument.AFTER,
        )
        if updated is None:  # the other person's answer returned it a moment ago
            return await answer_did_you_meet(database, checkout_id, user_id, answer)
    else:
        if answer == NOT_YET:
            raise CheckoutRefused(409, "This reading is over, so there's nothing to reschedule.")
        # One final answer each after the return; "not yet" from before can still become final.
        updated = await database.checkouts.find_one_and_update(
            {"_id": checkout_id, "status": RETURNED, f"{key}.answer": {"$nin": list(FINAL_ANSWERS)}},
            {"$set": {key: entry, "updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
        if updated is None:
            raise CheckoutRefused(409, "You've already answered.")

    if updated["status"] == RETURNED:
        await recompute_met(database, checkout_id)
        updated = await database.checkouts.find_one({"_id": checkout_id}) or updated
    return updated


async def recompute_met(database: AsyncDatabase, checkout_id: str) -> None:
    """Set `met` (a Past meet, kept so Past meets are one query) from the answers stored right now.

    Worked out by the database in one update, so when both people answer at the same moment the flag
    always matches the answers, whichever lands last: a "met" and no "no" (`is_past_meet`).
    """
    answers = {
        "$map": {
            "input": {"$objectToArray": {"$ifNull": ["$answers", {}]}},
            "as": "entry",
            "in": "$$entry.v.answer",
        }
    }
    await database.checkouts.update_one(
        {"_id": checkout_id, "status": RETURNED},
        [
            {
                "$set": {
                    "met": {
                        "$let": {
                            "vars": {"given": answers},
                            "in": {
                                "$and": [{"$in": [MET, "$$given"]}, {"$not": [{"$in": [DIDNT, "$$given"]}]}]
                            },
                        }
                    }
                }
            }
        ],
    )


def my_answer(checkout: dict, user_id: str) -> str | None:
    """This member's own answer to "Did you meet?", if any. Never show it to the other person."""
    return ((checkout.get("answers") or {}).get(user_id) or {}).get("answer")


async def past_meet_checkouts(database: AsyncDatabase, user_id: str) -> list[dict]:
    """The returned checkouts that are Past meets for this member, as reader or author, newest first."""
    mine = {"$or": [{"reader_id": user_id}, {"author_id": user_id}]}
    await _refresh(database, mine)
    cursor = database.checkouts.find({**mine, "status": RETURNED, "met": True}).sort(
        [("returned_at", DESCENDING), ("_id", DESCENDING)]
    )
    return await cursor.limit(LIST_LIMIT).to_list()


async def past_meets(database: AsyncDatabase, user_id: str) -> list[dict]:
    """Contract (docs/plan.md): the people this member has met, newest first.

    Each is `{"checkout_id", "other_id", "other_name", "book_id"}`, where `book_id` is the book that was
    checked out. For discovery (D4: recommend a book to someone you've met).
    """
    checkouts = await past_meet_checkouts(database, user_id)
    others = [c["author_id"] if c["reader_id"] == user_id else c["reader_id"] for c in checkouts]
    names = await full_names_of(database, list(set(others)))
    return [
        {
            "checkout_id": checkout["_id"],
            "other_id": other,
            "other_name": names.get(other, ""),
            "book_id": checkout["book_id"],
        }
        for checkout, other in zip(checkouts, others, strict=True)
    ]


@on_account_deleted
async def remove_checkouts_of(database: AsyncDatabase, user_id: str) -> None:
    """When a member deletes their account, their checkouts go too, both ways. That frees the copies
    they had taken, and their requests disappear from authors' lists."""
    await database.checkouts.delete_many({"$or": [{"reader_id": user_id}, {"author_id": user_id}]})


async def reader_book_of(database: AsyncDatabase, reader_id: str) -> dict | None:
    """The reader's own book, if it's on the shelf, for the author to look at."""
    book = await get_book_of(database, reader_id)
    return await get_public_book(database, book["_id"]) if book else None
