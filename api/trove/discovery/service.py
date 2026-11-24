"""Personalized discovery rules and the recommendation cache (docs/trove.md §5)."""

import asyncio
import hashlib
import json
import logging
import re
import unicodedata
from datetime import UTC, datetime, timedelta

from anthropic import APIError
from pydantic import BaseModel, Field, ValidationError
from pymongo.asynchronous.database import AsyncDatabase

from trove.ai.client import Claude, ClaudeRefused, text_of
from trove.ai.prompts import load_prompt
from trove.ai.scripted import ScriptedClaude
from trove.auth.service import on_account_deleted
from trove.books.models import BookCard
from trove.books.service import PUBLISHED, get_book_of, get_public_book, list_shelf
from trove.checkouts.service import fully_checked_out
from trove.discovery.models import LibrarianRecommendation, SearchResponse, SearchResult
from trove.interview.service import has_open_interview

RECOMMENDATION_DAYS = 7
CANDIDATE_LIMIT = 30
RECOMMENDATION_VERSION = 2
RECOMMENDATION_TIMEOUT_SECONDS = 45
SEARCH_CATALOG_LIMIT = 200
SEARCH_RESULT_LIMIT = 40
SEARCH_EXCERPT_LENGTH = 180

logger = logging.getLogger(__name__)
_recommendation_locks: dict[str, asyncio.Lock] = {}


class _Choice(BaseModel):
    book_id: str
    own_evidence: str = Field(min_length=1, max_length=240)
    candidate_evidence: str = Field(min_length=1, max_length=240)
    reason: str = Field(min_length=1, max_length=280)


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
    # Older D3 builds stored extracted profiles. Keep deleting those until the legacy collection is retired.
    await database.match_profiles.delete_many({"author_id": user_id})


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


def _public_text(book: dict) -> str:
    story = _story(book)
    parts = [story["title"], story.get("blurb") or ""]
    for chapter in story["chapters"]:
        parts.extend((chapter["title"], chapter["summary"]))
    return " ".join(parts)


def _json_object(text: str) -> str:
    """Accept the requested bare JSON and tolerate a model wrapping it in a Markdown fence."""
    stripped = text.strip()
    if stripped.startswith("```"):
        first_line = stripped.find("\n")
        stripped = stripped[first_line + 1 :] if first_line >= 0 else stripped
        if stripped.endswith("```"):
            stripped = stripped[:-3]
    start = stripped.find("{")
    end = stripped.rfind("}")
    return stripped[start : end + 1] if start >= 0 and end >= start else stripped


def _contains_evidence(book: dict, evidence: str) -> bool:
    normalized = _normalize(evidence)
    return bool(normalized) and normalized in _normalize(_public_text(book))


async def _ask_librarian(
    claude: Claude | ScriptedClaude | None,
    own: dict,
    candidates: list[dict],
) -> tuple[dict, str] | None:
    """Let Claude choose one eligible book, then verify its id and both grounding excerpts."""
    if claude is None:
        return None
    payload = {
        "member_book": _story(own),
        "candidate_books": [_story(book, candidate=True) for book in candidates],
    }
    try:
        async with asyncio.timeout(RECOMMENDATION_TIMEOUT_SECONDS):
            response = await claude.create(
                system=load_prompt("discovery/recommend"),
                max_tokens=900,
                messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            )
        choice = _Choice.model_validate_json(_json_object(text_of(response)))
    except (APIError, ClaudeRefused, TimeoutError, ValidationError, ValueError) as error:
        logger.warning("Librarian recommendation failed: %s", type(error).__name__)
        return None

    candidate = next((book for book in candidates if book["_id"] == choice.book_id), None)
    if candidate is None:
        logger.warning("Librarian recommendation rejected: candidate id was not eligible")
        return None
    if not _contains_evidence(own, choice.own_evidence) or not _contains_evidence(
        candidate, choice.candidate_evidence
    ):
        logger.warning("Librarian recommendation rejected: evidence was not grounded in both books")
        return None
    return candidate, " ".join(choice.reason.split())


def _card(book: dict) -> BookCard:
    return BookCard.model_validate({**book, "id": book["_id"]})


async def _cached(
    database: AsyncDatabase, cache: dict | None, source_fingerprint: str, user_id: str
) -> dict | None:
    if (
        cache is None
        or cache.get("version") != RECOMMENDATION_VERSION
        or cache.get("source_fingerprint") != source_fingerprint
    ):
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
        # Mid-interview, the next step is to carry on, not to start (the interviews feature says which).
        if await has_open_interview(database, user_id):
            return LibrarianRecommendation(state="continue_interview")
        return LibrarianRecommendation(state="create_book")
    if own["status"] not in PUBLISHED:
        return LibrarianRecommendation(state="finish_book")

    source_fingerprint = _fingerprint(own)
    # React development mode and two open tabs can ask at once. Only one paid Librarian call should run;
    # followers re-check the cache after the first request finishes.
    lock = _recommendation_locks.setdefault(user_id, asyncio.Lock())
    async with lock:
        now = datetime.now(UTC)
        cache = await database.recommendations.find_one({"user_id": user_id, "expires_at": {"$gt": now}})
        if book := await _cached(database, cache, source_fingerprint, user_id):
            return LibrarianRecommendation(state="recommendation", book=_card(book), reason=cache["reason"])

        # list_shelf excludes hidden and fully checked-out books. An off-shelf book may still privately
        # shape its owner's recommendation, but it can never appear among these candidates.
        candidates = [
            book for book in await list_shelf(database, limit=CANDIDATE_LIMIT) if book["author_id"] != user_id
        ]
        if not candidates:
            return LibrarianRecommendation(state="empty_shelf")

        chosen = await _ask_librarian(claude, own, candidates)
        if chosen is None:
            return LibrarianRecommendation(state="unavailable")
        book, reason = chosen

        expires_at = now + timedelta(days=RECOMMENDATION_DAYS)
        await database.recommendations.replace_one(
            {"user_id": user_id},
            {
                "user_id": user_id,
                "book_id": book["_id"],
                "reason": reason,
                "version": RECOMMENDATION_VERSION,
                "source_fingerprint": source_fingerprint,
                "book_fingerprint": _fingerprint(book, candidate=True),
                "created_at": now,
                "expires_at": expires_at,
            },
            upsert=True,
        )
        return LibrarianRecommendation(state="recommendation", book=_card(book), reason=reason)
