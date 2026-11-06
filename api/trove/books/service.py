"""The `books` collection and the contract functions other features call (docs/plan.md, "Contracts")."""

import base64
import binascii
from datetime import datetime

from pymongo import DESCENDING
from pymongo.asynchronous.database import AsyncDatabase

ON_SHELF = "on_shelf"
# Everything a reader-facing caller may receive. Anything else on the document (and anything added
# to it later) stays private unless it is listed here.
PUBLIC_FIELDS = {
    "_id": 1,
    "author_id": 1,
    "title": 1,
    "author_name": 1,
    "cover_style": 1,
    "blurb": 1,
    "chapters.id": 1,
    "chapters.title": 1,
    "chapters.summary": 1,
    "copies": 1,
    "is_sample": 1,
    "published_at": 1,
}
SHELF_SORT = [("published_at", DESCENDING), ("_id", DESCENDING)]


async def ensure_indexes(database: AsyncDatabase) -> None:
    # One book per member (docs/trove.md §3), even if two requests create one at the same moment.
    await database.books.create_index("author_id", unique=True, name="books_author_unique")
    await database.books.create_index([("status", 1), *SHELF_SORT], name="books_shelf_newest_first")


async def get_public_book(database: AsyncDatabase, book_id: str) -> dict | None:
    """The book as readers see it, or None if it isn't on the shelf.

    Includes `author_id` and `copies` for other features' own logic. Neither may be shown to a reader.
    """
    return await database.books.find_one({"_id": book_id, "status": ON_SHELF}, PUBLIC_FIELDS)


async def get_book_of(database: AsyncDatabase, user_id: str) -> dict | None:
    """That member's own book, whatever its status, or None if they don't have one yet."""
    return await database.books.find_one({"author_id": user_id})


async def list_shelf(database: AsyncDatabase, *, limit: int, after: str | None = None) -> list[dict]:
    """Books on the shelf, newest first, in the same shape as `get_public_book`.

    `after` is `shelf_cursor(...)` of the last book of the previous page. Raises ValueError if it is malformed.
    """
    query: dict = {"status": ON_SHELF}
    if after is not None:
        published_at, book_id = _decode_cursor(after)
        query["$or"] = [
            {"published_at": {"$lt": published_at}},
            {"published_at": published_at, "_id": {"$lt": book_id}},
        ]
    cursor = database.books.find(query, PUBLIC_FIELDS).sort(SHELF_SORT).limit(limit)
    return await cursor.to_list()


def shelf_cursor(book: dict) -> str:
    """An opaque position on the shelf, for `list_shelf(after=...)`."""
    raw = f"{book['published_at'].isoformat()}|{book['_id']}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[datetime, str]:
    try:
        published_at, book_id = base64.urlsafe_b64decode(cursor.encode()).decode().split("|", 1)
        return datetime.fromisoformat(published_at), book_id
    except (binascii.Error, UnicodeDecodeError, ValueError):
        raise ValueError("Invalid shelf cursor.") from None
