"""Personalized discovery rules and the recommendation cache (docs/trove.md §5)."""

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

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

RECOMMENDATION_DAYS = 7
CANDIDATE_LIMIT = 30
PROFILE_VERSION = 1
MAX_SIGNALS = 12
SEARCH_CATALOG_LIMIT = 200
SEARCH_RESULT_LIMIT = 40
SEARCH_EXCERPT_LENGTH = 180

SignalKind = Literal["interest", "domain", "knowledge", "experience", "goal", "location", "origin"]


class _Signal(BaseModel):
    kind: SignalKind
    label: str = Field(min_length=1, max_length=80)
    broader: list[str] = Field(default_factory=list, max_length=3)
    evidence: str = Field(min_length=1, max_length=200)


class _Profile(BaseModel):
    book_id: str
    signals: list[_Signal] = Field(max_length=MAX_SIGNALS)


class _Profiles(BaseModel):
    profiles: list[_Profile]


@dataclass(frozen=True)
class _Contribution:
    weight: int
    relation: Literal["shared", "related", "offers", "seeks"]
    own: str
    candidate: str
    umbrella: str | None = None


# One precise shared interest should outweigh geography, while knowledge that answers an explicit
# goal is the strongest single reason to talk. Related concepts receive roughly half the exact score.
SHARED_WEIGHTS: dict[SignalKind, int] = {
    "interest": 30,
    "domain": 22,
    "knowledge": 20,
    "experience": 18,
    "goal": 14,
    "location": 8,
    "origin": 8,
}
RELATED_WEIGHTS: dict[SignalKind, int] = {
    "interest": 16,
    "domain": 12,
    "knowledge": 12,
    "experience": 10,
    "goal": 8,
    "location": 5,
    "origin": 5,
}
COMPLEMENT_EXACT = 35
COMPLEMENT_RELATED = 18


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
    await database.match_profiles.create_index("author_id", name="match_profiles_author")


@on_account_deleted
async def remove_recommendation_of(database: AsyncDatabase, user_id: str) -> None:
    await database.recommendations.delete_one({"user_id": user_id})
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


def _clean_concept(value: str) -> str:
    return _normalize(value)[:80]


def _ground_profile(book: dict, profile: _Profile) -> _Profile:
    """Keep only concise signals backed by an exact excerpt of the public book."""
    public = _normalize(_public_text(book))
    signals: list[_Signal] = []
    seen: set[tuple[str, str]] = set()
    for signal in profile.signals:
        label = _clean_concept(signal.label)
        evidence = " ".join(signal.evidence.split())
        normalized_evidence = _normalize(evidence)
        key = (signal.kind, label)
        if not label or not normalized_evidence or normalized_evidence not in public or key in seen:
            continue
        broader = list(
            dict.fromkeys(
                concept for value in signal.broader if (concept := _clean_concept(value)) and concept != label
            )
        )[:3]
        signals.append(_Signal(kind=signal.kind, label=label, broader=broader, evidence=evidence))
        seen.add(key)
    return _Profile(book_id=book["_id"], signals=signals)


async def _profiles_for(
    database: AsyncDatabase,
    claude: Claude | ScriptedClaude | None,
    books: list[dict],
) -> dict[str, _Profile]:
    """Load current profiles and extract all stale books together, so each book pays for AI once."""
    if not books:
        return {}
    stored = {
        profile["_id"]: profile
        async for profile in database.match_profiles.find({"_id": {"$in": [book["_id"] for book in books]}})
    }
    profiles: dict[str, _Profile] = {}
    stale: list[dict] = []
    for book in books:
        cached = stored.get(book["_id"])
        if (
            cached
            and cached.get("version") == PROFILE_VERSION
            and cached.get("fingerprint") == _fingerprint(book)
        ):
            try:
                profiles[book["_id"]] = _Profile.model_validate(cached["profile"])
                continue
            except (KeyError, ValidationError):
                pass
        stale.append(book)

    if not stale or claude is None:
        return profiles
    payload = {"books": [_story(book) for book in stale]}
    try:
        response = await claude.create(
            system=load_prompt("discovery/profile"),
            max_tokens=min(8000, 400 + 260 * len(stale)),
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
        extracted = _Profiles.model_validate_json(text_of(response))
    except (APIError, ClaudeRefused, ValidationError, ValueError):
        return profiles

    stale_by_id = {book["_id"]: book for book in stale}
    for raw in extracted.profiles:
        book = stale_by_id.get(raw.book_id)
        if book is None:
            continue
        profile = _ground_profile(book, raw)
        profiles[book["_id"]] = profile
        await database.match_profiles.replace_one(
            {"_id": book["_id"]},
            {
                "_id": book["_id"],
                "author_id": book["author_id"],
                "fingerprint": _fingerprint(book),
                "version": PROFILE_VERSION,
                "profile": profile.model_dump(),
                "updated_at": datetime.now(UTC),
            },
            upsert=True,
        )
    return profiles


def _relation(first: _Signal, second: _Signal) -> tuple[Literal["exact", "related"], str] | None:
    if first.label == second.label:
        return "exact", first.label
    if first.label in second.broader:
        return "related", first.label
    if second.label in first.broader:
        return "related", second.label
    shared = next((concept for concept in first.broader if concept in second.broader), None)
    return ("related", shared) if shared else None


def _contributions(own: _Profile, candidate: _Profile) -> list[_Contribution]:
    found: dict[tuple[str, str, str], _Contribution] = {}
    for first in own.signals:
        for second in candidate.signals:
            relation = _relation(first, second)
            if relation is None:
                continue
            closeness, umbrella = relation
            contribution: _Contribution | None = None
            if {first.kind, second.kind} == {"knowledge", "goal"}:
                direction = "offers" if first.kind == "goal" else "seeks"
                contribution = _Contribution(
                    COMPLEMENT_EXACT if closeness == "exact" else COMPLEMENT_RELATED,
                    direction,
                    first.label,
                    second.label,
                    None if closeness == "exact" else umbrella,
                )
            elif first.kind == second.kind:
                contribution = _Contribution(
                    SHARED_WEIGHTS[first.kind] if closeness == "exact" else RELATED_WEIGHTS[first.kind],
                    "shared" if closeness == "exact" else "related",
                    first.label,
                    second.label,
                    None if closeness == "exact" else umbrella,
                )
            if contribution is None:
                continue
            key = (contribution.relation, contribution.umbrella or contribution.own, contribution.candidate)
            previous = found.get(key)
            if previous is None or contribution.weight > previous.weight:
                found[key] = contribution
    return sorted(
        found.values(),
        key=lambda item: (-item.weight, item.relation, item.own, item.candidate, item.umbrella or ""),
    )


def _score(own: _Profile, candidate: _Profile) -> tuple[int, _Contribution | None]:
    contributions = _contributions(own, candidate)
    # A longer book should not win just because Claude could name more things in it.
    return sum(item.weight for item in contributions[:4]), contributions[0] if contributions else None


def _reason(author: str, contribution: _Contribution) -> str:
    if contribution.relation == "shared":
        return f"You and {author} both write about {contribution.own}, giving you a concrete place to start."
    if contribution.relation == "offers":
        return f"{author}'s experience with {contribution.candidate} complements your goal around {contribution.own}."
    if contribution.relation == "seeks":
        return f"Your experience with {contribution.own} could complement {author}'s goal around {contribution.candidate}."
    return (
        f"Your book's {contribution.own} connects with {author}'s {contribution.candidate} "
        f"through {contribution.umbrella}."
    )


def _card(book: dict) -> BookCard:
    return BookCard.model_validate({**book, "id": book["_id"]})


async def _cached(
    database: AsyncDatabase, cache: dict | None, source_fingerprint: str, user_id: str
) -> dict | None:
    if (
        cache is None
        or cache.get("version") != PROFILE_VERSION
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

    profiles = await _profiles_for(database, claude, [own, *candidates])
    own_profile = profiles.get(own["_id"])
    if own_profile is None:
        return LibrarianRecommendation(state="unavailable")
    ranked = [
        (score, book["_id"], book, contribution)
        for book in candidates
        if (profile := profiles.get(book["_id"])) is not None
        for score, contribution in [_score(own_profile, profile)]
        if contribution is not None
    ]
    if not ranked:
        return LibrarianRecommendation(state="unavailable")
    _, _, book, contribution = min(ranked, key=lambda item: (-item[0], item[1]))
    reason = _reason(book.get("author_name", "this author"), contribution)

    expires_at = now + timedelta(days=RECOMMENDATION_DAYS)
    await database.recommendations.replace_one(
        {"user_id": user_id},
        {
            "user_id": user_id,
            "book_id": book["_id"],
            "reason": reason,
            "version": PROFILE_VERSION,
            "source_fingerprint": source_fingerprint,
            "book_fingerprint": _fingerprint(book, candidate=True),
            "created_at": now,
            "expires_at": expires_at,
        },
        upsert=True,
    )
    return LibrarianRecommendation(state="recommendation", book=_card(book), reason=reason)
