#!/usr/bin/env python3
"""Run every check CI runs, in the same order. Run this before every commit:

    python3 scripts/check.py          # check everything
    python3 scripts/check.py --fix    # also auto-fix formatting and lint first

Exits non-zero on the first failure, printing which step failed.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def steps(fix: bool) -> list[tuple[str, list[str], Path]]:
    api, web = ROOT / "api", ROOT / "web"
    fixes = [
        ("api: fix lint", ["uv", "run", "ruff", "check", "--fix", "."], api),
        ("api: format", ["uv", "run", "ruff", "format", "."], api),
        ("web: fix lint and format", ["npm", "run", "--silent", "format"], web),
    ]
    checks = [
        ("api: lint", ["uv", "run", "ruff", "check", "."], api),
        ("api: format", ["uv", "run", "ruff", "format", "--check", "."], api),
        ("api: tests", ["uv", "run", "pytest", "-q"], api),
        ("api client up to date", [sys.executable, "scripts/generate_api_client.py"], ROOT),
        ("api client committed", ["git", "diff", "--exit-code", "--", "api/openapi.json", "web/src/api/schema.ts"], ROOT),
        ("web: lint and format", ["npm", "run", "--silent", "lint"], web),
        ("web: types", ["npm", "run", "--silent", "typecheck"], web),
        ("web: tests", ["npm", "run", "--silent", "test"], web),
        ("web: build", ["npm", "run", "--silent", "build"], web),
    ]
    return (fixes if fix else []) + checks


def main() -> int:
    for name, command, cwd in steps(fix="--fix" in sys.argv):
        print(f"\n==> {name}", flush=True)
        if subprocess.run(command, cwd=cwd).returncode != 0:
            print(f"\nFAILED: {name}", file=sys.stderr)
            return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
