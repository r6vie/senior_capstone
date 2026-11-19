"""The Librarian's live notes: marks on the answer being typed, and the notebook beside it
(docs/librarian-plan.md; mechanics from docs/LIBRARIAN_SPEC.md).

Stateless over what it's given, like the engine. The service keeps the marks and the notebook on the
interview. Every line the model writes is checked here, because a schema can't check lengths, substrings
or grounding: a failure gets one retry with the broken rules listed, and anything still broken is dropped.
Nothing here ever reaches the book except a clip, which is the member's own words.
"""

import copy
import hashlib
import json
import re
import unicodedata
from typing import Literal

from anthropic import transform_schema
from pydantic import BaseModel, Field

from trove.ai.client import Claude, text_of
from trove.ai.prompts import load_prompt
from trove.interview import silence
from trove.interview.engine import Turn

# A cheap, quick model reads over the member's shoulder; Opus still writes the questions and the book.
# Thinking stays on: off, the notes in Overdue got markedly less sharp and much rarer.
NOTES_MODEL = "claude-haiku-5-5"
NOTES_EFFORT = "low"
NOTES_MAX_TOKENS = 8000
NOTE_CHARS = 32
ENTRY_CHARS = 60
SIGN_OFF_CHARS = 24
ANCHOR_WORDS = 8
CLIP_WORDS = 8
# Caps, per answer and per interview.
MAX_MARKS_PER_ANSWER = 3
MAX_ENTRY_ADDS_PER_CALL = 2
MAX_ENTRIES_PER_ANSWER = 3
MAX_CLIPS_PER_ANSWER = 1
# The payoffs that make the notes matter because they come back (docs/librarian-plan.md, "What makes it
# fun"): one back-cover line and one running bit per interview, at most two open bets, one concession.
MAX_BACK_COVER = 1
MAX_RUNNING_BITS = 1
MAX_OPEN_BETS = 2
MAX_CONCESSIONS = 1
BACK_COVER_WORDS = (5, 40)
RUNNING_BIT_COUNT = (3, 6)
# Lines the code writes itself, word for word, so they need no checking.
BACK_COVER_NOTE = "this goes on the back cover."
CONCESSION_NOTE = "fine. your call."
CALLED_NOTE = "called it."
LOST_NOTE = "wrong. good."
CREDIT_NOTES = ("better.", "there it is.")
# A clip is the member's own words, so it's used sparingly: about one entry in five.
CLIP_SHARE = 5
# Cost controls.
MAX_CALLS_PER_ANSWER = 8
MAX_CALLS_PER_HOUR = 200
# The model sees this many earlier answers, newest last.
EARLIER_ANSWERS = 8
# When the notebook comes back for a round of adding, it keeps at most this many entries.
NOTEBOOK_KEEP = 24

Move = Literal["underline", "strike", "circle", "note", "back_cover"]
Kind = Literal["chapter", "connection", "saving", "clip", "note", "bet"]
Status = Literal["open", "circled", "ticked", "called", "lost"]


class Mark(BaseModel):
    """A mark on the member's exact words: `anchor` is a substring of the answer, `occurrence` which
    one (1 is the first). The client places it only while the anchor still matches."""

    id: str
    move: Move
    anchor: str
    occurrence: int
    # The handwritten note above the anchor. A strike's note is the better word.
    note: str | None
    # A running bit's count, 3-6, drawn as "xN". Null for every other move.
    count: int | None = None
    # When the member sharpened the words this mark teased: its old note, struck, under the credit.
    struck_note: str | None = None


class Entry(BaseModel):
    """One line in the notebook. `anchors` are the member's words it was built on; when those words
    leave the answer, the entry is rubbed out. `source_turns` are interview turn numbers, 1 first."""

    id: str
    kind: Kind
    text: str
    anchors: list[str]
    source_turns: list[int]
    # Circled when a question was built on it, ticked for a `saving` entry that was asked.
    status: Status = "open"
    # Earlier wordings, struck through, oldest first.
    struck: list[str] = []
    # A settled bet's line: "called it." or "wrong. good.".
    outcome_note: str | None = None


# What the model returns. Ids and every check are added in code.


class _NewMark(BaseModel):
    move: Move
    anchor: str = Field(
        description="1-8 whole words copied exactly from the answer; for back_cover, one whole sentence."
    )
    occurrence: int = Field(1, description="Which occurrence of the anchor, 1 being the first.")
    note: str | None = Field(None, description="At most 32 characters. Required for a strike.")


class _NewEntry(BaseModel):
    kind: Kind
    text: str = Field(description="At most 60 characters. A clip is the member's exact words, at most 8.")
    anchors: list[str] = Field(description="The member's words this is built on, copied exactly.")
    source_turns: list[int] = Field(description="The turn numbers it draws on, the current one included.")


class _Revision(BaseModel):
    id: str
    text: str


class _Credit(BaseModel):
    id: str = Field(description="The id of a mark whose words the member has since sharpened.")
    anchor: str = Field(description="The sharpened words, 1-8, copied exactly from the answer now.")
    occurrence: int = 1
    note: Literal["better.", "there it is."]


class _Settle(BaseModel):
    id: str = Field(description="The id of an open bet.")
    outcome: Literal["called", "lost"]
    anchor: str = Field(description="The words in this answer that settle it, copied exactly.")


class _Notes(BaseModel):
    silent: bool = Field(description="True if the answer is about a subject that silences you.")
    keep_marks: list[str] = Field(description="Ids of current marks that still fit.")
    marks: list[_NewMark]
    keep_entries: list[str] = Field(description="Ids of this answer's entries that still fit.")
    revise: list[_Revision] = Field(description="Entries to reword: same id, new text.")
    erase: list[str] = Field(description="Ids of this answer's entries that no longer fit.")
    entries: list[_NewEntry]
    credit: list[_Credit] = Field(default_factory=list, description="Marks to credit for an edit.")
    settle: list[_Settle] = Field(default_factory=list, description="Open bets this answer settles.")
    concede: bool = Field(False, description="True to write the one concession of the interview.")


class Notes(BaseModel):
    """The result of one look at the answer. `marks` and `entries` are the full set that should show
    for this answer once it's applied; the service works out what the client keeps, adds and erases."""

    silent: bool
    marks: list[Mark]
    added_marks: list[Mark]
    # Marks credited for an edit: same id, new anchor and note.
    revised_marks: list[Mark] = []
    entries: list[Entry]
    added_entries: list[Entry]
    revised_entries: list[Entry]
    erased_entries: list[str]
    # Bets from earlier answers that this one settled, with the words that settled them.
    settled: list[tuple[Entry, str]] = []
    conceded: bool = False


# Ids are stable hashes, so the same mark or entry keeps its id across repeated calls.


def _hash(*parts: object) -> str:
    return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode()).hexdigest()[:16]


def mark_id(move: str, anchor: str, occurrence: int) -> str:
    return f"m_{_hash(move, anchor.casefold(), occurrence)}"


def entry_id(kind: str, turn: int, text: str) -> str:
    return f"n_{_hash(kind, turn, _fold(text))}"


# Text helpers.

_PUNCT = str.maketrans(
    {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-", "\u2014": "-"}
)
_STOP_WORDS = (
    "a an the and or but of to in on at for with from by about as into than then that this these those it its"
    " is was were be been being am are i me my mine you your yours he she they them their his her we us our"
    " not no so very just really also too more most some any all what which who when where why how there"
    " here do did does done have has had can could would should will shall may might must one two like"
    " thing things stuff kind sort lot lots get got make made know think"
)
_STOP = frozenset(_STOP_WORDS.split())


def _fold(text: str) -> str:
    return re.sub(r"\s+", " ", text.translate(_PUNCT)).strip().casefold()


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9][a-z0-9'-]*", _fold(text))


def content_words(text: str) -> set[str]:
    return {w.strip("'-") for w in _words(text) if len(w) >= 4 and w not in _STOP}


def occurrences(text: str, anchor: str) -> int:
    """Whole-word occurrences of `anchor` in `text`, ignoring case and curly punctuation."""
    needle = _fold(anchor)
    if not needle:
        return 0
    # "van" is in "the van's battery": a possessive still counts, a contraction ("don" in "don't") doesn't.
    return len(re.findall(rf"(?<![\w']){re.escape(needle)}(?!\w)(?!'(?!s\b)\w)", _fold(text)))


def anchor_holds(text: str, anchor: str, occurrence: int) -> bool:
    return 1 <= len(_words(anchor)) <= ANCHOR_WORDS and 1 <= occurrence <= occurrences(text, anchor)


def word_count(text: str) -> int:
    return len(text.split())


def _sentences_ended(text: str) -> int:
    return len(re.findall(r"[.!?](?=\s|$)", text))


def nothing_to_read(previous: str, text: str) -> bool:
    """The no-model shortcut. The Librarian reacts only after a sentence ends, so a look is skipped
    unless a sentence has ended since the last one, and the text has grown by 2 words or changed."""
    if _fold(previous) == _fold(text):
        return True
    ended = _sentences_ended(text) > _sentences_ended(previous) or (
        text.rstrip().endswith((".", "!", "?")) and _fold(text) != _fold(previous)
    )
    return not ended


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


# The checks on every line the Librarian writes.

SLANG = (
    "slay|bestie|main character|it's giving|no cap|rizz|rent free|vibes?|mood|era|delulu|ate|chef's kiss"
    "|unhinged|low-?key|high-?key|hits different|core memory|npc|based|ratio|load-bearing|but make it|is carrying"
    "|has entered the chat|lol|haha|lmao|omg|fr|tbh|ngl|iconic|bussin|sus|yeet|periodt|bruh"
)
# Talk about the interview itself: every line must stand on its own.
META = (
    r"question|questions|interview|quiz|so far|keep going|tell me more|go on|guess|next up|later on"
    r"|noted for later|the librarian|chapter \d|this answer|your answer"
)
# Never commented on unless the member used the word themselves.
SENSITIVE = (
    "money|salary|debt|religion|religious|god|church|faith|pray|gay|queer|trans|sex|sexy|dating|boyfriend"
    "|girlfriend|husband|wife|married|divorce|pregnant|weight|fat|skinny|ugly|pretty|health|sick|disease"
    "|therapy|depressed|anxious|race|gender|politics|democrat|republican|grades|gpa|smart|stupid|dumb|accent"
)
# Language, nationality and heritage are never commented on, not even admiringly.
HERITAGE = (
    "heritage|immigrant|immigrants|native|mother tongue|first language|second language|bilingual|accent"
    "|ethnic|ethnicity|culture|cultural|homeland|motherland|diaspora|abroad|foreign|nationality|citizen"
    "|american|african|asian|european|latin|hispanic|arab|arabic|chinese|mandarin|cantonese|japanese|korean"
    "|vietnamese|filipino|tagalog|indian|hindi|urdu|punjabi|tamil|telugu|bengali|pakistani|bangladeshi"
    "|nepali|persian|farsi|iranian|turkish|greek|italian|french|german|spanish|portuguese|brazilian|mexican"
    "|russian|ukrainian|polish|jewish|hebrew|yiddish|muslim|hindu|sikh|buddhist|christian|catholic|nigerian"
    "|ghanaian|kenyan|ethiopian|somali|egyptian|lebanese|syrian|haitian|cuban|puerto rican|dominican"
    "|colombian|venezuelan|peruvian|irish|scottish|english|british|canadian|swahili|yoruba|igbo"
)
_EMOJI = re.compile("[\U0001f000-\U0001faff☀-➿⬀-⯿️]")
_BANNED_CHARS = re.compile(r"[!\"#\u201c\u201d]")
_WE = re.compile(r"\b(we|us|our|ours|we're|we've|let's)\b", re.IGNORECASE)
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})
_CONTACT = [
    re.compile(r"(?:\+?\d[\s().-]*){7,}"),  # phone numbers
    re.compile(
        r"[\w.+-]+\s*(?:@|\(at\)|\[at\]|\s+at\s+)\s*[\w-]+\s*(?:\.|\(dot\)|\[dot\]|\s+dot\s+)\s*[a-z]{2,}",
        re.I,
    ),
    re.compile(r"https?://|www\.", re.I),
    re.compile(r"\b[\w-]+\.(?:com|org|net|edu|io|co|me|app|dev|ai|gg|ly|us|uk)\b", re.I),
    re.compile(r"(?<![\w.])@\w{2,}"),
]
# Lines kept from the prompt's examples: the model must not copy them.
PROMPT_EXAMPLES = {
    "a press release with a pulse.",
    "the spreadsheet has a fan.",
    "two sentences of warm-up.",
    "a verb would help.",
    "who signed off?",
    "a budget line, not a story.",
    "the deadline did that.",
    "betting this ends in a spreadsheet.",
    "the van has tenure.",
    "ch. ? the build that broke everyone",
    "a junior would pay for this.",
}


def _words_of(pattern: str) -> re.Pattern:
    return re.compile(rf"(?<![\w'])(?:{pattern})(?![\w'])", re.IGNORECASE)


# Generic lines aren't blocked in code: the prompt keeps them rare, and a rare one is fine.
_SLANG, _META = _words_of(SLANG), _words_of(META)
_SENSITIVE, _HERITAGE = _words_of(SENSITIVE), _words_of(HERITAGE)


def _deleet(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    # "j o h n" is a word spelled out to slip past a filter.
    plain = re.sub(r"\b(?:\w ){3,}\w\b", lambda m: m.group(0).replace(" ", ""), plain)
    return plain.translate(_LEET)


def line_problems(line: str, *, limit: int, member_text: str, clip: bool = False) -> list[str]:
    """Why a line the Librarian wrote breaks the rules. `member_text` is everything the member has
    said, for the terms only they may bring up. A clip is the member's own words, so only its length,
    the content filter and sensitive terms apply."""
    problems = []
    text = line.strip()
    if not text:
        return ["it's empty"]
    if len(text) > limit:
        problems.append(f"it's {len(text)} characters, and the limit is {limit}")
    for pattern in _CONTACT:
        if pattern.search(text) or pattern.search(_deleet(text)):
            problems.append("it has contact details, a link or a handle")
            break
    said = _fold(member_text)
    for found in {m.group(0).lower() for m in _SENSITIVE.finditer(text)}:
        if not re.search(rf"(?<![\w']){re.escape(found)}(?![\w'])", said):
            problems.append(f"it brings up {found!r}, which the member didn't")
    if clip:
        return problems
    if _BANNED_CHARS.search(text) or _EMOJI.search(text):
        problems.append("it has an exclamation mark, a quotation mark, a hashtag or an emoji")
    if _WE.search(text):
        problems.append('it says "we", "us" or "our"')
    if found := _SLANG.search(_deleet(text)):
        problems.append(f"it uses slang ({found.group(0)!r})")
    if found := _META.search(text):
        problems.append(f"it talks about the interview itself ({found.group(0)!r})")
    if found := _HERITAGE.search(text):
        problems.append(f"it comments on language or heritage ({found.group(0)!r})")
    capitals = [
        w for w in re.findall(r"\b[A-Z][\w'-]*", text) if w not in ("I", "I'm", "I'd", "I've", "I'll")
    ]
    if any(not re.search(rf"\b{re.escape(w)}\b", member_text) for w in capitals):
        problems.append("it isn't lowercase")
    if _fold(text) in PROMPT_EXAMPLES:
        problems.append("it copies an example from the instructions")
    return problems


# Grounding: each notebook kind names the member's words in its own way.


def _answer_of(turns: dict[int, str], turn: int) -> str:
    return turns.get(turn, "")


def entry_problems(entry: _NewEntry, *, turns: dict[int, str], current: int, member_text: str) -> list[str]:
    """`turns` holds the readable answers by turn number (silent and skipped ones left out),
    including the current one."""
    clip = entry.kind == "clip"
    problems = line_problems(entry.text, limit=ENTRY_CHARS, member_text=member_text, clip=clip)
    sources = sorted(set(entry.source_turns))
    if current not in sources:
        problems.append("it has to be about the answer being written now")
    if any(turn not in turns for turn in sources):
        problems.append("it draws on a turn that isn't there to read")
    if not entry.anchors:
        problems.append("it needs the member's words it was built on")
    for anchor in entry.anchors:
        if (
            not any(occurrences(_answer_of(turns, t), anchor) for t in sources)
            or word_count(anchor) > ANCHOR_WORDS
        ):
            problems.append(f"the anchor {anchor!r} isn't 1-8 of the member's words, copied exactly")
    said_words = content_words(" ".join(_answer_of(turns, t) for t in sources))
    if entry.kind == "clip":
        if word_count(entry.text) > CLIP_WORDS or not any(
            occurrences(_answer_of(turns, t), entry.text) for t in sources
        ):
            problems.append(f"a clip must be at most {CLIP_WORDS} of the member's words, copied exactly")
    elif entry.kind in ("chapter", "saving") and not content_words(entry.text) & said_words:
        problems.append("it has to name the member's own words")
    elif entry.kind == "connection":
        if len(sources) < 2:
            problems.append("a connection links this answer to an earlier one")
        elif not all(content_words(entry.text) & content_words(_answer_of(turns, t)) for t in sources):
            problems.append("a connection has to name words from both answers")
    return problems


def back_cover_holds(answer: str, anchor: str) -> bool:
    """A back-cover line is one whole sentence of the answer, word for word."""
    low, high = BACK_COVER_WORDS
    return low <= word_count(anchor) <= high and any(_fold(s) == _fold(anchor) for s in sentences(answer))


def running_count(answers: list[str], anchor: str) -> int:
    """How many answers, this one included, mention the running bit."""
    return sum(1 for text in answers if occurrences(text, anchor))


def mark_problems(mark: _NewMark, *, answer: str, earlier: list[str], member_text: str) -> list[str]:
    problems = []
    if mark.move == "back_cover":
        if not back_cover_holds(answer, mark.anchor):
            problems.append("a back_cover anchor must be one whole sentence of the answer, copied exactly")
    elif not anchor_holds(answer, mark.anchor, mark.occurrence):
        problems.append(f"the anchor {mark.anchor!r} isn't 1-8 whole words of the answer at that occurrence")
    if mark.move in ("strike", "note") and not (mark.note or "").strip():
        problems.append(f"a {mark.move} needs its note")
    if mark.note:
        problems += line_problems(mark.note, limit=NOTE_CHARS, member_text=member_text)
        if mark.move != "circle":
            # Only a callback circle may reach back to an earlier answer.
            stray = content_words(mark.note) - content_words(answer)
            if stray & content_words(" ".join(earlier)):
                problems.append("its note brings back words from an earlier answer")
    if found := _HERITAGE.search(mark.anchor):
        problems.append(f"it marks a language or heritage word ({found.group(0)!r})")
    if mark.move == "circle" and running_count([*earlier, answer], mark.anchor) < RUNNING_BIT_COUNT[0]:
        problems.append("a running bit is for a concrete thing that came up in at least two earlier answers")
    return problems


# The call.


class Context(BaseModel):
    """What the service hands over for one look at the answer."""

    question: str
    question_number: int
    # "the interview" or "a round of adding to their book".
    setting: str
    earlier: list[Turn]
    # Turn numbers of earlier answers that were silent: they're masked, never sent.
    silent_turns: list[int]
    answer: str
    pasted: bool
    marks: list[Mark]
    # This answer's open entries, which the model may keep, revise or erase.
    entries: list[Entry]
    # Earlier open entries, for connections and to avoid repeats. Read only, except open bets.
    notebook: list[Entry]
    # Marks whose words have left the answer since the last look: crediting an edit, or a concession.
    lost_marks: list[Mark] = []
    back_cover_used: bool = False
    running_bit_used: bool = False
    conceded: bool = False


def _earlier_block(context: Context) -> str:
    first = max(1, len(context.earlier) - EARLIER_ANSWERS + 1)
    lines = []
    for number, turn in enumerate(context.earlier, start=1):
        if number < first:
            continue
        answer = silence.MASKED if number in context.silent_turns else (turn.answer.strip() or "(skipped)")
        lines.append(f"Q{number}: {turn.question}\nA{number}: {answer}\n")
    return "\n".join(lines)


def _prefix(context: Context) -> str:
    """The part that stays the same for every look at one answer, so it's read from the cache."""
    return (
        f"<situation>\nThis is {context.setting}, answer number {context.question_number}.\n</situation>\n\n"
        f"<earlier_answers>\n{_earlier_block(context) or '(none yet)'}</earlier_answers>\n\n"
        f"<question>Q{context.question_number}: {context.question}</question>\n"
    )


def _now(context: Context) -> str:
    marks = [m.model_dump() for m in context.marks]
    entries = [e.model_dump(include={"id", "kind", "text", "anchors"}) for e in context.entries]
    notebook = [
        e.model_dump(include={"id", "kind", "text", "source_turns", "status"}) for e in context.notebook
    ]
    room = MAX_MARKS_PER_ANSWER - len(context.marks)
    bets = [e for e in context.notebook if e.kind == "bet" and e.status == "open"]
    lost = [m.model_dump(include={"id", "move", "anchor", "note"}) for m in context.lost_marks]
    used = {
        "back cover line": context.back_cover_used,
        "running bit": context.running_bit_used,
        "concession": context.conceded,
    }
    counts = (
        f"Marks on this answer: {len(context.marks)} of {MAX_MARKS_PER_ANSWER}. "
        f"Open bets: {len(bets)} of {MAX_OPEN_BETS}. "
        + " ".join(f"The {name} is {'used' if spent else 'still free'}." for name, spent in used.items())
        + f" New notebook entries this look: at most {MAX_ENTRY_ADDS_PER_CALL}."
    )
    pasted = "\nThe member pasted some of this text." if context.pasted else ""
    return (
        f"<notebook_so_far>\n{json.dumps(notebook, indent=1)}\n</notebook_so_far>\n\n"
        f"<this_answer_entries>\n{json.dumps(entries, indent=1)}\n</this_answer_entries>\n\n"
        f"<current_marks>\n{json.dumps(marks, indent=1)}\n</current_marks>\n\n"
        f"<marks_whose_words_left>\n{json.dumps(lost, indent=1)}\n</marks_whose_words_left>\n\n"
        f"<counts>{counts}{' No room for new marks.' if room <= 0 else ''}{pasted}</counts>\n\n"
        f"<answer>\n{context.answer}\n</answer>\n\n"
        "Look at the answer as it stands. Usually write nothing new."
    )


def _member_text(context: Context) -> str:
    said = [
        t.answer
        for n, t in enumerate(context.earlier, start=1)
        if n not in context.silent_turns and t.answer.strip()
    ]
    return " ".join([*said, context.answer])


def _readable_turns(context: Context) -> dict[int, str]:
    turns = {
        n: t.answer
        for n, t in enumerate(context.earlier, start=1)
        if n not in context.silent_turns and t.answer.strip()
    }
    turns[context.question_number] = context.answer
    return turns


def on_notes_model(claude: Claude) -> Claude:
    """The same client, with whatever guards it, on the notes model. The scripted stand-in is kept."""
    if not hasattr(claude, "request"):
        return claude
    notes = copy.copy(claude)
    notes.model = NOTES_MODEL
    return notes


async def _ask(claude: Claude, messages: list[dict]) -> tuple[_Notes, str]:
    response = await claude.create(
        max_tokens=NOTES_MAX_TOKENS,
        # Cached across every answer of every interview.
        system=[
            {"type": "text", "text": load_prompt("interview/notes"), "cache_control": {"type": "ephemeral"}}
        ],
        thinking={"type": "adaptive"},
        output_config={
            "effort": NOTES_EFFORT,
            "format": {"type": "json_schema", "schema": transform_schema(_Notes)},
        },
        messages=messages,
    )
    raw = text_of(response)
    return _Notes.model_validate_json(raw), raw


def _problems(raw: _Notes, context: Context) -> list[str]:
    """Every broken rule, for the one retry."""
    member = _member_text(context)
    earlier = [t.answer for n, t in enumerate(context.earlier, start=1) if n not in context.silent_turns]
    turns = _readable_turns(context)
    listed = []
    for n, mark in enumerate(raw.marks, start=1):
        listed += [
            f"mark {n}: {p}"
            for p in mark_problems(mark, answer=context.answer, earlier=earlier, member_text=member)
        ]
    for n, entry in enumerate(raw.entries, start=1):
        problems = entry_problems(entry, turns=turns, current=context.question_number, member_text=member)
        listed += [f"entry {n}: {p}" for p in problems]
    lost = {m.id: m for m in context.lost_marks}
    for credit in raw.credit:
        if credit.id not in lost:
            listed.append(f"credit {credit.id}: only a mark whose words left the answer can be credited")
        elif not anchor_holds(context.answer, credit.anchor, credit.occurrence):
            listed.append(f"credit {credit.id}: {credit.anchor!r} isn't 1-8 whole words of the answer")
    bets = {e.id for e in context.notebook if e.kind == "bet" and e.status == "open"}
    for settle in raw.settle:
        if settle.id not in bets:
            listed.append(f"settle {settle.id}: only an open bet can be settled")
        elif not occurrences(context.answer, settle.anchor) or word_count(settle.anchor) > ANCHOR_WORDS:
            listed.append(f"settle {settle.id}: {settle.anchor!r} isn't 1-8 words copied from this answer")
    own = {e.id: e for e in context.entries}
    for revision in raw.revise:
        if revision.id not in own:
            listed.append(f"revise {revision.id}: only this answer's entries can be revised")
            continue
        entry = own[revision.id]
        proposed = _NewEntry(
            kind=entry.kind, text=revision.text, anchors=entry.anchors, source_turns=entry.source_turns
        )
        listed += [
            f"revise {revision.id}: {p}"
            for p in entry_problems(
                proposed, turns=turns, current=context.question_number, member_text=member
            )
        ]
    return listed


async def look(claude: Claude, context: Context) -> Notes:
    """One look at the answer as it stands: what to keep, add, revise and erase. Raises like the
    engine (ClaudeRefused, SDK errors, ValueError); the service degrades to keeping everything."""
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": _prefix(context), "cache_control": {"type": "ephemeral"}},
                {"type": "text", "text": _now(context)},
            ],
        }
    ]
    raw, text = await _ask(claude, messages)
    if not raw.silent and (problems := _problems(raw, context)):
        retry = [
            *messages,
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": load_prompt("interview/notes_retry") + "\n\n- " + "\n- ".join(problems),
            },
        ]
        raw, _ = await _ask(claude, retry)
    return _apply(raw, context)


def _apply(raw: _Notes, context: Context) -> Notes:
    """Keep only what passes every check and fits every cap."""
    if raw.silent:
        return Notes(
            silent=True,
            marks=[],
            added_marks=[],
            entries=[],
            added_entries=[],
            revised_entries=[],
            erased_entries=[e.id for e in context.entries],
        )
    member = _member_text(context)
    earlier = [t.answer for n, t in enumerate(context.earlier, start=1) if n not in context.silent_turns]
    turns = _readable_turns(context)
    keep = set(raw.keep_marks)
    marks = [m for m in context.marks if m.id in keep and mark_holds(m, context.answer)]
    back_cover = context.back_cover_used or any(m.move == "back_cover" for m in marks)
    running = context.running_bit_used or any(m.move == "circle" for m in marks)
    every_answer = [*earlier, context.answer]
    # A member who sharpened marked words gets credit: the mark comes back on the new words.
    revised_marks = []
    lost = {m.id: m for m in context.lost_marks}
    for credit in raw.credit:
        old = lost.pop(credit.id, None)
        if old is None or not anchor_holds(context.answer, credit.anchor, credit.occurrence):
            continue
        if len(marks) >= MAX_MARKS_PER_ANSWER:
            break
        credited = old.model_copy(
            update={
                "anchor": credit.anchor,
                "occurrence": credit.occurrence,
                "note": credit.note,
                "struck_note": old.note,
            }
        )
        marks.append(credited)
        revised_marks.append(credited)
    added_marks = []
    for new in raw.marks:
        if len(marks) >= MAX_MARKS_PER_ANSWER:
            break
        if mark_problems(new, answer=context.answer, earlier=earlier, member_text=member):
            continue
        if (new.move == "back_cover" and back_cover) or (new.move == "circle" and running):
            continue
        note = (new.note or "").strip() or None
        count = None
        if new.move == "circle":
            count = min(running_count(every_answer, new.anchor), RUNNING_BIT_COUNT[1])
            # The client draws the count; a note that repeats it would show it twice.
            note = re.sub(r"^[\u00d7x]\s*\d+\.?\s*", "", note or "").strip() or None
        mark = Mark(
            id=mark_id(new.move, new.anchor, new.occurrence),
            move=new.move,
            anchor=new.anchor.strip(),
            occurrence=1 if new.move == "back_cover" else new.occurrence,
            note=None if new.move == "back_cover" else note,
            count=count,
        )
        if any(m.id == mark.id for m in marks):
            continue
        back_cover = back_cover or mark.move == "back_cover"
        running = running or mark.move == "circle"
        marks.append(mark)
        added_marks.append(mark)

    own = {e.id: e for e in context.entries}
    # An entry goes only when the model erases it: a reply that forgets to list one mustn't wipe the
    # notebook. Entries whose words left the answer were already rubbed out before this call.
    erased = [e for e in raw.erase if e in own]
    entries = [e for e in context.entries if e.id not in erased]
    revised = []
    for revision in raw.revise:
        entry = next((e for e in entries if e.id == revision.id), None)
        if entry is None or _fold(revision.text) == _fold(entry.text):
            continue
        proposed = _NewEntry(
            kind=entry.kind, text=revision.text, anchors=entry.anchors, source_turns=entry.source_turns
        )
        if entry_problems(proposed, turns=turns, current=context.question_number, member_text=member):
            continue
        updated = entry.model_copy(
            update={"text": revision.text.strip(), "struck": [*entry.struck, entry.text]}
        )
        entries = [updated if e.id == entry.id else e for e in entries]
        revised.append(updated)
    added_entries = []
    for mark in added_marks:
        if mark.move == "back_cover":
            # The back-cover line comes with its notebook line, built on the same sentence.
            line = Entry(
                id=entry_id("note", context.question_number, BACK_COVER_NOTE),
                kind="note",
                text=BACK_COVER_NOTE,
                anchors=[mark.anchor],
                source_turns=[context.question_number],
            )
            entries.append(line)
            added_entries.append(line)
    conceded = False
    if raw.concede and not context.conceded and lost:
        # Marked words were deleted rather than sharpened. Once an interview, it says so.
        anchors = [m.anchor for m in lost.values()]
        line = Entry(
            id=entry_id("note", context.question_number, CONCESSION_NOTE),
            kind="note",
            text=CONCESSION_NOTE,
            anchors=anchors,
            source_turns=[context.question_number],
        )
        entries.append(line)
        added_entries.append(line)
        conceded = True
    open_bets = {e.id: e for e in context.notebook if e.kind == "bet" and e.status == "open"}
    settled = []
    for settle in raw.settle:
        bet = open_bets.pop(settle.id, None)
        if bet is None or not occurrences(context.answer, settle.anchor):
            continue
        note = CALLED_NOTE if settle.outcome == "called" else LOST_NOTE
        settled.append(
            (bet.model_copy(update={"status": settle.outcome, "outcome_note": note}), settle.anchor)
        )
    bets_open = len(open_bets) + sum(e.kind == "bet" for e in entries)
    clips_here = sum(e.kind == "clip" for e in entries)
    clips_all = clips_here + sum(e.kind == "clip" for e in context.notebook)
    total = len(entries) + len(context.notebook)
    written = len(added_entries)
    for new in raw.entries:
        if len(added_entries) - written >= MAX_ENTRY_ADDS_PER_CALL or len(entries) >= MAX_ENTRIES_PER_ANSWER:
            break
        if entry_problems(new, turns=turns, current=context.question_number, member_text=member):
            continue
        # The first clip is always allowed; after that, about one entry in five at most.
        too_many = clips_all > 0 and (clips_all + 1) * CLIP_SHARE > total + 1
        if new.kind == "clip" and (clips_here >= MAX_CLIPS_PER_ANSWER or too_many):
            continue
        if new.kind == "bet" and bets_open >= MAX_OPEN_BETS:
            continue
        entry = Entry(
            id=entry_id(new.kind, context.question_number, new.text),
            kind=new.kind,
            text=new.text.strip(),
            anchors=[a.strip() for a in new.anchors],
            source_turns=sorted(set(new.source_turns)),
        )
        if any(e.id == entry.id or _fold(e.text) == _fold(entry.text) for e in [*entries, *context.notebook]):
            continue
        clips_here += entry.kind == "clip"
        clips_all += entry.kind == "clip"
        bets_open += entry.kind == "bet"
        total += 1
        entries.append(entry)
        added_entries.append(entry)
    return Notes(
        silent=False,
        marks=marks,
        added_marks=added_marks,
        revised_marks=revised_marks,
        entries=entries,
        added_entries=added_entries,
        revised_entries=revised,
        erased_entries=erased,
        settled=settled,
        conceded=conceded,
    )


# Keeping marks and entries true to the text as it changes, with no model call.


def mark_holds(mark: Mark, text: str) -> bool:
    if mark.move == "back_cover":
        return back_cover_holds(text, mark.anchor)
    return anchor_holds(text, mark.anchor, mark.occurrence)


def marks_that_hold(marks: list[Mark], text: str) -> list[Mark]:
    return [m for m in marks if mark_holds(m, text)]


def entries_that_hold(entries: list[Entry], text: str) -> list[Entry]:
    """An entry built on the answer being written is rubbed out once its words leave the answer.
    A clip has to stay verbatim, so it goes as soon as its words change."""

    def holds(entry: Entry) -> bool:
        if entry.kind == "clip":
            return bool(occurrences(text, entry.text))
        return any(occurrences(text, anchor) for anchor in entry.anchors)

    return [e for e in entries if holds(e)]


def trim_for_adding(notebook: list[dict]) -> list[dict]:
    """The notebook as it comes back when the author reopens the interview (I3): ticked `saving`
    entries go, then `note`s and settled bets; the rest, newest first, up to the cap, back in order."""
    kept = [e for e in notebook if not (e["kind"] == "saving" and e.get("status") == "ticked")]
    kept = [e for e in kept if e["kind"] != "note"]
    # An open bet stays to be called; a settled one has had its moment.
    kept = [e for e in kept if not (e["kind"] == "bet" and e.get("status", "open") != "open")]
    newest = list(reversed(kept))[:NOTEBOOK_KEEP]
    return list(reversed(newest))


def sign_off_problems(line: str, member_text: str) -> list[str]:
    return line_problems(line, limit=SIGN_OFF_CHARS, member_text=member_text)


class _SignOff(BaseModel):
    sign_off: str


async def write_sign_off(
    claude: Claude, *, title: str, blurb: str | None, chapter_titles: list[str], member_text: str
) -> str | None:
    """The Librarian's line under the title of the finished book, on the notes model. Checked like a
    note, with one retry; a line that still fails is left out. Never part of the book."""
    content = (
        f"<title>{title}</title>\n\n<back_cover>{blurb or ''}</back_cover>\n\n"
        "<chapters>\n" + "\n".join(f"- {t}" for t in chapter_titles) + "\n</chapters>"
    )
    messages: list[dict] = [{"role": "user", "content": content}]
    for _ in range(2):
        response = await on_notes_model(claude).create(
            max_tokens=NOTES_MAX_TOKENS,
            system=load_prompt("interview/sign_off"),
            thinking={"type": "adaptive"},
            output_config={
                "effort": NOTES_EFFORT,
                "format": {"type": "json_schema", "schema": transform_schema(_SignOff)},
            },
            messages=messages,
        )
        text = text_of(response)
        line = _SignOff.model_validate_json(text).sign_off.strip()
        problems = sign_off_problems(line, member_text)
        if not problems:
            return line
        retry = load_prompt("interview/sign_off_retry") + "\n\n- " + "\n- ".join(problems)
        messages = [*messages, {"role": "assistant", "content": text}, {"role": "user", "content": retry}]
    return None


def clips_of(notebook: list[dict]) -> list[str]:
    """The member's own words the Librarian clipped, offered to the book as preferred quotes."""
    return [e["text"] for e in notebook if e["kind"] == "clip"]
