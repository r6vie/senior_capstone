"""Grounded, interactive meeting preparation for conversations with alumni."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from auth import get_current_user
from database import get_database
from matching import MATCH_PROJECTION, public_profile, tokens
from models import SavedProfile


ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=500)]
AnswerText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class PrepRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    goal: ShortText


class AskRequest(PrepRequest):
    question: ShortText


class PracticeRequest(PrepRequest):
    answer: AnswerText
    turn: int = Field(default=0, ge=0, le=20)


class TimelineEntry(BaseModel):
    marker: str
    title: str
    detail: str
    source: str = "Member profile"


class Evidence(BaseModel):
    label: str
    value: str


class MeetingBrief(BaseModel):
    profile: SavedProfile
    headline: str
    overview: str
    timeline: list[TimelineEntry]
    shared_ground: list[str]
    conversation_starters: list[str]
    agenda: list[str]
    evidence: list[Evidence]
    grounding_notice: str


class AskResponse(BaseModel):
    answer: str
    evidence: list[Evidence]
    follow_ups: list[str]


class PracticeResponse(BaseModel):
    feedback: str
    strengths: list[str]
    suggestions: list[str]
    next_question: str


router = APIRouter(prefix="/meeting-prep", tags=["Meeting preparation"])


async def load_profiles(profile_id: str, user: dict, database) -> tuple[SavedProfile, SavedProfile | None]:
    target_document = await database.profiles.find_one({"_id": profile_id}, MATCH_PROJECTION)
    if target_document is None:
        raise HTTPException(status_code=404, detail="Alumni profile not found.")
    target = public_profile(target_document)
    if target.role != "alumni":
        raise HTTPException(status_code=422, detail="Meeting preparation is currently available for alumni profiles.")
    if target_document.get("owner_user_id") == user["_id"]:
        raise HTTPException(status_code=422, detail="Choose another member to prepare for a meeting.")

    current_document = await database.profiles.find_one({"owner_user_id": user["_id"]}, MATCH_PROJECTION)
    current = public_profile(current_document) if current_document else None
    return target, current


def shared_ground(target: SavedProfile, current: SavedProfile | None) -> list[str]:
    if current is None:
        return []
    shared: list[str] = []
    interest_terms = sorted(tokens(target.interests) & tokens(current.interests))
    if interest_terms:
        shared.append(f"Shared interests: {', '.join(interest_terms[:3])}")
    industry_terms = sorted(tokens(target.industry) & tokens(current.industry))
    if industry_terms:
        shared.append(f"Industry overlap: {', '.join(industry_terms[:2])}")
    location_terms = sorted(tokens(target.location) & tokens(current.location))
    if location_terms:
        shared.append(f"Location connection: {target.location}")
    need_terms = sorted(tokens(target.help_offered) & tokens(current.help_needed))
    if need_terms:
        shared.append(f"Their experience aligns with your needs in {', '.join(need_terms[:3])}")
    return shared[:4]


def starters(target: SavedProfile, goal: str) -> list[str]:
    questions = [f"I am hoping to {goal.rstrip('.').lower()}. What would you recommend as a first step?"]
    if target.help_offered:
        questions.append(f"You offer help with {target.help_offered[0]}. What lesson has shaped your approach?")
    elif target.expertise:
        questions.append(f"How did you build your experience in {target.expertise[0]}?")
    if target.background:
        questions.append("Looking back on your career journey, which decision taught you the most?")
    if target.interests:
        questions.append(f"What developments in {target.interests[0]} are you most excited about right now?")
    questions.append("Who else or what resource would you suggest I learn from next?")
    return questions[:5]


def make_brief(target: SavedProfile, current: SavedProfile | None, goal: str) -> MeetingBrief:
    timeline: list[TimelineEntry] = []
    if target.graduation_year:
        timeline.append(TimelineEntry(
            marker=str(target.graduation_year), title="CWRU chapter",
            detail=f"Graduated in {target.graduation_year}; listed affiliation: {target.affiliation}.",
        ))
    else:
        timeline.append(TimelineEntry(
            marker="CWRU", title="CWRU connection", detail=target.affiliation,
        ))
    if target.background:
        timeline.append(TimelineEntry(
            marker="Journey", title="Career background", detail=target.background,
        ))
    if target.expertise or target.industry:
        focus = ", ".join(target.expertise[:3]) or target.industry
        timeline.append(TimelineEntry(
            marker="Focus", title=target.industry or "Areas of expertise", detail=focus,
        ))
    if target.help_offered:
        timeline.append(TimelineEntry(
            marker="Now", title="Open to helping", detail=", ".join(target.help_offered[:4]),
        ))

    headline_parts = [part for part in [target.industry, target.expertise[0] if target.expertise else ""] if part]
    headline = " · ".join(headline_parts) or target.affiliation
    overview = target.background or (
        f"{target.name} is part of the {target.affiliation} community and has experience in "
        f"{', '.join(target.expertise[:3]) or 'entrepreneurship and mentoring'}."
    )
    conversation_starters = starters(target, goal)
    evidence = [
        Evidence(label="Affiliation", value=target.affiliation),
        Evidence(label="Location", value=target.location),
    ]
    if target.expertise:
        evidence.append(Evidence(label="Expertise", value=", ".join(target.expertise)))
    if target.help_offered:
        evidence.append(Evidence(label="Offers", value=", ".join(target.help_offered)))
    return MeetingBrief(
        profile=target,
        headline=headline,
        overview=overview,
        timeline=timeline,
        shared_ground=shared_ground(target, current),
        conversation_starters=conversation_starters,
        agenda=[
            "2 min · Introductions and shared CWRU context",
            f"10 min · Discuss your goal: {goal}",
            "10 min · Learn from their experience",
            "3 min · Agree on a useful next step",
        ],
        evidence=evidence,
        grounding_notice="Built only from member-provided profile information. Suggested questions are prompts, not claims about this person.",
    )


@router.post("/{profile_id}", response_model=MeetingBrief)
async def prepare_meeting(
    profile_id: str, request: PrepRequest, user: dict = Depends(get_current_user),
    database=Depends(get_database),
) -> MeetingBrief:
    target, current = await load_profiles(profile_id, user, database)
    return make_brief(target, current, request.goal)


@router.post("/{profile_id}/ask", response_model=AskResponse)
async def ask_about_profile(
    profile_id: str, request: AskRequest, user: dict = Depends(get_current_user),
    database=Depends(get_database),
) -> AskResponse:
    target, current = await load_profiles(profile_id, user, database)
    question_terms = tokens(request.question)
    evidence: list[Evidence] = []
    if question_terms & {"career", "background", "experience", "history", "journey", "work"}:
        answer = target.background or f"The profile lists {target.industry or 'their CWRU affiliation'}, but does not include a detailed career history yet."
        evidence.append(Evidence(label="Background", value=target.background or target.affiliation))
    elif question_terms & {"expertise", "skill", "skills", "know", "specialty"}:
        value = ", ".join(target.expertise) or "No expertise has been listed yet."
        answer = f"Their listed areas of expertise are {value}."
        evidence.append(Evidence(label="Expertise", value=value))
    elif question_terms & {"common", "shared", "overlap", "similar"}:
        common = shared_ground(target, current)
        answer = f"Based on both profiles, your common ground is: {'; '.join(common)}." if common else "The current profiles do not show a clear shared topic yet. Your CWRU connection is a good place to begin."
        evidence.append(Evidence(label="Profile comparison", value="; ".join(common) or "CWRU community"))
    elif question_terms & {"help", "advice", "ask", "mentor", "mentoring"}:
        value = ", ".join(target.help_offered) or ", ".join(target.expertise)
        answer = f"The strongest profile-grounded topics to ask about are {value or 'their CWRU and career experience'}."
        evidence.append(Evidence(label="Help offered", value=value or "Not specified"))
    elif question_terms & {"location", "remote", "meet", "meeting", "available"}:
        answer = f"They are based in {target.location}, list their availability as {target.availability}, and prefer {target.meeting_preference.replace('_', ' ')} meetings."
        evidence.extend([
            Evidence(label="Location", value=target.location),
            Evidence(label="Meeting preference", value=target.meeting_preference.replace("_", " ")),
        ])
    elif question_terms & {"graduate", "graduation", "cwru", "school", "university"}:
        year = f" and a graduation year of {target.graduation_year}" if target.graduation_year else ""
        answer = f"Their profile lists {target.affiliation}{year}."
        evidence.append(Evidence(label="CWRU information", value=f"{target.affiliation}{year}"))
    else:
        answer = make_brief(target, current, request.goal).overview
        evidence.append(Evidence(label="Profile summary", value=target.background or target.affiliation))
    return AskResponse(
        answer=answer,
        evidence=evidence,
        follow_ups=starters(target, request.goal)[:3],
    )


@router.post("/{profile_id}/practice", response_model=PracticeResponse)
async def practice_conversation(
    profile_id: str, request: PracticeRequest, user: dict = Depends(get_current_user),
    database=Depends(get_database),
) -> PracticeResponse:
    target, _ = await load_profiles(profile_id, user, database)
    words = request.answer.split()
    strengths: list[str] = []
    suggestions: list[str] = []
    if 20 <= len(words) <= 120:
        strengths.append("Your answer is focused and detailed enough for a conversation.")
    elif len(words) < 20:
        suggestions.append("Add one concrete example so the alumnus has something specific to respond to.")
    else:
        suggestions.append("Shorten the answer to your goal, one example, and one clear question.")
    if any(word in request.answer.casefold() for word in ("because", "learn", "building", "working", "goal")):
        strengths.append("You explain the motivation behind your request.")
    else:
        suggestions.append("Explain why this goal matters to you.")
    if "?" in request.answer:
        strengths.append("You leave room for a two-way conversation.")
    else:
        suggestions.append("End with a question that invites the alumnus to share their experience.")
    questions = starters(target, request.goal)
    return PracticeResponse(
        feedback="This is a profile-based coaching exercise, not a prediction of what the alumnus will say.",
        strengths=strengths or ["You have a clear starting point for the conversation."],
        suggestions=suggestions or ["Practice saying it naturally rather than memorizing every word."],
        next_question=questions[(request.turn + 1) % len(questions)],
    )
