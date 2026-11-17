#!/usr/bin/env python3
"""Print what real Claude calls have cost so far, from the ledger at AI_USAGE_LOG in .env:

    python3 scripts/ai_spend.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    sys.exit(subprocess.run(["uv", "run", "python", "-m", "trove.ai.usage"], cwd=ROOT / "api").returncode)
