"""Saved interviews: read a run's Markdown, keep real transcripts as fixtures, and hand them out.

Book-writing work replays these instead of interviewing again, which is where most of the money goes.

    uv run python -m evals.saved fixture evals/out/interview/<run>/dana.md   # writes evals/fixtures/dana.json
    uv run python -m evals.saved packet evals/fixtures/dana.json             # what an editor reads
    uv run python -m evals.saved audit evals/fixtures/dana.json              # what a claim auditor reads

A run here is a plain dict, and evals.book writes the same shape:
    {persona, slug, source, turns: [{question, answer, phase, playback}],
     book: {titles, pool, title, chapters, blurbs: {draft, finished, after_removal}, rewrite}}
"""

import json
import re
import sys
from pathlib import Path

from trove.interview.engine import Turn

from .interview.personas import PERSONAS

FIXTURES = Path(__file__).resolve().parent / "fixtures"
# Never named in a prompt or tuned on: a replay of these is the honest check on anything that improves.
HOLDOUTS = {"ana", "lena"}

_QUESTION = re.compile(r"^\*\*Q\d+ \[(sweep|dig|shape)[^\]]*\]\*\* (.*)", re.S)


def parse_run(markdown: str, *, source: str = "") -> dict:
    """A saved eval run as a dict. Tolerates every format the interview eval has written."""
    persona = markdown.splitlines()[0].removeprefix("## ").strip()
    sections = dict(_sections(markdown))
    turns = [turn for block in sections["Transcript"].split("\n\n---\n\n") if (turn := _turn(block))]
    finished = next(name for name in sections if name.startswith("Finished book"))
    book = {
        "titles": _titles(sections["Titles"]),
        "pool": _chapters(sections["Pool"]),
        "title": finished.removeprefix("Finished book: ").strip(),
        "chapters": _chapters(sections[finished]),
        "blurbs": _blurbs(sections.get("Blurbs", "")),
        "rewrite": _rewrite(sections.get("Rewrite of the last chapter", "")),
    }
    return {
        "persona": persona,
        "slug": persona.split()[0].lower(),
        "source": source,
        "turns": turns,
        "book": book,
    }


def _sections(markdown: str) -> list[tuple[str, str]]:
    parts = re.split(r"^### (.+)$", markdown, flags=re.M)
    return [(parts[n].strip(), parts[n + 1].strip()) for n in range(1, len(parts), 2)]


def _turn(block: str) -> dict | None:
    question = phase = None
    playback = None
    answer: list[str] = []
    for paragraph in block.strip().split("\n\n"):
        if match := _QUESTION.match(paragraph):
            phase, question = match.group(1), match.group(2).strip()
        elif paragraph.startswith("> playback:"):
            playback = paragraph.removeprefix("> playback:").strip()
        elif paragraph.startswith("**A:**"):
            answer.append(paragraph.removeprefix("**A:**").strip())
        elif answer:
            answer.append(paragraph)  # a long answer runs over several paragraphs
    # The last entry of a run is the closing line, which nobody answered.
    if question is None or not answer:
        return None
    text = "\n\n".join(answer)
    return {
        "question": question,
        "answer": "" if text == "*(skips)*" else text,
        "phase": phase,
        "playback": playback,
    }


def _titles(section: str) -> list[dict]:
    found = re.findall(r"^\d+\. \*\*(.+?)\*\*: (.*)$", section, flags=re.M)
    return [{"title": title, "why": why.strip()} for title, why in found]


def _chapters(section: str) -> list[dict]:
    chapters = []
    for match in re.finditer(r"^- \*\*(.+?)\*\*: (.*(?:\n  > .*)*)", section, flags=re.M):
        summary, *quotes = match.group(2).split("\n  > ")
        chapters.append({"title": match.group(1), "summary": summary.strip(), "quotes": quotes})
    return chapters


def _blurbs(section: str) -> dict:
    labels = {"Draft": "draft", "Finished": "finished", "After": "after_removal"}
    blurbs = {}
    for match in re.finditer(r"^\*\*(\w+).*?\*\* \(.*?\):\n> (.*)$", section, flags=re.M):
        if match.group(1) in labels:
            blurbs[labels[match.group(1)]] = match.group(2).strip()
    return blurbs


def _rewrite(section: str) -> dict | None:
    chapters = _chapters(section.split("After:")[-1])
    return chapters[-1] if chapters else None


def write_fixture(run_path: Path) -> Path:
    run = parse_run(run_path.read_text(encoding="utf-8"), source=f"{run_path.parent.name}/{run_path.name}")
    if not any(p["name"] == run["persona"] for p in PERSONAS):
        raise SystemExit(f"{run['persona']} isn't in personas.py.")
    path = FIXTURES / f"{run['slug']}.json"
    path.write_text(json.dumps(run, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def fixtures() -> dict[str, dict]:
    runs = (json.loads(path.read_text(encoding="utf-8")) for path in sorted(FIXTURES.glob("*.json")))
    return {run["slug"]: run for run in runs if "turns" in run}


def load_run(path: Path) -> dict:
    """A run from a fixture or book JSON, or from an interview eval's Markdown."""
    text = path.read_text(encoding="utf-8")
    return json.loads(text) if path.suffix == ".json" else parse_run(text, source=path.name)


def turns_of(run: dict) -> list[Turn]:
    return [Turn(question=t["question"], answer=t["answer"], phase=t["phase"]) for t in run["turns"]]


def persona_of(run: dict) -> dict:
    return next(p for p in PERSONAS if p["name"] == run["persona"])


def packet(run: dict) -> str:
    """What an editor reads: the interview and the book, with nothing that gives away what we hoped for."""
    book = run["book"]
    lines = ["# The interview", ""]
    for n, turn in enumerate(run["turns"], start=1):
        if turn.get("playback"):
            lines += [f"(Librarian plays back) {turn['playback']}", ""]
        lines += [f"Q{n}. {turn['question']}", "", f"A{n}. {turn['answer'] or '(skipped)'}", ""]
    lines += ["# The three titles offered", ""]
    lines += [f"- {t['title']}: {t['why']}" for t in book["titles"]]
    lines += ["", f"# The finished book: {book['title']}", ""]
    if book["blurbs"].get("finished"):
        lines += ["Back cover:", "", book["blurbs"]["finished"], ""]
    for n, chapter in enumerate(book["chapters"], start=1):
        lines += [f"Chapter {n}: {chapter['title']}", "", chapter["summary"], ""]
        lines += [f"> {quote}" for quote in chapter["quotes"]]
        lines += [""]
    return "\n".join(lines)


def audit_packet(run: dict) -> str:
    """Every member's answer, then every sentence the book writes in the member's voice, numbered."""
    book = run["book"]
    lines = ["# The member's answers: the only allowed source", ""]
    for n, turn in enumerate(run["turns"], start=1):
        lines += [f"Q{n} (context only, not a source). {turn['question']}"]
        lines += [f"A{n}. {turn['answer'] or '(skipped)'}", ""]
    lines += ["# What to audit", ""]
    written = [(f"Chapter {n}", c) for n, c in enumerate(book["chapters"], start=1)]
    if book.get("rewrite"):
        written.append(("Rewrite of the last chapter", book["rewrite"]))
    number = 0
    for label, chapter in written:
        lines += [f"## {label}: {chapter['title']}"]
        for sentence in _split_sentences(chapter["summary"]):
            number += 1
            lines += [f"[S{number}] {sentence}"]
        lines += [""]
    for name, blurb in (book.get("blurbs") or {}).items():
        if name != "draft":
            lines += [f"## Back cover ({name})"]
            for sentence in _split_sentences(blurb):
                number += 1
                lines += [f"[S{number}] {sentence}"]
            lines += [""]
    lines += ["## Why each title is you (addressed to the member)"]
    for title in book["titles"]:
        number += 1
        lines += [f"[S{number}] {title['title']}: {title['why']}"]
    return "\n".join(lines) + "\n"


def _split_sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


if __name__ == "__main__":
    command, *paths = sys.argv[1:]
    for raw in paths:
        if command == "fixture":
            print(write_fixture(Path(raw)))
        elif command == "packet":
            print(packet(load_run(Path(raw))))
        elif command == "audit":
            print(audit_packet(load_run(Path(raw))))
