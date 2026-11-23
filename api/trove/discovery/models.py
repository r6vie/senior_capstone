from typing import Literal

from pydantic import BaseModel

from trove.books.models import BookCard

RecommendationState = Literal[
    "create_book",
    "continue_interview",
    "finish_book",
    "recommendation",
    "empty_shelf",
    "unavailable",
]


class LibrarianRecommendation(BaseModel):
    """What the shelf's Librarian cover shows for this signed-in member."""

    state: RecommendationState
    book: BookCard | None = None
    reason: str | None = None


class SearchResult(BaseModel):
    book: BookCard
    excerpt: str


class SearchResponse(BaseModel):
    results: list[SearchResult]
