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
        description="An optional résumé PDF, base64-encoded. The file isn't kept. Its text is deleted when "
        "the interview ends, or 30 days after the last activity, and nothing from it goes into the book.",
    )


class AnswerRequest(RequestBody):
    answer: NonEmptyText = Field(max_length=5000)
    question_id: str = Field(description="The `question_id` of the question this answers.")


class SkipRequest(RequestBody):
    question_id: str = Field(description="The `question_id` of the question being skipped.")


class FinishRequest(RequestBody):
    answer: NonEmptyText | None = Field(
        None,
        max_length=5000,
        description="What's in the field: saved as the waiting question's answer first.",
    )
    question_id: str | None = Field(None, description="The `question_id` that `answer` answers.")


class ShapeRequest(RequestBody):
    correction: NonEmptyText | None = Field(
        None, max_length=5000, description="What's different. Leave out to confirm: \"Yes, that's me\"."
    )


class TitleRequest(RequestBody):
    title: int = Field(ge=0, le=2, description="Which of the three titles, by position.")


class RevisionBlurbRequest(RequestBody):
    approved: list[str] = Field(description="The ids of the changes the member has selected.")


class RevisionBlurbResponse(BaseModel):
    """The back cover for that selection, for the member to read before confirming."""

    blurb: str | None


class RevisionRequest(RequestBody):
    approved: list[str] = Field(description="The ids of the changes to apply. The rest are dropped.")
    blurb: Literal["keep", "use"] = Field(
        "keep",
        description='"use" applies the back cover last shown for exactly this selection, from '
        '`proposed_blurb` or POST /interview/revision/blurb. "keep" leaves the old one.',
    )


class RemovalRequest(RequestBody):
    chapter_id: str


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
    """The question after a reading, for its author only."""

    id: str
    question: str
    created_at: datetime
    # Who the reading was with, for "After your reading with…". On this screen only: never in a
    # prompt or a book. Null if it can't be found.
    reader_name: str | None


class ReadingAnswerRequest(RequestBody):
    answer: NonEmptyText = Field(max_length=5000)


class Question(BaseModel):
    # Sent back with the answer, so a resend can't land on a question the member never saw.
    question_id: str
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
    # revising if writing the changes failed. No count is ever shown.
    can_finish: bool
    # The Librarian has enough; the client can go straight to POST /interview/finish.
    ready_for_reveal: bool
    # A draft found too little for three chapters. Show "I need a little more before I can write your
    # book." `can_finish` stays false until enough more is answered, so there's no retry that can't work.
    needs_more: bool
    # Still too little at the turn limit, with no question waiting. Everything is saved. "Keep answering"
    # is POST /interview/question; the member can also leave.
    at_limit: bool
    # The three titles while choosing, and while reviewing so another can be picked.
    titles: list[TitleOption] | None
    # The back-cover blurb, first person, 2-4 sentences: the draft's while choosing, then the book's.
    blurb: str | None
    # While revising: the changes are being written, are ready, or failed. A failure is retried
    # once on its own when the member comes back; after that POST /interview/finish tries again.
    revision_status: Literal["writing", "ready", "failed"] | None
    # The proposed changes once ready. Nothing changes on the shelf until POST /interview/revision.
    changes: list[Change] | None
    # The proposed back cover, if every change is approved.
    proposed_blurb: str | None
    # The last round earned no changes, so the book is as it was. The app says so plainly.
    nothing_new: bool


class StaleQuestionResponse(BaseModel):
    """The 409 when an answer or skip names a question that isn't the one waiting. Nothing was saved."""

    detail: str
    interview: InterviewResponse
