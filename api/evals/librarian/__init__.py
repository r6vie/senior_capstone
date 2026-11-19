"""Librarian evals, and the loop for tuning its prompt: fixed answers typed look by look, then an Opus
judge on every line written. Only Haiku runs in the app; the judge runs here, in testing.

    uv run python -m evals.librarian            # lists the cases and the cost of a run; spends nothing
    uv run python -m evals.librarian all        # runs every case (costs money: see ESTIMATE)
    uv run python -m evals.librarian grief jargon

Must pass: every silent case stays silent; no line fails the professional-tone test; nothing judged
ungrounded (entries are also checked in code). Targets: sharp at 3/5 or better on average, some lines worth a
screenshot, at least one notebook entry on most non-silent answers, and the payoff cases (a credited edit,
bets called and lost, the back-cover line, the running bit) landing. Output: evals/out/librarian/<time>.md.
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from anthropic import transform_schema
from pydantic import BaseModel

from evals.run import OUT_DIR
from evals.usage import CountingClaude, product_client
from trove.ai.client import Claude, get_claude, text_of
from trove.interview import librarian, silence
from trove.interview.engine import Turn

from .cases import CASES

JUDGE_PROMPT = (Path(__file__).resolve().parent / "judge.md").read_text(encoding="utf-8").strip()
# The organization limits concurrent requests, so cases run a few at a time.
CONCURRENT_CASES = 3
# About 90 Haiku looks across the cases (a few retry), and one Opus judge call per case that wrote anything.
ESTIMATE = "about $0.90 a run: Haiku notes about $0.12, the Opus judge about $0.025 a case"


class LineVerdict(BaseModel):
    id: str
    professional: bool
    aimed_at_person: bool
    sharp: int
    screenshot: bool
    grounded: bool
    why: str


class Verdict(BaseModel):
    lines: list[LineVerdict]
    fits_answer: int
    missed: str


def _context(case: dict, answer: str, marks, entries, notebook, lost, conceded) -> librarian.Context:
    earlier = [Turn(question=q, answer=a, phase="dig") for q, a in case.get("earlier", [])]
    return librarian.Context(
        question=case["question"],
        question_number=len(earlier) + 1,
        setting=case.get("setting", "the interview"),
        earlier=earlier,
        silent_turns=[n for n, t in enumerate(earlier, start=1) if silence.is_silent(t.answer)],
        answer=answer,
        pasted=case.get("pasted", False),
        marks=marks,
        entries=entries,
        notebook=notebook,
        lost_marks=lost,
        conceded=conceded,
    )


def _looks(case: dict) -> list[str]:
    """The texts the Librarian sees, in order: each ends a sentence, as the service requires."""
    if "looks" in case:
        return case["looks"]
    parts = librarian.sentences(case["answer"])
    return [parts[0], case["answer"]] if len(parts) > 1 else [case["answer"]]


async def _typed(notes: Claude, case: dict) -> dict:
    """The answer typed look by look, as the service runs it: server silence first, marks whose words
    left the answer offered for credit, and bets from earlier answers open to settle."""
    marks, entries, credits, settled, conceded = [], [], [], [], False
    notebook = [librarian.Entry.model_validate(entry) for entry in case.get("notebook", [])]
    for text in _looks(case):
        if silence.is_silent(text):
            return {"silent": True, "how": "pattern"}
        held = librarian.marks_that_hold(marks, text)
        lost = [m for m in marks if m not in held]
        entries = librarian.entries_that_hold(entries, text)
        looked = await librarian.look(notes, _context(case, text, held, entries, notebook, lost, conceded))
        if looked.silent:
            return {"silent": True, "how": "model"}
        marks, entries = looked.marks, looked.entries
        credits += looked.revised_marks
        conceded = conceded or looked.conceded
        for bet, _ in looked.settled:
            settled.append(bet)
            notebook = [bet if e.id == bet.id else e for e in notebook]
    return {
        "silent": False,
        "how": "model",
        "marks": marks,
        "entries": entries,
        "credits": credits,
        "settled": settled,
    }


def _lines(marks, entries, settled) -> list[dict]:
    lines = []
    for m in marks:
        if not m.note and m.move != "back_cover":
            continue
        line = {"id": m.id, "kind": f"mark ({m.move}) on {m.anchor!r}", "text": m.note or "(back cover)"}
        if m.struck_note:
            line["credits_an_edit_of"] = m.struck_note
        if m.count:
            line["running_bit_count"] = m.count
        lines.append(line)
    # Lines the code writes word for word ("this goes on the back cover.") are the plan's, not the model's.
    fixed = {librarian.BACK_COVER_NOTE, librarian.CONCESSION_NOTE}
    lines += [
        {"id": e.id, "kind": f"notebook {e.kind}", "text": e.text} for e in entries if e.text not in fixed
    ]
    lines += [
        {"id": b.id, "kind": f"bet {b.status}", "text": f"{b.text} / {b.outcome_note}"} for b in settled
    ]
    return lines


async def _judge(judge: Claude, case: dict, lines: list[dict]) -> Verdict:
    looks = case.get("looks")
    shown = "\n".join(f"look {n}: {t}" for n, t in enumerate(looks, 1)) if looks else case["answer"]
    earlier = "\n".join(f"Q: {q}\nA: {a}" for q, a in case.get("earlier", []))
    content = (
        (f"<earlier_answers>\n{earlier}\n</earlier_answers>\n\n" if earlier else "")
        + f"<question>{case['question']}</question>\n\n<answer>\n{shown}\n</answer>\n\n"
        f"<lines>\n{json.dumps(lines, indent=1)}\n</lines>"
    )
    response = await judge.create(
        max_tokens=8000,
        system=JUDGE_PROMPT,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "medium",
            "format": {"type": "json_schema", "schema": transform_schema(Verdict)},
        },
        messages=[{"role": "user", "content": content}],
    )
    return Verdict.model_validate_json(text_of(response))


async def run_case(notes: Claude, judge: Claude, case: dict) -> dict:
    typed = await _typed(notes, case)
    marks, entries, settled = typed.get("marks", []), typed.get("entries", []), typed.get("settled", [])
    written = " ".join([*(m.note or "" for m in marks), *(e.text for e in entries)]).lower()
    moves = {m.move for m in marks} | {b.status for b in settled}
    if typed.get("credits"):
        moves.add("credit")
    result = {
        "case": case,
        "silent": typed["silent"],
        "how": typed["how"],
        "marks": [m.model_dump() for m in marks],
        "entries": [e.model_dump() for e in entries],
        "settled": [b.model_dump() for b in settled],
        "payoff": case["wants"] in moves if case.get("wants") else None,
        "forbidden": [w for w in case.get("must_not", []) if re.search(rf"\b{re.escape(w)}\b", written)],
    }
    lines = _lines(marks, entries, settled)
    if not typed["silent"] and lines:
        result["verdict"] = (await _judge(judge, case, lines)).model_dump()
    return result


def _report(everything: list[dict]) -> str:
    failed = [r for r in everything if "failed" in r]
    results = [r for r in everything if "failed" not in r]
    silent_cases = [r for r in results if r["case"]["expect"] == "silent"]
    talking = [r for r in results if r["case"]["expect"] != "silent"]
    verdicts = [line for r in results for line in r.get("verdict", {}).get("lines", [])]
    sharp = sum(v["sharp"] for v in verdicts) / len(verdicts) if verdicts else 0
    unprofessional = [v for v in verdicts if not v["professional"] or v["aimed_at_person"]]
    notes_cases = [r for r in talking if r["case"]["expect"] == "notes"]
    payoffs = [r for r in results if r["payoff"] is not None]
    lines = [
        "# Librarian evals",
        "",
        f"- Silent cases silent: {sum(r['silent'] for r in silent_cases)}/{len(silent_cases)} (must be all)",
        f"- Talking cases wrongly silent: {sum(r['silent'] for r in talking)}",
        f"- Lines failing the tone test: {len(unprofessional)} (must be 0)",
        f"- Lines judged ungrounded: {sum(not v['grounded'] for v in verdicts)} (must be 0)",
        f"- Forbidden words written: {sum(len(r['forbidden']) for r in results)} (must be 0)",
        f"- Sharp, average: {sharp:.2f}/5 over {len(verdicts)} lines (target 3+)",
        f"- Would screenshot: {sum(v['screenshot'] for v in verdicts)}/{len(verdicts)} lines",
        f"- Notes cases with a notebook entry: {sum(bool(r['entries']) for r in notes_cases)}/{len(notes_cases)}",
        f"- Payoffs that landed: {sum(r['payoff'] for r in payoffs)}/{len(payoffs)}",
        f"- Cases that failed to run: {len(failed)} {[r['case']['name'] for r in failed]}",
        "",
    ]
    for r in results:
        case = r["case"]
        lines += [f"## {case['name']} ({case['expect']})", "", f"> {case['answer']}", ""]
        if r["silent"]:
            lines += [f"Silent ({r['how']}).", ""]
            continue
        for mark in r["marks"]:
            extra = f" x{mark['count']}" if mark.get("count") else ""
            credit = f" (was: {mark['struck_note']})" if mark.get("struck_note") else ""
            lines.append(f"- mark {mark['move']}{extra} on *{mark['anchor']}*: {mark['note'] or ''}{credit}")
        for entry in r["entries"]:
            lines.append(f"- notebook {entry['kind']}: {entry['text']}")
        for bet in r["settled"]:
            lines.append(f"- bet {bet['status']}: {bet['text']} / {bet['outcome_note']}")
        if r["payoff"] is not None:
            lines.append(f"- wanted {case['wants']}: {'yes' if r['payoff'] else 'no'}")
        if r["forbidden"]:
            lines.append(f"- ⚠️ wrote {r['forbidden']}")
        for v in r.get("verdict", {}).get("lines", []):
            flag = "" if v["professional"] and not v["aimed_at_person"] and v["grounded"] else " ⚠️"
            shot = ", screenshot" if v["screenshot"] else ""
            lines.append(f"  - judge {v['id']}: sharp {v['sharp']}{shot}{flag}, {v['why']}")
        if "verdict" in r:
            lines.append(f"  - fits {r['verdict']['fits_answer']}/5; missed: {r['verdict']['missed']}")
        lines.append("")
    return "\n".join(lines)


async def main(names: list[str]) -> None:
    if not names:
        print("\n".join(f"{c['name']}: {c['expect']}" for c in CASES))
        print(f"\nA run of all {len(CASES)} cases costs {ESTIMATE}. Nothing was spent.")
        return
    chosen = CASES if names == ["all"] else [c for c in CASES if any(c["name"].startswith(n) for n in names)]
    claude = get_claude()
    notes = CountingClaude(librarian.on_notes_model(claude))
    judge = CountingClaude(product_client(claude))
    gate = asyncio.Semaphore(CONCURRENT_CASES)

    async def one(case: dict) -> dict:
        async with gate:
            try:
                return await run_case(notes, judge, case)
            except Exception as error:  # one case failing shouldn't lose the run
                print(f"failed: {case['name']}: {type(error).__name__}: {error}", flush=True)
                return {"case": case, "failed": f"{type(error).__name__}"}

    results = [r for r in await asyncio.gather(*(one(case) for case in chosen))]
    folder = OUT_DIR / "librarian"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{datetime.now():%Y-%m-%d_%H%M%S}.md"
    path.write_text(_report(list(results)) + "\n", encoding="utf-8")
    print(
        f"Saved {path}. Notes: {notes.line()}. Judge: {judge.line()}. Total: ${notes.dollars() + judge.dollars():.2f}"
    )


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
