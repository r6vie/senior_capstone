from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pymongo.asynchronous.database import AsyncDatabase

from trove.ai.client import Claude, get_claude, optional_claude
from trove.auth.service import get_current_user
from trove.books.models import MyBookResponse
from trove.core.database import get_database
from trove.interview import service
from trove.interview.models import (
    AnswerRequest,
    FinishRequest,
    InterviewResponse,
    ReadingAnswerRequest,
    ReadingQuestionResponse,
    RemovalRequest,
    RevisionChoicesRequest,
    RevisionRequest,
    ShapeRequest,
    SkipRequest,
    SparkRequest,
    SparkResponse,
    StaleQuestionResponse,
    StartRequest,
    TitleRequest,
)
from trove.interview.service import interview_view

router = APIRouter(prefix="/interview", tags=["Interview"])
STALE_QUESTION_RESPONSES = {409: {"model": StaleQuestionResponse}}


def stale_question(error: service.StaleQuestion) -> JSONResponse:
    """The current state comes with the 409, so the client can move to the question that's waiting."""
    body = StaleQuestionResponse(detail=error.detail, interview=interview_view(error.interview))
    return JSONResponse(status_code=409, content=jsonable_encoder(body))


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
    background: BackgroundTasks,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude | None = Depends(optional_claude),
) -> InterviewResponse:
    """The member's interview, for resuming where they left off. If writing proposed changes failed,
    a return tries once more on its own."""
    return await service.current_view(database, user, claude, background)


@router.post("/question", response_model=InterviewResponse)
async def ask_again(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Write the waiting question again after a failed attempt (a 502, or `question` is null)."""
    return interview_view(await service.ask_again(database, claude, user))


@router.post("/answers", response_model=InterviewResponse, responses=STALE_QUESTION_RESPONSES)
async def answer(
    data: AnswerRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Answer the waiting question. The answer is saved first, then the next question is written."""
    try:
        return interview_view(
            await service.answer(
                database, claude, user, data.answer, shape=False, question_id=data.question_id
            )
        )
    except service.StaleQuestion as error:
        return stale_question(error)


@router.post("/skip", response_model=InterviewResponse, responses=STALE_QUESTION_RESPONSES)
async def skip(
    data: SkipRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Skip the waiting question and get the next one. Not on the Shape step (409)."""
    try:
        return interview_view(await service.skip(database, claude, user, data.question_id))
    except service.StaleQuestion as error:
        return stale_question(error)


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


@router.post("/finish", response_model=InterviewResponse, responses=STALE_QUESTION_RESPONSES)
async def finish(
    background: BackgroundTasks,
    data: FinishRequest | None = None,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """End the interview: stage goes to `drafting`, and the three titles are written in the background
    (`step_status`). With too little material it says `needs_more` instead. In a round of adding, end
    the round: the proposed changes are written in the background (`revision_status`). After a
    failed write, try again.
    `answer` is saved first as the answer to the waiting question, with no question after it."""
    try:
        return interview_view(
            await service.finish(
                database,
                claude,
                user,
                background,
                data.answer if data else None,
                data.question_id if data else None,
            )
        )
    except service.StaleQuestion as error:
        return stale_question(error)


@router.post("/title", response_model=InterviewResponse)
async def choose_title(
    data: TitleRequest,
    background: BackgroundTasks,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Choose one of the three titles. Stage goes to `finishing`, and the book is written to match in
    the background (`step_status`). After a failure, send this again."""
    return interview_view(await service.choose_title(database, claude, user, data.title, background))


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
    """Tell the chapter again. `rewrite_unchanged` means it couldn't be told better, and nothing changed."""
    return await service.rewrite_chapter(database, claude, user, chapter_id)


@router.post("/book/chapters/{chapter_id}/restore", response_model=MyBookResponse)
async def restore_chapter(
    chapter_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyBookResponse:
    """Go back to the chapter's last version (`has_previous`), during the review."""
    return await service.restore_chapter(database, user, chapter_id)


@router.post("/book/blurb", response_model=MyBookResponse)
async def rewrite_blurb(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> MyBookResponse:
    """Write the draft's back cover again."""
    return await service.rewrite_blurb(database, claude, user)


@router.post("/book/title", response_model=MyBookResponse)
async def change_title(
    data: TitleRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> MyBookResponse:
    """Change to another of the three titles (`titles`), finishing the book again to match."""
    return await service.change_title(database, claude, user, data.title)


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


@router.put("/revision/choices", response_model=InterviewResponse)
async def save_revision_choices(
    data: RevisionChoicesRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> InterviewResponse:
    """Save which changes are approved so far, as they're pressed. Nothing is applied."""
    return interview_view(await service.save_choices(database, user, data.approved))


@router.post("/revision/blurb", response_model=InterviewResponse)
async def revision_blurb(
    background: BackgroundTasks,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Get the back cover for the saved choices, to read before confirming (`selection_blurb_status`).
    Written in the background when it has to be. Also the retry after `failed` or `stale`."""
    return interview_view(await service.start_selection_blurb(database, claude, user, background))


@router.post("/revision", response_model=MyBookResponse)
async def apply_revision(
    data: RevisionRequest,
    background: BackgroundTasks,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> MyBookResponse:
    """Apply the approved changes to the book on the shelf. The rest are dropped and not proposed
    again. A reading answer saved meanwhile then gets its own proposal."""
    return await service.apply_revision(database, claude, user, data.approved, data.blurb, background)


@router.post("/removal", response_model=InterviewResponse)
async def propose_removal(
    data: RemovalRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> InterviewResponse:
    """Propose taking a chapter out of a book on the shelf. Confirmed like any change. 409 at three chapters."""
    return interview_view(await service.propose_removal(database, user, data.chapter_id))


@router.post("/book/undo", response_model=MyBookResponse)
async def undo_revision(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> MyBookResponse:
    """Take back the last applied revision (`can_undo`), until the next one is applied."""
    return await service.undo_revision(database, user)


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
    background: BackgroundTasks,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
    claude: Claude = Depends(get_claude),
) -> InterviewResponse:
    """Answer it. From `done`, changes are written in the background (`revision_status`). During a
    round it joins the round. While changes are waiting, it runs after the member decides."""
    return interview_view(
        await service.answer_reading_question(database, claude, user, question_id, data.answer, background)
    )


@router.post("/reading-questions/{question_id}/dismiss", status_code=204)
async def dismiss_reading_question(
    question_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> None:
    """Dismiss it, as quietly as a skip: never shown, never counted."""
    await service.dismiss_reading_question(database, user, question_id)
