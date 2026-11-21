"""Personalized discovery rules and the recommendation cache (docs/trove.md §5)."""

import hashlib
import json
from datetime import UTC, datetime, timedelta

from anthropic import APIError
from pydantic import BaseModel, ValidationError
from pymongo.asynchronous.database import AsyncDatabase

from trove.ai.client import Claude, ClaudeRefused, text_of
from trove.ai.prompts import load_prompt
from trove.ai.scripted import ScriptedClaude
from trove.auth.service import on_account_deleted
from trove.books.models import BookCard
from trove.books.service import PUBLISHED, get_book_of, get_public_book, list_shelf
from trove.checkouts.service import fully_checked_out
from trove.discovery.models import LibrarianRecommendation

RECOMMENDATION_DAYS = 7
CANDIDATE_LIMIT = 30
MAX_REASON_LENGTH = 300


class _Choice(BaseModel):
    book_id: str
    reason: str


async def ensure_indexes(database: AsyncDatabase) -> None:
    await database.recommendations.create_index("user_id", unique=True, name="recommendations_user_unique")
    await database.recommendations.create_index(
        "expires_at", expireAfterSeconds=0, name="recommendations_expiry"
    )


@on_account_deleted
async def remove_recommendation_of(database: AsyncDatabase, user_id: str) -> None:
    await database.recommendations.delete_one({"user_id": user_id})


def _story(book: dict, *, candidate: bool = False) -> dict:
    """Only public story fields may shape a recommendation or be sent to Claude."""
    story = {
        "book_id": book["_id"],
        "title": book["title"],
        "blurb": book.get("blurb"),
        "chapters": [
            {"title": chapter["title"], "summary": chapter["summary"]} for chapter in book.get("chapters", [])
        ],
    }
    if candidate:
        story["author_name"] = book.get("author_name", "")
    return story


def _fingerprint(book: dict, *, candidate: bool = False) -> str:
    encoded = json.dumps(_story(book, candidate=candidate), sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def _card(book: dict) -> BookCard:
    return BookCard.model_validate({**book, "id": book["_id"]})


async def _cached(
    database: AsyncDatabase, cache: dict | None, source_fingerprint: str, user_id: str
) -> dict | None:
    if cache is None or cache.get("source_fingerprint") != source_fingerprint:
        return None
    book = await get_public_book(database, cache.get("book_id", ""))
    if book is None or cache.get("book_fingerprint") != _fingerprint(book, candidate=True):
        return None
    if book["author_id"] == user_id or await fully_checked_out(database, [book]):
        return None
    return book


async def librarian_recommendation(
    database: AsyncDatabase,
    user_id: str,
    claude: Claude | ScriptedClaude | None,
) -> LibrarianRecommendation:
    """Return one stable, grounded recommendation, or the member's next book-making step."""
    own = await get_book_of(database, user_id)
    if own is None:
        return LibrarianRecommendation(state="create_book")
    if own["status"] not in PUBLISHED:
        return LibrarianRecommendation(state="finish_book")

    source_fingerprint = _fingerprint(own)
    now = datetime.now(UTC)
    cache = await database.recommendations.find_one({"user_id": user_id, "expires_at": {"$gt": now}})
    if book := await _cached(database, cache, source_fingerprint, user_id):
        return LibrarianRecommendation(state="recommendation", book=_card(book), reason=cache["reason"])

    # list_shelf excludes off-shelf and fully checked-out books. The owner's own book is never a
    # candidate, but an off-shelf book can still be the private source for their recommendation.
    candidates = [
        book for book in await list_shelf(database, limit=CANDIDATE_LIMIT) if book["author_id"] != user_id
    ]
    if not candidates:
        return LibrarianRecommendation(state="empty_shelf")
    by_id = {book["_id"]: book for book in candidates}

    if claude is None:
        return LibrarianRecommendation(state="unavailable")

    payload = {
        "member_book": _story(own),
        "candidate_books": [_story(book, candidate=True) for book in candidates],
    }
    try:
        response = await claude.create(
            system=load_prompt("discovery/recommendation"),
            max_tokens=300,
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
        choice = _Choice.model_validate_json(text_of(response))
    except (APIError, ClaudeRefused, ValidationError, ValueError):
        return LibrarianRecommendation(state="unavailable")

    book = by_id.get(choice.book_id)
    reason = " ".join(choice.reason.split())
    if book is None or not reason or len(reason) > MAX_REASON_LENGTH:
        return LibrarianRecommendation(state="unavailable")

    expires_at = now + timedelta(days=RECOMMENDATION_DAYS)
    await database.recommendations.replace_one(
        {"user_id": user_id},
        {
            "user_id": user_id,
            "book_id": book["_id"],
            "reason": reason,
            "source_fingerprint": source_fingerprint,
            "book_fingerprint": _fingerprint(book, candidate=True),
            "created_at": now,
            "expires_at": expires_at,
        },
        upsert=True,
    )
    return LibrarianRecommendation(state="recommendation", book=_card(book), reason=reason)
