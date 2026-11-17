"""Ask the interviewer for one next question at chosen points in a saved interview.

Far cheaper than a whole interview: one Opus call a checkpoint, and the same member's answers every
time, so a question-writing change can be compared directly.

    uv run python -m evals.probe --list          # every checkpoint; spends nothing
    uv run python -m evals.probe thin skip       # all checkpoints of these kinds
    uv run python -m evals.probe door dana:7     # kinds and single points mix

Kinds: `thin` right after answers run thin, `skip` right after a skip (both found in the transcript),
and `door`, a detail the interview left unopened, listed by hand in fixtures/probes.json. `dana:7`
means Dana's interview after 7 turns.
"""

import asyncio
import json
import sys
from datetime import datetime

from evals.lints import lint_question
from evals.run import OUT_DIR
from evals.saved import FIXTURES, fixtures, persona_of, turns_of
from evals.usage import CountingClaude, product_client
from trove.ai.client import get_claude
from trove.interview import engine


def checkpoints() -> list[dict]:
    points = []
    for slug, run in fixtures().items():
        turns = turns_of(run)
        for n in range(1, len(turns)):
            seen = turns[:n]
            if engine._skipped(seen[-1]):
                points.append(
                    {"slug": slug, "after": n, "kind": "skip", "note": "other ground; no rephrasing"}
                )
            elif engine._running_thin(seen) and not engine._running_thin(seen[:-1]):
                points.append(
                    {"slug": slug, "after": n, "kind": "thin", "note": "a sharper angle, in a real context"}
                )
    doors = FIXTURES / "probes.json"
    return points + (json.loads(doors.read_text(encoding="utf-8")) if doors.exists() else [])


def chosen(words: list[str]) -> list[dict]:
    points = checkpoints()
    picked = [p for p in points if p["kind"] in words]
    for word in words:
        if ":" in word:
            slug, after = word.split(":")
            picked.append({"slug": slug, "after": int(after), "kind": "point", "note": ""})
    return picked


async def probe(claude, point: dict) -> str:
    run = fixtures()[point["slug"]]
    turns = turns_of(run)
    seen = turns[: point["after"]]
    plan = await engine.plan_turn(claude, turns=seen, resume_text=persona_of(run).get("resume"))
    last = seen[-1]
    was = turns[point["after"]].question if point["after"] < len(turns) else "(the interview ended here)"
    flags = [f"{f.level}: {f.rule}" for f in lint_question(plan.question, plan.phase)]
    return "\n\n".join(
        [
            f"## {point['slug']} after {point['after']} turns [{point['kind']}]",
            f"Looking for: {point['note']}" if point["note"] else "",
            f"**Last question:** {last.question}\n\n**Answer:** {last.answer or '(skipped)'}",
            f"**Then, in the saved run [{turns[point['after']].phase if point['after'] < len(turns) else '-'}]:** {was}",
            f"**Now [{plan.phase}]:** {plan.question}",
            f"Flags: {'; '.join(flags) or 'none'}",
        ]
    )


async def main(words: list[str]) -> None:
    if not words or words == ["--list"]:
        for point in checkpoints():
            print(f"{point['slug']}:{point['after']:<3} {point['kind']:5} {point['note']}")
        return
    points = chosen(words)
    counting = CountingClaude(product_client(get_claude()))
    sections = await asyncio.gather(*(probe(counting, point) for point in points))
    folder = OUT_DIR / "probe"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{datetime.now():%Y-%m-%d_%H%M%S}.md"
    path.write_text("\n\n---\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Saved {path}. {counting.line()}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
