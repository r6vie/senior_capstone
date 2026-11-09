"""Free checks on any saved run: no model, no money.

    uv run python -m evals.lint evals/fixtures/dana.json evals/out/book/<run>/*.json

An error breaks a written rule. A warning is a flag for the reader, not a verdict. These can't say
whether a book is good; evals/rubric.md is for that.
"""

import re
from dataclasses import dataclass

from trove.interview import engine
from trove.interview.engine import Turn

# Question shapes the spec bans (docs/trove.md §4). A hit is a flag for the reader, not a verdict.
BANNED = {
    "tell me about yourself": r"tell me (a bit |a little )?about yourself|walk me through your (background|résumé|resume)",
    "importance of": r"importance of|why (is|does) .{0,40} matter",
    "how do you balance": r"\bbalanc(e|ing)\b",
    "yes/no opener": r"^(do|did|are|were|is|was|have|has|can|could|would|will) you\b",
    "two questions": r"\?.+\?",
    # §4, §9.9: thin answers get sharper questions, never small talk or reassurance.
    "small talk": r"last (saturday|sunday|weekend|week)\b|for fun\b|hobb(y|ies)|how('s| is| was) your (day|week)"
    r"|what did you do (today|yesterday|this week)",
    "reassurance": r"anything counts|that'?s (okay|ok|fine|totally fine)|no (wrong|bad) answers?"
    r"|don'?t worry|no pressure|it'?s (okay|ok|fine)|even (a )?small",
    "praise": r"that'?s (really |so |very )?(great|amazing|impressive|fascinating|interesting|cool|wonderful)"
    r"|great (answer|question|story)|love that|what a\b|impressive|fascinating|\bwow\b",
}
# Summaries must be the chapter, not a description of it.
META = r"\b(reader|readers|this chapter|the chapter|conversation|30-minute|talk would|it comes from|covers)\b"
# The blurb is a back cover: framing about the book, and hype, are both banned.
BLURB_META = r"\b(this book|in this book|the book|chapters?|readers?|here i share|my story)\b"
HYPE = (
    r"\b(passionate|passion|journey|unique|incredible|amazing|everything you need|game[- ]chang\w*|unlock\w*"
    r"|insights?|lessons? learned|invaluable|transformative|empower\w*|navigat(e|ing) the|secrets? of"
    r"|the art of|beyond the|deep dive|world[- ]class)\b"
)
# The closing line editors called the worst sentence in three books of five: it shrinks the audience, and
# promises what the page has already said.
OFFER = r"\bI can (tell|show) you\b|\bI('ll| will) tell you\b|\bif you'?re (trying|stuck|sitting|facing|working)\b"
# Openers that repeat easily. Two of one kind in an interview is already a pattern the member hears.
TEMPLATES = {
    "almost did instead": r"almost (do|did)|\binstead\b.*\?$",
    "think of the last time": r"think (of|about|back to) (the|a) (last|time|first)",
    "what would you tell": r"what (would|do) you (tell|say to)",
    "walk me through": r"walk me through",
    "figured out": r"what did you figure out",
    "what do people get wrong": r"get wrong",
    "come to you for": r"come to you",
}
_STOP = set(
    [
        "the",
        "a",
        "an",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "at",
        "for",
        "with",
        "from",
        "by",
        "how",
        "why",
        "what",
        "when",
        "who",
        "my",
        "your",
        "i",
        "you",
        "it",
        "is",
        "was",
        "be",
        "not",
        "no",
        "that",
        "this",
        "these",
        "those",
        "first",
        "last",
        "one",
        "two",
        "three",
        "before",
        "after",
        "into",
        "out",
        "up",
        "down",
        "over",
        "nobody",
        "everyone",
        "never",
        "always",
        "only",
        "still",
    ]
)
# Words every question uses, so sharing one says nothing about the subject.
_COMMON_ASKS = set(
    [
        "think",
        "time",
        "people",
        "make",
        "did",
        "do",
        "does",
        "doing",
        "thing",
        "something",
        "someone",
        "get",
        "got",
        "tell",
        "say",
        "said",
        "ask",
        "asked",
        "come",
        "part",
        "kind",
        "most",
        "more",
        "much",
        "way",
        "work",
        "working",
        "use",
        "used",
        "need",
        "want",
        "know",
        "knew",
        "find",
        "found",
        "people's",
        "went",
        "going",
        "take",
        "took",
        "give",
        "gave",
        "keep",
        "kept",
        "run",
        "ran",
        "figure",
        "happen",
        "happened",
        "change",
        "changed",
        "start",
        "started",
        "right",
        "actually",
        "really",
        "you've",
        "you'd",
        "they",
        "them",
        "their",
        "there",
        "then",
    ]
)
NO_INSTANCE = r"\b(don'?t (remember|recall)|can'?t (think of|remember|recall)|don'?t have (a|one|an)\b|nothing (dramatic|specific)|don'?t want to make up)\b"
INSTANCE_ASK = r"\b(one (time|specific|particular)|specific|exactly which|which (one|time|day|week)|think of (a|the)|the (last|first) time)\b"
_PLAYED_DOWN = r"\b(big deal|don'?t think|wouldn'?t (say|call)|not really|overstat\w*|was just|teacher'?s|someone else|by myself)\b"
_RESUME_STOP = {
    "Case", "Western", "Reserve", "University", "CWRU", "B", "S", "M", "A", "BA", "BS", "MS", "MBA", "PhD",
}  # fmt: skip
_NUMBER_WORDS = dict(
    zip(
        [
            "three",
            "four",
            "five",
            "six",
            "seven",
            "eight",
            "nine",
            "ten",
            "eleven",
            "twelve",
            "thirteen",
            "fourteen",
            "fifteen",
            "sixteen",
            "seventeen",
            "eighteen",
            "nineteen",
            "twenty",
            "thirty",
            "forty",
            "fifty",
            "sixty",
            "seventy",
            "eighty",
            "ninety",
            "hundred",
        ],
        [*range(3, 21), 30, 40, 50, 60, 70, 80, 90, 100],
        strict=True,
    )
)
_MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


# The simulated member sometimes writes its reasoning, and a book written from that isn't a test of anything.
# "Profile" fails even in a line a member might say: a false alarm costs one retry, a miss costs a run.
OUT_OF_CHARACTER = (
    r"\bprofile\b|\bthe persona\b|\bsimulat\w+"
    r"|\b(she|he|they)'?d? (would|might) (answer|reply|say)\b|\b(her|his|their) (answer|reply) would\b"
    r"|^this (one )?is (a |an )?\w+(, \w+)*( and \w+)?( question)?(, so| and)"
)


@dataclass(frozen=True)
class Finding:
    level: str  # "error" or "warn"
    rule: str
    where: str
    detail: str

    def __str__(self) -> str:
        return f"{self.level:5} {self.rule:22} {self.where:18} {self.detail}"


def lint_question(question: str, phase: str = "dig", where: str = "question") -> list[Finding]:
    findings = [
        Finding("warn" if name == "yes/no opener" else "error", name, where, question[:90])
        for name, pattern in BANNED.items()
        if re.search(pattern, question, re.I | re.S) and not (phase == "shape" and name == "yes/no opener")
    ]
    if question.count("?") > 1 and not any(f.rule == "two questions" for f in findings):
        findings.append(Finding("error", "two questions", where, question[:90]))
    if len(question.split()) > 25:
        findings.append(Finding("warn", "long question", where, f"{len(question.split())} words"))
    return findings


def lint_answers(turns: list[Turn]) -> list[Finding]:
    return [
        Finding("error", "member out of character", f"A{n}", turn.answer[:90])
        for n, turn in enumerate(turns, start=1)
        if re.search(OUT_OF_CHARACTER, turn.answer, re.I)
    ]


def lint_questions(turns: list[Turn]) -> list[Finding]:
    findings = []
    for n, turn in enumerate(turns, start=1):
        findings += lint_question(turn.question, turn.phase, f"Q{n}")
    return findings + _repeated_shapes(turns) + _interview_flags(turns)


def _repeated_shapes(turns: list[Turn]) -> list[Finding]:
    findings = []
    asks = {n: _ask_sentence(t.question) for n, t in enumerate(turns, start=1) if t.phase != "shape"}
    for name, pattern in TEMPLATES.items():
        hits = [f"Q{n}" for n, ask in asks.items() if re.search(pattern, ask)]
        if len(hits) >= 2:
            findings.append(Finding("warn", "repeated shape", ",".join(hits), name))
    openers: dict[str, list[str]] = {}
    for n, ask in asks.items():
        openers.setdefault(" ".join(ask.split()[:4]), []).append(f"Q{n}")
    for opener, hits in openers.items():
        if len(hits) >= 3:
            findings.append(Finding("warn", "repeated opener", ",".join(hits), opener))
    return findings


def _interview_flags(turns: list[Turn]) -> list[Finding]:
    findings = []
    asked = [t for t in turns if t.phase != "shape"]
    if asked:
        double = sum(bool(re.search(r", and (what|how|who|why|did|was)\b", t.question, re.I)) for t in asked)
        if double / len(asked) > 0.10:
            findings.append(
                Finding("warn", "two asks in one", "interview", f"{double} of {len(asked)} questions")
            )
        first = sum(bool(re.search(r"\bfirst\b", t.question, re.I)) for t in asked)
        if first / len(asked) > 0.20:
            findings.append(
                Finding("warn", "first everywhere", "interview", f"{first} of {len(asked)} questions")
            )
    if turns and re.search(r"studying or working on", turns[0].question, re.I):
        findings.append(Finding("error", "form-letter opening", "Q1", turns[0].question[:90]))
    findings += _sweep_area_flags(turns)
    for n, turn in enumerate(turns):
        later = turns[n + 1 :]
        if not turn.answer.strip():
            # Judged by subject, not wording: a skip means "not this", however the next one is phrased.
            subject = _subject_words(turn.question)
            hits = [
                f"Q{n + 2 + m}" for m, t in enumerate(later) if len(subject & _subject_words(t.question)) >= 2
            ]
            if hits:
                detail = f"came back at {','.join(hits)}: {turn.question[:60]}"
                findings.append(Finding("warn", "back to skipped subject", f"Q{n + 1}", detail))
        elif (
            later
            and re.search(NO_INSTANCE, turn.answer, re.I)
            and re.search(INSTANCE_ASK, later[0].question, re.I)
        ):
            findings.append(Finding("warn", "pressed after no example", f"Q{n + 2}", later[0].question[:90]))
    return findings


def _subject_words(question: str) -> set[str]:
    return _content_words(_ask_sentence(question)) - _COMMON_ASKS


def _sweep_area_flags(turns: list[Turn]) -> list[Finding]:
    counts: dict[str, list[str]] = {}
    for n, turn in enumerate(turns, start=1):
        if turn.phase == "sweep":
            for word in _subject_words(turn.question):
                counts.setdefault(word, []).append(f"Q{n}")
    return [
        Finding("warn", "sweep stuck in one area", ",".join(hits), word)
        for word, hits in counts.items()
        if len(hits) > 2
    ]


def _ask_sentence(question: str) -> str:
    # A short bridge often comes first; the shape a member hears is the sentence that asks.
    sentences = re.split(r"(?<=[.!?])\s+", question.strip().lower())
    return next((s for s in reversed(sentences) if s.endswith("?")), sentences[-1])


def lint_book(book: dict, turns: list[Turn], *, resume: str | None = None, author: str = "") -> list[Finding]:
    findings = _lint_titles(book.get("titles", [])) + _lint_disowned(book, turns)
    chapters = book.get("chapters", [])
    if chapters and not engine.MIN_CHAPTERS <= len(chapters) <= engine.MAX_CHAPTERS:
        findings.append(Finding("error", "chapter count", "book", str(len(chapters))))
    written = {f"chapter {n}": c for n, c in enumerate(chapters, start=1)}
    written |= {f"pool {n}": c for n, c in enumerate(book.get("pool", []), start=1)}
    if book.get("rewrite"):
        written["rewrite"] = book["rewrite"]
    for where, chapter in written.items():
        findings += _lint_chapter(chapter, turns, where)
    findings += _lint_chapter_titles(chapters)
    for name, blurb in (book.get("blurbs") or {}).items():
        findings += _lint_blurb(blurb, f"blurb {name}")
    # What a reader sees, and what a member can put on the shelf.
    shelf = {w: f"{c['title']}. {c['summary']}" for w, c in written.items()} | {
        f"blurb {n}": b for n, b in (book.get("blurbs") or {}).items()
    }
    shelf |= {f"title {n}": t["title"] for n, t in enumerate(book.get("titles", []), start=1)}
    answers = "\n".join(t.answer for t in turns)
    for where, text in shelf.items():
        findings += _lint_grounding(text, answers, where, resume=resume, author=author)
    # Titles are in title case, so the name check only reads running text.
    prose = {w: c["summary"] for w, c in written.items()} | (book.get("blurbs") or {})
    for where, text in prose.items():
        findings += [Finding("warn", "possible name", where, name) for name in _names(text)]
    return findings


def _lint_disowned(book: dict, turns: list[Turn]) -> list[Finding]:
    """A title or opening chapter built on what the member played down when asked "Is this you?"."""
    shape = [t for t in turns if t.phase == "shape" and t.answer.strip()]
    if not shape:
        return []
    clauses = re.split(r"(?<=[.!?,;])\s+", shape[-1].answer)
    disowned = set().union(*(_content_words(c) for c in clauses if re.search(_PLAYED_DOWN, c, re.I)), set())
    disowned -= _COMMON_ASKS | _content_words(
        "big deal think say call really just teacher someone else myself"
    )
    targets = {f"title {n}": t["title"] for n, t in enumerate(book.get("titles", []), start=1)}
    if book.get("chapters"):
        targets["chapter 1"] = book["chapters"][0]["title"]
    return [
        Finding("warn", "disowned at Shape", where, f"{text}: {', '.join(sorted(shared))}")
        for where, text in targets.items()
        if (shared := _content_words(text) & disowned)
    ]


def _lint_titles(titles: list[dict]) -> list[Finding]:
    findings = []
    if titles and len(titles) != 3:
        findings.append(Finding("error", "three titles", "titles", str(len(titles))))
    for n, title in enumerate(titles, start=1):
        words = len(title["title"].split())
        if not 2 <= words <= 7:
            findings.append(Finding("error", "title length", f"title {n}", title["title"]))
        if len(title["why"]) > 140:
            findings.append(Finding("error", "why length", f"title {n}", f"{len(title['why'])} chars"))
        if re.search(HYPE, title["title"], re.I):
            findings.append(Finding("error", "hype", f"title {n}", title["title"]))
    for a in range(len(titles)):
        for b in range(a + 1, len(titles)):
            shared = _content_words(titles[a]["title"]) & _content_words(titles[b]["title"])
            if shared:
                level = "error" if len(shared) >= 2 else "warn"
                detail = f"{titles[a]['title']} / {titles[b]['title']}: {', '.join(sorted(shared))}"
                findings.append(Finding(level, "titles overlap", f"titles {a + 1},{b + 1}", detail))
    return findings


def _content_words(text: str) -> set[str]:
    words = re.findall(r"[a-z']+", text.lower())
    return {re.sub(r"(ing|ed|es|s)$", "", w) for w in words if w not in _STOP and len(w) > 2}


def _lint_chapter(chapter: dict, turns: list[Turn], where: str) -> list[Finding]:
    findings = []
    title, summary, quotes = chapter["title"], chapter["summary"], chapter["quotes"]
    if not 2 <= len(title.split()) <= 8:
        findings.append(Finding("error", "title length", where, title))
    if ":" in title:
        findings.append(Finding("warn", "colon in title", where, title))
    if len(summary) > 300:
        findings.append(Finding("error", "summary length", where, f"{len(summary)} chars"))
    if _sentences(summary) > 2:
        findings.append(Finding("warn", "summary sentences", where, str(_sentences(summary))))
    if len(re.findall(r"\b(then|next|after that|finally|second)\b", summary, re.I)) >= 2:
        findings.append(Finding("warn", "steps in summary", where, summary[:80]))
    if found := re.findall(META, summary, re.I):
        findings.append(Finding("error", "meta phrasing", where, ", ".join(found)))
    if found := re.findall(r"\byou(r)?\b", summary, re.I):
        findings.append(Finding("warn", "second person", where, summary[:80]))
    if not re.search(r"\b(I|my|me|mine|we|our)\b", summary):
        findings.append(Finding("warn", "not first person", where, summary[:80]))
    # A quote earns its place by adding a line the summary can't say, not by repeating it.
    said = set(re.findall(r"[a-z']+", summary.lower()))
    for quote in quotes:
        words = set(re.findall(r"[a-z']+", quote.lower()))
        if words and len(words & said) / len(words) >= 0.7:
            findings.append(Finding("warn", "quote repeats summary", where, quote[:70]))
    if not 1 <= len(quotes) <= 3:
        findings.append(Finding("error", "quote count", where, str(len(quotes))))
    grounded = engine.grounded_quotes(quotes, turns)
    for quote in quotes:
        # The engine also drops quotes too short to show anything; that's the length rule below.
        if quote not in grounded and len(quote.split()) >= engine.MIN_QUOTE_WORDS:
            findings.append(Finding("error", "quote not verbatim", where, quote[:90]))
        words = len(quote.split())
        if not 5 <= words <= 60:
            findings.append(Finding("warn", "quote length", where, f"{words} words: {quote[:50]}"))
    return findings


def _lint_chapter_titles(chapters: list[dict]) -> list[Finding]:
    openers: dict[str, int] = {}
    for chapter in chapters:
        opener = " ".join(chapter["title"].lower().split()[:2])
        openers[opener] = openers.get(opener, 0) + 1
    findings = [
        Finding("warn", "chapter titles alike", "chapters", f"{count} open with {opener!r}")
        for opener, count in openers.items()
        if count >= 2
    ]
    for a in range(len(chapters)):
        for b in range(a + 1, len(chapters)):
            shared = _content_words(chapters[a]["title"]) & _content_words(chapters[b]["title"])
            if len(shared) >= 2:
                detail = f"{chapters[a]['title']} / {chapters[b]['title']}"
                findings.append(Finding("warn", "chapter titles alike", "chapters", detail))
    return findings


def _lint_blurb(blurb: str, where: str) -> list[Finding]:
    findings = []
    if len(blurb) > engine.MAX_BLURB:
        findings.append(Finding("error", "blurb length", where, f"{len(blurb)} chars"))
    if not 2 <= _sentences(blurb) <= 4:
        findings.append(Finding("error", "blurb sentences", where, str(_sentences(blurb))))
    if not re.search(r"\b(I|my|me)\b", blurb):
        findings.append(Finding("error", "not first person", where, blurb[:80]))
    if found := re.findall(BLURB_META, blurb, re.I):
        findings.append(Finding("error", "meta phrasing", where, ", ".join(found)))
    if re.search(OFFER, blurb, re.I):
        findings.append(Finding("error", "stock offer", where, blurb[-90:]))
    return findings


def _lint_grounding(text: str, answers: str, where: str, *, resume: str | None, author: str) -> list[Finding]:
    findings = []
    if found := re.findall(HYPE, text, re.I):
        findings.append(Finding("error", "hype", where, ", ".join(sorted({str(f) for f in found}))))
    if author and re.search(rf"\b{re.escape(author)}\b", text):
        findings.append(Finding("error", "author's name", where, author))
    for number in sorted(_numbers(text) - _numbers(answers)):
        findings.append(Finding("warn", "number not in answers", where, str(number)))
    for term in _resume_terms(resume):
        if re.search(rf"\b{re.escape(term)}\b", text):
            said = re.search(rf"\b{re.escape(term)}\b", answers, re.I)
            level, rule = ("warn", "résumé term, said too") if said else ("error", "résumé term in book")
            findings.append(Finding(level, rule, where, term))
    return findings


def _sentences(text: str) -> int:
    return len(re.findall("[.!?](?=[\\s\"\u201d\u2019')]|$)", text.strip()))


def _numbers(text: str) -> set[int]:
    found = {int(n.replace(",", "")) for n in re.findall(r"\b\d[\d,]*\b", text)}
    return found | {_NUMBER_WORDS[w] for w in re.findall(r"[a-z]+", text.lower()) if w in _NUMBER_WORDS}


def _resume_terms(resume: str | None) -> list[str]:
    if not resume:
        return []
    words = re.findall(r"\b[A-Z][A-Za-z]+\b|\b(?:19|20)\d\d\b", resume)
    return sorted({w for w in words if w not in _RESUME_STOP})


def _names(text: str) -> set[str]:
    """Two capitalized words in a row, away from the start of a sentence: a person or a company."""
    found = set()
    for match in re.finditer(r"(?<=[a-z,;] )([A-Z][a-z]+(?: [A-Z][a-z]+)+)", text):
        if not any(word in _MONTHS for word in match.group(1).split()):
            found.add(match.group(1))
    found |= set(re.findall(r"\b(?:Dr|Mr|Ms|Mrs|Prof|Professor)\.? [A-Z][a-z]+", text))
    found |= set(re.findall(r"\b[A-Z][a-z]+ (?:Inc|LLC|Corp|Ltd|Labs|Group)\b", text))
    return found


# A change note says what was added and nothing about how good it is.
NOTE_PRAISE = (
    r"\b(great|powerful|rich|richer|stronger|deeper|sharper|better|vivid|compelling|strong|nice|beautiful"
    r"|insightful|impressive|wonderful|amazing|important|valuable|meaningful|fascinating|now shines)\b"
)


def lint_change(change: dict, *, current_summary: str | None = None, where: str = "change") -> list[Finding]:
    """One proposed change to a shelved book, in the shape `revise_book` returns."""
    findings = _lint_grounding(change["summary"], change["summary"], where, resume=None, author="")
    if len(change["summary"]) > 300:
        findings.append(Finding("error", "summary length", where, f"{len(change['summary'])} chars"))
    if found := re.findall(NOTE_PRAISE, change.get("note") or "", re.I):
        findings.append(Finding("error", "praise in note", where, ", ".join(found)))
    if current_summary:
        # The screen underlines added words, so an improvement has to keep what was there (R4-03).
        kept = [s for s in re.split(r"(?<=[.!?])\s+", current_summary) if s and s in change["summary"]]
        total = len(re.split(r"(?<=[.!?])\s+", current_summary))
        if len(kept) < total:
            findings.append(
                Finding("warn", "improve reworded", where, f"kept {len(kept)} of {total} sentences")
            )
    return findings


def lint_across(runs: list[dict]) -> list[Finding]:
    """Sameness that only shows when reading several books: the shelf is read as a set (R6-06)."""
    findings = []
    phrases: dict[str, set[str]] = {}
    for run in runs:
        for turn in run["turns"]:
            words = re.findall(r"[a-z']+", _ask_sentence(turn["question"]))
            for n in range(len(words) - 3):
                phrases.setdefault(" ".join(words[n : n + 4]), set()).add(run["slug"])
    # Half the runs asking the same four words is a template, not a coincidence.
    shared = [
        p
        for p, slugs in phrases.items()
        if len(runs) >= 2 and len(slugs) * 2 >= len(runs) and not _generic(p)
    ]
    findings += [Finding("warn", "same words across books", "questions", p) for p in sorted(shared)]
    titles = [(run["slug"], t["title"]) for run in runs for t in run["book"].get("titles", [])]
    endings: dict[str, list[str]] = {}
    for slug, title in titles:
        endings.setdefault(title.split()[-1].lower(), []).append(f"{slug}: {title}")
        rest = title.split()[1:]
        if len(rest) >= 2 and sum(w[0].isupper() for w in rest) >= 2:
            findings.append(Finding("warn", "title case", slug, title))
    findings += [
        Finding("warn", "titles end alike", word, "; ".join(hits))
        for word, hits in endings.items()
        if len(hits) >= 2 and word not in _STOP - {"first", "last"}
    ]
    return findings


def _generic(phrase: str) -> bool:
    # Only the plainest wording of a question is shared by chance, so those don't count.
    return len(set(phrase.split()) - _STOP - _COMMON_ASKS) < 2


def lint_playbacks(run: dict) -> list[Finding]:
    return [
        Finding("error", "long playback", f"Q{n}", f"{len(t['playback'].split())} words")
        for n, t in enumerate(run["turns"], start=1)
        if t.get("playback") and len(t["playback"].split()) > engine.MAX_PLAYBACK_WORDS
    ]


def lint_run(run: dict, *, resume: str | None = None) -> list[Finding]:
    turns = [Turn(question=t["question"], answer=t["answer"], phase=t["phase"]) for t in run["turns"]]
    author = run.get("persona", "").split(" ")[0]
    book = lint_book(run["book"], turns, resume=resume, author=author)
    return lint_playbacks(run) + lint_answers(turns) + lint_questions(turns) + book
