from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from trove.core.models import NonEmptyText, RequestBody
from trove.interview.engine import Change, TitleOption, TurnPhase
from trove.interview.librarian import Entry, Mark

# interviewing → choosing (three titles shown) → reviewing (draft book) → done (on the shelf).
# Later, done → adding (a short new round) → revising (proposed changes to approve) → done.
# drafting (titles being written) and finishing (the book being written) sit between the first stages,
# so a refresh in the middle shows the wait, not a screen where every action fails.
Stage = Literal[
    "interviewing", "drafting", "choosing", "finishing", "reviewing", "done", "adding", "revising"
]
# A 5 MB PDF, base64-encoded.
MAX_RESUME_BASE64 = 7_000_000


class StartRequest(RequestBody):
    resume_pdf: str | None = Field(
        None,
        max_length=MAX_RESUME_BASE64,
        description="An optional résumé PDF, base64-encoded. The file isn't kept. Its text is deleted when "
        "the interview ends, or 30 days after the last activity, and nothing from it goes into the book.",
    )


class ResumeRequest(RequestBody):
    resume_pdf: str = Field(
        max_length=MAX_RESUME_BASE64,
        description="A résumé PDF, base64-encoded, replacing any attached before. It shapes the questions "
        "from here on, never the book. The file isn't kept. Its text is deleted when the interview ends, or "
        "30 days after the last activity.",
    )


class AnswerRequest(RequestBody):
    answer: NonEmptyText = Field(max_length=5000)
    question_id: str = Field(description="The `question_id` of the question this answers.")


class SkipRequest(RequestBody):
    question_id: str = Field(description="The `question_id` of the question being skipped.")


class NotesRequest(RequestBody):
    """One look at the answer while the member types. Earlier turns are already on the server."""

    question_id: str = Field(description="The `question_id` of the question being answered.")
    text: str = Field(max_length=5000, description="The answer as it stands.")
    previous_text: str = Field("", max_length=5000, description="The answer at the last call.")
    pasted: bool = Field(False, description="Whether some of the text was pasted.")
    shown: list[str] = Field(
        default_factory=list, max_length=200, description="Ids of the marks and entries on screen now."
    )


class MarksDelta(BaseModel):
    # Marks to leave in place. Anything on screen in none of these lists is rubbed out.
    keep: list[str]
    add: list[Mark]
    # Same id, changed: an edit credited ("better."), with the old note in `struck_note`.
    revise: list[Mark]
    erase: list[str]


class NotebookDelta(BaseModel):
    keep: list[str]
    add: list[Entry]
    # Same id, new wording: strike the old text and write the new.
    revise: list[Entry]
    # Rub these out.
    erase: list[str]


class NotesResponse(BaseModel):
    """What the Librarian does now. Place a mark only while its anchor and occurrence still match the
    text: a late reply is then harmless. On `silent`, rub everything from this answer out and write
    nothing more on it."""

    silent: bool
    marks: MarksDelta
    notebook: NotebookDelta


class AnsweredTurn(BaseModel):
    """An answered or skipped question, with the marks the Librarian left on it, for going back."""

    question: str
    answer: str
    marks: list[Mark]
    silent: bool


class LibrarianState(BaseModel):
    """Everything the Librarian left so far, so going back and resuming show exactly what was there.
    Only while interviewing or adding: it's hidden after the reveal, never deleted."""

    turns: list[AnsweredTurn]
    # The marks on the answer being written, and whether it has gone quiet.
    current_marks: list[Mark]
    current_silent: bool
    notebook: list[Entry]


class FinishRequest(RequestBody):
    answer: NonEmptyText | None = Field(
        None,
        max_length=5000,
        description="What's in the field: saved as the waiting question's answer first.",
    )
    question_id: str | None = Field(None, description="The `question_id` that `answer` answers.")


class TitleRequest(RequestBody):
    title: int = Field(ge=0, le=2, description="Which of the three titles, by position.")


class RevisionChoicesRequest(RequestBody):
    approved: list[str] = Field(description="The ids of the changes approved so far. Saved, not applied.")


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
    # The Librarian's notebook entry this question was built on: circled, or ticked if a `saving` one.
    builds_on: str | None = None


class InterviewResponse(BaseModel):
    stage: Stage
    # The question waiting for an answer. Null while interviewing means it couldn't be written:
    # POST /interview/question tries again.
    question: Question | None
    # What the member was last talking about, for "Last time you were telling me about…".
    topic: str | None
    # Whether any answer is saved yet: "Welcome back" instead of the start screen. Never a count.
    has_answers: bool
    # A résumé is attached and shaping the questions. Only ever true while interviewing.
    has_resume: bool = False
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
    # True from a little before Shape until Shape: "Most of the way there." The client never counts.
    nearly_done: bool
    # What the Librarian said on ending the interview, to hold on screen during the title wait.
    closing_line: str | None
    # The three titles while choosing, and while reviewing so another can be picked.
    titles: list[TitleOption] | None
    # The back-cover blurb, first person, 2-4 sentences: the draft's while choosing, then the book's.
    blurb: str | None
    # While drafting or finishing: the writing is going on, or failed. Poll GET /interview. A failure
    # is retried once when the member comes back; after that the same POST tries again.
    step_status: Literal["writing", "failed"] | None
    # While finishing: the title being written.
    chosen_title: str | None
    # While revising: the changes are being written, are ready, or failed. A failure is retried
    # once on its own when the member comes back; after that POST /interview/finish tries again.
    revision_status: Literal["writing", "ready", "failed"] | None
    # The proposed changes once ready. Nothing changes on the shelf until POST /interview/revision.
    changes: list[Change] | None
    # The proposed back cover, if every change is approved.
    proposed_blurb: str | None
    # While revising: the member's saved choices, null until they've made any.
    approved_changes: list[str] | None
    # The back cover for those choices, to read before confirming. `stale` means the choices changed
    # after it was written: POST /interview/revision/blurb again. Null means it hasn't been asked for.
    selection_blurb_status: Literal["writing", "ready", "failed", "stale"] | None
    selection_blurb: str | None
    # The last round earned no changes, so the book is as it was. The app says so plainly.
    nothing_new: bool
    # It earned none because the only changes named someone or somewhere. Say why, and offer another
    # go: `reading_question_id` is open again, and POST .../answer takes the new words.
    dropped_for_names: bool
    reading_question_id: str | None
    # With `dropped_for_names`: the answer, for the field, so the member needn't type it again, and the
    # words that counted as names, in the order they said them. Null otherwise.
    reading_answer: str | None
    dropped_words: list[str] | None
    # The Librarian's marks and notebook while interviewing or adding (L1). Null otherwise.
    librarian: LibrarianState | None = None
    # The Librarian's handwritten line under the title, at the reveal of the finished book.
    sign_off: str | None = None


class StaleQuestionResponse(BaseModel):
    """The 409 when an answer or skip names a question that isn't the one waiting. Nothing was saved."""

    detail: str
    interview: InterviewResponse
    # True only when this exact answer was saved by an earlier send whose reply was lost. False means
    # these words were NOT saved: the member moved on elsewhere, so keep them in the field.
    already_saved: bool
