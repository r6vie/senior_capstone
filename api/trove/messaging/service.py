"""The message rules (docs/trove.md §6) and the contract functions other features call.

`messages` holds what people wrote and the app's notes, one document each. `message_threads` holds one
document per checkout (its `_id` is the checkout id) with what the thread needs to remember: who is
on it, when each person last read it, the latest message each person hasn't written themselves, and
when each was last emailed.
"""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import full_names_of, on_account_deleted
from trove.checkouts.service import ACCEPTED, get_checkout, get_checkout_for
from trove.notifications.service import notify_new_message

RATE_LIMIT = 30  # messages per person per thread...
RATE_WINDOW = timedelta(hours=1)  # ...in this long
EMAIL_GAP = timedelta(minutes=10)  # at most one new-message email per thread per person in this long
MAX_NOTE = 300
THREAD_LIMIT = 500  # messages returned for one thread; threads are short in practice

# A thread can be read while the checkout is in one of these states, and written to in the first.
# When C4 adds "Did you meet?", the returned state belongs in READABLE only: read-only history.
WRITABLE = {ACCEPTED}
READABLE = {ACCEPTED}


class MessageRefused(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


# Missing, someone else's, or not accepted yet all look the same, so nothing leaks about a checkout.
NOT_FOUND = MessageRefused(404, "We couldn't find that conversation.")


async def ensure_indexes(database: AsyncDatabase) -> None:
    await database.messages.create_index(
        [("checkout_id", ASCENDING), ("sent_at", ASCENDING), ("_id", ASCENDING)], name="messages_thread"
    )
    await database.messages.create_index("participants", name="messages_participants")
    await database.message_threads.create_index("participants", name="threads_participants")


def as_utc(value: datetime) -> datetime:
    # MongoDB hands back naive datetimes; they are always UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def other_person(checkout: dict, user_id: str) -> str:
    return checkout["author_id"] if user_id == checkout["reader_id"] else checkout["reader_id"]


async def readable_checkout(database: AsyncDatabase, checkout_id: str, user_id: str) -> dict:
    """The checkout, if this member is on it and its thread is open or kept as history. Else 404."""
    checkout = await get_checkout_for(database, checkout_id, user_id)
    if checkout is None or checkout["status"] not in READABLE:
        raise NOT_FOUND
    return checkout


def can_write(checkout: dict) -> bool:
    return checkout["status"] in WRITABLE


async def messages_of(database: AsyncDatabase, checkout_id: str) -> list[dict]:
    """The thread's latest messages and notes (up to THREAD_LIMIT), oldest first.

    The checkout note isn't stored here. Fetched newest first, so a very long thread drops its oldest
    messages rather than its newest.
    """
    cursor = database.messages.find({"checkout_id": checkout_id}).sort(
        [("sent_at", DESCENDING), ("_id", DESCENDING)]
    )
    return list(reversed(await cursor.limit(THREAD_LIMIT).to_list()))


async def _add(database: AsyncDatabase, checkout: dict, *, sender_id: str | None, text: str) -> dict:
    """Store a message (or, with no sender, an app note) and mark it new for whoever didn't write it."""
    now = datetime.now(UTC)
    participants = [checkout["reader_id"], checkout["author_id"]]
    message = {
        "_id": str(uuid4()),
        "checkout_id": checkout["_id"],
        "participants": participants,
        "sender_id": sender_id,
        "text": text,
        "sent_at": now,
    }
    await database.messages.insert_one(message)
    await database.message_threads.update_one(
        {"_id": checkout["_id"]},
        {
            "$set": {f"incoming.{person}": now for person in participants if person != sender_id},
            "$setOnInsert": {"participants": participants},
        },
        upsert=True,
    )
    return message


async def send(database: AsyncDatabase, checkout: dict, sender_id: str, text: str) -> dict:
    """One of the two people writes in the thread. Raises MessageRefused if a rule stops it."""
    if not can_write(checkout):
        raise MessageRefused(409, "This conversation is closed. You can still read it.")
    since = datetime.now(UTC) - RATE_WINDOW
    recent = await database.messages.count_documents(
        {"checkout_id": checkout["_id"], "sender_id": sender_id, "sent_at": {"$gt": since}}
    )
    if recent >= RATE_LIMIT:
        raise MessageRefused(429, "You've sent a lot of messages in the last hour. Please wait a little.")
    message = await _add(database, checkout, sender_id=sender_id, text=text)
    # Reading your own thread is implied by writing in it.
    await mark_read(database, checkout["_id"], sender_id)
    return message


async def post_note(database: AsyncDatabase, checkout_id: str, text: str) -> dict | None:
    """Post a short app note into an accepted checkout's thread, such as a confirmed meeting time.

    For other features (docs/plan.md, "Contracts"). Notes show differently from people's messages and
    count as new for both people. Returns the note, or None (posting nothing) if the thread isn't open.
    To email both people about it, pass the note to `email_new_message` as a background task.
    """
    text = " ".join(text.split())[:MAX_NOTE]
    checkout = await get_checkout(database, checkout_id) if text else None
    if checkout is None or not can_write(checkout):
        return None
    return await _add(database, checkout, sender_id=None, text=text)


async def email_new_message(database: AsyncDatabase, message: dict) -> None:
    """Email whoever didn't write `message`, at most once per 10 minutes per thread for each person.

    Run it as a background task, so email trouble never fails the request. Respects the email switch.
    """
    checkout = await get_checkout(database, message["checkout_id"])
    if checkout is None:
        return
    sender_id = message["sender_id"]
    sender_name = (await full_names_of(database, [sender_id])).get(sender_id, "") if sender_id else ""
    for person in (checkout["reader_id"], checkout["author_id"]):
        if person == sender_id or not await claim_email_slot(database, checkout["_id"], person):
            continue
        await notify_new_message(
            database,
            message_id=message["_id"],
            checkout_id=checkout["_id"],
            recipient_id=person,
            sender_name=sender_name,
            book_title=checkout["book_title"],
        )


async def mark_read(database: AsyncDatabase, checkout_id: str, user_id: str) -> None:
    await database.message_threads.update_one(
        {"_id": checkout_id, "participants": user_id},
        {"$set": {f"read.{user_id}": datetime.now(UTC)}},
    )


async def checkouts_with_new_messages(
    database: AsyncDatabase, user_id: str, checkout_ids: list[str]
) -> set[str]:
    """The checkouts among `checkout_ids` with a message or note this member hasn't read yet.

    For the private "New message" marker on the Checkouts page. Never show it to the other person,
    and never as a count.
    """
    threads = database.message_threads.find(
        {"_id": {"$in": checkout_ids}, "participants": user_id}, {"incoming": 1, "read": 1}
    )
    unread = set()
    async for thread in threads:
        incoming = (thread.get("incoming") or {}).get(user_id)
        read = (thread.get("read") or {}).get(user_id)
        if incoming and (read is None or as_utc(incoming) > as_utc(read)):
            unread.add(thread["_id"])
    return unread


async def claim_email_slot(database: AsyncDatabase, checkout_id: str, user_id: str) -> bool:
    """True, and remembered, if this person may be emailed about this thread now (10-minute gap).

    Claimed in one atomic update, so two messages at the same moment can't both send an email.
    """
    now = datetime.now(UTC)
    claimed = await database.message_threads.find_one_and_update(
        {
            "_id": checkout_id,
            "participants": user_id,
            "$or": [
                {f"emailed.{user_id}": {"$exists": False}},
                {f"emailed.{user_id}": {"$lte": now - EMAIL_GAP}},
            ],
        },
        {"$set": {f"emailed.{user_id}": now}},
        return_document=ReturnDocument.AFTER,
    )
    return claimed is not None


@on_account_deleted
async def remove_messages_of(database: AsyncDatabase, user_id: str) -> None:
    """When a member deletes their account, every thread they were in goes too, for both people."""
    await database.messages.delete_many({"participants": user_id})
    await database.message_threads.delete_many({"participants": user_id})
