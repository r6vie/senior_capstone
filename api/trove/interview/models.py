from typing import Literal

from pydantic import BaseModel, Field

from trove.core.models import NonEmptyText, RequestBody
from trove.interview.engine import Phase, TitleOption

# interviewing → choosing (three titles shown) → reviewing (draft book) → done (on the shelf)
Stage = Literal["interviewing", "choosing", "reviewing", "done"]
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


class ShapeRequest(RequestBody):
    correction: NonEmptyText | None = Field(
        None, max_length=5000, description="What's different. Leave out to confirm: \"Yes, that's me\"."
    )


class TitleRequest(RequestBody):
    title: int = Field(ge=0, le=2, description="Which of the three titles, by position.")


class Question(BaseModel):
    text: str
    phase: Phase
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
    # "I've said enough. Show me my book" may be offered. No count is ever shown.
    can_finish: bool
    # The Librarian has enough; the client can go straight to POST /interview/finish.
    ready_for_reveal: bool
    # The three titles while choosing.
    titles: list[TitleOption] | None
    # The back-cover blurb, first person, 2-4 sentences: the draft's while choosing, then the book's.
    blurb: str | None
