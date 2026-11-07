"""The `books` collection and the contract functions other features call (docs/plan.md, "Contracts")."""

import base64
import binascii
from datetime import UTC, datetime
from uuid import uuid4

from pymongo import DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from trove.auth.service import full_names_of
from trove.books.models import DEFAULT_COPIES, MyBookResponse

ON_SHELF = "on_shelf"
DRAFT = "draft"
# Books have 3 to 5 chapters (docs/trove.md §4), so removing one stops at three.
MIN_CHAPTERS = 3
# Covers are plain white until a cover direction is chosen.
WHITE_COVER = "cover-1"
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
    "published_at": 1,
}
SHELF_SORT = [("published_at", DESCENDING), ("_id", DESCENDING)]


async def ensure_indexes(database: AsyncDatabase) -> None:
    # One book per member (docs/trove.md §3), even if two requests create one at the same moment.
    await database.books.create_index("author_id", unique=True, name="books_author_unique")
    await database.books.create_index([("status", 1), *SHELF_SORT], name="books_shelf_newest_first")


async def get_public_book(database: AsyncDatabase, book_id: str) -> dict | None:
    """The book as readers see it, or None if it isn't on the shelf.

    `author_name` is the author's full name. Includes `author_id` and `copies` for other features' own
    logic; neither may be shown to a reader. Never includes employer, title, links or contact details.
    """
    return await _named(
        database, await database.books.find_one({"_id": book_id, "status": ON_SHELF}, PUBLIC_FIELDS)
    )


async def get_book_of(database: AsyncDatabase, user_id: str) -> dict | None:
    """That member's own book, whatever its status, or None if they don't have one yet."""
    return await _named(database, await database.books.find_one({"author_id": user_id}))


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
    return await with_author_names(database, await cursor.to_list())


async def with_author_names(database: AsyncDatabase, books: list[dict]) -> list[dict]:
    """Set each book's `author_name` to its author's current full name from their account.

    The name stored on the book is kept only where there's no account behind it (sample books).
    """
    names = await full_names_of(database, list({book["author_id"] for book in books}))
    for book in books:
        book["author_name"] = names.get(book["author_id"]) or book.get("author_name", "")
    return books


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


class BookExists(Exception):
    """The member already has a book; there is one per member."""


def my_book_view(book: dict) -> MyBookResponse:
    """A member's own book as its author sees it, including the grounding quotes and copies."""
    return MyBookResponse.model_validate({**book, "id": book["_id"], "blurb": book.get("blurb")})


async def create_draft_book(
    database: AsyncDatabase,
    *,
    author_id: str,
    title: str,
    chapters: list[dict],
    blurb: str | None = None,
) -> dict:
    """Save a finished interview's book as a draft only its author sees. Raises BookExists."""
    now = datetime.now(UTC)
    book = {
        "_id": str(uuid4()),
        "author_id": author_id,
        # Shown from the account when the book is read; stored as a fallback.
        "author_name": (await full_names_of(database, [author_id])).get(author_id, ""),
        "title": title,
        "cover_style": WHITE_COVER,
        "blurb": blurb,
        "chapters": chapters,
        "copies": DEFAULT_COPIES,
        "status": DRAFT,
        "is_sample": False,
        "published_at": None,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await database.books.insert_one(book)
    except DuplicateKeyError:
        raise BookExists() from None
    return book


async def _named(database: AsyncDatabase, book: dict | None) -> dict | None:
    return (await with_author_names(database, [book]))[0] if book else None


async def remove_chapter(
    database: AsyncDatabase, author_id: str, chapter_id: str, *, blurb: str | None = None
) -> dict | None:
    """Remove a chapter from the author's draft, if more than MIN_CHAPTERS remain. None if it can't.

    `blurb`, if given, replaces the blurb in the same update, since it should match what's left.
    """
    changes: dict = {"updated_at": datetime.now(UTC)}
    if blurb is not None:
        changes["blurb"] = blurb
    book = await database.books.find_one_and_update(
        {
            "author_id": author_id,
            "status": DRAFT,
            "chapters.id": chapter_id,
            # Checked in the same update, so two quick removals can't go below the minimum.
            f"chapters.{MIN_CHAPTERS}": {"$exists": True},
        },
        {"$pull": {"chapters": {"id": chapter_id}}, "$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    return await _named(database, book)


async def replace_chapter(database: AsyncDatabase, author_id: str, chapter: dict) -> dict | None:
    """Swap in a rewritten chapter with the same id, in the author's draft. None if there is none."""
    book = await database.books.find_one_and_update(
        {"author_id": author_id, "status": DRAFT, "chapters.id": chapter["id"]},
        {"$set": {"chapters.$": chapter, "updated_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER,
    )
    return await _named(database, book)


async def put_on_shelf(database: AsyncDatabase, author_id: str) -> dict | None:
    """Publish the author's draft. None if they have no draft."""
    now = datetime.now(UTC)
    book = await database.books.find_one_and_update(
        {"author_id": author_id, "status": DRAFT},
        {"$set": {"status": ON_SHELF, "published_at": now, "updated_at": now}},
        return_document=ReturnDocument.AFTER,
    )
    return await _named(database, book)
