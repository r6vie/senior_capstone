"""The interview engine: the AI half of the interview (docs/trove.md §4, §9.3, §9.4).

Stateless functions over the transcript. The interview service stores turns and calls these;
nothing here touches the database. Prompts live in trove/ai/prompts/interview/.

Errors: ClaudeRefused when Claude declines, Anthropic SDK errors as they come, and ValueError
(pydantic's ValidationError is one) when a reply is unusable even after a retry.
"""

import json
import re
from typing import Literal
from uuid import uuid4

from anthropic import transform_schema
from pydantic import BaseModel, Field

from trove.ai.client import Claude, text_of
from trove.ai.prompts import load_prompt

Phase = Literal["sweep", "dig", "shape"]

# The spec asks for about 15-25 questions. Past SHAPE_BY the Librarian is told to wrap up;
# at MAX_QUESTIONS the reveal is forced. Before MIN_ANSWERS a reveal is never offered.
MIN_ANSWERS = 8
SHAPE_BY = 21
MAX_QUESTIONS = 25
MIN_CHAPTERS, MAX_CHAPTERS = 3, 5
# The back-cover blurb fits the book's `blurb` field (B1).
MAX_BLURB = 600

# Questions are on the member's critical path, so they think less than the one-off book steps.
QUESTION_EFFORT = "medium"
BOOK_EFFORT = "high"
MAX_TOKENS = 16000


class Turn(BaseModel):
    question: str
    answer: str
    phase: Phase


class NextTurn(BaseModel):
    question: str
    phase: Phase
    # Set only in Shape: the one-or-two-line "Is this you?" summary in the member's own words.
    playback: str | None
    ready_for_reveal: bool
    # A few words for "Last time you were telling me about {topic}." Display only, never the book.
    topic: str


class DraftChapter(BaseModel):
    id: str
    title: str
    summary: str
    quotes: list[str]


class TitleOption(BaseModel):
    title: str
    why: str


class Draft(BaseModel):
    pool: list[DraftChapter]
    titles: list[TitleOption]
    # The back cover for the pool as a whole. None only on drafts saved before blurbs existed.
    blurb: str | None = None


class FinishedBook(BaseModel):
    chapters: list[DraftChapter]
    blurb: str | None


# What Claude returns. Ids and quote checks are added in code, never trusted to the model.


class Thread(BaseModel):
    thread: str = Field(description="A few words naming the thread.")
    missing: str = Field(description="One line on what this thread still needs.")


class TurnPlan(BaseModel):
    threads: list[Thread] = Field(description="Private ranking, strongest first.")
    phase: Phase
    question: str
    playback: str | None
    topic: str
    ready_for_reveal: bool


class _Chapter(BaseModel):
    title: str
    summary: str
    quotes: list[str]


class _Draft(BaseModel):
    pool: list[_Chapter]
    titles: list[TitleOption]
    blurb: str


class _Retold(BaseModel):
    title: str
    summary: str


class _FinishedChapter(BaseModel):
    pool_id: str
    title: str
    summary: str


class _Finished(BaseModel):
    chapters: list[_FinishedChapter]
    blurb: str


class _Blurb(BaseModel):
    blurb: str


async def next_turn(claude: Claude, *, turns: list[Turn], resume_text: str | None) -> NextTurn:
    """The Librarian's next question, given every turn so far."""
    plan = await plan_turn(claude, turns=turns, resume_text=resume_text)
    return NextTurn(
        question=plan.question,
        phase=plan.phase,
        playback=plan.playback,
        ready_for_reveal=plan.ready_for_reveal,
        topic=plan.topic,
    )


async def plan_turn(claude: Claude, *, turns: list[Turn], resume_text: str | None) -> TurnPlan:
    """next_turn plus the private thread ranking, which the evals read."""
    plan = await _ask(
        claude, "interview/interviewer", _turn_blocks(turns, resume_text), TurnPlan, QUESTION_EFFORT
    )

    answered = sum(1 for turn in turns if turn.answer.strip())
    if not turns:
        plan.phase = "sweep"
    if answered < MIN_ANSWERS:
        plan.ready_for_reveal = False
    if len(turns) >= MAX_QUESTIONS:
        plan.ready_for_reveal = True
    if plan.phase != "shape":
        plan.playback = None
    return plan


async def draft_book(claude: Claude, *, turns: list[Turn]) -> Draft:
    """One shared pool of grounded chapters, three titles that read it differently (§9.4), and a
    back-cover blurb."""
    content = f"{_transcript(turns)}\n\nDraft the pool of chapters, the three titles and the blurb."
    for _ in range(2):
        raw = await _ask(claude, "interview/draft", content, _Draft, BOOK_EFFORT)
        pool = []
        for chapter in raw.pool:
            quotes = grounded_quotes(chapter.quotes, turns)
            if quotes:
                pool.append(
                    DraftChapter(id=str(uuid4()), title=chapter.title, summary=chapter.summary, quotes=quotes)
                )
        blurb = _usable_blurb(raw.blurb)
        if len(pool) >= MIN_CHAPTERS and len(raw.titles) >= 3 and blurb:
            return Draft(pool=pool, titles=raw.titles[:3], blurb=blurb)
    raise ValueError("The draft didn't have enough grounded chapters, three titles and a blurb.")


async def finish_book(claude: Claude, *, turns: list[Turn], draft: Draft, title: str) -> FinishedBook:
    """3 to 5 chapters from the pool, in reading order, angled to the chosen title, and the blurb
    rewritten for them."""
    pool = {chapter.id: chapter for chapter in draft.pool}
    listing = json.dumps(
        [{"pool_id": c.id, "title": c.title, "summary": c.summary} for c in draft.pool], indent=1
    )
    content = (
        f"{_transcript(turns)}\n\n<pool>\n{listing}\n</pool>\n\n"
        f"<chosen_title>{title}</chosen_title>\n\nFinish the book for this title."
    )
    raw = await _ask(claude, "interview/finish", content, _Finished, BOOK_EFFORT)

    chapters: list[DraftChapter] = []
    for chosen in raw.chapters:
        source = pool.get(chosen.pool_id)
        if source and all(c.id != source.id for c in chapters):
            chapters.append(
                DraftChapter(id=source.id, title=chosen.title, summary=chosen.summary, quotes=source.quotes)
            )
    # A short or garbled pick still yields a usable book: top up from the pool, in pool order.
    for source in draft.pool:
        if len(chapters) >= MIN_CHAPTERS:
            break
        if all(c.id != source.id for c in chapters):
            chapters.append(source)
    # An unusable blurb falls back to the draft's, which is grounded in the same interview.
    blurb = _usable_blurb(raw.blurb) or draft.blurb
    return FinishedBook(chapters=chapters[:MAX_CHAPTERS], blurb=blurb)


async def write_blurb(claude: Claude, *, turns: list[Turn], chapters: list[DraftChapter]) -> str:
    """A fresh back-cover blurb for these chapters, after a change to what the book covers."""
    listing = json.dumps([{"title": c.title, "summary": c.summary} for c in chapters], indent=1)
    content = (
        f"{_transcript(turns)}\n\n<book_chapters>\n{listing}\n</book_chapters>\n\n"
        "Write the back-cover blurb for this book."
    )
    for _ in range(2):
        raw = await _ask(claude, "interview/blurb", content, _Blurb, BOOK_EFFORT)
        blurb = _usable_blurb(raw.blurb)
        if blurb:
            return blurb
    raise ValueError("The blurb was empty or too long.")


async def rewrite_chapter(
    claude: Claude, *, turns: list[Turn], chapters: list[DraftChapter], chapter_id: str
) -> DraftChapter:
    """The same chapter, better told: a new title and summary, keeping its id, topic and quotes."""
    current = next((chapter for chapter in chapters if chapter.id == chapter_id), None)
    if current is None:
        raise ValueError(f"No chapter {chapter_id!r} in this book.")
    listing = json.dumps(
        [{**chapter.model_dump(), "rewrite_this": chapter.id == chapter_id} for chapter in chapters],
        indent=1,
    )
    content = (
        f"{_transcript(turns)}\n\n<book_chapters>\n{listing}\n</book_chapters>\n\n"
        "Rewrite the title and summary of the chapter marked rewrite_this."
    )
    raw = await _ask(claude, "interview/rewrite", content, _Retold, BOOK_EFFORT)
    # The quotes are what tie the chapter to its topic, so they never change on a rewrite.
    return current.model_copy(update={"title": raw.title, "summary": raw.summary})


def _usable_blurb(blurb: str) -> str | None:
    """The blurb if it fits. One that runs long is cut back to its last whole sentence that fits,
    as long as two sentences remain; cutting can't add anything ungrounded."""
    blurb = blurb.strip()
    if len(blurb) > MAX_BLURB:
        ends = [m.end() for m in re.finditer(r"[.!?](?=\s|$)", blurb[: MAX_BLURB + 1])]
        blurb = blurb[: ends[-1]] if len(ends) >= 2 else ""
    return blurb or None


def grounded_quotes(quotes: list[str], turns: list[Turn]) -> list[str]:
    """The quotes that appear verbatim in one of the member's answers, ignoring case, spacing and
    curly-vs-straight punctuation. Anything else may be the model's words, so it's dropped."""
    answers = [_normalize(turn.answer) for turn in turns]
    kept = []
    for quote in quotes:
        needle = _normalize(quote)
        if needle and any(needle in answer for answer in answers) and quote.strip() not in kept:
            kept.append(quote.strip())
    return kept


_PUNCTUATION = str.maketrans(
    {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-"}
)


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(_PUNCTUATION)).strip().strip("\"'").strip().casefold()


def _transcript(turns: list[Turn]) -> str:
    return "\n".join(
        ["<interview>", *(_render(n, turn) for n, turn in enumerate(turns, start=1)), "</interview>"]
    )


def _render(number: int, turn: Turn) -> str:
    answer = turn.answer.strip() or "(skipped)"
    return f"Q{number} [{turn.phase}]: {turn.question}\nA{number}: {answer}\n"


def _turn_blocks(turns: list[Turn], resume_text: str | None) -> list[dict]:
    """The transcript as one content block per turn, with a cache breakpoint on the newest turn.
    Each request then extends the previous one's prefix, so the interview so far is read from
    the cache instead of being paid for again on every question."""
    blocks = []
    if resume_text and resume_text.strip():
        blocks.append({"type": "text", "text": f"<resume>\n{resume_text.strip()}\n</resume>\n"})
    blocks.append({"type": "text", "text": "<interview>\n"})
    blocks += [{"type": "text", "text": _render(n, turn)} for n, turn in enumerate(turns, start=1)]
    blocks[-1]["cache_control"] = {"type": "ephemeral"}
    blocks.append({"type": "text", "text": f"</interview>\n\n{_status(turns)}"})
    return blocks


def _status(turns: list[Turn]) -> str:
    asked = len(turns)
    answered = sum(1 for turn in turns if turn.answer.strip())
    if not turns:
        return "The interview is starting. Ask the first question."
    note = f"Questions asked so far: {asked}. Answered: {answered}."
    if asked >= MAX_QUESTIONS:
        return f"{note} That is the limit: set ready_for_reveal to true and close."
    if asked >= SHAPE_BY:
        return f"{note} Move to Shape now if you aren't there already."
    if answered < MIN_ANSWERS:
        return f"{note} It's too early for the reveal."
    return note


async def _ask[T: BaseModel](
    claude: Claude, prompt: str, content: str | list[dict], model: type[T], effort: str
) -> T:
    response = await claude.create(
        max_tokens=MAX_TOKENS,
        system=load_prompt(prompt),
        thinking={"type": "adaptive"},
        output_config={
            "effort": effort,
            "format": {"type": "json_schema", "schema": transform_schema(model)},
        },
        messages=[{"role": "user", "content": content}],
    )
    return model.model_validate_json(text_of(response))
