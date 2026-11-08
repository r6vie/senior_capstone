"""Interview evals: a simulated member answers the real interview engine, end to end.

    uv run python -m evals.run interview          # one persona at a time, the standard runner
    uv run python -m evals.interview [names...]   # personas in parallel, one file each

Each case runs the whole interview until the Librarian is ready for the reveal, then drafts the
book, finishes it with the first title, rewrites its last chapter and rewrites the blurb as if the
first chapter were removed. The output is Markdown for a
human to read: the transcript with the private thread ranking, the book, quote checks, flags for
banned question types, and what the persona should have surfaced. Costs money: a few dollars a
persona.
"""

import re
from pathlib import Path

from trove.ai.client import Claude, text_of
from trove.interview import engine
from trove.interview.engine import Turn

from .personas import PERSONAS

CASES = PERSONAS
ANSWERER_PROMPT = (Path(__file__).resolve().parent / "answerer.md").read_text(encoding="utf-8").strip()
# The answerer only plays a part, so it thinks little. It never touches the engine's settings.
ANSWERER_EFFORT = "low"

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
    "reassurance": r"anything counts|that'?s (okay|ok|fine|totally fine|great|amazing)|no (wrong|bad) answers?"
    r"|don'?t worry|no pressure|it'?s (okay|ok|fine)|even (a )?small|great (answer|question)|love that",
}


# Summaries must be the chapter, not a description of it.
META = r"\b(reader|readers|this chapter|the chapter|conversation|30-minute|talk would|it comes from|covers)\b"
# The blurb is a back cover: framing about the book, and hype, are both banned.
BLURB_META = r"\b(this book|in this book|the book|chapters?|readers?|here i share|my story)\b"
HYPE = r"\b(passionate|passion|journey|unique|incredible|amazing|everything you need|game[- ]chang\w*|unlock\w*)\b"


class CountingClaude(Claude):
    """Passes calls through and adds up tokens, so each case reports what it cost."""

    def __init__(self, inner: Claude):
        self.model = inner.model
        self.inner = inner
        self.input_tokens = self.output_tokens = self.cached_tokens = self.calls = 0

    async def create(self, **params):
        response = await self.inner.create(**params)
        usage = response.usage
        self.calls += 1
        self.input_tokens += usage.input_tokens + (usage.cache_creation_input_tokens or 0)
        self.cached_tokens += usage.cache_read_input_tokens or 0
        self.output_tokens += usage.output_tokens
        return response


async def answer(
    claude: Claude, persona: dict, turns: list[Turn], question: str, playback: str | None
) -> str:
    asked = f"{playback}\n\n{question}" if playback else question
    asked += '\n\n(A quiet "Skip" button is always on screen.)'
    content = (
        f"<profile>\n{persona['profile'].strip()}\n</profile>\n\n"
        f"{engine._transcript(turns)}\n\n<newest_question>\n{asked}\n</newest_question>"
    )
    response = await claude.create(
        max_tokens=4000,
        system=ANSWERER_PROMPT,
        thinking={"type": "adaptive"},
        output_config={"effort": ANSWERER_EFFORT},
        messages=[{"role": "user", "content": content}],
    )
    return text_of(response)


async def run_case(claude: Claude, case: dict) -> str:
    counting = CountingClaude(claude)
    turns: list[Turn] = []
    log = []
    while True:
        plan = await engine.plan_turn(counting, turns=turns, resume_text=case["resume"])
        ranking = " / ".join(f"{t.thread} ({t.missing})" for t in plan.threads[:4])
        flags = [name for name, pattern in BANNED.items() if re.search(pattern, plan.question, re.I | re.S)]
        if plan.phase == "shape" and plan.playback:
            flags = [f for f in flags if f != "yes/no opener"]
        entry = [f"**Q{len(turns) + 1} [{plan.phase}]** {plan.question}"]
        if plan.playback:
            entry.append(f"> playback: {plan.playback}")
        entry.append(f"<sub>topic: {plan.topic} · threads: {ranking}</sub>")
        if flags:
            entry.append(f"⚠️ flags: {', '.join(flags)}")
        if plan.ready_for_reveal:
            log.append("\n\n".join([*entry, "*(ready for reveal)*"]))
            break
        if engine._running_thin(turns):
            entry.insert(1, "<sub>↻ answers running thin: sharper angle asked for</sub>")
        reply = (await answer(counting, case, turns, plan.question, plan.playback)).strip()
        skipped = reply == "SKIP"
        entry.append("**A:** *(skips)*" if skipped else f"**A:** {reply}")
        log.append("\n\n".join(entry))
        turns.append(Turn(question=plan.question, answer="" if skipped else reply, phase=plan.phase))

    draft = await engine.draft_book(counting, turns=turns)
    title = draft.titles[0].title
    finished = await engine.finish_book(counting, turns=turns, draft=draft, title=title)
    book = finished.chapters
    rewritten = await engine.rewrite_chapter(
        counting, turns=turns, chapters=finished.chapters, chapter_id=finished.chapters[-1].id
    )
    after_removal = await engine.write_blurb(counting, turns=turns, chapters=finished.chapters[1:])

    phases = [t.phase for t in turns]
    asked = engine._questions_asked(turns)
    all_flags = sum(entry.count("⚠️ flags") for entry in log)
    sections = [
        f"**{asked} questions** (sweep {phases.count('sweep')}, dig {phases.count('dig')}, "
        f"shape {phases.count('shape')}); hit the cap: {'⚠️ yes' if asked >= engine.MAX_QUESTIONS else 'no'}; "
        f"skips {sum(not t.answer.strip() for t in turns)}; questions flagged {all_flags}; "
        f"grounded pool {len(draft.pool)}, finished {len(book)} chapters. {counting.calls} calls, {counting.input_tokens:,} input "
        f"+ {counting.cached_tokens:,} cached, {counting.output_tokens:,} output tokens.",
        "**Should surface:**\n" + "\n".join(f"- {item}" for item in case["should_surface"]),
        "**Repeated after a skip:** " + (", ".join(_repeated_after_skip(turns)) or "none"),
        "### Transcript\n\n" + "\n\n---\n\n".join(log),
        "### Titles\n\n" + "\n".join(f"{n}. **{t.title}**: {t.why}" for n, t in enumerate(draft.titles, 1)),
        "### Pool\n\n" + "\n\n".join(_chapter(c) for c in draft.pool),
        f"### Finished book: {title}\n\n" + "\n\n".join(_chapter(c) for c in book),
        "### Blurbs\n\n"
        + "\n\n".join(
            f"**{label}** ({_blurb_check(text)}):\n> {text}"
            for label, text in [
                ("Draft", draft.blurb or ""),
                (f"Finished: {title}", finished.blurb or ""),
                ("After removing the first chapter", after_removal),
            ]
        ),
        f"### Rewrite of the last chapter\n\nBefore:\n{_chapter(book[-1])}\n\nAfter:\n{_chapter(rewritten)}",
    ]
    summaries = [c.summary for c in [*draft.pool, *book, rewritten]]
    meta = [m for summary in summaries for m in re.findall(META, summary, re.I)]
    sections.insert(1, f"**Meta phrasing in summaries:** {len(meta)} ({', '.join(meta) or 'none'})")
    return "\n\n".join(sections)


def _blurb_check(blurb: str) -> str:
    sentences = len(re.findall(r"[.!?](\s|$)", blurb.strip()))
    first_person = bool(re.search(r"\b(I|my|me)\b", blurb))
    flags = [
        f"{name}: {', '.join(found)}"
        for name, pattern in [("meta", BLURB_META), ("hype", HYPE)]
        if (found := re.findall(pattern, blurb, re.I))
    ]
    if not 2 <= sentences <= 4:
        flags.append(f"{sentences} sentences")
    if not first_person:
        flags.append("not first person")
    return f"{len(blurb)} chars" + (f", ⚠️ {'; '.join(flags)}" if flags else ", ok")


def _repeated_after_skip(turns: list[Turn]) -> list[str]:
    """Skipped questions the interviewer came back to: a later question sharing most of its words."""

    def words(text: str) -> set[str]:
        return {w for w in re.findall(r"[a-z']+", text.lower()) if len(w) > 3}

    repeats = []
    for n, turn in enumerate(turns):
        skipped = words(turn.question)
        if turn.answer.strip() or not skipped:
            continue
        if any(len(skipped & words(later.question)) / len(skipped) > 0.6 for later in turns[n + 1 :]):
            repeats.append(f"Q{n + 1}")
    return repeats


def _chapter(chapter: engine.DraftChapter) -> str:
    quotes = "\n".join(f"  > {q}" for q in chapter.quotes)
    return f"- **{chapter.title}**: {chapter.summary}\n{quotes}"
