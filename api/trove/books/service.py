"""The `books` collection and the contract functions other features call (docs/plan.md, "Contracts")."""

import asyncio
import base64
import binascii
import re
from datetime import UTC, datetime
from uuid import uuid4

from pymongo import DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from trove.auth.service import full_names_of, on_account_deleted
from trove.books.models import DEFAULT_COPIES, MyBookResponse

ON_SHELF = "on_shelf"
# Taken down by its author: not on the shelf, not openable by readers, still theirs to work on.
OFF_SHELF = "off_shelf"
PUBLISHED = (ON_SHELF, OFF_SHELF)
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


async def shelf_books_of(database: AsyncDatabase, author_ids: list[str]) -> dict[str, dict]:
    """Each author's book if it's on the shelf, by author id: `_id` and `title` only, in one database trip."""
    books = database.books.find(
        {"author_id": {"$in": author_ids}, "status": ON_SHELF}, {"title": 1, "author_id": 1}
    )
    return {book["author_id"]: book async for book in books}


async def list_shelf(database: AsyncDatabase, *, limit: int, after: str | None = None) -> list[dict]:
    """Books on the shelf, newest first, in the same shape as `get_public_book`.

    A book whose copies are all out quietly leaves the shelf until one comes back (docs/trove.md §6).
    It still opens from a direct link. `after` is `shelf_cursor(...)` of the last book of the
    previous page. Raises ValueError if it is malformed.
    """
    # Imported here because checkouts already imports this module.
    from trove.checkouts.service import fully_checked_out

    shelf: list[dict] = []
    # Hidden books would leave a page short, so keep reading until it's full or the shelf runs out.
    while len(shelf) < limit:
        query: dict = {"status": ON_SHELF}
        if after is not None:
            published_at, book_id = _decode_cursor(after)
            query["$or"] = [
                {"published_at": {"$lt": published_at}},
                {"published_at": published_at, "_id": {"$lt": book_id}},
            ]
        batch = await database.books.find(query, PUBLIC_FIELDS).sort(SHELF_SORT).limit(limit).to_list()
        if not batch:
            break
        # Which copies are out, and the authors' names, read at the same time.
        lent, _ = await asyncio.gather(fully_checked_out(database, batch), with_author_names(database, batch))
        shelf.extend(book for book in batch if book["_id"] not in lent)
        after = shelf_cursor(batch[-1])
    return shelf[:limit]


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


def my_book_view(book: dict, *, undoable: bool = True) -> MyBookResponse:
    """A member's own book as its author sees it, including the grounding quotes and copies."""
    return MyBookResponse.model_validate(
        {
            **book,
            "id": book["_id"],
            "blurb": book.get("blurb"),
            "chapters": book["chapters"],
            "can_undo": undoable and bool(book.get("previous_version")),
            "revised_at": (book.get("previous_version") or {}).get("applied_at"),
        }
    )


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


def blurb_edited(book: dict) -> bool:
    """Whether the member wrote this back cover themselves. Their words are never rewritten for them.
    Books from before the flag count as unedited."""
    return bool(book.get("blurb_edited"))


async def _set_unedited_blurb(database: AsyncDatabase, book: dict | None, blurb: str | None) -> dict | None:
    """Put the Librarian's new back cover on `book`, unless the member has written their own since.
    Checked in the update itself, so an edit saved meanwhile is never overwritten."""
    if book is None or blurb is None:
        return book
    updated = await database.books.find_one_and_update(
        {"_id": book["_id"], "blurb_edited": {"$ne": True}},
        {"$set": {"blurb": blurb}},
        return_document=ReturnDocument.AFTER,
    )
    # Not updated: the member's own words are there now, so show those, not the copy read before.
    return updated or await database.books.find_one({"_id": book["_id"]}) or book


async def remove_chapter(
    database: AsyncDatabase, author_id: str, chapter_id: str, *, blurb: str | None = None
) -> dict | None:
    """Remove a chapter from the author's draft, if more than MIN_CHAPTERS remain. None if it can't.

    `blurb`, if given, replaces the blurb, since it should match what's left, unless the member wrote
    their own back cover.
    """
    changes: dict = {"updated_at": datetime.now(UTC)}
    book = await database.books.find_one_and_update(
        {
            "author_id": author_id,
            "status": DRAFT,
            "chapters.id": chapter_id,
            # Checked in the same update, so two quick removals can't go below the minimum.
            f"chapters.{MIN_CHAPTERS}": {"$exists": True},
        },
        # The old back cover described a chapter that's gone.
        {"$pull": {"chapters": {"id": chapter_id}}, "$set": changes, "$unset": {"previous_blurb": ""}},
        return_document=ReturnDocument.AFTER,
    )
    return await _named(database, await _set_unedited_blurb(database, book, blurb))


async def retitle_draft(
    database: AsyncDatabase, author_id: str, *, title: str, chapters: list[dict], blurb: str | None
) -> dict | None:
    """Replace the author's draft with one finished for another title, keeping a back cover the member
    wrote themselves. None if they have no draft."""
    book = await database.books.find_one_and_update(
        {"author_id": author_id, "status": DRAFT},
        {
            "$set": {"title": title, "chapters": chapters, "updated_at": datetime.now(UTC)},
            # The old back cover described the old book.
            "$unset": {"previous_blurb": ""},
        },
        return_document=ReturnDocument.AFTER,
    )
    return await _named(database, await _set_unedited_blurb(database, book, blurb))


def revised_chapters(
    chapters: list[dict], *, improved: list[dict], added: list[dict], removed: list[str]
) -> list[dict]:
    """The chapters after a revision. `improved` replace the ones with their ids, in place. `added`
    each go where their `position` says (1 is first), or at the end without one."""
    replacements = {chapter["id"]: chapter for chapter in improved}
    result = [
        replacements.get(chapter["id"], chapter) for chapter in chapters if chapter["id"] not in removed
    ]
    for chapter in added:
        position = chapter.get("position")
        index = len(result) if position is None else max(0, min(position - 1, len(result)))
        result.insert(index, {key: value for key, value in chapter.items() if key != "position"})
    return result


async def apply_revision(
    database: AsyncDatabase,
    author_id: str,
    *,
    improved: list[dict],
    added: list[dict],
    removed: list[str],
    blurb: str | None,
) -> dict | None:
    """Apply approved changes to the author's book on the shelf, in one update, keeping what was
    there so it can be undone. `blurb` None keeps the old one. None if there's no such book, it
    changed meanwhile, or it would fall below MIN_CHAPTERS.

    `published_at` doesn't change: the shelf isn't a feed, and a revision doesn't bump a book.
    """
    book = await database.books.find_one({"author_id": author_id, "status": {"$in": PUBLISHED}})
    if book is None:
        return None
    chapters = revised_chapters(book["chapters"], improved=improved, added=added, removed=removed)
    if len(chapters) < MIN_CHAPTERS:
        return None
    changes: dict = {
        "chapters": chapters,
        "previous_version": {
            "chapters": book["chapters"],
            "blurb": book.get("blurb"),
            "blurb_edited": blurb_edited(book),
            "applied_at": datetime.now(UTC),
        },
        "updated_at": datetime.now(UTC),
    }
    if blurb is not None:
        # The member chose the Librarian's new back cover over their own, on the changes screen.
        changes["blurb"] = blurb
        changes["blurb_edited"] = False
    updated = await database.books.find_one_and_update(
        # Only if the book hasn't changed since it was read, so two approvals can't lose one.
        {"_id": book["_id"], "status": book["status"], "updated_at": book["updated_at"]},
        {"$set": changes},
        return_document=ReturnDocument.AFTER,
    )
    return await _named(database, updated)


async def undo_revision(database: AsyncDatabase, author_id: str) -> dict | None:
    """Put back the chapters and blurb from before the last revision, in one update. None if there's
    nothing to undo. Never reader-facing: `previous_version` isn't in PUBLIC_FIELDS."""
    book = await database.books.find_one({"author_id": author_id, "status": {"$in": PUBLISHED}})
    previous = book.get("previous_version") if book else None
    if not previous:
        return None
    restored = await database.books.find_one_and_update(
        {"_id": book["_id"], "updated_at": book["updated_at"]},
        {
            "$set": {
                "chapters": previous["chapters"],
                "blurb": previous["blurb"],
                # Saved before the flag existed, a version leaves it as it is.
                "blurb_edited": previous.get("blurb_edited", blurb_edited(book)),
                # Edits can change the title too; revisions never do.
                "title": previous.get("title", book["title"]),
                "updated_at": datetime.now(UTC),
            },
            "$unset": {"previous_version": ""},
        },
        return_document=ReturnDocument.AFTER,
    )
    return await _named(database, restored)


async def put_on_shelf(database: AsyncDatabase, author_id: str) -> dict | None:
    """Publish the author's draft. None if they have no draft."""
    now = datetime.now(UTC)
    book = await database.books.find_one_and_update(
        {"author_id": author_id, "status": DRAFT},
        # Earlier versions of chapters are for the review only.
        {
            "$set": {"status": ON_SHELF, "published_at": now, "updated_at": now},
            "$unset": {"chapters.$[].previous": "", "previous_blurb": ""},
        },
        return_document=ReturnDocument.AFTER,
    )
    return await _named(database, book)


# The member's own edits (docs/review/decisions.md, rows 30 to 33).

CONTACT_REFUSED = "Contact details are shared only when you accept a checkout, so they can't go on your book."
_CONTACT = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"https?://|\bwww\.", re.IGNORECASE),
    re.compile(r"\b[\w-]+\.(?:com|org|net|edu|io|co|me|dev|app|ly|us|ai|gov|info)\b", re.IGNORECASE),
    # A phone number: ten digits or more in a run of digits and separators, or 555-0134.
    re.compile(r"(?:\+?\d[\s().-]*){10,}"),
    re.compile(r"\b\d{3}[-.]\d{4}\b"),
]


class EditRefused(Exception):
    """The edit can't be saved. `detail` is said to the member as it is."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail


def check_text(*texts: str | None) -> None:
    """Refuse contact details: they're shared only on an accepted checkout (CLAUDE.md)."""
    if any(text and pattern.search(text) for text in texts for pattern in _CONTACT):
        raise EditRefused(422, CONTACT_REFUSED)


def _snapshot(book: dict) -> dict:
    """What undo puts back. `kind` says an edit made it, so undo doesn't treat it as a declined change."""
    return {
        "chapters": book["chapters"],
        "blurb": book.get("blurb"),
        "blurb_edited": blurb_edited(book),
        "title": book["title"],
        "applied_at": datetime.now(UTC),
        "kind": "edit",
    }


async def _own_book(database: AsyncDatabase, author_id: str) -> dict:
    book = await database.books.find_one({"author_id": author_id})
    if book is None:
        raise EditRefused(404, "You don't have a book yet.")
    return book


async def _save(database: AsyncDatabase, book: dict, changes: dict) -> dict:
    updated = await database.books.find_one_and_update(
        # Only if nothing else changed it since it was read, so an edit can't undo another change.
        {"_id": book["_id"], "updated_at": book["updated_at"]},
        {"$set": {**changes, "updated_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise EditRefused(409, "Your book changed while you were editing. Look at it again, then save.")
    return await _named(database, updated)


async def edit_book(
    database: AsyncDatabase, author_id: str, *, title: str | None = None, blurb: str | None = None
) -> dict:
    """Save the member's own title or back cover. On a published book, saved means live, and undo
    takes it back. `published_at` stays."""
    check_text(title, blurb)
    book = await _own_book(database, author_id)
    changes: dict = {}
    if title is not None:
        changes["title"] = title
    if blurb is not None:
        changes["blurb"] = blurb
        # The member's own words now: nothing the Librarian does later writes over them.
        changes["blurb_edited"] = True
    if book["status"] != DRAFT:
        changes["previous_version"] = _snapshot(book)
    return await _save(database, book, changes)


async def edit_chapter(
    database: AsyncDatabase,
    author_id: str,
    chapter_id: str,
    *,
    title: str | None = None,
    summary: str | None = None,
) -> dict:
    """Save the member's own chapter title or summary. Its quotes stay. On a published book, undo
    takes it back."""
    check_text(title, summary)
    book = await _own_book(database, author_id)
    index = next((n for n, c in enumerate(book["chapters"]) if c["id"] == chapter_id), None)
    if index is None:
        raise EditRefused(404, "That chapter isn't in your book.")
    chapter = book["chapters"][index]
    edited = {**chapter, "title": title or chapter["title"], "summary": summary or chapter["summary"]}
    changes: dict = {f"chapters.{index}": edited}
    if book["status"] != DRAFT:
        changes["previous_version"] = _snapshot(book)
    return await _save(database, book, changes)


async def take_off_shelf(database: AsyncDatabase, author_id: str) -> dict | None:
    """Take the book down: readers can't find or open it, so no new checkouts. What's already
    arranged goes ahead. None if the book isn't on the shelf."""
    return await _named(
        database,
        await database.books.find_one_and_update(
            {"author_id": author_id, "status": ON_SHELF},
            {"$set": {"status": OFF_SHELF, "updated_at": datetime.now(UTC)}},
            return_document=ReturnDocument.AFTER,
        ),
    )


async def put_back_on_shelf(database: AsyncDatabase, author_id: str) -> dict | None:
    """Put a book that was taken down back. `published_at` stays, so it returns to the same place."""
    return await _named(
        database,
        await database.books.find_one_and_update(
            {"author_id": author_id, "status": OFF_SHELF},
            {"$set": {"status": ON_SHELF, "updated_at": datetime.now(UTC)}},
            return_document=ReturnDocument.AFTER,
        ),
    )


@on_account_deleted
async def delete_books_of(database: AsyncDatabase, user_id: str) -> None:
    """Account deletion: the member's book goes, shelf and all. Safe to run twice."""
    await database.books.delete_many({"author_id": user_id})
