"""Adding to a book on the shelf: one round's questions, and the changes it proposes.

    uv run python -m evals.growing          # lists the cases; spends nothing
    uv run python -m evals.growing all      # or name cases. About 5 Opus calls in all.

Each case starts from a saved interview and its finished book, so nothing is interviewed again.
Results go to evals/out/growing/<timestamp>.md. Lint runs on them, and a person reads the rest.
"""

import asyncio
import re
import sys
from datetime import datetime

from evals.lints import lint_change, lint_question
from evals.run import OUT_DIR
from evals.saved import fixtures, turns_of
from evals.usage import CountingClaude, product_client
from trove.ai.client import get_claude
from trove.interview import engine
from trove.interview.engine import Turn

BOOK = "mateo"
# A chapter this member removed (R1-31): it must never come back in a question or a change.
REMOVED = {
    "title": "The hard week with the review",
    "summary": "A crack went to review the week a shop doubled its order.",
}
SPARK = {"id": "spark-1", "title": "The customer who taught me to raise my prices"}
NEW_FACT = (
    "Last winter a shop sent back forty skeins because the red had rubbed off on a customer's white sweater. "
    "I'd changed my alum supplier in the fall and never tested the new batch, because it was the same grade on the label."
)
THIN = "Not much has changed, really."
# R1-33: what a reader said about themselves must not reach the book. The name is invented.
READING = (
    "Sam Okafor from Vantage Mills asked how I'd handle leaving, since she's about to quit. "
    "What surprised me was being asked how I decide a batch has failed, because I've never written that rule down."
)
CASES = {
    "adding-opens": "A first question: finds a gap, stays off the removed chapter, treats the spark as a cue",
    "adding-follows": "After an answer with a cost in it, the next question stays there",
    "revise-new-fact": "A new fact improves a chapter: its sentences stay, words are added, the note has no praise",
    "revise-thin": "A thin answer earns nothing: an empty list is right",
    "revise-reading": "A reading answer: the other person's name and situation stay out",
}


def _book() -> tuple[list[Turn], list[engine.DraftChapter], str | None]:
    run = fixtures()[BOOK]
    chapters = [
        engine.DraftChapter(id=f"chapter-{n}", title=c["title"], summary=c["summary"], quotes=c["quotes"])
        for n, c in enumerate(run["book"]["chapters"], start=1)
    ]
    return turns_of(run), chapters, run["book"]["blurbs"].get("finished")


def _removed_words(text: str) -> list[str]:
    return [w for w in ("load rating", "doubled", "the review") if re.search(w, text, re.I)]


async def adding_case(claude, name: str) -> str:
    turns, chapters, _ = _book()
    start = len(turns)
    if name == "adding-follows":
        turns = [
            *turns,
            Turn(
                question="What went wrong with a batch since we last talked?", answer=NEW_FACT, phase="adding"
            ),
        ]
    plan = await engine.next_adding_turn(
        claude, turns=turns, round_start=start, chapters=chapters, sparks=[SPARK], off_limits=[REMOVED]
    )
    flags = [f"{f.level}: {f.rule}" for f in lint_question(plan.question)]
    flags += [f"error: back on removed chapter ({w})" for w in _removed_words(plan.question)]
    return f"**Question:** {plan.question}\n\nspark_id: {plan.spark_id}; done: {plan.done}\n\nFlags: {'; '.join(flags) or 'none'}"


async def revise_case(claude, name: str) -> str:
    turns, chapters, blurb = _book()
    start = len(turns)
    answer, phase = {
        "revise-new-fact": (NEW_FACT, "adding"),
        "revise-thin": (THIN, "adding"),
        "revise-reading": (READING, "reading"),
    }[name]
    question = "What did they ask you about that surprised you?" if phase == "reading" else "What's changed?"
    said = [*turns, Turn(question=question, answer=answer, phase=phase)]
    revision = await engine.revise_book(
        claude,
        turns=said,
        round_start=start,
        chapters=chapters,
        blurb=blurb,
        off_limits=[REMOVED],
        member_names=["Mateo"],
    )
    lines = [f"{len(revision.changes)} changes; dropped for names: {revision.dropped_for_names}"]
    by_id = {c.id: c for c in chapters}
    for change in revision.changes:
        current = by_id[change.chapter_id].summary if change.chapter_id else None
        flags = lint_change(change.model_dump(), current_summary=current, where=change.kind)
        text = f"{change.title} {change.summary} {change.note} {' '.join(change.quotes)}"
        leaked = [w for w in ("Sam", "Okafor", "Vantage", "quit", "leaving") if re.search(rf"\b{w}\b", text)]
        lines += [
            f"- **{change.kind}: {change.title}**: {change.summary}",
            f"  - before: {current}" if current else "",
            f"  - note: {change.note}",
            *(f"  - > {q}" for q in change.quotes),
            f"  - flags: {'; '.join(str(f) for f in flags) or 'none'}",
            f"  - ⚠️ names the other person: {leaked}" if name == "revise-reading" and leaked else "",
            f"  - ⚠️ back on removed chapter: {_removed_words(text)}" if _removed_words(text) else "",
        ]
    if revision.blurb:
        lines.append(f"\nProposed blurb: {revision.blurb}")
    return "\n".join(line for line in lines if line)


async def run_case(claude, name: str) -> str:
    runner = adding_case if name.startswith("adding") else revise_case
    try:
        body = await runner(claude, name)
    except Exception as error:  # one case failing shouldn't lose the others
        body = f"**Failed:** {type(error).__name__}: {error}"
    return f"## {name}\n\nLooking for: {CASES[name]}\n\n{body}"


async def main(names: list[str]) -> None:
    if not names:
        print("\n".join(f"{name}: {why}" for name, why in CASES.items()))
        return
    chosen = list(CASES) if names == ["all"] else names
    counting = CountingClaude(product_client(get_claude()))
    sections = await asyncio.gather(*(run_case(counting, name) for name in chosen))
    folder = OUT_DIR / "growing"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{datetime.now():%Y-%m-%d_%H%M%S}.md"
    path.write_text("\n\n---\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Saved {path}. {counting.line()}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
