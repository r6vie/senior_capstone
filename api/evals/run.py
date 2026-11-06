"""Run one feature's evals against the real Claude API and save the outputs for a human to read.

    uv run python -m evals.run <feature>

Each eval suite is a module `evals/<feature>.py` defining:

    CASES: list[dict]                                  # fixed inputs, e.g. test personas
    async def run_case(claude: Claude, case: dict) -> str   # returns Markdown to review

Outputs go to evals/out/<feature>/<timestamp>.md (git-ignored). These calls cost money.
"""

import asyncio
import importlib
import sys
from datetime import datetime
from pathlib import Path

from trove.ai.client import get_claude

OUT_DIR = Path(__file__).resolve().parent / "out"


async def main(feature: str) -> int:
    try:
        suite = importlib.import_module(f"evals.{feature}")
    except ModuleNotFoundError:
        print(f"No eval suite at evals/{feature}.py yet.", file=sys.stderr)
        return 1
    claude = get_claude()
    sections = []
    for number, case in enumerate(suite.CASES, start=1):
        print(f"[{number}/{len(suite.CASES)}] {case.get('name', number)}")
        sections.append(f"## {case.get('name', number)}\n\n{await suite.run_case(claude, case)}")
    path = OUT_DIR / feature / f"{datetime.now():%Y-%m-%d_%H%M%S}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(f"Saved {path}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(asyncio.run(main(sys.argv[1])))
