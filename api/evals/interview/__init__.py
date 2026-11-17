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

from anthropic import transform_schema
from pydantic import BaseModel

from trove.ai.client import Claude, text_of
from trove.interview import engine
from trove.interview.engine import Turn

from ..lints import BANNED, BLURB_META, HYPE, META, OUT_OF_CHARACTER, lint_questions
from ..usage import CountingClaude, member_client, product_client
from .personas import PERSONAS

CASES = PERSONAS
ANSWERER_PROMPT = (Path(__file__).resolve().parent / "answerer.md").read_text(encoding="utf-8").strip()
# The answerer only plays a part, so it thinks little, on a cheap model (evals/usage.py).
ANSWERER_EFFORT = "low"


class MemberReply(BaseModel):
    answer: str
    skipped: bool


async def answer(
    claude: Claude, persona: dict, turns: list[Turn], question: str, playback: str | None
) -> MemberReply:
    asked = f"{playback}\n\n{question}" if playback else question
    asked += '\n\n(A quiet "Skip" button is always on screen.)'
    content = (
        f"<profile>\n{persona['profile'].strip()}\n</profile>\n\n"
        f"{engine._transcript(turns)}\n\n<newest_question>\n{asked}\n</newest_question>"
    )
    for _ in range(2):
        response = await claude.create(
            max_tokens=4000,
            system=ANSWERER_PROMPT,
            thinking={"type": "adaptive"},
            output_config={
                "effort": ANSWERER_EFFORT,
                "format": {"type": "json_schema", "schema": transform_schema(MemberReply)},
            },
            messages=[{"role": "user", "content": content}],
        )
        reply = MemberReply.model_validate_json(text_of(response))
        if not re.search(OUT_OF_CHARACTER, reply.answer, re.I):
            return reply
    # A player's reasoning saved as the member's words would become quotable material for the book.
    raise ValueError(f"The simulated member broke character: {reply.answer[:120]!r}")


async def run_case(claude: Claude, case: dict) -> str:
    counting = CountingClaude(product_client(claude))
    member = CountingClaude(member_client(claude))
    turns: list[Turn] = []
    first_moment = None
    log = []
    while True:
        plan = await engine.plan_turn(counting, turns=turns, resume_text=case["resume"])
        if first_moment is None and any(t.has_moment for t in plan.threads):
            first_moment = len(turns)
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
        reply = await answer(member, case, turns, plan.question, plan.playback)
        skipped = reply.skipped or not reply.answer.strip()
        reply = reply.answer.strip()
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
        f"grounded pool {len(draft.pool)}, finished {len(book)} chapters.\n\n"
        f"Cost: {counting.line()}; member {member.line()}.",
        f"**First concrete moment:** {first_moment and f'A{first_moment}'}"
        + (" ⚠️ later than Q6" if not first_moment or first_moment > 6 else ""),
        "**Should surface:**\n" + "\n".join(f"- {item}" for item in case["should_surface"]),
        "**Lint:**\n" + "\n".join(f"- {f}" for f in lint_questions(turns) if f.rule != "repeated opener"),
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


def _chapter(chapter: engine.DraftChapter) -> str:
    quotes = "\n".join(f"  > {q}" for q in chapter.quotes)
    return f"- **{chapter.title}**: {chapter.summary}\n{quotes}"
