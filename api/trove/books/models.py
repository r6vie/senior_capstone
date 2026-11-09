from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# Books are plain white for now; the style is stored so covers can differ later without a migration.
CoverStyle = Literal["cover-1", "cover-2", "cover-3", "cover-4", "cover-5", "cover-6", "cover-7", "cover-8"]
BookStatus = Literal["draft", "on_shelf"]
DEFAULT_COPIES = 3


class Chapter(BaseModel):
    id: str
    title: str
    summary: str


class AuthorChapter(Chapter):
    # The member's own interview words this chapter is grounded in. Only the author sees them.
    quotes: list[str]
    # In review, a rewrite can be taken back (POST /interview/book/chapters/{id}/restore).
    has_previous: bool = False


class BookCard(BaseModel):
    """A book as it appears on the shelf."""

    id: str
    title: str
    author_name: str
    cover_style: CoverStyle
    blurb: str | None


class PublicBookResponse(BookCard):
    """A book as readers see it: the author's full name, but no contacts, copy counts or grounding quotes."""

    chapters: list[Chapter]


class ShelfPage(BaseModel):
    books: list[BookCard]
    # Pass as `after` to get the next page; null on the last page.
    next: str | None


class MyBookResponse(BaseModel):
    """The signed-in member's own book, as its author sees it."""

    id: str
    title: str
    author_name: str
    cover_style: CoverStyle
    blurb: str | None
    chapters: list[AuthorChapter]
    copies: int
    status: BookStatus
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime
    # The last applied revision can be taken back now (POST /interview/book/undo). False while questions
    # or changes are open on the book, even if a revision is there to undo.
    can_undo: bool = False
    # When the last revision was applied, for "Your book was updated on Nov 9." Null once undone.
    revised_at: datetime | None = None
    # In review, a rewritten back cover can be taken back (POST /interview/book/blurb/restore).
    has_previous_blurb: bool = False
    # After a rewrite: it couldn't be told better from what the member said, so nothing changed.
    rewrite_unchanged: bool = False
