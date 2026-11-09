"""The `interviews` collection and the interview's steps, from the first question to the shelf.

The engine (`engine.py`) writes questions and books; this module keeps the state, saves after every
answer, and checks each step happens in order.
"""

import base64
import binascii
import contextlib
import io
import logging
import re
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import anthropic
from fastapi import BackgroundTasks, HTTPException
from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError
from pypdf import PdfReader
from starlette.concurrency import run_in_threadpool

from trove.ai.client import Claude, ClaudeRefused
from trove.ai.usage import BudgetExceeded
from trove.auth.service import full_names_of
from trove.books import service as books
from trove.books.models import MyBookResponse
from trove.checkouts import service as checkouts
from trove.core.config import get_settings
from trove.interview import engine, resume_terms
from trove.interview.engine import Change, Draft, DraftChapter, Turn
from trove.interview.models import (
    InterviewResponse,
    Question,
    ReadingQuestionResponse,
    SparkResponse,
)

# After this many answers the member may say "I've said enough" (docs/trove.md §4).
EXIT_AFTER_ANSWERS = 10
SHAPE_CONFIRMED = "Yes, that's me."
# The stages with a question waiting for an answer.
ASKING_STAGES = ("interviewing", "adding")
MAX_RESUME_PAGES = 20
# Enough to shape questions; a résumé is a page or two.
MAX_RESUME_CHARS = 20_000
# An abandoned interview's résumé text goes this long after the last activity (decisions.md, row 13).
RESUME_TEXT_DAYS = 30
# After a draft finds too little, this many more answers before another one is worth paying for.
MORE_ANSWERS_BEFORE_REDRAFT = 3
# "Most of the way there" shows at this many answers, a little before Shape. The scripted interview is
# shorter than a real one, so it says so sooner.
NEARLY_DONE_ANSWERS = 13
NEARLY_DONE_ANSWERS_SCRIPTED = 9
# Unused sparks a member may keep (docs/review/decisions.md, row 5).
MAX_UNUSED_SPARKS = 12
# Sparks a round can work from, so it never turns into a list of other people's titles.
MAX_SPARKS_PER_ROUND = 3
READING_QUESTION = "What did they ask you about that surprised you?"
# Older reading questions go away on their own, as quietly as a dismissal.
READING_QUESTION_DAYS = 14
# Writing changes that hasn't finished by now died with the server, so it counts as failed.
WRITING_TIMEOUT = timedelta(minutes=5)
SPARK_REDACTED = "that topic"

logger = logging.getLogger(__name__)


async def ensure_indexes(database: AsyncDatabase) -> None:
    # One interview per member, even if two starts arrive at the same moment.
    await database.interviews.create_index("user_id", unique=True, name="interviews_user_unique")
    # MongoDB deletes the document itself, so an abandoned résumé goes without anyone coming back.
    await database.resume_texts.create_index(
        "last_activity_at", expireAfterSeconds=RESUME_TEXT_DAYS * 86400, name="resume_texts_expire"
    )
    await database.sparks.create_index(
        [("user_id", ASCENDING), ("chapter_id", ASCENDING)], unique=True, name="sparks_user_chapter_unique"
    )
    # One question per reading, however many times the meeting is confirmed.
    await database.reading_questions.create_index(
        "checkout_id", unique=True, name="reading_questions_checkout_unique"
    )
    await database.reading_questions.create_index("author_id", name="reading_questions_author")


class StaleQuestion(Exception):
    """The answer or skip names a question that isn't the one waiting. Nothing was saved."""

    detail = "That isn't the question waiting for an answer."

    def __init__(self, interview: dict, *, already_saved: bool):
        self.interview = interview
        self.already_saved = already_saved


def _already_saved(interview: dict, question_id: str | None, text: str) -> bool:
    """Whether this exact answer to this question is the one saved last. Then a lost reply is all that
    went wrong. Anything else means these words were not saved."""
    turns = interview["turns"]
    return bool(
        question_id
        and turns
        and interview.get("last_question_id") == question_id
        and turns[-1]["answer"] == text.strip()
    )


def check_question(interview: dict, question_id: str | None, text: str) -> None:
    current = interview.get("current")
    if question_id is not None and (current is None or current.get("question_id", "") != question_id):
        raise StaleQuestion(interview, already_saved=_already_saved(interview, question_id, text))


def conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=409, detail=detail)


def answered_count(interview: dict) -> int:
    return sum(1 for turn in interview["turns"] if turn["answer"].strip())


def needs_more_material(interview: dict) -> bool:
    thin_at = interview.get("thin_at")
    return thin_at is not None and answered_count(interview) < thin_at + MORE_ANSWERS_BEFORE_REDRAFT


def _last_reading_answer(interview: dict) -> str | None:
    answers = [turn["answer"] for turn in interview["turns"] if turn["phase"] == "reading"]
    return answers[-1] if answers else None


def interview_view(interview: dict, book: dict | None = None) -> InterviewResponse:
    """`book` is the member's book, if the interview has made one; its blurb is the current one."""
    current = interview.get("current")
    stage = interview["stage"]
    ready = interview.get("ready_for_reveal", False)
    # A skip is saved as a turn with no answer. It unlocks nothing, and it's never counted or shown.
    answered = answered_count(interview)
    proposal = interview.get("proposal")
    needs_more = stage == "interviewing" and needs_more_material(interview)
    if stage == "adding":
        new = interview["turns"][interview["round_start"] :]
        can_finish = any(turn["answer"].strip() for turn in new)
    elif stage == "revising":
        can_finish = revision_status(interview) == "failed"
    elif stage == "drafting":
        can_finish = write_state(interview) == "failed"
    else:
        can_finish = stage == "interviewing" and not needs_more and (ready or answered >= EXIT_AFTER_ANSWERS)
    selection_status, selection_blurb = selection_blurb_state(proposal)
    dropped = interview.get("dropped_for_names", False)
    return InterviewResponse(
        stage=stage,
        question=Question(
            question_id=current.get("question_id", ""),
            text=current["question"],
            phase=current["phase"],
            playback=current.get("playback"),
        )
        if current
        else None,
        topic=interview.get("topic"),
        has_answers=answered > 0,
        can_finish=can_finish,
        ready_for_reveal=ready,
        needs_more=needs_more,
        nearly_done=nearly_done(interview, answered),
        at_limit=needs_more and current is None and len(interview["turns"]) >= engine.MAX_TURNS,
        titles=interview["draft"]["titles"]
        if stage in ("choosing", "finishing", "reviewing") and interview.get("draft")
        else None,
        blurb=book.get("blurb") if book else (interview.get("draft") or {}).get("blurb"),
        step_status=write_state(interview) if stage in ("drafting", "finishing") else None,
        chosen_title=interview.get("chosen_title") if stage == "finishing" else None,
        revision_status=revision_status(interview) if stage == "revising" else None,
        approved_changes=proposal.get("choices") if proposal else None,
        selection_blurb_status=selection_status,
        selection_blurb=selection_blurb,
        changes=[Change.model_validate(change) for change in proposal["changes"]] if proposal else None,
        proposed_blurb=proposal["blurb"] if proposal else None,
        nothing_new=interview.get("nothing_new", False),
        dropped_for_names=dropped,
        reading_question_id=interview.get("reading_question_id") if dropped else None,
        reading_answer=_last_reading_answer(interview) if dropped else None,
        dropped_words=interview.get("dropped_words", []) if dropped else None,
    )


def _timed_out(started: datetime) -> bool:
    started = started if started.tzinfo else started.replace(tzinfo=UTC)
    return datetime.now(UTC) - started > WRITING_TIMEOUT


def write_state(interview: dict) -> str:
    """`write_status`, with writing that died with the server counted as failed."""
    status = interview.get("write_status") or "failed"
    return "failed" if status == "writing" and _timed_out(interview["updated_at"]) else status


def revision_status(interview: dict) -> str:
    return "ready" if interview.get("proposal") else write_state(interview)


def selection_blurb_state(proposal: dict | None) -> tuple[str | None, str | None]:
    """The state of the back cover written for the saved choices, and its text once it's usable."""
    selection = (proposal or {}).get("selection")
    if not selection:
        return None, None
    if selection["approved"] != proposal.get("choices"):
        return "stale", None
    status = selection["status"]
    if status == "writing" and _timed_out(selection["started_at"]):
        return "failed", None
    return status, selection["blurb"] if status == "ready" else None


def nearly_done(interview: dict, answered: int) -> bool:
    if interview["stage"] != "interviewing" or (interview.get("current") or {}).get("phase") == "shape":
        return False
    scripted = get_settings().ai_mode == "scripted"
    return answered >= (NEARLY_DONE_ANSWERS_SCRIPTED if scripted else NEARLY_DONE_ANSWERS)


async def current_view(
    database: AsyncDatabase, user: dict, claude: Claude | None, background: BackgroundTasks
) -> InterviewResponse:
    interview = await get_interview(database, user["_id"])
    failed = (
        revision_status(interview) == "failed"
        if interview["stage"] == "revising"
        else interview["stage"] in WRITERS and write_state(interview) == "failed"
    )
    if claude and failed and not interview.get("write_retried"):
        # The member came back to a failed write: try once more without asking them to.
        interview = await restart_writing(database, claude, interview, background)
    book = (
        await books.get_book_of(database, user["_id"])
        if interview["stage"] in ("reviewing", "done", "adding", "revising")
        else None
    )
    return interview_view(interview, book)


async def get_interview(database: AsyncDatabase, user_id: str) -> dict:
    interview = await database.interviews.find_one({"user_id": user_id})
    if interview is None:
        raise HTTPException(status_code=404, detail="You haven't started your interview yet.")
    return interview


def read_resume(resume_pdf: str) -> str:
    """The text of a base64-encoded PDF. The file itself is never kept."""
    try:
        data = base64.b64decode(resume_pdf, validate=True)
    except binascii.Error:
        data = b""
    if not data.startswith(b"%PDF"):
        raise HTTPException(status_code=422, detail="The résumé must be a PDF.")
    try:
        reader = PdfReader(io.BytesIO(data))
        pages = reader.pages[:MAX_RESUME_PAGES]
        text = "\n".join(page.extract_text() or "" for page in pages).strip()
    except Exception:
        # Résumés are untrusted files, and a broken PDF can fail in many ways inside the parser.
        text = ""
    if not text:
        raise HTTPException(
            status_code=422, detail="We couldn't read any text in that PDF. You can start without it."
        )
    return text[:MAX_RESUME_CHARS]


async def ask_engine(call):
    """Run one engine call; a failure becomes a 502 the member can retry. Nothing saved is lost."""
    try:
        return await call
    except engine.NotEnoughMaterial:
        # Not a failure to retry: the caller asks for more answers instead.
        raise
    # ValueError covers pydantic's ValidationError.
    except (ClaudeRefused, BudgetExceeded, anthropic.APIError, ValueError):
        raise HTTPException(
            status_code=502, detail="The Librarian couldn't answer just now. Please try again."
        ) from None


def turns_of(interview: dict) -> list[Turn]:
    return [Turn.model_validate(turn) for turn in interview["turns"]]


def _answers(interview: dict) -> list[str]:
    return [turn["answer"] for turn in interview["turns"]]


def book_turns(interview: dict) -> list[Turn]:
    """The transcript the book-writing steps read. Questions lose any term only the résumé had, so a
    résumé fact can't come through as the member's. Questions that worked from a spark lose its
    title, for the same reason."""
    turns = turns_of(interview)
    terms = resume_terms.only_in_resume(
        interview.get("resume_terms", []), _answers(interview), interview["_id"]
    )
    for turn in turns:
        turn.question = resume_terms.redact(turn.question, terms, interview["_id"])
    for title in interview.get("asked_spark_titles", []):
        pattern = re.compile(re.escape(title), re.IGNORECASE)
        for turn in turns:
            turn.question = pattern.sub(SPARK_REDACTED, turn.question)
    return turns


def leak_check(interview: dict):
    """A check for book output: does this text carry a term only the résumé had?"""
    terms = resume_terms.only_in_resume(
        interview.get("resume_terms", []), _answers(interview), interview["_id"]
    )
    return lambda text: resume_terms.mentions(text, terms, interview["_id"])


def spark_titles_of(interview: dict) -> list[str]:
    return interview.get("asked_spark_titles", [])


def off_limits_of(interview: dict) -> list[dict]:
    """What the member removed or declined. The Librarian doesn't ask about it or propose it again."""
    return [
        {"title": item["title"], "summary": item["summary"]}
        for item in [*interview.get("removed_chapters", []), *interview.get("declined_changes", [])]
    ]


async def remember_removed(database: AsyncDatabase, interview_id: str, chapters: list[dict]) -> None:
    await database.interviews.update_one(
        {"_id": interview_id},
        {"$push": {"removed_chapters": {"$each": [_remembered(chapter) for chapter in chapters]}}},
    )


def _remembered(chapter: dict) -> dict:
    return {"id": chapter.get("id"), "title": chapter["title"], "summary": chapter["summary"]}


async def resume_text_of(database: AsyncDatabase, interview: dict) -> str | None:
    """The résumé text, if it's still here. Reading it counts as activity, which keeps it from expiring."""
    saved = await database.resume_texts.find_one_and_update(
        {"_id": interview["_id"]}, {"$set": {"last_activity_at": datetime.now(UTC)}}
    )
    return saved["text"] if saved else None


async def write_question(
    database: AsyncDatabase, claude: Claude, interview: dict
) -> tuple[dict | None, str, bool, str | None]:
    """The next question to save, what the member was last talking about, whether that's enough, and
    the spark the question works from."""
    sparks = await spark_cues(database, interview)
    if interview["stage"] == "adding":
        book = await books.get_book_of(database, interview["user_id"])
        turn = await ask_engine(
            engine.next_adding_turn(
                claude,
                turns=turns_of(interview),
                round_start=interview["round_start"],
                chapters=[DraftChapter.model_validate(chapter) for chapter in book["chapters"]],
                sparks=sparks,
                off_limits=off_limits_of(interview),
            )
        )
        question = {"question": turn.question, "phase": "adding", "playback": None}
        return None if turn.done else question, turn.topic, turn.done, turn.spark_id
    turn = await ask_engine(
        engine.next_turn(
            claude,
            turns=turns_of(interview),
            resume_text=await resume_text_of(database, interview),
            sparks=sparks,
            more_material=needs_more_material(interview),
        )
    )
    ready = turn.ready_for_reveal
    question = None if ready else turn.model_dump(include={"question", "phase", "playback"})
    return question, turn.topic, ready, turn.spark_id


async def ask_next_question(database: AsyncDatabase, claude: Claude, interview: dict) -> dict:
    """Write the next question for an interview that is waiting for one, and save it. At the turn
    limit with too few answers for any book, it stops and lets the member decide (`at_limit`)."""
    if (
        interview["stage"] == "interviewing"
        and len(interview["turns"]) >= engine.MAX_TURNS
        and answered_count(interview) < engine.MIN_ANSWERS
        and not needs_more_material(interview)
    ):
        return await database.interviews.find_one_and_update(
            {"_id": interview["_id"]},
            {
                "$set": {
                    "thin_at": answered_count(interview),
                    "ready_for_reveal": False,
                    "updated_at": datetime.now(UTC),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
    question, topic, ready, spark_id = await write_question(database, claude, interview)
    if question:
        question["question_id"] = str(uuid4())
    updated = await database.interviews.find_one_and_update(
        # Only if no other request has written the question in the meantime.
        {"_id": interview["_id"], "stage": interview["stage"], "current": None},
        {
            "$set": {
                "current": question,
                "topic": topic,
                "ready_for_reveal": ready,
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if updated and spark_id and question:
        updated = await use_spark(database, updated, spark_id)
    return updated or await get_interview(database, interview["user_id"])


async def start(database: AsyncDatabase, claude: Claude, user: dict, resume_pdf: str | None) -> dict:
    # A member with a book adds to it (POST /interview/reopen). They can't start over.
    if await books.get_book_of(database, user["_id"]) is not None:
        raise conflict("You already have a book.")
    resume_text = await run_in_threadpool(read_resume, resume_pdf) if resume_pdf else None
    now = datetime.now(UTC)
    interview_id = str(uuid4())
    interview = {
        "_id": interview_id,
        "user_id": user["_id"],
        "stage": "interviewing",
        "resume_terms": resume_terms.resume_terms(resume_text, interview_id) if resume_text else [],
        "turns": [],
        "current": None,
        "topic": None,
        "ready_for_reveal": False,
        "draft": None,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await database.interviews.insert_one(interview)
    except DuplicateKeyError:
        raise conflict("You've already started your interview.") from None
    if resume_text:
        await database.resume_texts.insert_one(
            {"_id": interview_id, "text": resume_text, "last_activity_at": now}
        )
    return await ask_next_question(database, claude, interview)


async def ask_again(database: AsyncDatabase, claude: Claude, user: dict) -> dict:
    """Write the waiting question if an earlier attempt failed. Does nothing if one is already there."""
    interview = await get_interview(database, user["_id"])
    if interview["stage"] not in ASKING_STAGES:
        raise conflict("The interview is over.")
    if interview["current"] is not None or interview["ready_for_reveal"]:
        return interview
    return await ask_next_question(database, claude, interview)


async def answer(
    database: AsyncDatabase,
    claude: Claude,
    user: dict,
    text: str,
    *,
    shape: bool,
    question_id: str | None = None,
) -> dict:
    """Save the answer to the waiting question, then ask the next one. `question_id` is the question
    the member was looking at: a resend after a lost response must not land on the next one."""
    interview = await get_interview(database, user["_id"])
    check_question(interview, question_id, text)
    current = interview["current"]
    if interview["stage"] not in ASKING_STAGES or current is None:
        raise conflict("There's no question waiting for an answer.")
    if (current["phase"] == "shape") != shape:
        raise conflict("This step is the Shape step." if not shape else "This isn't the Shape step.")
    turn = {"question": current["question"], "answer": text, "phase": current["phase"]}
    # Saved before the next question is written, so a failure there never loses the answer.
    saved = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": interview["stage"], "current": current},
        {
            "$push": {"turns": turn},
            "$set": {
                "current": None,
                "last_question_id": current.get("question_id"),
                "updated_at": datetime.now(UTC),
            },
        },
        return_document=ReturnDocument.AFTER,
    )
    if saved is None:
        latest = await get_interview(database, user["_id"])
        raise StaleQuestion(latest, already_saved=_already_saved(latest, question_id, text))
    return await ask_next_question(database, claude, saved)


async def skip(database: AsyncDatabase, claude: Claude, user: dict, question_id: str) -> dict:
    """Move past the waiting question, saved with an empty answer. Not on the Shape step, which
    needs a confirmation or a correction (docs/review/decisions.md, row 6)."""
    return await answer(database, claude, user, "", shape=False, question_id=question_id)


async def save_last_answer(database: AsyncDatabase, interview: dict, text: str) -> dict:
    """Save what was in the field when the member chose to finish, with no question after it. Only
    if finishing is allowed with it counted, so a refused finish leaves the question waiting."""
    current = interview["current"]
    if interview["stage"] not in ASKING_STAGES or current is None:
        raise conflict("There's no question waiting for an answer.")
    turn = {"question": current["question"], "answer": text, "phase": current["phase"]}
    if not interview_view({**interview, "turns": [*interview["turns"], turn]}).can_finish:
        raise conflict("Keep going a little longer first.")
    saved = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": interview["stage"], "current": current},
        {
            "$push": {"turns": turn},
            "$set": {
                "current": None,
                "last_question_id": current.get("question_id"),
                "updated_at": datetime.now(UTC),
            },
        },
        return_document=ReturnDocument.AFTER,
    )
    if saved is None:
        raise conflict("That question was already answered.")
    return saved


async def finish(
    database: AsyncDatabase,
    claude: Claude,
    user: dict,
    background: BackgroundTasks,
    answer_text: str | None = None,
    question_id: str | None = None,
) -> dict:
    """End the interview and write the pool of chapters and the three titles. `answer_text` is
    saved first, so words in the field are never dropped."""
    interview = await get_interview(database, user["_id"])
    if answer_text is not None:
        check_question(interview, question_id, answer_text)
        interview = await save_last_answer(database, interview, answer_text)
    if interview["stage"] in ("adding", "revising"):
        return await finish_round(database, claude, interview, background)
    if interview["stage"] == "drafting":
        if write_state(interview) == "failed":
            return await restart_writing(database, claude, interview, background)
        return interview
    if interview["stage"] != "interviewing":
        raise conflict("The interview is already over.")
    if not interview_view(interview).can_finish:
        raise conflict("Keep going a little longer first.")
    # Below the floor a draft can't work, so don't pay for one.
    if answered_count(interview) < engine.MIN_ANSWERS:
        return await ask_for_more_material(database, claude, interview)
    moved = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": "interviewing"},
        {
            "$set": {
                "stage": "drafting",
                "write_status": "writing",
                "write_retried": False,
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if moved is None:
        raise conflict("The interview is already over.")
    background.add_task(write_draft, database, claude, moved["_id"])
    return moved


async def _write_failed(database: AsyncDatabase, interview_id: str, stage: str) -> None:
    logger.exception("Couldn't finish the %s step for interview %s", stage, interview_id)
    await database.interviews.update_one(
        {"_id": interview_id, "stage": stage},
        {"$set": {"write_status": "failed", "updated_at": datetime.now(UTC)}},
    )


async def write_draft(database: AsyncDatabase, claude: Claude, interview_id: str) -> None:
    """Runs in the background: the pool of chapters and the three titles."""
    interview = await database.interviews.find_one({"_id": interview_id, "stage": "drafting"})
    if interview is None:
        return
    try:
        draft = await engine.draft_book(
            claude,
            turns=book_turns(interview),
            leaks=leak_check(interview),
            spark_titles=spark_titles_of(interview),
        )
    except engine.NotEnoughMaterial:
        with contextlib.suppress(HTTPException):  # A failed question can be asked again.
            await ask_for_more_material(database, claude, interview)
        return
    except Exception:
        await _write_failed(database, interview_id, "drafting")
        return
    updated = await database.interviews.find_one_and_update(
        {"_id": interview_id, "stage": "drafting"},
        {
            "$set": {
                "stage": "choosing",
                "draft": draft.model_dump(),
                "current": None,
                "write_status": None,
                "updated_at": datetime.now(UTC),
            }
        },
    )
    if updated is not None:
        # The interview has ended, so the résumé text goes (docs/trove.md §4).
        await database.resume_texts.delete_one({"_id": interview_id})


async def ask_for_more_material(database: AsyncDatabase, claude: Claude, interview: dict) -> dict:
    """A draft found too little, and trying again can't help. Carry on on new ground: on the waiting
    question if there is one, on a new one if not, or stop at the turn limit and let the member decide."""
    updated = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": {"$in": ["interviewing", "drafting"]}},
        {
            "$set": {
                "stage": "interviewing",
                "write_status": None,
                "thin_at": answered_count(interview),
                "ready_for_reveal": False,
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise conflict("The interview is already over.")
    if updated["current"] is None and len(updated["turns"]) < engine.MAX_TURNS:
        return await ask_next_question(database, claude, updated)
    return updated


async def reviewing_interview(database: AsyncDatabase, user: dict) -> dict:
    interview = await get_interview(database, user["_id"])
    if interview["stage"] != "reviewing":
        raise conflict("There's no book waiting for review.")
    return interview


async def choose_title(
    database: AsyncDatabase, claude: Claude, user: dict, index: int, background: BackgroundTasks
) -> dict:
    """Choose the title, and write the book to match in the background. After a failed write this
    tries again, with whichever title is sent."""
    interview = await get_interview(database, user["_id"])
    failed = interview["stage"] == "finishing" and write_state(interview) == "failed"
    if interview["stage"] == "finishing" and not failed:
        return interview
    if interview["stage"] != "choosing" and not failed:
        raise conflict("There are no titles to choose from.")
    moved = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": interview["stage"], "updated_at": interview["updated_at"]},
        {
            "$set": {
                "stage": "finishing",
                "chosen_title": interview["draft"]["titles"][index]["title"],
                "write_status": "writing",
                "write_retried": False,
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if moved is None:
        return await get_interview(database, user["_id"])
    background.add_task(write_book, database, claude, moved["_id"])
    return moved


async def write_book(database: AsyncDatabase, claude: Claude, interview_id: str) -> None:
    """Runs in the background: finish the book to match the chosen title, and save it as a draft."""
    interview = await database.interviews.find_one({"_id": interview_id, "stage": "finishing"})
    if interview is None:
        return
    try:
        finished = await engine.finish_book(
            claude,
            turns=book_turns(interview),
            draft=Draft.model_validate(interview["draft"]),
            title=interview["chosen_title"],
            leaks=leak_check(interview),
            spark_titles=spark_titles_of(interview),
        )
    except Exception:
        await _write_failed(database, interview_id, "finishing")
        return
    # A book that already exists was made by an earlier write of this same step.
    with contextlib.suppress(books.BookExists):
        await books.create_draft_book(
            database,
            author_id=interview["user_id"],
            title=interview["chosen_title"],
            chapters=[chapter.model_dump() for chapter in finished.chapters],
            blurb=finished.blurb,
        )
    await database.interviews.update_one(
        {"_id": interview_id, "stage": "finishing"},
        {"$set": {"stage": "reviewing", "write_status": None, "updated_at": datetime.now(UTC)}},
    )


async def own_draft(database: AsyncDatabase, user: dict, chapter_id: str) -> dict:
    book = await books.get_book_of(database, user["_id"])
    if book is None or all(chapter["id"] != chapter_id for chapter in book["chapters"]):
        raise HTTPException(status_code=404, detail="That chapter isn't in your book.")
    return book


async def remove_chapter(
    database: AsyncDatabase, claude: Claude, user: dict, chapter_id: str
) -> MyBookResponse:
    interview = await reviewing_interview(database, user)
    book = await own_draft(database, user, chapter_id)
    remaining = [DraftChapter.model_validate(c) for c in book["chapters"] if c["id"] != chapter_id]
    if len(remaining) < books.MIN_CHAPTERS:
        raise conflict(f"A book needs at least {books.MIN_CHAPTERS} chapters.")
    # The book no longer covers what it did, so the back cover is rewritten for what's left. A rewrite
    # keeps each chapter's topic, so it leaves the blurb alone.
    blurb = await ask_engine(
        engine.write_blurb(
            claude, turns=book_turns(interview), chapters=remaining, leaks=leak_check(interview)
        )
    )
    gone = next(chapter for chapter in book["chapters"] if chapter["id"] == chapter_id)
    book = await books.remove_chapter(database, user["_id"], chapter_id, blurb=blurb)
    if book is None:
        raise conflict(f"A book needs at least {books.MIN_CHAPTERS} chapters.")
    await remember_removed(database, interview["_id"], [gone])
    return books.my_book_view(book)


async def rewrite_chapter(
    database: AsyncDatabase, claude: Claude, user: dict, chapter_id: str
) -> MyBookResponse:
    interview = await reviewing_interview(database, user)
    book = await own_draft(database, user, chapter_id)
    chapters = [DraftChapter.model_validate(chapter) for chapter in book["chapters"]]
    current = next(chapter for chapter in book["chapters"] if chapter["id"] == chapter_id)
    chapter = await ask_engine(
        engine.rewrite_chapter(
            claude,
            turns=book_turns(interview),
            chapters=chapters,
            chapter_id=chapter_id,
            leaks=leak_check(interview),
        )
    )
    if chapter.title == current["title"] and chapter.summary == current["summary"]:
        return books.my_book_view(book, rewrite_unchanged=True)
    updated = await books.replace_chapter(
        database,
        user["_id"],
        {
            **chapter.model_dump(),
            "id": chapter_id,
            "previous": {"title": current["title"], "summary": current["summary"]},
        },
    )
    if updated is None:
        raise conflict("Your book is already on the shelf.")
    return books.my_book_view(updated)


async def restore_chapter(database: AsyncDatabase, user: dict, chapter_id: str) -> MyBookResponse:
    """Go back to a chapter's last version, during the review."""
    await reviewing_interview(database, user)
    await own_draft(database, user, chapter_id)
    book = await books.restore_chapter(database, user["_id"], chapter_id)
    if book is None:
        raise conflict("There's no earlier version of that chapter.")
    return books.my_book_view(book)


async def rewrite_blurb(database: AsyncDatabase, claude: Claude, user: dict) -> MyBookResponse:
    """Write the draft's back cover again."""
    interview = await reviewing_interview(database, user)
    book = await books.get_book_of(database, user["_id"])
    blurb = await ask_engine(
        engine.write_blurb(
            claude,
            turns=book_turns(interview),
            chapters=[DraftChapter.model_validate(chapter) for chapter in book["chapters"]],
            leaks=leak_check(interview),
        )
    )
    book = await books.set_draft_blurb(database, user["_id"], blurb, previous=book.get("blurb"))
    if book is None:
        raise conflict("Your book is already on the shelf.")
    return books.my_book_view(book)


async def restore_blurb(database: AsyncDatabase, user: dict) -> MyBookResponse:
    """Go back to the last back cover, during the review."""
    await reviewing_interview(database, user)
    book = await books.restore_draft_blurb(database, user["_id"])
    if book is None:
        raise conflict("There's no earlier back cover.")
    return books.my_book_view(book)


async def change_title(database: AsyncDatabase, claude: Claude, user: dict, index: int) -> MyBookResponse:
    """Change to another of the three titles. The book is finished again to match, from the pool,
    without any chapter the member removed. Earlier rewrites of chapters may be replaced."""
    interview = await reviewing_interview(database, user)
    book = await books.get_book_of(database, user["_id"])
    if not interview.get("draft"):
        raise conflict("There are no other titles to choose from.")
    draft = Draft.model_validate(interview["draft"])
    title = draft.titles[index].title
    if title == book["title"]:
        return books.my_book_view(book)
    removed = {item.get("id") for item in interview.get("removed_chapters", [])}
    pool = [chapter for chapter in draft.pool if chapter.id not in removed]
    if len(pool) < books.MIN_CHAPTERS:
        raise conflict(f"A book needs at least {books.MIN_CHAPTERS} chapters.")
    finished = await ask_engine(
        engine.finish_book(
            claude,
            turns=book_turns(interview),
            draft=draft.model_copy(update={"pool": pool}),
            title=title,
            leaks=leak_check(interview),
            spark_titles=spark_titles_of(interview),
        )
    )
    book = await books.retitle_draft(
        database,
        user["_id"],
        title=title,
        chapters=[chapter.model_dump() for chapter in finished.chapters],
        blurb=finished.blurb,
    )
    if book is None:
        raise conflict("Your book is already on the shelf.")
    return books.my_book_view(book)


async def put_on_shelf(database: AsyncDatabase, user: dict) -> MyBookResponse:
    interview = await reviewing_interview(database, user)
    book = await books.put_on_shelf(database, user["_id"])
    if book is None:
        raise conflict("Your book is already on the shelf.")
    await database.interviews.update_one(
        {"_id": interview["_id"]}, {"$set": {"stage": "done", "updated_at": datetime.now(UTC)}}
    )
    return books.my_book_view(book)


# Adding to a book on the shelf (I3).


async def interview_for_book(database: AsyncDatabase, user_id: str) -> dict:
    """The member's interview. A book on the shelf with no interview behind it (seeded, say) gets
    one with empty turns, so it can be added to like any other."""
    interview = await database.interviews.find_one({"user_id": user_id})
    if interview is not None:
        return interview
    book = await books.get_book_of(database, user_id)
    if book is None or book["status"] != books.ON_SHELF:
        raise HTTPException(status_code=404, detail="You haven't started your interview yet.")
    now = datetime.now(UTC)
    interview = {
        "_id": str(uuid4()),
        "user_id": user_id,
        "stage": "done",
        "turns": [],
        "current": None,
        "topic": None,
        "ready_for_reveal": False,
        "draft": None,
        "created_at": now,
        "updated_at": now,
    }
    with contextlib.suppress(DuplicateKeyError):
        await database.interviews.insert_one(interview)
    return await get_interview(database, user_id)


async def reopen(database: AsyncDatabase, claude: Claude, user: dict) -> dict:
    """Start a short new round of questions. The earlier turns stay as grounding material, and the
    book on the shelf doesn't change unless the member approves a change."""
    interview = await interview_for_book(database, user["_id"])
    if interview["stage"] == "adding":
        return interview
    if interview["stage"] == "revising":
        raise conflict("Your proposed changes are waiting for you.")
    book = await books.get_book_of(database, user["_id"])
    if interview["stage"] != "done" or book is None or book["status"] != books.ON_SHELF:
        raise conflict("Only a book on the shelf can be added to.")
    opened = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": "done"},
        {
            "$set": {
                "stage": "adding",
                "round_start": len(interview["turns"]),
                "current": None,
                "ready_for_reveal": False,
                "nothing_new": False,
                "dropped_for_names": False,
                "sparks_asked": 0,
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if opened is None:
        raise conflict("Only a book on the shelf can be added to.")
    return await ask_next_question(database, claude, opened)


async def finish_round(
    database: AsyncDatabase, claude: Claude, interview: dict, background: BackgroundTasks
) -> dict:
    """Move to revising and write the proposed changes in the background, so the member can leave.
    GET /interview reports `revision_status`."""
    if interview["stage"] == "revising":
        status = revision_status(interview)
        if status == "ready":
            raise conflict("Your proposed changes are waiting for you.")
        if status == "writing":
            return interview
        return await restart_writing(database, claude, interview, background)
    if not interview_view(interview).can_finish:
        raise conflict("Answer at least one question first.")
    moved = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": "adding"},
        {
            "$set": {
                "stage": "revising",
                "current": None,
                "proposal": None,
                # Anything saved after this point waits for the next proposal.
                "round_end": len(interview["turns"]),
                "write_status": "writing",
                "write_retried": False,
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if moved is None:
        return await get_interview(database, interview["user_id"])
    background.add_task(write_proposal, database, claude, moved["_id"])
    return moved


async def restart_writing(
    database: AsyncDatabase, claude: Claude, interview: dict, background: BackgroundTasks
) -> dict:
    """Run a failed background step again. Only one request gets to, however many arrive."""
    moved = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": interview["stage"], "updated_at": interview["updated_at"]},
        {"$set": {"write_status": "writing", "write_retried": True, "updated_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER,
    )
    if moved is None:
        return await get_interview(database, interview["user_id"])
    background.add_task(WRITERS[interview["stage"]], database, claude, moved["_id"])
    return moved


async def write_proposal(database: AsyncDatabase, claude: Claude, interview_id: str) -> None:
    """Runs in the background, with nobody to send an error to, so every failure lands in `write_status`."""
    interview = await database.interviews.find_one({"_id": interview_id})
    if interview is None or interview["stage"] != "revising" or interview.get("proposal"):
        return
    try:
        book = await books.get_book_of(database, interview["user_id"])
        names = await full_names_of(database, [interview["user_id"]])
        turns = book_turns(interview)[: interview["round_end"]]
        revision = await engine.revise_book(
            claude,
            turns=turns,
            round_start=interview["round_start"],
            chapters=[DraftChapter.model_validate(chapter) for chapter in book["chapters"]],
            blurb=book.get("blurb"),
            off_limits=off_limits_of(interview),
            member_names=list(names.values()),
            spark_titles=spark_titles_of(interview),
            leaks=leak_check(interview),
        )
    except Exception:
        logger.exception("Couldn't write the proposed changes for interview %s", interview_id)
        await database.interviews.update_one(
            {"_id": interview_id, "stage": "revising", "proposal": None},
            {"$set": {"write_status": "failed", "updated_at": datetime.now(UTC)}},
        )
        return
    if revision.changes:
        await database.interviews.update_one(
            {"_id": interview_id, "stage": "revising", "proposal": None},
            {
                "$set": {
                    "proposal": revision.model_dump(),
                    "write_status": "ready",
                    "updated_at": datetime.now(UTC),
                }
            },
        )
        return
    # Nothing usable: say so plainly and go back to the book as it was. If only a name stood in the
    # way, the question opens again, so the member can say it without the name.
    if revision.dropped_for_names and interview.get("reading_question_id"):
        await database.reading_questions.update_one(
            {"_id": interview["reading_question_id"]}, {"$set": {"answered_at": None}}
        )
    next_round = await end_revising(
        database,
        interview_id,
        {
            "nothing_new": True,
            "dropped_for_names": revision.dropped_for_names,
            "dropped_words": revision.dropped_words,
        },
    )
    if next_round:
        await write_proposal(database, claude, interview_id)


async def end_revising(database: AsyncDatabase, interview_id: str, fields: dict) -> bool:
    """Leave revising. A reading answer saved meanwhile starts its own proposal; True if one did."""
    interview = await database.interviews.find_one({"_id": interview_id})
    round_end = interview.get("round_end", len(interview["turns"]))
    now = datetime.now(UTC)
    if len(interview["turns"]) > round_end:
        await database.interviews.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    **fields,
                    "proposal": None,
                    "round_start": round_end,
                    "round_end": len(interview["turns"]),
                    "write_status": "writing",
                    "write_retried": False,
                    "updated_at": now,
                }
            },
        )
        return True
    await database.interviews.update_one(
        {"_id": interview_id},
        {"$set": {**fields, "stage": "done", "proposal": None, "current": None, "updated_at": now}},
    )
    return False


def _selected(proposal: dict, approved: list[str]) -> list[dict]:
    chosen = set(approved)
    if chosen - {change["id"] for change in proposal["changes"]}:
        raise HTTPException(status_code=422, detail="That isn't one of the proposed changes.")
    return [change for change in proposal["changes"] if change["id"] in chosen]


def _revision_parts(changes: list[dict]) -> dict:
    return {
        "improved": [_approved_chapter(c, c["chapter_id"]) for c in changes if c["kind"] == "improve"],
        "added": [
            {**_approved_chapter(c, c["id"]), "position": c.get("position")}
            for c in changes
            if c["kind"] == "new"
        ],
        "removed": [c["chapter_id"] for c in changes if c["kind"] == "remove"],
    }


def _shown_blurb(proposal: dict, changes: list[dict]) -> str | None:
    """The back cover the member has already seen for exactly this selection, if there is one."""
    if len(changes) == len(proposal["changes"]) and proposal.get("blurb"):
        return proposal["blurb"]
    selection = proposal.get("selection") or {}
    if selection.get("status") == "ready" and selection["approved"] == sorted(c["id"] for c in changes):
        return selection["blurb"]
    return None


async def revising_proposal(database: AsyncDatabase, user: dict) -> tuple[dict, dict]:
    interview = await get_interview(database, user["_id"])
    proposal = interview.get("proposal")
    if interview["stage"] != "revising" or not proposal:
        raise conflict("There are no proposed changes to review.")
    return interview, proposal


async def save_choices(database: AsyncDatabase, user: dict, approved: list[str]) -> dict:
    """Save the member's choices as they're pressed, so they survive leaving. Nothing is applied."""
    interview, proposal = await revising_proposal(database, user)
    choices = sorted(change["id"] for change in _selected(proposal, approved))
    updated = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": "revising"},
        {"$set": {"proposal.choices": choices}},
        return_document=ReturnDocument.AFTER,
    )
    return updated or await get_interview(database, user["_id"])


async def start_selection_blurb(
    database: AsyncDatabase, claude: Claude, user: dict, background: BackgroundTasks
) -> dict:
    """Get the back cover for the saved choices, for the member to read before confirming. With some
    declined it's written in the background, because the proposed one may describe a declined chapter."""
    interview, proposal = await revising_proposal(database, user)
    if proposal.get("choices") is None:
        raise conflict("Choose which changes you want first.")
    status, _ = selection_blurb_state(proposal)
    if status in ("writing", "ready"):
        return interview
    changes = _selected(proposal, proposal["choices"])
    book = await books.get_book_of(database, user["_id"])
    selection = {
        "approved": proposal["choices"],
        "blurb": None,
        "status": "writing",
        "started_at": datetime.now(UTC),
    }
    shown = _full_proposal_blurb(proposal, changes) if changes else book.get("blurb")
    if shown or not changes:
        selection |= {"blurb": shown, "status": "ready"}
    updated = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": "revising"},
        {"$set": {"proposal.selection": selection}},
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        return await get_interview(database, user["_id"])
    if selection["status"] == "writing":
        background.add_task(write_selection_blurb, database, claude, interview["_id"], proposal["choices"])
    return updated


def _full_proposal_blurb(proposal: dict, changes: list[dict]) -> str | None:
    return proposal.get("blurb") if len(changes) == len(proposal["changes"]) else None


async def write_selection_blurb(
    database: AsyncDatabase, claude: Claude, interview_id: str, approved: list[str]
) -> None:
    """Runs in the background. If the choices have changed by the time it lands, it's marked stale by
    comparison with them, and never applied."""
    interview = await database.interviews.find_one({"_id": interview_id, "stage": "revising"})
    if interview is None or not interview.get("proposal"):
        return
    this_write = {"_id": interview_id, "stage": "revising", "proposal.selection.approved": approved}
    try:
        book = await books.get_book_of(database, interview["user_id"])
        changes = _selected(interview["proposal"], approved)
        chapters = books.revised_chapters(book["chapters"], **_revision_parts(changes))
        blurb = await engine.write_blurb(
            claude,
            turns=book_turns(interview),
            chapters=[DraftChapter.model_validate(chapter) for chapter in chapters],
            leaks=leak_check(interview),
        )
    except Exception:
        logger.exception("Couldn't write the back cover for interview %s", interview_id)
        await database.interviews.update_one(this_write, {"$set": {"proposal.selection.status": "failed"}})
        return
    await database.interviews.update_one(
        this_write, {"$set": {"proposal.selection.status": "ready", "proposal.selection.blurb": blurb}}
    )


async def nothing_open(database: AsyncDatabase, user_id: str) -> bool:
    """Contract for books: no questions or changes are open on this member's book, so it can be undone."""
    interview = await database.interviews.find_one({"user_id": user_id}, {"stage": 1})
    return interview is None or interview["stage"] == "done"


async def apply_revision(
    database: AsyncDatabase,
    claude: Claude,
    user: dict,
    approved: list[str],
    blurb_choice: str,
    background: BackgroundTasks,
) -> MyBookResponse:
    """Apply the approved changes and drop the rest. The book on the shelf changes only here, and
    only with text the member was shown."""
    interview, proposal = await revising_proposal(database, user)
    changes = _selected(proposal, approved)
    book = await books.get_book_of(database, user["_id"])
    if changes:
        blurb = None
        if blurb_choice == "use":
            blurb = _shown_blurb(proposal, changes)
            if blurb is None:
                raise conflict("Read the back cover for this selection first.")
        parts = _revision_parts(changes)
        removed = [c for c in book["chapters"] if c["id"] in parts["removed"]]
        book = await books.apply_revision(database, user["_id"], **parts, blurb=blurb)
        if book is None:
            raise conflict("That can't be applied to your book as it is now. Please look at it again.")
        if removed:
            await remember_removed(database, interview["_id"], removed)
    declined = [
        _remembered(change)
        for change in proposal["changes"]
        if change not in changes and change["kind"] != "remove"
    ]
    if declined:
        await database.interviews.update_one(
            {"_id": interview["_id"]}, {"$push": {"declined_changes": {"$each": declined}}}
        )
    if await end_revising(database, interview["_id"], {}):
        # A reading answer saved meanwhile is being written up, so this can't be undone just yet.
        background.add_task(write_proposal, database, claude, interview["_id"])
        return books.my_book_view(book, undoable=False)
    return books.my_book_view(book)


def _approved_chapter(change: dict, chapter_id: str) -> dict:
    return {
        "id": chapter_id,
        "title": change["title"],
        "summary": change["summary"],
        "quotes": change["quotes"],
    }


async def propose_removal(database: AsyncDatabase, user: dict, chapter_id: str) -> dict:
    """Take a chapter out of a book on the shelf. It goes through the same confirm step as any other
    change: nothing happens until POST /interview/revision."""
    interview = await interview_for_book(database, user["_id"])
    book = await books.get_book_of(database, user["_id"])
    if interview["stage"] != "done" or book is None or book["status"] != books.ON_SHELF:
        raise conflict("Finish what's waiting in your book first.")
    chapter = next((c for c in book["chapters"] if c["id"] == chapter_id), None)
    if chapter is None:
        raise HTTPException(status_code=404, detail="That chapter isn't in your book.")
    if len(book["chapters"]) <= books.MIN_CHAPTERS:
        raise conflict(f"A book needs at least {books.MIN_CHAPTERS} chapters.")
    change = Change(
        id=str(uuid4()),
        kind="remove",
        chapter_id=chapter_id,
        title=chapter["title"],
        summary=chapter["summary"],
        quotes=chapter["quotes"],
        note="Takes this chapter out of your book.",
        current={"title": chapter["title"], "summary": chapter["summary"]},
    )
    updated = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": "done"},
        {
            "$set": {
                "stage": "revising",
                "proposal": {"changes": [change.model_dump()], "blurb": None},
                "round_start": len(interview["turns"]),
                "round_end": len(interview["turns"]),
                "write_status": "ready",
                "nothing_new": False,
                "dropped_for_names": False,
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise conflict("Finish what's waiting in your book first.")
    return updated


async def cancel_removal(
    database: AsyncDatabase, claude: Claude, user: dict, background: BackgroundTasks
) -> dict:
    """Back out of a removal the member started: back to `done`, and nothing is recorded as declined."""
    interview, proposal = await revising_proposal(database, user)
    if any(change["kind"] != "remove" for change in proposal["changes"]):
        raise conflict("There's no removal to cancel.")
    if await end_revising(database, interview["_id"], {}):
        background.add_task(write_proposal, database, claude, interview["_id"])
    return await get_interview(database, user["_id"])


async def undo_revision(database: AsyncDatabase, user: dict) -> MyBookResponse:
    """Put the book back as it was before the last applied revision."""
    interview = await interview_for_book(database, user["_id"])
    if interview["stage"] != "done":
        raise conflict("Finish what's waiting in your book first.")
    before = await books.get_book_of(database, user["_id"])
    book = await books.undo_revision(database, user["_id"])
    if book is None:
        raise conflict("There's nothing to undo.")
    restored = {chapter["id"]: chapter for chapter in book["chapters"]}
    undone = [
        _remembered(chapter)
        for chapter in before["chapters"]
        if chapter["id"] not in restored or chapter != restored[chapter["id"]]
    ]
    back = [chapter_id for chapter_id in restored if chapter_id not in {c["id"] for c in before["chapters"]}]
    # What they took back isn't asked about again. A removal they took back is no longer off limits.
    await database.interviews.update_one(
        {"_id": interview["_id"]},
        {
            "$push": {"declined_changes": {"$each": undone}},
            "$pull": {"removed_chapters": {"id": {"$in": back}}},
        },
    )
    return books.my_book_view(book)


# The background steps that can be run again after a failure, by the stage they belong to.
WRITERS = {"drafting": write_draft, "finishing": write_book, "revising": write_proposal}


# Sparks (I5). Private to the member who saved them. Nothing here is ever read for anyone else.


def spark_view(spark: dict) -> SparkResponse:
    return SparkResponse.model_validate({**spark, "id": spark["_id"]})


async def spark_cues(database: AsyncDatabase, interview: dict) -> list[dict]:
    """What the Librarian may work from now: only ids and titles, newest first, up to the round's
    limit. Never a chapter's summary, its author or the title of its book."""
    room = MAX_SPARKS_PER_ROUND - interview.get("sparks_asked", 0)
    if room <= 0:
        return []
    cursor = database.sparks.find({"user_id": interview["user_id"], "used_at": None}, {"chapter_title": 1})
    newest = await cursor.sort([("created_at", DESCENDING), ("_id", DESCENDING)]).limit(room).to_list()
    return [{"id": spark["_id"], "title": spark["chapter_title"]} for spark in newest]


async def use_spark(database: AsyncDatabase, interview: dict, spark_id: str) -> dict:
    """A spark is used only once a question has actually worked from it. Unused ones stay saved."""
    spark = await database.sparks.find_one_and_update(
        {"_id": spark_id, "user_id": interview["user_id"], "used_at": None},
        {"$set": {"used_at": datetime.now(UTC)}},
    )
    if spark is None:
        return interview
    return await database.interviews.find_one_and_update(
        {"_id": interview["_id"]},
        {"$inc": {"sparks_asked": 1}, "$addToSet": {"asked_spark_titles": spark["chapter_title"]}},
        return_document=ReturnDocument.AFTER,
    )


async def add_spark(database: AsyncDatabase, user: dict, book_id: str, chapter_id: str) -> SparkResponse:
    """Save "I have one like this" on a chapter of someone else's book. Saving it twice is fine."""
    book = await books.get_public_book(database, book_id)
    chapter = next((c for c in book["chapters"] if c["id"] == chapter_id), None) if book else None
    if chapter is None:
        raise HTTPException(status_code=404, detail="That chapter isn't on the shelf.")
    if book["author_id"] == user["_id"]:
        raise conflict("This is your own book.")
    existing = await database.sparks.find_one({"user_id": user["_id"], "chapter_id": chapter_id})
    if existing and existing["used_at"] is None:
        return spark_view(existing)
    unused = await database.sparks.count_documents({"user_id": user["_id"], "used_at": None})
    if unused >= MAX_UNUSED_SPARKS:
        raise conflict("You have plenty saved for your next round. Remove one to add another.")
    now = datetime.now(UTC)
    if existing:
        # Used in an earlier round, and saved again: it goes back in for the next one.
        await database.sparks.update_one(
            {"_id": existing["_id"]}, {"$set": {"used_at": None, "created_at": now}}
        )
        return spark_view({**existing, "used_at": None, "created_at": now})
    spark = {
        "_id": str(uuid4()),
        "user_id": user["_id"],
        "book_id": book_id,
        "chapter_id": chapter_id,
        "chapter_title": chapter["title"],
        "created_at": now,
        "used_at": None,
    }
    try:
        await database.sparks.insert_one(spark)
    except DuplicateKeyError:
        return spark_view(await database.sparks.find_one({"user_id": user["_id"], "chapter_id": chapter_id}))
    return spark_view(spark)


async def list_sparks(database: AsyncDatabase, user: dict) -> list[SparkResponse]:
    """The member's own sparks waiting for their next round."""
    cursor = database.sparks.find({"user_id": user["_id"], "used_at": None}).sort("created_at", ASCENDING)
    return [spark_view(spark) for spark in await cursor.to_list()]


async def remove_spark(database: AsyncDatabase, user: dict, spark_id: str) -> None:
    result = await database.sparks.delete_one({"_id": spark_id, "user_id": user["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="That spark isn't yours, or it's gone.")


# The question after a reading (I6).


async def ask_after_reading(database: AsyncDatabase, author_id: str, checkout_id: str) -> None:
    """Contract for checkouts (C4): call once "Did you meet?" confirms the meeting happened. Safe to
    call again. The reader isn't stored here, so they can't reach a prompt or a book."""
    # Two confirmations at the same moment: the other one made it.
    with contextlib.suppress(DuplicateKeyError):
        await database.reading_questions.update_one(
            {"checkout_id": checkout_id},
            {
                "$setOnInsert": {
                    "_id": str(uuid4()),
                    "author_id": author_id,
                    "created_at": datetime.now(UTC),
                    "answered_at": None,
                    "dismissed_at": None,
                }
            },
            upsert=True,
        )


async def list_reading_questions(database: AsyncDatabase, user: dict) -> list[ReadingQuestionResponse]:
    """The newest question waiting, with who the reading was with. Older ones go away after a while."""
    waiting = {"author_id": user["_id"], "answered_at": None, "dismissed_at": None}
    newest = await database.reading_questions.find_one(
        waiting, sort=[("created_at", DESCENDING), ("_id", DESCENDING)]
    )
    if newest is None:
        return []
    now = datetime.now(UTC)
    await database.reading_questions.update_many(
        {
            **waiting,
            "_id": {"$ne": newest["_id"]},
            "created_at": {"$lt": now - timedelta(days=READING_QUESTION_DAYS)},
        },
        {"$set": {"dismissed_at": now}},
    )
    return [
        ReadingQuestionResponse(
            id=newest["_id"],
            question=READING_QUESTION,
            created_at=newest["created_at"],
            reader_name=await _reader_name(database, user["_id"], newest["checkout_id"]),
        )
    ]


async def _reader_name(database: AsyncDatabase, author_id: str, checkout_id: str) -> str | None:
    checkout = await checkouts.get_checkout_for(database, checkout_id, author_id)
    if checkout is None:
        return None
    return (await full_names_of(database, [checkout["reader_id"]])).get(checkout["reader_id"])


async def claim_reading_question(database: AsyncDatabase, user: dict, question_id: str, field: str) -> None:
    """Mark a waiting question answered or dismissed. It can only happen once."""
    claimed = await database.reading_questions.update_one(
        {"_id": question_id, "author_id": user["_id"], "answered_at": None, "dismissed_at": None},
        {"$set": {field: datetime.now(UTC)}},
    )
    if claimed.modified_count == 0:
        raise HTTPException(status_code=404, detail="That question isn't waiting for you.")


async def dismiss_reading_question(database: AsyncDatabase, user: dict, question_id: str) -> None:
    await claim_reading_question(database, user, question_id, "dismissed_at")


async def answer_reading_question(
    database: AsyncDatabase,
    claude: Claude,
    user: dict,
    question_id: str,
    text: str,
    background: BackgroundTasks,
) -> dict:
    """Save the answer as a turn. From `done` it goes to revise right away. During a round it's
    included when the round finishes. While changes are waiting, it runs after the member decides."""
    interview = await interview_for_book(database, user["_id"])
    if interview["stage"] not in ("done", "adding", "revising"):
        raise conflict("Finish your book first.")
    await claim_reading_question(database, user, question_id, "answered_at")
    await database.interviews.update_one(
        {"_id": interview["_id"]}, {"$set": {"reading_question_id": question_id}}
    )
    turn = {"question": READING_QUESTION, "answer": text, "phase": "reading"}
    now = datetime.now(UTC)
    if interview["stage"] == "done":
        count = len(interview["turns"])
        updated = await database.interviews.find_one_and_update(
            {"_id": interview["_id"], "stage": "done"},
            {
                "$push": {"turns": turn},
                "$set": {
                    "stage": "revising",
                    "round_start": count,
                    "round_end": count + 1,
                    "proposal": None,
                    "current": None,
                    "nothing_new": False,
                    "dropped_for_names": False,
                    "write_status": "writing",
                    "write_retried": False,
                    "updated_at": now,
                },
            },
            return_document=ReturnDocument.AFTER,
        )
        if updated is not None:
            background.add_task(write_proposal, database, claude, updated["_id"])
            return updated
    # In a round or waiting on a decision. `updated_at` stays, as nothing about the state has moved.
    return await database.interviews.find_one_and_update(
        {"_id": interview["_id"]}, {"$push": {"turns": turn}}, return_document=ReturnDocument.AFTER
    )
