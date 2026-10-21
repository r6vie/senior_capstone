"""Explainable matching between a student's need and alumni profiles."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from auth import get_current_user
from database import get_database
from models import MeetingPreference, Profile, SavedProfile


SearchText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
OptionalFilter = Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)]


class MatchSearchRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")

    query: SearchText
    industry: OptionalFilter = ""
    location: OptionalFilter = ""
    meeting_preference: MeetingPreference | None = None
    limit: int = Field(default=12, ge=1, le=25)


class MatchResult(BaseModel):
    profile: SavedProfile
    score: int = Field(ge=0, le=100)
    reasons: list[str]
    score_breakdown: dict[str, int]


router = APIRouter(prefix="/matches", tags=["Matching"])
MATCH_PROJECTION = {
    "_id": 1,
    "owner_user_id": 1,
    **{field: 1 for field in Profile.model_fields},
}

STOP_WORDS = {
    "a", "an", "and", "are", "for", "from", "help", "i", "in", "is", "looking",
    "me", "my", "of", "on", "someone", "the", "to", "want", "with", "who",
}
SYNONYMS = {
    "fundraise": "funding", "fundraising": "funding", "capital": "funding",
    "investor": "funding", "investors": "funding", "venture": "funding",
    "founder": "startup", "founders": "startup", "entrepreneurship": "startup",
    "entrepreneurial": "startup", "businesses": "business", "companies": "business",
    "health": "healthcare", "medical": "healthcare", "biotech": "healthcare",
    "regulatory": "regulation", "fda": "regulation", "compliance": "regulation",
    "developer": "software", "engineering": "software", "technical": "software",
    "product": "product", "products": "product", "marketing": "growth",
    "sales": "growth", "networking": "connections", "introductions": "connections",
    "mentor": "mentoring", "mentorship": "mentoring", "advice": "mentoring",
}


def tokens(*values: str | list[str]) -> set[str]:
    words: set[str] = set()
    for value in values:
        text = " ".join(value) if isinstance(value, list) else value
        for word in re.findall(r"[a-z0-9]+", text.casefold()):
            if word not in STOP_WORDS and len(word) > 1:
                words.add(SYNONYMS.get(word, word))
    return words


def similarity(source: set[str], target: set[str]) -> tuple[float, list[str]]:
    if not source or not target:
        return 0.0, []
    shared = sorted(source & target)
    # Four meaningful shared concepts constitute a full signal for a category.
    return min(1.0, len(shared) / min(4, len(source))), shared


def public_profile(document: dict) -> SavedProfile:
    data = {
        **{field: document[field] for field in Profile.model_fields if field in document},
        "id": str(document["_id"]),
    }
    if "role" not in document:
        data["role"] = "student" if "student" in document.get("affiliation", "").casefold() else "alumni"
    return SavedProfile.model_validate(data)


def score_candidate(
    candidate: SavedProfile,
    current: SavedProfile,
    query: str,
    industry_filter: str = "",
    location_filter: str = "",
    meeting_preference: MeetingPreference | None = None,
) -> MatchResult:
    explicit_need = tokens(query, current.help_needed)
    context = tokens(query, current.interests, current.industry)

    expertise_similarity, expertise_terms = similarity(
        explicit_need, tokens(candidate.expertise, candidate.help_offered),
    )
    interest_similarity, interest_terms = similarity(
        context, tokens(candidate.interests, candidate.industry),
    )
    help_similarity, help_terms = similarity(
        tokens(query, current.help_needed), tokens(candidate.help_offered),
    )
    background_similarity, background_terms = similarity(
        tokens(query, industry_filter),
        tokens(candidate.background, candidate.affiliation, candidate.industry),
    )

    expertise_score = round(40 * expertise_similarity)
    interest_score = round(20 * interest_similarity)
    help_score = round(15 * help_similarity)
    background_score = round(10 * background_similarity)
    availability_score = {"available": 10, "limited": 5, "unavailable": 0}[candidate.availability]

    desired_location = location_filter or current.location
    same_location = bool(tokens(desired_location) & tokens(candidate.location))
    meeting_matches = (
        meeting_preference is None
        or candidate.meeting_preference == "either"
        or candidate.meeting_preference == meeting_preference
    )
    if same_location:
        location_score = 5
    elif meeting_matches and candidate.meeting_preference in {"remote", "either"}:
        location_score = 3
    else:
        location_score = 0

    breakdown = {
        "expertise": expertise_score,
        "interests": interest_score,
        "help_alignment": help_score,
        "background": background_score,
        "availability": availability_score,
        "location": location_score,
    }
    score = min(100, sum(breakdown.values()))

    reasons: list[str] = []
    if expertise_terms:
        reasons.append(f"Expertise aligns with {', '.join(expertise_terms[:3])}")
    if help_terms:
        reasons.append(f"Offers relevant help with {', '.join(help_terms[:3])}")
    if interest_terms:
        reasons.append(f"Shares interests in {', '.join(interest_terms[:3])}")
    if background_terms:
        reasons.append(f"Relevant background in {', '.join(background_terms[:3])}")
    if same_location:
        reasons.append(f"Located near {desired_location}")
    elif meeting_matches and candidate.meeting_preference in {"remote", "either"}:
        reasons.append("Available to connect remotely")
    if candidate.availability == "available":
        reasons.append("Currently open to helping")
    if not reasons:
        reasons.append("Alumni profile available for network discovery")

    return MatchResult(
        profile=candidate,
        score=score,
        reasons=reasons[:4],
        score_breakdown=breakdown,
    )


async def current_profile(user: dict, database) -> SavedProfile:
    document = await database.profiles.find_one(
        {"owner_user_id": user["_id"]}, MATCH_PROJECTION,
    )
    if document is None:
        raise HTTPException(
            status_code=409,
            detail="Create your profile before using personalized matching.",
        )
    return public_profile(document)


async def alumni_profiles(user: dict, database) -> list[SavedProfile]:
    query = {
        "owner_user_id": {"$ne": user["_id"]},
        "$or": [{"role": "alumni"}, {"role": {"$exists": False}}],
    }
    cursor = database.profiles.find(query, MATCH_PROJECTION).limit(100)
    documents = await cursor.to_list(length=100)
    profiles = [public_profile(document) for document in documents]
    return [profile for profile in profiles if profile.role == "alumni"]


@router.post("/search", response_model=list[MatchResult])
async def search_matches(
    request: MatchSearchRequest,
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
) -> list[MatchResult]:
    """Rank alumni against a student's current need and optional filters."""
    student = await current_profile(user, database)
    results = [
        score_candidate(
            candidate, student, request.query, request.industry,
            request.location, request.meeting_preference,
        )
        for candidate in await alumni_profiles(user, database)
        if candidate.availability != "unavailable"
    ]
    return sorted(results, key=lambda match: (-match.score, match.profile.name))[:request.limit]


@router.get("/recommended", response_model=list[MatchResult])
async def recommended_matches(
    limit: int = 6,
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
) -> list[MatchResult]:
    """Recommend alumni using the student's saved profile rather than a new query."""
    if not 1 <= limit <= 25:
        raise HTTPException(status_code=422, detail="Limit must be between 1 and 25.")
    student = await current_profile(user, database)
    recommendation_query = " ".join([
        *student.help_needed, *student.interests, student.industry,
    ]).strip() or "mentoring"
    results = [
        score_candidate(candidate, student, recommendation_query)
        for candidate in await alumni_profiles(user, database)
        if candidate.availability != "unavailable"
    ]
    return sorted(results, key=lambda match: (-match.score, match.profile.name))[:limit]
