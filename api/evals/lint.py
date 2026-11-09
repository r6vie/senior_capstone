"""Lint saved runs for free: uv run python -m evals.lint <run.json or run.md>..."""

import sys
from collections import Counter
from pathlib import Path

from evals.lints import lint_across, lint_run
from evals.saved import load_run, persona_of


def main(paths: list[str]) -> int:
    errors = 0
    runs = []
    for raw in paths:
        run = load_run(Path(raw))
        runs.append(run)
        findings = lint_run(run, resume=persona_of(run).get("resume"))
        counts = Counter(f.level for f in findings)
        print(f"\n{raw}: {counts['error']} errors, {counts['warn']} warnings")
        print("\n".join(f"  {f}" for f in findings))
        errors += counts["error"]
    if len(runs) > 1:
        print("\nAcross these books:")
        print("\n".join(f"  {f}" for f in lint_across(runs)))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
