"""The `interviews` collection and the interview's steps, from the first question to the shelf.

The engine (`engine.py`) writes questions and books; this module keeps the state, saves after every
answer, and checks each step happens in order.
"""

import base64
import binascii
import contextlib
import io
from datetime import UTC, datetime
from uuid import uuid4

import anthropic
from fastapi import HTTPException
from pymongo import ASCENDING, ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError
from pypdf import PdfReader
from starlette.concurrency import run_in_threadpool

from trove.ai.client import Claude, ClaudeRefused
from trove.ai.usage import BudgetExceeded
from trove.books import service as books
from trove.books.models import MyBookResponse
from trove.interview import engine
from trove.interview.engine import Change, Draft, DraftChapter, Revision, Turn
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
READING_QUESTION = "What did they ask you about that surprised you?"


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
        can_finish = proposal is None
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
        changes=[Change.model_validate(change) for change in proposal["changes"]] if proposal else None,
        proposed_blurb=proposal["blurb"] if proposal else None,
        nothing_new=interview.get("nothing_new", False),
    )


async def current_view(database: AsyncDatabase, user: dict) -> InterviewResponse:
    interview = await get_interview(database, user["_id"])
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


async def write_question(
    database: AsyncDatabase, claude: Claude, interview: dict
) -> tuple[dict | None, str, bool]:
    """The next question to save, what the member was last talking about, and whether that's enough."""
    sparks = await unused_spark_titles(database, interview["user_id"])
    if interview["stage"] == "adding":
        book = await books.get_book_of(database, interview["user_id"])
        turn = await ask_engine(
            engine.next_adding_turn(
                claude,
                turns=turns_of(interview),
                round_start=interview["round_start"],
                chapters=[DraftChapter.model_validate(chapter) for chapter in book["chapters"]],
                sparks=sparks,
            )
        )
        question = {"question": turn.question, "phase": "adding", "playback": None}
        return None if turn.done else question, turn.topic, turn.done
    turn = await ask_engine(
        engine.next_turn(
            claude, turns=turns_of(interview), resume_text=interview.get("resume_text"), sparks=sparks
        )
    )
    ready = turn.ready_for_reveal
    return None if ready else turn.model_dump(include={"question", "phase", "playback"}), turn.topic, ready


async def ask_next_question(database: AsyncDatabase, claude: Claude, interview: dict) -> dict:
    """Write the next question for an interview that is waiting for one, and save it."""
    question, topic, ready = await write_question(database, claude, interview)
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


async def finish(database: AsyncDatabase, claude: Claude, user: dict) -> dict:
    """End the interview and write the pool of chapters and the three titles."""
    interview = await get_interview(database, user["_id"])
    if interview["stage"] in ("adding", "revising"):
        return await finish_round(database, claude, interview)
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
    await mark_sparks_used(database, user["_id"])
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
    book = await books.remove_chapter(database, user["_id"], chapter_id, blurb=blurb)
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


# Adding to a book on the shelf (I3).


async def reopen(database: AsyncDatabase, claude: Claude, user: dict) -> dict:
    """Start a short new round of questions. The earlier turns stay as grounding material, and the
    book on the shelf doesn't change unless the member approves a change."""
    interview = await get_interview(database, user["_id"])
    if interview["stage"] == "adding":
        return interview
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
                "updated_at": datetime.now(UTC),
            }
        },
        return_document=ReturnDocument.AFTER,
    )
    if opened is None:
        raise conflict("Only a book on the shelf can be added to.")
    return await ask_next_question(database, claude, opened)


async def finish_round(database: AsyncDatabase, claude: Claude, interview: dict) -> dict:
    """Write the proposed changes. The stage moves first, so a failure here loses nothing and
    POST /interview/finish simply tries again."""
    if interview["stage"] == "revising" and interview.get("proposal") is not None:
        raise conflict("Your proposed changes are waiting for you.")
    if interview["stage"] == "adding":
        if not interview_view(interview).can_finish:
            raise conflict("Answer at least one question first.")
        moved = await database.interviews.find_one_and_update(
            {"_id": interview["_id"], "stage": "adding"},
            {
                "$set": {
                    "stage": "revising",
                    "current": None,
                    "proposal": None,
                    "updated_at": datetime.now(UTC),
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        if moved is None:
            return await get_interview(database, interview["user_id"])
        interview = moved
        await mark_sparks_used(database, interview["user_id"])
    return await write_proposal(database, claude, interview)


async def write_proposal(database: AsyncDatabase, claude: Claude, interview: dict) -> dict:
    book = await books.get_book_of(database, interview["user_id"])
    revision: Revision = await ask_engine(
        engine.revise_book(
            claude,
            turns=turns_of(interview),
            round_start=interview["round_start"],
            chapters=[DraftChapter.model_validate(chapter) for chapter in book["chapters"]],
            blurb=book.get("blurb"),
        )
    )
    if not revision.changes:
        # Nothing usable: say so plainly and go back to the book as it was.
        changes = {"stage": "done", "proposal": None, "nothing_new": True}
    else:
        changes = {"proposal": revision.model_dump()}
    updated = await database.interviews.find_one_and_update(
        {"_id": interview["_id"], "stage": "revising", "proposal": None},
        {"$set": {**changes, "updated_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER,
    )
    return updated or await get_interview(database, interview["user_id"])


async def apply_revision(
    database: AsyncDatabase, claude: Claude, user: dict, approved: list[str]
) -> MyBookResponse:
    """Apply the approved changes and drop the rest. The book on the shelf changes only here."""
    interview = await get_interview(database, user["_id"])
    proposal = interview.get("proposal")
    if interview["stage"] != "revising" or proposal is None:
        raise conflict("There are no proposed changes to review.")
    chosen = set(approved)
    if chosen - {change["id"] for change in proposal["changes"]}:
        raise HTTPException(status_code=422, detail="That isn't one of the proposed changes.")
    changes = [change for change in proposal["changes"] if change["id"] in chosen]
    book = await books.get_book_of(database, user["_id"])
    if changes:
        improved = [_approved_chapter(c, c["chapter_id"]) for c in changes if c["kind"] == "improve"]
        added = [_approved_chapter(c, c["id"]) for c in changes if c["kind"] == "new"]
        # The proposed back cover fits only if everything was approved. Otherwise it may describe a
        # declined chapter, so a new one is written for what the book will actually hold.
        blurb = proposal["blurb"] if len(changes) == len(proposal["changes"]) else None
        if not blurb:
            replacements = {chapter["id"]: chapter for chapter in improved}
            chapters = [replacements.get(c["id"], c) for c in book["chapters"]] + added
            blurb = await ask_engine(
                engine.write_blurb(
                    claude,
                    turns=turns_of(interview),
                    chapters=[DraftChapter.model_validate(chapter) for chapter in chapters],
                )
            )
        book = await books.apply_revision(database, user["_id"], improved=improved, added=added, blurb=blurb)
        if book is None:
            raise conflict("Your book changed while this was being applied. Please try again.")
    await database.interviews.update_one(
        {"_id": interview["_id"]},
        {"$set": {"stage": "done", "proposal": None, "current": None, "updated_at": datetime.now(UTC)}},
    )
    return books.my_book_view(book)


def _approved_chapter(change: dict, chapter_id: str) -> dict:
    return {
        "id": chapter_id,
        "title": change["title"],
        "summary": change["summary"],
        "quotes": change["quotes"],
    }


# Sparks (I5). Private to the member who saved them. Nothing here is ever read for anyone else.


def spark_view(spark: dict) -> SparkResponse:
    return SparkResponse.model_validate({**spark, "id": spark["_id"]})


async def unused_spark_titles(database: AsyncDatabase, user_id: str) -> list[str]:
    """Only the titles: never a chapter's summary, its author or the title of its book."""
    cursor = database.sparks.find({"user_id": user_id, "used_at": None}, {"chapter_title": 1})
    return [spark["chapter_title"] for spark in await cursor.sort("created_at", ASCENDING).to_list()]


async def mark_sparks_used(database: AsyncDatabase, user_id: str) -> None:
    await database.sparks.update_many(
        {"user_id": user_id, "used_at": None}, {"$set": {"used_at": datetime.now(UTC)}}
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
    cursor = database.reading_questions.find(
        {"author_id": user["_id"], "answered_at": None, "dismissed_at": None}
    ).sort("created_at", ASCENDING)
    return [
        ReadingQuestionResponse(
            id=question["_id"], question=READING_QUESTION, created_at=question["created_at"]
        )
        for question in await cursor.to_list()
    ]


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
    database: AsyncDatabase, claude: Claude, user: dict, question_id: str, text: str
) -> dict:
    """Save the answer as a turn, then propose changes as a round of adding does. During a round it
    simply joins that round."""
    interview = await get_interview(database, user["_id"])
    if interview["stage"] not in ("done", "adding"):
        raise conflict("Finish what's waiting in your book first.")
    await claim_reading_question(database, user, question_id, "answered_at")
    turn = {"question": READING_QUESTION, "answer": text, "phase": "reading"}
    now = datetime.now(UTC)
    if interview["stage"] == "adding":
        updated = await database.interviews.find_one_and_update(
            {"_id": interview["_id"], "stage": "adding"},
            {"$push": {"turns": turn}, "$set": {"updated_at": now}},
            return_document=ReturnDocument.AFTER,
        )
    else:
        updated = await database.interviews.find_one_and_update(
            {"_id": interview["_id"], "stage": "done"},
            {
                "$push": {"turns": turn},
                "$set": {
                    "stage": "revising",
                    "round_start": len(interview["turns"]),
                    "proposal": None,
                    "current": None,
                    "nothing_new": False,
                    "updated_at": now,
                },
            },
            return_document=ReturnDocument.AFTER,
        )
        if updated is not None:
            return await write_proposal(database, claude, updated)
    if updated is None:
        await database.reading_questions.update_one({"_id": question_id}, {"$set": {"answered_at": None}})
        raise conflict("Finish what's waiting in your book first.")
    return updated
