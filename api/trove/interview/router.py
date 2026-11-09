from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase

from trove.ai.client import Claude, get_claude
from trove.auth.service import get_current_user
from trove.books.models import MyBookResponse
from trove.core.database import get_database
from trove.interview import service
from trove.interview.models import AnswerRequest, InterviewResponse, ShapeRequest, StartRequest, TitleRequest
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
    """End the interview and get three titles, each with why it's you."""
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
