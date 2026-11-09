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
from trove.interview import engine
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
    await database.sparks.create_index(
        [("user_id", ASCENDING), ("chapter_id", ASCENDING)], unique=True, name="sparks_user_chapter_unique"
    )
    # One question per reading, however many times the meeting is confirmed.
    await database.reading_questions.create_index(
        "checkout_id", unique=True, name="reading_questions_checkout_unique"
    )
    await database.reading_questions.create_index("author_id", name="reading_questions_author")


def conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=409, detail=detail)


def interview_view(interview: dict, book: dict | None = None) -> InterviewResponse:
    """`book` is the member's book, if the interview has made one; its blurb is the current one."""
    current = interview.get("current")
    stage = interview["stage"]
    ready = interview.get("ready_for_reveal", False)
    # A skip is saved as a turn with no answer. It unlocks nothing, and it's never counted or shown.
    answered = sum(1 for turn in interview["turns"] if turn["answer"].strip())
    proposal = interview.get("proposal")
    if stage == "adding":
        new = interview["turns"][interview["round_start"] :]
        can_finish = any(turn["answer"].strip() for turn in new)
    elif stage == "revising":
        can_finish = revision_status(interview) == "failed"
    else:
        can_finish = stage == "interviewing" and (ready or answered >= EXIT_AFTER_ANSWERS)
    return InterviewResponse(
        stage=stage,
        question=Question(text=current["question"], phase=current["phase"], playback=current.get("playback"))
        if current
        else None,
        topic=interview.get("topic"),
        has_answers=answered > 0,
        can_finish=can_finish,
        ready_for_reveal=ready,
        titles=interview["draft"]["titles"] if stage == "choosing" else None,
        blurb=book.get("blurb") if book else (interview.get("draft") or {}).get("blurb"),
        revision_status=revision_status(interview) if stage == "revising" else None,
        changes=[Change.model_validate(change) for change in proposal["changes"]] if proposal else None,
        proposed_blurb=proposal["blurb"] if proposal else None,
        nothing_new=interview.get("nothing_new", False),
    )


def revision_status(interview: dict) -> str:
    if interview.get("proposal"):
        return "ready"
    status = interview.get("write_status", "failed")
    if status == "writing":
        updated_at = interview["updated_at"]
        started = updated_at if updated_at.tzinfo else updated_at.replace(tzinfo=UTC)
        if datetime.now(UTC) - started > WRITING_TIMEOUT:
            return "failed"
    return status


async def current_view(
    database: AsyncDatabase, user: dict, claude: Claude | None, background: BackgroundTasks
) -> InterviewResponse:
    interview = await get_interview(database, user["_id"])
    if (
        claude
        and interview["stage"] == "revising"
        and revision_status(interview) == "failed"
        and not interview.get("write_retried")
    ):
        # The member came back to a failed write: try once more without asking them to.
        interview = await restart_writing(database, claude, interview, background, retried=True)
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
    # ValueError covers pydantic's ValidationError.
    except (ClaudeRefused, BudgetExceeded, anthropic.APIError, ValueError):
        raise HTTPException(
            status_code=502, detail="The Librarian couldn't answer just now. Please try again."
        ) from None


def turns_of(interview: dict) -> list[Turn]:
    return [Turn.model_validate(turn) for turn in interview["turns"]]


def book_turns(interview: dict) -> list[Turn]:
    """The transcript the book-writing steps read. Questions that worked from a spark lose its title,
    so someone else's words can't come through as this member's."""
    turns = turns_of(interview)
    for title in interview.get("asked_spark_titles", []):
        pattern = re.compile(re.escape(title), re.IGNORECASE)
        for turn in turns:
            turn.question = pattern.sub(SPARK_REDACTED, turn.question)
    return turns


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
            claude, turns=turns_of(interview), resume_text=interview.get("resume_text"), sparks=sparks
        )
    )
    ready = turn.ready_for_reveal
    question = None if ready else turn.model_dump(include={"question", "phase", "playback"})
    return question, turn.topic, ready, turn.spark_id


async def ask_next_question(database: AsyncDatabase, claude: Claude, interview: dict) -> dict:
    """Write the next question for an interview that is waiting for one, and save it."""
    question, topic, ready, spark_id = await write_question(database, claude, interview)
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
    interview = {
        "_id": str(uuid4()),
        "user_id": user["_id"],
        "stage": "interviewing",
        "turns": [],
        "current": None,
        "topic": None,
        "ready_for_reveal": False,
        "resume_text": resume_text,
        "draft": None,
        "created_at": now,
        "updated_at": now,
    }
    try:
        await database.interviews.insert_one(interview)
    except DuplicateKeyError:
        raise conflict("You've already started your interview.") from None
    return await ask_next_question(database, claude, interview)


async def ask_again(database: AsyncDatabase, claude: Claude, user: dict) -> dict:
    """Write the waiting question if an earlier attempt failed. Does nothing if one is already there."""
    interview = await get_interview(database, user["_id"])
    if interview["stage"] not in ASKING_STAGES:
        raise conflict("The interview is over.")
    if interview["current"] is not None or interview["ready_for_reveal"]:
        return interview
    return await ask_next_question(database, claude, interview)


async def answer(database: AsyncDatabase, claude: Claude, user: dict, text: str, *, shape: bool) -> dict:
    """Save the answer to the waiting question, then ask the next one."""
    interview = await get_interview(database, user["_id"])
    current = interview["current"]
    if interview["stage"] not in ASKING_STAGES or current is None:
        raise conflict("There's no question waiting for an answer.")
    if (current["phase"] == "shape") != shape:
        raise conflict("This step is the Shape step." if not shape else "This isn't the Shape step.")
    turn = {"question": current["question"], "answer": text, "phase": current["phase"]}
    # Saved before the next question is written, so a failure there never loses the answer.
    saved = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": interview["stage"], "current": current},
        {"$push": {"turns": turn}, "$set": {"current": None, "updated_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER,
    )
    if saved is None:
        raise conflict("That question was already answered.")
    return await ask_next_question(database, claude, saved)


async def skip(database: AsyncDatabase, claude: Claude, user: dict) -> dict:
    """Move past the waiting question, saved with an empty answer. Not on the Shape step, which
    needs a confirmation or a correction (docs/review/decisions.md, row 6)."""
    return await answer(database, claude, user, "", shape=False)


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
        {"$push": {"turns": turn}, "$set": {"current": None, "updated_at": datetime.now(UTC)}},
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
) -> dict:
    """End the interview and write the pool of chapters and the three titles. `answer_text` is
    saved first, so words in the field are never dropped."""
    interview = await get_interview(database, user["_id"])
    if answer_text is not None:
        interview = await save_last_answer(database, interview, answer_text)
    if interview["stage"] in ("adding", "revising"):
        return await finish_round(database, claude, interview, background)
    if interview["stage"] != "interviewing":
        raise conflict("The interview is already over.")
    if not interview_view(interview).can_finish:
        raise conflict("Keep going a little longer first.")
    draft = await ask_engine(engine.draft_book(claude, turns=turns_of(interview)))
    updated = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": "interviewing"},
        {
            "$set": {
                "stage": "choosing",
                "draft": draft.model_dump(),
                "current": None,
                "updated_at": datetime.now(UTC),
            },
            # The interview has ended, so the résumé text goes (docs/trove.md §4).
            "$unset": {"resume_text": ""},
        },
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise conflict("The interview is already over.")
    return updated


async def reviewing_interview(database: AsyncDatabase, user: dict) -> dict:
    interview = await get_interview(database, user["_id"])
    if interview["stage"] != "reviewing":
        raise conflict("There's no book waiting for review.")
    return interview


async def choose_title(database: AsyncDatabase, claude: Claude, user: dict, index: int) -> MyBookResponse:
    """Finish the book to match the chosen title, and save it as a draft."""
    interview = await get_interview(database, user["_id"])
    if interview["stage"] != "choosing":
        raise conflict("There are no titles to choose from.")
    draft = Draft.model_validate(interview["draft"])
    title = draft.titles[index].title
    finished = await ask_engine(
        engine.finish_book(claude, turns=turns_of(interview), draft=draft, title=title)
    )
    try:
        book = await books.create_draft_book(
            database,
            author_id=user["_id"],
            title=title,
            chapters=[chapter.model_dump() for chapter in finished.chapters],
            blurb=finished.blurb,
        )
    except books.BookExists:
        raise conflict("You already have a book.") from None
    await database.interviews.update_one(
        {"_id": interview["_id"]}, {"$set": {"stage": "reviewing", "updated_at": datetime.now(UTC)}}
    )
    return books.my_book_view(book)


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
    blurb = await ask_engine(engine.write_blurb(claude, turns=turns_of(interview), chapters=remaining))
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
    chapter = await ask_engine(
        engine.rewrite_chapter(claude, turns=turns_of(interview), chapters=chapters, chapter_id=chapter_id)
    )
    updated = await books.replace_chapter(database, user["_id"], {**chapter.model_dump(), "id": chapter_id})
    if updated is None:
        raise conflict("Your book is already on the shelf.")
    return books.my_book_view(updated)


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
        "resume_text": None,
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
        return await restart_writing(database, claude, interview, background, retried=False)
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
    database: AsyncDatabase, claude: Claude, interview: dict, background: BackgroundTasks, *, retried: bool
) -> dict:
    moved = await database.interviews.find_one_and_update(
        {
            "_id": interview["_id"],
            "stage": "revising",
            "proposal": None,
            "updated_at": interview["updated_at"],
        },
        {"$set": {"write_status": "writing", "write_retried": True, "updated_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER,
    )
    if moved is None:
        return await get_interview(database, interview["user_id"])
    background.add_task(write_proposal, database, claude, moved["_id"])
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
            spark_titles=interview.get("asked_spark_titles", []),
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
    # Nothing usable: say so plainly and go back to the book as it was.
    next_round = await end_revising(database, interview_id, {"nothing_new": True})
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
    if selection.get("approved") == sorted(change["id"] for change in changes):
        return selection["blurb"]
    return None


async def revising_proposal(database: AsyncDatabase, user: dict) -> tuple[dict, dict]:
    interview = await get_interview(database, user["_id"])
    proposal = interview.get("proposal")
    if interview["stage"] != "revising" or not proposal:
        raise conflict("There are no proposed changes to review.")
    return interview, proposal


async def revision_blurb(
    database: AsyncDatabase, claude: Claude, user: dict, approved: list[str]
) -> str | None:
    """The back cover for the selected changes, for the member to read before confirming. With some
    of them declined it's written now, because the proposed one may describe a declined chapter."""
    interview, proposal = await revising_proposal(database, user)
    changes = _selected(proposal, approved)
    book = await books.get_book_of(database, user["_id"])
    if not changes:
        return book.get("blurb")
    shown = _shown_blurb(proposal, changes)
    if shown:
        return shown
    chapters = books.revised_chapters(book["chapters"], **_revision_parts(changes))
    blurb = await ask_engine(
        engine.write_blurb(
            claude,
            turns=book_turns(interview),
            chapters=[DraftChapter.model_validate(chapter) for chapter in chapters],
        )
    )
    await database.interviews.update_one(
        {"_id": interview["_id"], "stage": "revising"},
        {"$set": {"proposal.selection": {"approved": sorted(c["id"] for c in changes), "blurb": blurb}}},
    )
    return blurb


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
        background.add_task(write_proposal, database, claude, interview["_id"])
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
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if updated is None:
        raise conflict("Finish what's waiting in your book first.")
    return updated


async def undo_revision(database: AsyncDatabase, user: dict) -> MyBookResponse:
    """Put the book back as it was before the last applied revision."""
    interview = await interview_for_book(database, user["_id"])
    if interview["stage"] != "done":
        raise conflict("Finish what's waiting in your book first.")
    book = await books.undo_revision(database, user["_id"])
    if book is None:
        raise conflict("There's nothing to undo.")
    # A chapter that's back is no longer one the member removed.
    titles = [chapter["title"] for chapter in book["chapters"]]
    await database.interviews.update_one(
        {"_id": interview["_id"]}, {"$pull": {"removed_chapters": {"title": {"$in": titles}}}}
    )
    return books.my_book_view(book)


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
