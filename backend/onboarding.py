"""Onboarding API: the basics form, the AI interview, and members' own facts."""

from datetime import datetime, timezone
from uuid import uuid4

import anthropic
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import PlainTextResponse

from auth import get_current_user
from database import get_database
from interviewer import (
    KICKOFF, InterviewRefused, answer_text, get_claude, opening_note, run_turn, snapshot, turn_note,
)
from member_data import (
    compute_coverage, delete_fact, edit_fact, fact_out, member_facts, profile_for,
    render_profile_md, save_basics, shared_fact, visible_facts,
)
from member_models import (
    BasicsForm, FactEdit, FactOut, InterviewState, InterviewTurn, MemberAnswer, OnboardingStatus,
    Question, SharedFact,
)

router = APIRouter(dependencies=[Depends(get_current_user)], tags=["Onboarding"])
MAX_TURNS = 150  # answers per interview; keeps a runaway tab from running up the AI bill
RETURNING = "(The member came back to continue.)"
SORRY = "Sorry, that answer didn't go through. Try rewording it, or skip this question."


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def require_basics(database, user: dict) -> dict:
    profile = await profile_for(database, user["_id"])
    if profile is None or not profile.get("core"):
        raise HTTPException(status_code=409, detail="Fill in the basics form first.")
    return profile


async def turn_view(database, user: dict, session: dict) -> InterviewTurn:
    profile = await profile_for(database, user["_id"])
    facts = await member_facts(database, user["_id"])
    question = session.get("question")
    return InterviewTurn(
        interview=InterviewState(
            session_id=session["_id"], status=session["status"],
            question=Question.model_validate(question) if question else None,
            done=session.get("done", False), answered=session.get("answered", 0),
            added=session.get("added", []), notice=session.get("notice"),
        ),
        facts=[fact_out(fact) for fact in facts],
        coverage=compute_coverage((profile or {}).get("core"), facts),
    )


def changed_since(before: list[dict], after: list[dict]) -> list[str]:
    seen = {fact["_id"]: fact["updated_at"] for fact in before}
    return [fact["_id"] for fact in after if seen.get(fact["_id"]) != fact["updated_at"]]


async def take_turn(
    database, claude, user: dict, profile: dict, session: dict, member_text: str, note: str, answered: bool,
) -> dict:
    """Run one AI turn and save it: the facts it learned and the next question."""
    before = await member_facts(database, user["_id"])
    changes = {"updated_at": utcnow(), "status": "active", "notice": None}
    try:
        result = await run_turn(
            database, claude, user["_id"], session["api_messages"], member_text, note, profile.get("core"),
        )
    except InterviewRefused:
        # Nothing goes into the API transcript; the member keeps the same question.
        changes["notice"] = SORRY
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="The interviewer is busy. Try again in a minute.") from None
    except (anthropic.APIConnectionError, anthropic.InternalServerError):
        raise HTTPException(status_code=503, detail="Couldn't reach the interviewer. Try again shortly.") from None
    except anthropic.APIStatusError:
        raise HTTPException(status_code=502, detail="The interviewer had a problem with that answer.") from None
    except RuntimeError:
        raise HTTPException(status_code=502, detail="The interviewer got stuck. Try rewording your answer.") from None
    else:
        after = await member_facts(database, user["_id"])
        changes.update(
            api_messages=result.api_messages, known=snapshot(after), added=changed_since(before, after),
            question={"id": f"q-{uuid4().hex[:12]}", **result.question.model_dump(exclude={"done"})},
            done=result.question.done, answered=session.get("answered", 0) + int(answered),
        )
    # Only save if no other tab finished a turn meanwhile; transcripts must stay append-only.
    outcome = await database.interview_sessions.update_one(
        {"_id": session["_id"], "turns": session["turns"]},
        {"$set": changes, "$inc": {"turns": 1}},
    )
    if outcome.matched_count == 0:
        raise HTTPException(status_code=409, detail="This interview changed in another tab. Reload to continue.")
    return {**session, **changes, "turns": session["turns"] + 1}


async def own_session(database, user: dict, session_id: str) -> dict:
    session = await database.interview_sessions.find_one({"_id": session_id, "user_id": user["_id"]})
    if session is None:
        raise HTTPException(status_code=404, detail="Interview not found.")
    return session


# ---------------------------------------------------------------- basics

async def onboarding_status(database, user: dict) -> OnboardingStatus:
    profile = await profile_for(database, user["_id"])
    session = await database.interview_sessions.find_one({"user_id": user["_id"], "status": "active"})
    core = (profile or {}).get("core")
    return OnboardingStatus(
        basics_done=core is not None, basics=BasicsForm.model_validate(core) if core else None,
        open_interview_id=session["_id"] if session else None,
        coverage=compute_coverage(core, await member_facts(database, user["_id"])),
    )


@router.post("/onboarding/basics", response_model=OnboardingStatus)
async def submit_basics(
    form: BasicsForm, user: dict = Depends(get_current_user), database=Depends(get_database),
) -> OnboardingStatus:
    """Save the basics form. Creates your profile if you don't have one; safe to resubmit."""
    await save_basics(database, user, form)
    return await onboarding_status(database, user)


@router.get("/onboarding/status", response_model=OnboardingStatus)
async def get_onboarding_status(
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> OnboardingStatus:
    return await onboarding_status(database, user)


# ---------------------------------------------------------------- interview

@router.post("/interview/sessions", response_model=InterviewTurn)
async def start_interview(
    user: dict = Depends(get_current_user), database=Depends(get_database), claude=Depends(get_claude),
) -> InterviewTurn:
    """Start your interview, or continue it. Each member has one interview they can return to."""
    profile = await require_basics(database, user)
    session = await database.interview_sessions.find_one({"user_id": user["_id"]})
    facts = await member_facts(database, user["_id"])
    if session is None:
        now = utcnow()
        session = {
            "_id": str(uuid4()), "user_id": user["_id"], "status": "active", "turns": 0, "answered": 0,
            "api_messages": [], "known": {}, "question": None, "done": False, "added": [],
            "created_at": now, "updated_at": now,
        }
        await database.interview_sessions.insert_one(session)
        session = await take_turn(
            database, claude, user, profile, session, KICKOFF, opening_note(profile, facts), answered=False,
        )
    elif not session.get("question"):
        note = turn_note(profile, facts, session["known"])
        session = await take_turn(database, claude, user, profile, session, RETURNING, note, answered=False)
    elif session["status"] == "finished":
        # The question they left on is still waiting; any fact edits reach the AI with their next answer.
        await database.interview_sessions.update_one({"_id": session["_id"]}, {"$set": {"status": "active"}})
        session = {**session, "status": "active"}
    return await turn_view(database, user, session)


@router.get("/interview/sessions/current", response_model=InterviewTurn)
async def current_interview(
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> InterviewTurn:
    session = await database.interview_sessions.find_one({"user_id": user["_id"]})
    if session is None:
        raise HTTPException(status_code=404, detail="You haven't started an interview yet.")
    return await turn_view(database, user, session)


@router.post("/interview/sessions/{session_id}/answers", response_model=InterviewTurn)
async def answer(
    session_id: str, body: MemberAnswer, user: dict = Depends(get_current_user),
    database=Depends(get_database), claude=Depends(get_claude),
) -> InterviewTurn:
    """Answer (or skip) the current question; the reply has the next one and what was added."""
    session = await own_session(database, user, session_id)
    question = session.get("question")
    if session["status"] != "active" or question is None:
        raise HTTPException(status_code=409, detail="This interview is paused. Start it again to continue.")
    if body.question_id != question["id"]:
        raise HTTPException(status_code=409, detail="That question has changed. Reload to see the current one.")
    if session["turns"] >= MAX_TURNS:
        raise HTTPException(status_code=409, detail="You've answered a lot already. Edit your facts directly instead.")
    if question["choices"] and not set(body.choices) <= set(question["choices"]):
        raise HTTPException(status_code=422, detail="Pick from the suggested answers, or type your own.")
    if not question["multiple"] and len(body.choices) > 1:
        raise HTTPException(status_code=422, detail="Pick one suggested answer.")
    profile = await require_basics(database, user)
    note = turn_note(profile, await member_facts(database, user["_id"]), session["known"])
    member_text = answer_text(question, body.choices, body.text, body.skipped)
    session = await take_turn(database, claude, user, profile, session, member_text, note, answered=not body.skipped)
    return await turn_view(database, user, session)


@router.post("/interview/sessions/{session_id}/finish", response_model=InterviewTurn)
async def finish_interview(
    session_id: str, user: dict = Depends(get_current_user), database=Depends(get_database),
) -> InterviewTurn:
    """You pressed Done. Your facts are kept, and you can continue the interview later."""
    session = await own_session(database, user, session_id)
    await database.interview_sessions.update_one(
        {"_id": session_id}, {"$set": {"status": "finished", "updated_at": utcnow()}},
    )
    return await turn_view(database, user, {**session, "status": "finished"})


# ---------------------------------------------------------------- your own facts

@router.get("/me/facts", response_model=list[FactOut])
async def my_facts(user: dict = Depends(get_current_user), database=Depends(get_database)) -> list[FactOut]:
    return [fact_out(fact) for fact in await member_facts(database, user["_id"])]


@router.patch("/me/facts/{fact_id}", response_model=FactOut)
async def change_fact(
    fact_id: str, edit: FactEdit, user: dict = Depends(get_current_user), database=Depends(get_database),
) -> FactOut:
    """Edit a fact's text or visibility, or confirm it as-is. Any edit also confirms it."""
    fact = await edit_fact(database, user["_id"], fact_id, edit)
    if fact is None:
        raise HTTPException(status_code=404, detail="Fact not found.")
    return fact_out(fact)


@router.delete("/me/facts/{fact_id}", status_code=204, response_class=Response)
async def remove_fact(
    fact_id: str, user: dict = Depends(get_current_user), database=Depends(get_database),
) -> Response:
    """Permanently delete one of your facts. Matching stops using it right away."""
    if not await delete_fact(database, user["_id"], fact_id):
        raise HTTPException(status_code=404, detail="Fact not found.")
    return Response(status_code=204)


@router.get("/me/profile.md", response_class=PlainTextResponse)
async def my_profile_markdown(
    user: dict = Depends(get_current_user), database=Depends(get_database),
) -> PlainTextResponse:
    """Your full profile as the matcher reads it, private facts included (marked)."""
    profile = await profile_for(database, user["_id"])
    name = profile["name"] if profile else user["name"]
    facts = await member_facts(database, user["_id"])
    markdown = render_profile_md(name, (profile or {}).get("core"), facts)
    return PlainTextResponse(markdown, media_type="text/markdown; charset=utf-8")


# ---------------------------------------------------------------- other members' facts

@router.get("/profiles/{profile_id}/facts", response_model=list[SharedFact])
async def profile_facts(
    profile_id: str, user: dict = Depends(get_current_user), database=Depends(get_database),
) -> list[SharedFact]:
    """The facts on someone's profile that you're allowed to see."""
    profile = await database.profiles.find_one({"_id": profile_id}, {"owner_user_id": 1})
    if profile is None or not profile.get("owner_user_id"):
        raise HTTPException(status_code=404, detail="Profile not found.")
    return [shared_fact(fact) for fact in await visible_facts(database, profile["owner_user_id"], user["_id"])]
