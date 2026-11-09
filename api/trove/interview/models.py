from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from trove.core.models import NonEmptyText, RequestBody
from trove.interview.engine import Change, TitleOption, TurnPhase

# interviewing → choosing (three titles shown) → reviewing (draft book) → done (on the shelf).
# Later, done → adding (a short new round) → revising (proposed changes to approve) → done.
Stage = Literal["interviewing", "choosing", "reviewing", "done", "adding", "revising"]
# A 5 MB PDF, base64-encoded.
MAX_RESUME_BASE64 = 7_000_000


class StartRequest(RequestBody):
    resume_pdf: str | None = Field(
        None,
        max_length=MAX_RESUME_BASE64,
        description="An optional résumé PDF, base64-encoded. Never stored.",
    )


class AnswerRequest(RequestBody):
    answer: NonEmptyText = Field(max_length=5000)


class FinishRequest(RequestBody):
    answer: NonEmptyText | None = Field(
        None,
        max_length=5000,
        description="What's in the field: saved as the waiting question's answer first.",
    )


class ShapeRequest(RequestBody):
    correction: NonEmptyText | None = Field(
        None, max_length=5000, description="What's different. Leave out to confirm: \"Yes, that's me\"."
    )


class TitleRequest(RequestBody):
    title: int = Field(ge=0, le=2, description="Which of the three titles, by position.")


class RevisionRequest(RequestBody):
    approved: list[str] = Field(description="The ids of the changes to apply. The rest are dropped.")


class SparkRequest(RequestBody):
    book_id: str
    chapter_id: str


class SparkResponse(BaseModel):
    """A chapter that made this member think "I have one like this". Only they ever see it."""

    id: str
    book_id: str
    chapter_id: str
    chapter_title: str
    created_at: datetime


class ReadingQuestionResponse(BaseModel):
    """The question after a reading. Nothing here says who the reader was."""

    id: str
    question: str
    created_at: datetime


class ReadingAnswerRequest(RequestBody):
    answer: NonEmptyText = Field(max_length=5000)


class Question(BaseModel):
    text: str
    phase: TurnPhase
    # On the Shape step: what the Librarian heard, played back for the member to confirm or correct.
    playback: str | None


class InterviewResponse(BaseModel):
    stage: Stage
    # The question waiting for an answer. Null while interviewing means it couldn't be written:
    # POST /interview/question tries again.
    question: Question | None
    # What the member was last talking about, for "Last time you were telling me about…".
    topic: str | None
    # Whether any answer is saved yet: "Welcome back" instead of the start screen. Never a count.
    has_answers: bool
    # "I've said enough. Show me my book" may be offered: POST /interview/finish. Also true while
    # revising if the changes still need writing. No count is ever shown.
    can_finish: bool
    # The Librarian has enough; the client can go straight to POST /interview/finish.
    ready_for_reveal: bool
    # The three titles while choosing.
    titles: list[TitleOption] | None
    # The back-cover blurb, first person, 2-4 sentences: the draft's while choosing, then the book's.
    blurb: str | None
    # The proposed changes while revising. Null while revising means they couldn't be written:
    # POST /interview/finish tries again. Nothing is on the shelf until POST /interview/revision.
    changes: list[Change] | None
    # The proposed back cover, if every change is approved.
    proposed_blurb: str | None
    # The last round earned no changes, so the book is as it was. The app says so plainly.
    nothing_new: bool
