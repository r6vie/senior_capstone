from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from trove.core.models import NonEmptyText, RequestBody
from trove.interview.engine import MAX_BLURB, MAX_SUMMARY

# Books are plain white for now; the style is stored so covers can differ later without a migration.
CoverStyle = Literal["cover-1", "cover-2", "cover-3", "cover-4", "cover-5", "cover-6", "cover-7", "cover-8"]
BookStatus = Literal["draft", "on_shelf", "off_shelf"]
# The AI's summaries and blurbs have these limits too. Titles have none in the prompts, so these
# leave room (docs/review/decisions.md, row 30).
MAX_BOOK_TITLE = 80
MAX_CHAPTER_TITLE = 100
# The Librarian writes 150-250 words; this leaves the member room to write more.
MAX_CHAPTER_BODY = 4000
DEFAULT_COPIES = 3


class Chapter(BaseModel):
    id: str
    title: str
    summary: str
    # The chapter's text, a few short paragraphs separated by a blank line. Null until the Librarian has
    # written it, or on books from before chapters had text: show the summary instead.
    body: str | None = None


class AuthorChapter(Chapter):
    # The member's own interview words this chapter is grounded in. Only the author sees them.
    quotes: list[str]


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


class BookEdit(RequestBody):
    """The member's own words for their book's title or back cover. Plain text."""

    title: NonEmptyText | None = Field(None, max_length=MAX_BOOK_TITLE)
    blurb: NonEmptyText | None = Field(None, max_length=MAX_BLURB)

    @model_validator(mode="after")
    def something_to_change(self):
        if self.title is None and self.blurb is None:
            raise ValueError("Send a title or a blurb to change.")
        return self


class ChapterEdit(RequestBody):
    """The member's own words for a chapter's title, summary or text. Its quotes stay as they are."""

    title: NonEmptyText | None = Field(None, max_length=MAX_CHAPTER_TITLE)
    summary: NonEmptyText | None = Field(None, max_length=MAX_SUMMARY)
    # Once the member saves their own text, the Librarian never writes over it.
    body: NonEmptyText | None = Field(None, max_length=MAX_CHAPTER_BODY)

    @model_validator(mode="after")
    def something_to_change(self):
        if self.title is None and self.summary is None and self.body is None:
            raise ValueError("Send a title, a summary or a text to change.")
        return self
