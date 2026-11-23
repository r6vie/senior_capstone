"""Personalized discovery rules and the recommendation cache (docs/trove.md §5)."""

import hashlib
import json
import re
import unicodedata
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
from trove.discovery.models import LibrarianRecommendation, SearchResponse, SearchResult

RECOMMENDATION_DAYS = 7
CANDIDATE_LIMIT = 30
MAX_REASON_LENGTH = 300
SEARCH_CATALOG_LIMIT = 200
SEARCH_RESULT_LIMIT = 40
SEARCH_EXCERPT_LENGTH = 180


class _Choice(BaseModel):
    book_id: str
    reason: str


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return " ".join(
        re.findall(
            r"[^\W_]+", "".join(character for character in decomposed if not unicodedata.combining(character))
        )
    )


def _query_terms(query: str) -> list[str]:
    return list(dict.fromkeys(_normalize(query).split()))


def _matches(text: str, term: str) -> bool:
    return any(word.startswith(term) for word in _normalize(text).split())


def _excerpt(text: str, terms: list[str]) -> str:
    compact = " ".join(text.split())
    if len(compact) <= SEARCH_EXCERPT_LENGTH:
        return compact
    folded = compact.casefold()
    positions = [position for term in terms if (position := folded.find(term)) >= 0]
    start = max(0, min(positions, default=0) - 50)
    end = min(len(compact), start + SEARCH_EXCERPT_LENGTH)
    if start:
        start = compact.find(" ", start) + 1
    if end < len(compact):
        end = compact.rfind(" ", start, end)
    return f"{'…' if start else ''}{compact[start:end]}{'…' if end < len(compact) else ''}"


def _searchable_fields(book: dict) -> list[tuple[int, str]]:
    fields = [
        (8, book["title"]),
        (8, f"By {book.get('author_name', '')}"),
    ]
    if book.get("blurb"):
        fields.append((4, book["blurb"]))
    for chapter in book.get("chapters", []):
        fields.append((6, f"{chapter['title']} — {chapter['summary']}"))
        fields.append((3, chapter["summary"]))
    return fields


def _search_match(book: dict, terms: list[str]) -> tuple[int, str] | None:
    fields = _searchable_fields(book)
    best_for_term = [
        max((weight for weight, text in fields if _matches(text, term)), default=0) for term in terms
    ]
    if not all(best_for_term):
        return None
    matching = [
        (sum(_matches(text, term) for term in terms), weight, text)
        for weight, text in fields
        if any(_matches(text, term) for term in terms)
    ]
    _, _, text = max(matching, key=lambda field: (field[0], field[1]))
    phrase_bonus = 8 if _normalize(" ".join(terms)) in _normalize(book["title"]) else 0
    return sum(best_for_term) + phrase_bonus, _excerpt(text, terms)


async def search_books(database: AsyncDatabase, query: str) -> SearchResponse:
    """Search every public word in available books. Names are searchable; private book fields never are."""
    terms = _query_terms(query)
    if not terms or len(_normalize(query)) < 2:
        return SearchResponse(results=[])
    books = await list_shelf(database, limit=SEARCH_CATALOG_LIMIT)
    matches = [
        (score, book, excerpt)
        for book in books
        if (match := _search_match(book, terms)) is not None
        for score, excerpt in [match]
    ]
    matches.sort(key=lambda item: (-item[0], item[1]["title"].casefold(), item[1]["_id"]))
    return SearchResponse(
        results=[
            SearchResult(book=_card(book), excerpt=excerpt)
            for _, book, excerpt in matches[:SEARCH_RESULT_LIMIT]
        ]
    )


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
