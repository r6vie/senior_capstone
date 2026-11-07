"""The `interviews` collection and the interview's steps, from the first question to the shelf.

The engine (`engine.py`) writes questions and books; this module keeps the state, saves after every
answer, and checks each step happens in order.
"""

import base64
import binascii
import io
from datetime import UTC, datetime
from uuid import uuid4

import anthropic
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError
from pypdf import PdfReader
from starlette.concurrency import run_in_threadpool

from trove.ai.client import Claude, ClaudeRefused
from trove.books import service as books
from trove.books.models import MyBookResponse
from trove.interview import engine
from trove.interview.engine import Draft, DraftChapter, Turn
from trove.interview.models import InterviewResponse, Question

# After this many answers the member may say "I've said enough" (docs/trove.md §4).
EXIT_AFTER_ANSWERS = 10
SHAPE_CONFIRMED = "Yes, that's me."
MAX_RESUME_PAGES = 20
# Enough to shape questions; a résumé is a page or two.
MAX_RESUME_CHARS = 20_000


async def ensure_indexes(database: AsyncDatabase) -> None:
    # One interview per member, even if two starts arrive at the same moment.
    await database.interviews.create_index("user_id", unique=True, name="interviews_user_unique")


def conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=409, detail=detail)


def interview_view(interview: dict) -> InterviewResponse:
    current = interview.get("current")
    stage = interview["stage"]
    ready = interview.get("ready_for_reveal", False)
    return InterviewResponse(
        stage=stage,
        question=Question(text=current["question"], phase=current["phase"], playback=current.get("playback"))
        if current
        else None,
        topic=interview.get("topic"),
        has_answers=bool(interview["turns"]),
        can_finish=stage == "interviewing" and (ready or len(interview["turns"]) >= EXIT_AFTER_ANSWERS),
        ready_for_reveal=ready,
        titles=interview["draft"]["titles"] if stage == "choosing" else None,
    )


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
    except (ClaudeRefused, anthropic.APIError, ValueError):  # ValueError covers pydantic ValidationError
        raise HTTPException(
            status_code=502, detail="The Librarian couldn't answer just now. Please try again."
        ) from None


def turns_of(interview: dict) -> list[Turn]:
    return [Turn.model_validate(turn) for turn in interview["turns"]]


async def ask_next_question(database: AsyncDatabase, claude: Claude, interview: dict) -> dict:
    """Write the next question for an interview that is waiting for one, and save it."""
    turn = await ask_engine(
        engine.next_turn(claude, turns=turns_of(interview), resume_text=interview.get("resume_text"))
    )
    ready = turn.ready_for_reveal
    updated = await database.interviews.find_one_and_update(
        # Only if no other request has written the question in the meantime.
        {"_id": interview["_id"], "stage": "interviewing", "current": None},
        {
            "$set": {
                "current": None if ready else turn.model_dump(include={"question", "phase", "playback"}),
                "topic": turn.topic,
                "ready_for_reveal": ready,
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    return updated or await get_interview(database, interview["user_id"])


async def start(database: AsyncDatabase, claude: Claude, user: dict, resume_pdf: str | None) -> dict:
    # Adding to an existing book is a later item (I3), so a member with a book can't start over.
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
    if interview["stage"] != "interviewing":
        raise conflict("The interview is over.")
    if interview["current"] is not None or interview["ready_for_reveal"]:
        return interview
    return await ask_next_question(database, claude, interview)


async def answer(database: AsyncDatabase, claude: Claude, user: dict, text: str, *, shape: bool) -> dict:
    """Save the answer to the waiting question, then ask the next one."""
    interview = await get_interview(database, user["_id"])
    current = interview["current"]
    if interview["stage"] != "interviewing" or current is None:
        raise conflict("There's no question waiting for an answer.")
    if (current["phase"] == "shape") != shape:
        raise conflict("This step is the Shape step." if not shape else "This isn't the Shape step.")
    turn = {"question": current["question"], "answer": text, "phase": current["phase"]}
    # Saved before the next question is written, so a failure there never loses the answer.
    saved = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": "interviewing", "current": current},
        {"$push": {"turns": turn}, "$set": {"current": None, "updated_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER,
    )
    if saved is None:
        raise conflict("That question was already answered.")
    return await ask_next_question(database, claude, saved)


async def finish(database: AsyncDatabase, claude: Claude, user: dict) -> dict:
    """End the interview and write the pool of chapters and the three titles."""
    interview = await get_interview(database, user["_id"])
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
    chapters = await ask_engine(
        engine.finish_book(claude, turns=turns_of(interview), draft=draft, title=title)
    )
    try:
        book = await books.create_draft_book(
            database,
            author_id=user["_id"],
            author_name=user["first_name"],
            title=title,
            chapters=[chapter.model_dump() for chapter in chapters],
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


async def remove_chapter(database: AsyncDatabase, user: dict, chapter_id: str) -> MyBookResponse:
    await reviewing_interview(database, user)
    await own_draft(database, user, chapter_id)
    book = await books.remove_chapter(database, user["_id"], chapter_id)
    if book is None:
        raise conflict(f"A book needs at least {books.MIN_CHAPTERS} chapters.")
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
