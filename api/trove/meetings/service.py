"""Arranging one meeting per accepted checkout (docs/trove.md §9.7).

Each person offers a few start times; the app shows where they overlap; either person confirms one.
Only the two people on the checkout can see or change anything. The meeting is kept in the
`meetings` collection, one document per checkout (its `_id` is the checkout id).
"""

from datetime import UTC, datetime, timedelta

from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import on_account_deleted
from trove.checkouts.service import ACCEPTED, get_checkout_for
from trove.meetings.models import SLOT_MINUTES

REMINDER_HOURS = 24  # the reminder goes out when the meeting is this close


class MeetingRefused(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


NOT_FOUND = MeetingRefused(404, "Checkout not found.")


async def accepted_checkout(database: AsyncDatabase, checkout_id: str, user_id: str) -> dict:
    """The checkout, if this member is on it and the author said yes. Anything else looks the same."""
    checkout = await get_checkout_for(database, checkout_id, user_id)
    if checkout is None or checkout["status"] != ACCEPTED:
        raise NOT_FOUND
    return checkout


def _offered(meeting: dict | None, user_id: str) -> list[datetime]:
    return [_utc(t) for t in (meeting or {}).get("times", {}).get(user_id, [])]


def _utc(value: datetime) -> datetime:
    # MongoDB hands back naive datetimes; they are always UTC.
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def other_person(checkout: dict, user_id: str) -> str:
    return checkout["author_id"] if user_id == checkout["reader_id"] else checkout["reader_id"]


def view_parts(meeting: dict | None, checkout: dict, user_id: str, now: datetime) -> dict:
    mine = _offered(meeting, user_id)
    theirs = _offered(meeting, other_person(checkout, user_id))
    return {
        "my_times": [t for t in mine if t > now],
        "their_times": [t for t in theirs if t > now],
        "shared_times": sorted(t for t in set(mine) & set(theirs) if t > now),
        "start": _utc(meeting["start"]) if meeting and meeting.get("start") else None,
        "video_link": (meeting or {}).get("video_link"),
        "place_note": (meeting or {}).get("place_note"),
    }


@on_account_deleted
async def remove_meetings_of(database: AsyncDatabase, user_id: str) -> None:
    """When a member deletes their account, the times they offered, the link and the meeting go too."""
    await database.meetings.delete_many({"$or": [{"reader_id": user_id}, {"author_id": user_id}]})


async def get_meeting(database: AsyncDatabase, checkout_id: str) -> dict | None:
    return await database.meetings.find_one({"_id": checkout_id})


async def offer_times(
    database: AsyncDatabase, checkout: dict, user_id: str, times: list[datetime], now: datetime
) -> dict:
    if any(t <= now for t in times):
        raise MeetingRefused(422, "Pick times that haven't passed yet.")
    return await database.meetings.find_one_and_update(
        {"_id": checkout["_id"]},
        {
            "$set": {f"times.{user_id}": times, "updated_at": now},
            "$setOnInsert": {
                "created_at": now,
                "reader_id": checkout["reader_id"],
                "author_id": checkout["author_id"],
                "book_title": checkout["book_title"],
            },
        },
        upsert=True,
        return_document=True,
    )


async def confirm(
    database: AsyncDatabase, checkout: dict, user_id: str, start: datetime, now: datetime
) -> dict:
    meeting = await get_meeting(database, checkout["_id"])
    offered = set(_offered(meeting, checkout["reader_id"])) | set(_offered(meeting, checkout["author_id"]))
    if start <= now or start not in offered:
        raise MeetingRefused(422, "Choose one of the times you or they offered.")
    return await database.meetings.find_one_and_update(
        {"_id": checkout["_id"]},
        {"$set": {"start": start, "confirmed_by": user_id, "updated_at": now}},
        return_document=True,
    )


async def set_details(
    database: AsyncDatabase, checkout: dict, video_link: str | None, place_note: str | None, now: datetime
) -> dict:
    return await database.meetings.find_one_and_update(
        {"_id": checkout["_id"]},
        {
            "$set": {"video_link": video_link, "place_note": place_note, "updated_at": now},
            "$setOnInsert": {
                "created_at": now,
                "reader_id": checkout["reader_id"],
                "author_id": checkout["author_id"],
                "book_title": checkout["book_title"],
                "times": {},
            },
        },
        upsert=True,
        return_document=True,
    )


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> list[str]:
    """Calendar files wrap lines at 75 bytes; continuation lines start with a space."""
    encoded, parts = line.encode(), []
    while len(encoded) > 75:
        cut = 75
        while encoded[cut] & 0xC0 == 0x80:  # don't split a character
            cut -= 1
        parts.append(encoded[:cut].decode())
        encoded = b" " + encoded[cut:]
    parts.append(encoded.decode())
    return parts


def calendar_invite(checkout: dict, meeting: dict, other_name: str) -> str:
    """An .ics file for the confirmed meeting."""
    start = _utc(meeting["start"])
    stamp = "%Y%m%dT%H%M%SZ"
    details = [f"Trove: {checkout['book_title']}"]
    if meeting.get("video_link"):
        details.append(f"Video link: {meeting['video_link']}")
    if meeting.get("place_note"):
        details.append(f"Where: {meeting['place_note']}")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Trove//Meeting//EN",
        "BEGIN:VEVENT",
        f"UID:{checkout['_id']}@trove",
        f"DTSTAMP:{_utc(meeting['updated_at']).strftime(stamp)}",
        f"DTSTART:{start.strftime(stamp)}",
        f"DTEND:{(start + timedelta(minutes=SLOT_MINUTES)).strftime(stamp)}",
        f"SUMMARY:{_escape(f'Trove: {checkout["book_title"]} with {other_name}')}",
        f"DESCRIPTION:{_escape(chr(10).join(details))}",
    ]
    where = meeting.get("video_link") or meeting.get("place_note")
    if where:
        lines.append(f"LOCATION:{_escape(where)}")
    lines += ["END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(part for line in lines for part in _fold(line)) + "\r\n"


async def due_reminders(database: AsyncDatabase, now: datetime) -> list[dict]:
    """Confirmed meetings that start within the next REMINDER_HOURS."""
    cursor = database.meetings.find({"start": {"$gt": now, "$lte": now + timedelta(hours=REMINDER_HOURS)}})
    return [meeting async for meeting in cursor]
