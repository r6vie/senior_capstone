from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from trove.ai.client import Claude, get_claude
from trove.auth.service import get_current_user
from trove.books.models import MyBookResponse
from trove.core.database import get_database
from trove.interview import service
from trove.interview.models import (
    AnswerRequest,
    InterviewResponse,
    ReadingAnswerRequest,
    ReadingQuestionResponse,
    RevisionRequest,
    ShapeRequest,
    SparkRequest,
    SparkResponse,
    StartRequest,
    TitleRequest,
)
from trove.interview.service import interview_view

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("", response_model=InterviewResponse, status_code=201)
async def start(
    data: StartRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Start the interview and get the first question. A member with a book can't start again (409)."""
    return interview_view(await service.start(database, claude, user, data.resume_pdf))


@router.get("", response_model=InterviewResponse)
async def current(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> InterviewResponse:
    """The member's interview, for resuming where they left off."""
    return await service.current_view(database, user)


@router.post("/question", response_model=InterviewResponse)
async def ask_again(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Write the waiting question again after a failed attempt (a 502, or `question` is null)."""
    return interview_view(await service.ask_again(database, claude, user))


@router.post("/answers", response_model=InterviewResponse)
async def answer(
    data: AnswerRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Answer the waiting question. The answer is saved first, then the next question is written."""
    return interview_view(await service.answer(database, claude, user, data.answer, shape=False))


@router.post("/skip", response_model=InterviewResponse)
async def skip(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Skip the waiting question and get the next one. Not on the Shape step (409)."""
    return interview_view(await service.skip(database, claude, user))


@router.post("/shape", response_model=InterviewResponse)
async def shape(
    data: ShapeRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Confirm the Librarian's playback ("Yes, that's me"), or correct it."""
    text = data.correction or service.SHAPE_CONFIRMED
    return interview_view(await service.answer(database, claude, user, text, shape=True))


@router.post("/finish", response_model=InterviewResponse)
async def finish(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """End the interview and get three titles, each with why it's you. In a round of adding, end
    the round and get proposed changes. While revising with `changes` null, write them again."""
    return interview_view(await service.finish(database, claude, user))


@router.post("/title", response_model=MyBookResponse)
async def choose_title(
    data: TitleRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> MyBookResponse:
    """Choose one of the three titles. The book is finished to match and saved as a draft."""
    return await service.choose_title(database, claude, user, data.title)


@router.delete("/book/chapters/{chapter_id}", response_model=MyBookResponse)
async def remove_chapter(
    chapter_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> MyBookResponse:
    """Remove a chapter from the draft. The blurb is rewritten for the chapters that are left."""
    return await service.remove_chapter(database, claude, user, chapter_id)


@router.post("/book/chapters/{chapter_id}/rewrite", response_model=MyBookResponse)
async def rewrite_chapter(
    chapter_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> MyBookResponse:
    return await service.rewrite_chapter(database, claude, user, chapter_id)


@router.post("/book/shelve", response_model=MyBookResponse)
async def put_on_shelf(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyBookResponse:
    """Put the finished book on the shelf. The interview is then done."""
    return await service.put_on_shelf(database, user)


@router.post("/reopen", response_model=InterviewResponse)
async def reopen(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Add to a book on the shelf: a short new round of questions. The book doesn't change yet."""
    return interview_view(await service.reopen(database, claude, user))


@router.post("/revision", response_model=MyBookResponse)
async def apply_revision(
    data: RevisionRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> MyBookResponse:
    """Apply the approved changes to the book on the shelf. The rest are dropped."""
    return await service.apply_revision(database, claude, user, data.approved)


@router.post("/sparks", response_model=SparkResponse)
async def add_spark(
    data: SparkRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> SparkResponse:
    """ "I have one like this" on a chapter of someone else's book. Private: its author never knows."""
    return await service.add_spark(database, user, data.book_id, data.chapter_id)


@router.get("/sparks", response_model=list[SparkResponse])
async def list_sparks(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> list[SparkResponse]:
    """The member's own sparks waiting for their next round."""
    return await service.list_sparks(database, user)


@router.delete("/sparks/{spark_id}", status_code=204)
async def remove_spark(
    spark_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> None:
    await service.remove_spark(database, user, spark_id)


@router.get("/reading-questions", response_model=list[ReadingQuestionResponse])
async def list_reading_questions(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> list[ReadingQuestionResponse]:
    """The question waiting after a reading, if there is one."""
    return await service.list_reading_questions(database, user)


@router.post("/reading-questions/{question_id}/answer", response_model=InterviewResponse)
async def answer_reading_question(
    question_id: str,
    data: ReadingAnswerRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Answer it, and get proposed changes to the book (or `nothing_new`)."""
    return interview_view(
        await service.answer_reading_question(database, claude, user, question_id, data.answer)
    )


@router.post("/reading-questions/{question_id}/dismiss", status_code=204)
async def dismiss_reading_question(
    question_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> None:
    """Dismiss it, as quietly as a skip: never shown, never counted."""
    await service.dismiss_reading_question(database, user, question_id)
