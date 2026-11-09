"""The interview engine: the AI half of the interview (docs/trove.md §4, §9.3, §9.4).

Stateless functions over the transcript. The interview service stores turns and calls these;
nothing here touches the database. Prompts live in trove/ai/prompts/interview/.

Errors: ClaudeRefused when Claude declines, Anthropic SDK errors as they come, and ValueError
(pydantic's ValidationError is one) when a reply is unusable even after a retry.
"""

import json
import re
from collections.abc import Callable
from difflib import SequenceMatcher
from typing import Literal
from uuid import uuid4

from anthropic import transform_schema
from pydantic import BaseModel, Field

from trove.ai.client import Claude, text_of
from trove.ai.prompts import load_prompt

Phase = Literal["sweep", "dig", "shape"]
# Turns after the first interview: a question of an adding round (I3), or the question after a reading (I6).
TurnPhase = Literal["sweep", "dig", "shape", "adding", "reading"]

# The spec asks for about 15-25 questions. Past SHAPE_BY the Librarian is told to wrap up;
# at MAX_QUESTIONS the reveal is forced. Before MIN_ANSWERS a reveal is never offered.
MIN_ANSWERS = 8
SHAPE_BY = 21
MAX_QUESTIONS = 25
# Skipped questions don't count toward MAX_QUESTIONS (skips are never counted, §4), so a hard
# limit on all questions keeps an interview from running forever.
MAX_TURNS = 40
# Sweep covers at least this many questions before Dig, whatever the first answer offers.
MIN_SWEEP = 4
# Answers run thin (docs/trove.md §4, §9.9) when this many of the last few are short or unsure.
# The signal is internal: it changes the angle of the next question and is never shown.
THIN_WINDOW, THIN_SWITCH = 3, 2
SHORT_ANSWER_WORDS, UNSURE_ANSWER_WORDS = 10, 15
MIN_CHAPTERS, MAX_CHAPTERS = 3, 5
# A quote shorter than this can't show a chapter is theirs ("I made it.").
MIN_QUOTE_WORDS = 5
# A rewrite this close to the original isn't a rewrite.
REWRITE_TOO_CLOSE = 0.9
# A book may grow past its first version, to this many chapters (docs/review/decisions.md, row 1).
MAX_BOOK_CHAPTERS = 8
# A round of adding is short. Skips count only toward the second limit, so skipping can't run forever.
MAX_ADDING_ANSWERS, MAX_ADDING_TURNS = 8, 14
# A proposed chapter title this close to a spark's title is someone else's title, so it's rejected.
SPARK_TITLE_TOO_CLOSE = 0.8
# Capitalized words that aren't names, for checking reading answers. Anything else capitalized is
# treated as a name: at worst a quote is dropped, which the member never sees as a loss of their words.
NOT_NAMES = frozenset(
    [
        "a",
        "about",
        "after",
        "again",
        "all",
        "also",
        "although",
        "an",
        "and",
        "another",
        "any",
        "are",
        "as",
        "at",
        "because",
        "been",
        "before",
        "being",
        "both",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "during",
        "each",
        "even",
        "every",
        "few",
        "first",
        "for",
        "from",
        "had",
        "has",
        "have",
        "he",
        "her",
        "here",
        "his",
        "how",
        "i",
        "i'd",
        "i'll",
        "i'm",
        "i've",
        "if",
        "in",
        "into",
        "is",
        "it",
        "it's",
        "its",
        "just",
        "last",
        "later",
        "like",
        "maybe",
        "more",
        "most",
        "much",
        "my",
        "next",
        "no",
        "not",
        "now",
        "of",
        "on",
        "once",
        "one",
        "only",
        "or",
        "other",
        "our",
        "out",
        "over",
        "really",
        "she",
        "since",
        "so",
        "some",
        "someone",
        "still",
        "such",
        "than",
        "that",
        "that's",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "they'd",
        "this",
        "those",
        "though",
        "to",
        "two",
        "until",
        "usually",
        "very",
        "was",
        "we",
        "we'd",
        "were",
        "what",
        "when",
        "where",
        "which",
        "while",
        "who",
        "why",
        "will",
        "with",
        "would",
        "yes",
        "you",
        "your",
        "honestly",
    ]
)
# The back-cover blurb fits the book's `blurb` field (B1).
MAX_BLURB = 600

# "Is this you?" is the most personal moment of the interview, on a phone (R1-14 in the quality notes).
MAX_PLAYBACK_WORDS = 30
# Shape is 1-3 questions, and following a hedge can stretch it, so it gets a nudge to close here.
MAX_SHAPE = 4

# Questions are on the member's critical path, so they think less than the one-off book steps.
QUESTION_EFFORT = "medium"
BOOK_EFFORT = "high"
MAX_TOKENS = 16000


class NotEnoughMaterial(ValueError):
    """The answers can't yet make enough grounded chapters. Trying again can't help: only more answers can."""


class Turn(BaseModel):
    question: str
    # Empty when the member skipped the question.
    answer: str
    phase: TurnPhase


class NextTurn(BaseModel):
    question: str
    phase: Phase
    # Set only in Shape: the one-or-two-line "Is this you?" summary in the member's own words.
    playback: str | None
    ready_for_reveal: bool
    # A few words for "Last time you were telling me about {topic}." Display only, never the book.
    topic: str
    # The spark this question works from, if any.
    spark_id: str | None = None


class AddingTurn(BaseModel):
    """The next step of an adding round. `done` means no more questions: `question` is empty."""

    question: str
    topic: str
    done: bool
    spark_id: str | None = Field(None, description="The id of the spark this question works from, if any.")


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


class CurrentChapter(BaseModel):
    title: str
    summary: str


class Change(BaseModel):
    """One proposed change to a book on the shelf, which the member approves or declines."""

    id: str
    kind: Literal["new", "improve", "remove"]
    # The chapter an `improve` replaces or a `remove` takes out. Null for a new chapter.
    chapter_id: str | None
    title: str
    summary: str
    quotes: list[str]
    # One line to the member on what changed.
    note: str
    # What's there now, so the member can compare. Null for a new chapter.
    current: CurrentChapter | None
    # Where a new chapter goes, 1 being first. Null means last.
    position: int | None = None


class Revision(BaseModel):
    changes: list[Change]
    # The back cover if every change is approved. Null means it has to be written first.
    blurb: str | None
    # No changes survive, and at least one was dropped only for naming someone or somewhere.
    dropped_for_names: bool = False
    # Then, the words in the reading answers that count as names, in the order they were said.
    dropped_words: list[str] = []


# What Claude returns. Ids and quote checks are added in code, never trusted to the model.


class Thread(BaseModel):
    thread: str = Field(description="A few words naming the thread.")
    has_moment: bool = Field(description="Whether the member gave a specific moment or method for it.")
    missing: str = Field(description="One line on what this thread still needs.")


class TurnPlan(BaseModel):
    threads: list[Thread] = Field(description="Private ranking, strongest first.")
    phase: Phase
    question: str
    playback: str | None
    topic: str
    ready_for_reveal: bool
    spark_id: str | None = Field(None, description="The id of the spark this question works from, if any.")


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


class _Change(BaseModel):
    kind: Literal["new", "improve"]
    chapter_id: str | None
    title: str
    summary: str
    quotes: list[str]
    note: str
    position: int | None = Field(
        None, description="Where a new chapter goes, 1 being first. Null means last."
    )


class _Revision(BaseModel):
    changes: list[_Change]
    blurb: str


async def next_turn(
    claude: Claude,
    *,
    turns: list[Turn],
    resume_text: str | None,
    sparks: list[dict] | None = None,
    more_material: bool = False,
) -> NextTurn:
    """The Librarian's next question, given every turn so far. `more_material` means a draft has just
    found too little, so the interview carries on past its usual limits."""
    plan = await plan_turn(
        claude, turns=turns, resume_text=resume_text, sparks=sparks, more_material=more_material
    )
    return NextTurn(
        question=plan.question,
        phase=plan.phase,
        playback=plan.playback,
        ready_for_reveal=plan.ready_for_reveal,
        topic=plan.topic,
        spark_id=plan.spark_id,
    )


async def plan_turn(
    claude: Claude,
    *,
    turns: list[Turn],
    resume_text: str | None,
    sparks: list[dict] | None = None,
    more_material: bool = False,
) -> TurnPlan:
    """next_turn plus the private thread ranking, which the evals read."""
    blocks = _turn_blocks(turns, resume_text, sparks, more_material)
    plan = await _ask(claude, "interview/interviewer", blocks, TurnPlan, QUESTION_EFFORT)
    if plan.phase == "shape" and len((plan.playback or "").split()) > MAX_PLAYBACK_WORDS:
        limit = f"\n\nThe playback must be at most {MAX_PLAYBACK_WORDS} words. Write it again, shorter."
        retry = [*blocks[:-1], {**blocks[-1], "text": blocks[-1]["text"] + limit}]
        plan = await _ask(claude, "interview/interviewer", retry, TurnPlan, QUESTION_EFFORT)

    answered = sum(1 for turn in turns if turn.answer.strip())
    if not turns:
        plan.phase = "sweep"
    if _questions_asked(turns) >= MAX_QUESTIONS or len(turns) >= MAX_TURNS:
        plan.ready_for_reveal = True
    # The floor wins over the limits: a book is never drafted from fewer answers than this.
    if answered < MIN_ANSWERS:
        plan.ready_for_reveal = False
    if more_material:
        plan.ready_for_reveal = False
        plan.phase = "dig"
    if plan.phase != "shape":
        plan.playback = None
    return plan


def _never(_text: str) -> bool:
    return False


async def draft_book(
    claude: Claude,
    *,
    turns: list[Turn],
    leaks: Callable[[str], bool] = _never,
    spark_titles: list[str] | None = None,
) -> Draft:
    """One shared pool of grounded chapters, three titles that read it differently (§9.4), and a
    back-cover blurb. `leaks` says whether text carries a term from outside the member's answers: that
    forces one retry, and after that the item is dropped. Raises NotEnoughMaterial if too few chapters
    survive, because then only more answers can help."""
    content = f"{_transcript(turns)}\n\nDraft the pool of chapters, the three titles and the blurb."
    pool: list[DraftChapter] = []
    for attempt in range(2):
        raw = await _ask(claude, "interview/draft", content, _Draft, BOOK_EFFORT)
        written = [
            raw.blurb,
            *(f"{t.title} {t.why}" for t in raw.titles),
            *(f"{c.title} {c.summary}" for c in raw.pool),
        ]
        if attempt == 0 and any(leaks(text) for text in written):
            continue
        pool = []
        used: set[str] = set()
        for chapter in raw.pool:
            # A quote grounds only one chapter: three chapters on one sentence are one chapter.
            quotes = _unused(grounded_quotes(chapter.quotes, turns), used)
            public = f"{chapter.title} {chapter.summary}"
            if quotes and not leaks(public) and not _too_close_to_a_spark(chapter.title, spark_titles):
                used |= {_normalize(quote) for quote in quotes}
                pool.append(
                    DraftChapter(id=str(uuid4()), title=chapter.title, summary=chapter.summary, quotes=quotes)
                )
        titles = [t for t in raw.titles if not leaks(f"{t.title} {t.why}")]
        blurb = _usable_blurb(raw.blurb)
        if blurb and leaks(blurb):
            blurb = None
        if len(pool) >= MIN_CHAPTERS and len(titles) >= 3 and blurb:
            titles = [t.model_copy(update={"title": _sentence_case(t.title, turns)}) for t in titles[:3]]
            return Draft(pool=pool, titles=titles, blurb=blurb)
    if len(pool) < MIN_CHAPTERS:
        raise NotEnoughMaterial("The draft didn't have enough grounded chapters.")
    raise ValueError("The draft didn't have three titles and a blurb.")


async def finish_book(
    claude: Claude,
    *,
    turns: list[Turn],
    draft: Draft,
    title: str,
    leaks: Callable[[str], bool] = _never,
    spark_titles: list[str] | None = None,
) -> FinishedBook:
    """3 to 5 chapters from the pool, in reading order, angled to the chosen title, and the blurb
    rewritten for them. Anything that fails a check falls back to the pool's own text."""
    pool = {chapter.id: chapter for chapter in draft.pool}
    listing = json.dumps(
        [{"pool_id": c.id, "title": c.title, "summary": c.summary} for c in draft.pool], indent=1
    )
    content = (
        f"{_transcript(turns)}\n\n<pool>\n{listing}\n</pool>\n\n"
        f"<chosen_title>{title}</chosen_title>\n\nFinish the book for this title."
    )
    raw = await _ask(claude, "interview/finish", content, _Finished, BOOK_EFFORT)
    if any(leaks(f"{c.title} {c.summary}") for c in raw.chapters) or leaks(raw.blurb):
        raw = await _ask(claude, "interview/finish", content, _Finished, BOOK_EFFORT)

    chapters: list[DraftChapter] = []
    for chosen in raw.chapters:
        source = pool.get(chosen.pool_id)
        if source and all(c.id != source.id for c in chapters):
            unusable = leaks(f"{chosen.title} {chosen.summary}") or _too_close_to_a_spark(
                chosen.title, spark_titles
            )
            chapters.append(
                source
                if unusable
                else DraftChapter(
                    id=source.id, title=chosen.title, summary=chosen.summary, quotes=source.quotes
                )
            )
    # A short or garbled pick still yields a usable book: top up from the pool, in pool order.
    for source in draft.pool:
        if len(chapters) >= MIN_CHAPTERS:
            break
        if all(c.id != source.id for c in chapters):
            chapters.append(source)
    # An unusable blurb falls back to the draft's, which is grounded in the same interview.
    blurb = _usable_blurb(raw.blurb)
    if not blurb or leaks(blurb):
        blurb = draft.blurb
    return FinishedBook(chapters=chapters[:MAX_CHAPTERS], blurb=blurb)


async def write_blurb(
    claude: Claude, *, turns: list[Turn], chapters: list[DraftChapter], leaks: Callable[[str], bool] = _never
) -> str:
    """A fresh back-cover blurb for these chapters, after a change to what the book covers."""
    listing = json.dumps([{"title": c.title, "summary": c.summary} for c in chapters], indent=1)
    content = (
        f"{_transcript(turns)}\n\n<book_chapters>\n{listing}\n</book_chapters>\n\n"
        "Write the back-cover blurb for this book."
    )
    for _ in range(2):
        raw = await _ask(claude, "interview/blurb", content, _Blurb, BOOK_EFFORT)
        blurb = _usable_blurb(raw.blurb)
        if blurb and not leaks(blurb):
            return blurb
    raise ValueError("The blurb was empty, too long or carried a term the member never said.")


async def rewrite_chapter(
    claude: Claude,
    *,
    turns: list[Turn],
    chapters: list[DraftChapter],
    chapter_id: str,
    leaks: Callable[[str], bool] = _never,
    spark_titles: list[str] | None = None,
) -> DraftChapter:
    """The same chapter, better told: a new title and summary, keeping its id, topic and quotes. One
    too close to the original gets one more try. After that the original comes back unchanged."""
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
    for attempt in range(2):
        note = "\n\nThe last attempt was too close to the original. Tell it differently." if attempt else ""
        raw = await _ask(claude, "interview/rewrite", content + note, _Retold, BOOK_EFFORT)
        close = SequenceMatcher(None, current.summary, raw.summary).ratio() > REWRITE_TOO_CLOSE
        if (
            not close
            and not leaks(f"{raw.title} {raw.summary}")
            and not _too_close_to_a_spark(raw.title, spark_titles)
        ):
            # The quotes are what tie the chapter to its topic, so they never change on a rewrite.
            return current.model_copy(update={"title": raw.title, "summary": raw.summary})
    return current


async def next_adding_turn(
    claude: Claude,
    *,
    turns: list[Turn],
    round_start: int,
    chapters: list[DraftChapter],
    sparks: list[dict],
    off_limits: list[dict] | None = None,
) -> AddingTurn:
    """The next question of a round of adding to a book on the shelf, or the end of the round."""
    new = turns[round_start:]
    answered = sum(1 for turn in new if not _skipped(turn))
    # At the limit there's nothing to ask Claude, so nothing is spent.
    if answered >= MAX_ADDING_ANSWERS or len(new) >= MAX_ADDING_TURNS:
        return AddingTurn(question="", topic="what you've just added", done=True)
    plan = await _ask(
        claude,
        "interview/adding",
        _adding_blocks(turns, round_start, chapters, sparks, off_limits),
        AddingTurn,
        QUESTION_EFFORT,
    )
    if plan.done and answered > 0:
        return plan.model_copy(update={"question": ""})
    if not plan.question.strip():
        raise ValueError("The adding round has to ask something before it can end.")
    return plan.model_copy(update={"done": False})


async def revise_book(
    claude: Claude,
    *,
    turns: list[Turn],
    round_start: int,
    chapters: list[DraftChapter],
    blurb: str | None,
    off_limits: list[dict] | None = None,
    member_names: list[str] | None = None,
    spark_titles: list[str] | None = None,
    leaks: Callable[[str], bool] = _never,
) -> Revision:
    """Proposed changes to the book from the round's answers. Grounding is checked here: a change
    must quote the member verbatim, and at least once from this round. An empty list is a real
    result: a thin answer can earn nothing. `member_names` never reach the prompt: they're how the
    check on reading answers tells the member's name from someone else's."""
    room = max(0, MAX_BOOK_CHAPTERS - len(chapters))
    listing = json.dumps([chapter.model_dump() for chapter in chapters], indent=1)
    content = (
        f"{_transcript(turns[:round_start])}\n\n{_new_round(turns, round_start)}\n\n"
        f"<book_chapters>\n{listing}\n</book_chapters>\n\n"
        f"<current_blurb>{blurb or ''}</current_blurb>\n\n<room>{room}</room>{_off_limits_block(off_limits)}\n\n"
        "Propose the changes these new answers earn."
    )
    raw = await _ask(claude, "interview/revise", content, _Revision, BOOK_EFFORT)
    if any(leaks(f"{c.title} {c.summary}") for c in raw.changes) or leaks(raw.blurb):
        raw = await _ask(claude, "interview/revise", content, _Revision, BOOK_EFFORT)
    by_id = {chapter.id: chapter for chapter in chapters}
    new_turns = turns[round_start:]
    others = _other_people(new_turns, member_names or [])
    changes: list[Change] = []
    used = {_normalize(quote) for chapter in chapters for quote in chapter.quotes}
    named = False
    for change in raw.changes:
        quotes = [
            q for q in grounded_quotes(change.quotes, turns) if not _names_someone(q, new_turns, others)
        ]
        new_quotes = _unused(grounded_quotes(quotes, new_turns), used)
        public = f"{change.title} {change.summary}"
        said_new = grounded_quotes(change.quotes, new_turns)
        if _mentions_any(public, others) or (
            not new_quotes and any(_names_someone(quote, new_turns, others) for quote in said_new)
        ):
            named = True
            continue
        if not new_quotes or leaks(public) or _too_close_to_a_spark(change.title, spark_titles):
            continue
        current = None
        if change.kind == "improve":
            chapter = by_id.get(change.chapter_id or "")
            if chapter is None or any(c.chapter_id == chapter.id for c in changes):
                continue
            # Text that didn't change isn't a change, whatever quote it cites.
            if _normalize(change.title) == _normalize(chapter.title) and _normalize(
                change.summary
            ) == _normalize(chapter.summary):
                continue
            current = CurrentChapter(title=chapter.title, summary=chapter.summary)
            # The chapter keeps the words it stands on, plus what was added.
            quotes = [*chapter.quotes, *new_quotes]
        elif change.kind == "new" and room > 0:
            room -= 1
            quotes = _unused(quotes, used)
        else:
            continue
        used |= {_normalize(quote) for quote in quotes}
        changes.append(
            Change(
                id=str(uuid4()),
                kind=change.kind,
                chapter_id=change.chapter_id if change.kind == "improve" else None,
                title=change.title,
                summary=change.summary,
                quotes=quotes,
                note=PLAIN_NOTE if _PRAISE.search(change.note) else change.note,
                current=current,
                position=change.position if change.kind == "new" else None,
            )
        )
    proposed = _usable_blurb(raw.blurb) if changes else None
    if proposed and (_mentions_any(proposed, others) or leaks(proposed)):
        proposed = None
    dropped = named and not changes
    return Revision(
        changes=changes,
        blurb=proposed,
        dropped_for_names=dropped,
        dropped_words=_in_order_said(new_turns, others) if dropped else [],
    )


# The "what changed" line states the addition. Praise in it is flattery under the member's own book.
_PRAISE = re.compile(
    r"\b(great|amazing|impressive|fascinating|wonderful|powerful|compelling|richer|stronger|better|"
    r"beautiful|brilliant|vivid|excellent|sharper)\b",
    re.IGNORECASE,
)
PLAIN_NOTE = "Adds what you just said."


def _unused(quotes: list[str], used: set[str]) -> list[str]:
    return [quote for quote in quotes if _normalize(quote) not in used]


def _capitalized_words(text: str) -> set[str]:
    return set(re.findall(r"\b[A-Z][A-Za-z-]+", text))


def _other_people(new_turns: list[Turn], member_names: list[str]) -> set[str]:
    """Capitalized words in reading answers that may name someone. The member's own names don't count."""
    own = {part.casefold() for name in member_names for part in name.split()}
    words: set[str] = set()
    for turn in new_turns:
        if turn.phase == "reading":
            words |= _capitalized_words(turn.answer)
    return {w for w in words if w.casefold() not in NOT_NAMES and w.casefold() not in own}


def _in_order_said(new_turns: list[Turn], others: set[str]) -> list[str]:
    said = [
        word
        for turn in new_turns
        if turn.phase == "reading"
        for word in re.findall(r"\b[A-Z][A-Za-z-]+", turn.answer)
        if word in others
    ]
    return list(dict.fromkeys(said))


def _names_someone(quote: str, new_turns: list[Turn], others: set[str]) -> bool:
    """Whether a quote from a reading answer has a possible name in it."""
    from_reading = bool(grounded_quotes([quote], [t for t in new_turns if t.phase == "reading"]))
    return from_reading and _mentions_any(quote, others)


def _mentions_any(text: str, words: set[str]) -> bool:
    return bool(_capitalized_words(text) & words)


def _too_close_to_a_spark(title: str, spark_titles: list[str] | None) -> bool:
    return any(
        SequenceMatcher(None, title.casefold(), spark.casefold()).ratio() >= SPARK_TITLE_TOO_CLOSE
        for spark in spark_titles or []
    )


def _off_limits_block(off_limits: list[dict] | None) -> str:
    if not off_limits:
        return ""
    return f"\n\n<off_limits>\n{json.dumps(off_limits, indent=1)}\n</off_limits>"


def _new_round(turns: list[Turn], round_start: int) -> str:
    rendered = (_render(n, turn) for n, turn in enumerate(turns, start=1) if n > round_start)
    return "\n".join(["<new_round>", *rendered, "</new_round>"])


def _sparks_block(sparks: list[dict] | None) -> str:
    """Only titles of other people's chapters, as a cue. The prompts say none of it is about the member."""
    if not sparks:
        return ""
    listed = "\n".join(f"- [{spark['id']}] {spark['title']}" for spark in sparks)
    return f"\n\n<sparks>\n{listed}\n</sparks>"


def _adding_blocks(
    turns: list[Turn],
    round_start: int,
    chapters: list[DraftChapter],
    sparks: list[dict],
    off_limits: list[dict] | None = None,
) -> list[dict]:
    """The book and the earlier interview, then one block per new turn with a cache breakpoint on
    the newest, so each question of the round reads what came before from the cache."""
    listing = json.dumps([{"title": c.title, "summary": c.summary} for c in chapters], indent=1)
    new = turns[round_start:]
    blocks = [
        {
            "type": "text",
            "text": f"<book_chapters>\n{listing}\n</book_chapters>\n\n{_transcript(turns[:round_start])}\n\n",
        },
        {"type": "text", "text": "<new_round>\n"},
    ]
    blocks += [
        {"type": "text", "text": _render(n, turn)} for n, turn in enumerate(new, start=round_start + 1)
    ]
    blocks[-1]["cache_control"] = {"type": "ephemeral"}
    answered = sum(1 for turn in new if not _skipped(turn))
    status = f"Questions answered this round: {answered}."
    if new and _skipped(new[-1]):
        status += " The member skipped the last question. Move to other ground."
    skipped = [turn.question for turn in new if _skipped(turn)]
    if skipped:
        status += " Skipped so far, so stay off these subjects: " + " | ".join(skipped)
    if len(chapters) >= MAX_BOOK_CHAPTERS:
        status += (
            " The book is at its limit of chapters. Only improve: hunt for what's thin, not for new chapters."
        )
    tail = f"{status}{_sparks_block(sparks)}{_off_limits_block(off_limits)}"
    blocks.append({"type": "text", "text": f"</new_round>\n\n{tail}"})
    return blocks


def _sentence_case(title: str, turns: list[Turn]) -> str:
    """One case for titles on one shelf. A word stays capitalized only if the member wrote it that way
    somewhere other than the start of a sentence, which is how a name looks."""
    first, *rest = title.split()
    if sum(word[0].isupper() for word in rest) < 2:
        return title
    answers = " ".join(turn.answer for turn in turns)
    named = set(re.findall(r"(?<=[a-z,;] )[A-Z][\w'-]*", answers))
    return " ".join([first, *(word if word in named else word.lower() for word in rest)])


def _usable_blurb(blurb: str) -> str | None:
    """The blurb if it fits. One that runs long is cut back to its last whole sentence that fits,
    as long as two sentences remain; cutting can't add anything ungrounded."""
    blurb = blurb.strip()
    if len(blurb) > MAX_BLURB:
        ends = [m.end() for m in re.finditer(r"[.!?](?=\s|$)", blurb[: MAX_BLURB + 1])]
        blurb = blurb[: ends[-1]] if len(ends) >= 2 else ""
    return blurb or None


def grounded_quotes(quotes: list[str], turns: list[Turn]) -> list[str]:
    """The quotes of at least MIN_QUOTE_WORDS that appear verbatim in one of the member's answers,
    ignoring case, spacing and curly-vs-straight punctuation. Anything else may be the model's words,
    or too little to show the chapter is theirs, so it's dropped."""
    answers = [_normalize(turn.answer) for turn in turns]
    kept = []
    for quote in quotes:
        needle = _normalize(quote)
        long_enough = len(needle.split()) >= MIN_QUOTE_WORDS
        if long_enough and any(needle in answer for answer in answers) and quote.strip() not in kept:
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


# Short or unsure answers are the main sign a question didn't land. A long answer that says
# "I don't know" on the way to a story isn't one.
_UNSURE = re.compile(
    r"\b(i don'?t know|idk|not sure|no idea|not really|nothing (really|much|special|interesting)"
    r"|can'?t think|nothing comes to mind|i don'?t have (anything|much|a story|one))\b",
    re.IGNORECASE,
)


def _thin(turn: Turn) -> bool:
    words = len(turn.answer.split())
    return words < SHORT_ANSWER_WORDS or (words < UNSURE_ANSWER_WORDS and bool(_UNSURE.search(turn.answer)))


def _running_thin(turns: list[Turn]) -> bool:
    # A skip says "not this ground", not "I'm unsure", so it isn't a thin answer.
    recent = [turn for turn in turns if not _skipped(turn)][-THIN_WINDOW:]
    return sum(map(_thin, recent)) >= THIN_SWITCH


def _skipped(turn: Turn) -> bool:
    return not turn.answer.strip()


def _questions_asked(turns: list[Turn]) -> int:
    return sum(1 for turn in turns if not _skipped(turn))


def _turn_blocks(
    turns: list[Turn], resume_text: str | None, sparks: list[dict] | None = None, more_material: bool = False
) -> list[dict]:
    """The transcript as one content block per turn, with a cache breakpoint on the newest turn.
    Each request then extends the previous one's prefix, so the interview so far is read from
    the cache instead of being paid for again on every question."""
    blocks = []
    if resume_text and resume_text.strip():
        blocks.append({"type": "text", "text": f"<resume>\n{resume_text.strip()}\n</resume>\n"})
    blocks.append({"type": "text", "text": "<interview>\n"})
    blocks += [{"type": "text", "text": _render(n, turn)} for n, turn in enumerate(turns, start=1)]
    blocks[-1]["cache_control"] = {"type": "ephemeral"}
    blocks.append(
        {"type": "text", "text": f"</interview>\n\n{_status(turns, more_material)}{_sparks_block(sparks)}"}
    )
    return blocks


def _status(turns: list[Turn], more_material: bool = False) -> str:
    if more_material:
        return "The material can't yet make three distinct chapters. Open an area not yet covered."
    asked = _questions_asked(turns)
    answered = sum(1 for turn in turns if turn.answer.strip())
    if not turns:
        return "The interview is starting. Ask the first question."
    notes = [f"Questions asked so far: {asked}. Answered: {answered}."]
    if _skipped(turns[-1]):
        notes.append(
            "The member skipped the last question. Move to other ground: don't rephrase it and don't "
            "mention the skip."
        )
    elif _running_thin(turns):
        notes.append(
            'Answers are running thin. Change the angle now (see "When answers run thin"), and treat this '
            "area as closed until Dig."
        )
    skipped = [turn.question for turn in turns if _skipped(turn)]
    if skipped:
        notes.append("Skipped so far, so stay off these subjects: " + " | ".join(skipped))
    shaped = sum(1 for turn in turns if turn.phase == "shape")
    if shaped >= MAX_SHAPE:
        notes.append("Shape has run its course: set ready_for_reveal to true and close.")
    swept = sum(1 for turn in turns if turn.phase == "sweep")
    if swept < MIN_SWEEP and all(turn.phase == "sweep" for turn in turns):
        notes.append(
            f"Sweep questions so far: {swept}. Stay in Sweep and open a different area of their life "
            "before you dig, however promising the last answer was."
        )
    if asked >= MAX_QUESTIONS or len(turns) >= MAX_TURNS:
        notes.append("That is the limit: set ready_for_reveal to true and close.")
    elif asked >= SHAPE_BY:
        notes.append("Move to Shape now if you aren't there already.")
    elif answered < MIN_ANSWERS:
        notes.append("It's too early for the reveal.")
    return " ".join(notes)


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
