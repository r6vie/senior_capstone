"""Run interview personas in parallel, one output file each:

    uv run python -m evals.interview              # every persona
    uv run python -m evals.interview Siddharth    # personas whose name starts with these words

Outputs go to evals/out/interview/<timestamp>/ (git-ignored). Costs money.
"""

import asyncio
import sys
from datetime import datetime

from evals.interview import CASES, run_case
from evals.run import OUT_DIR
from trove.ai.client import get_claude


async def run_one(claude, case: dict, folder) -> None:
    slug = case["name"].split()[0].lower()
    try:
        body = await run_case(claude, case)
    except Exception as error:  # one persona failing shouldn't lose the others
        body = f"**Failed:** {type(error).__name__}: {error}"
    (folder / f"{slug}.md").write_text(f"## {case['name']}\n\n{body}\n", encoding="utf-8")
    print(f"done: {case['name']}", flush=True)


async def main(names: list[str]) -> None:
    cases = [c for c in CASES if not names or any(c["name"].startswith(n) for n in names)]
    folder = OUT_DIR / "interview" / f"{datetime.now():%Y-%m-%d_%H%M%S}"
    folder.mkdir(parents=True, exist_ok=True)
    claude = get_claude()
    await asyncio.gather(*(run_one(claude, case, folder) for case in cases))
    print(f"Saved {folder}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
