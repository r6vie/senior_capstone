#!/usr/bin/env python3
"""Add about 20 clearly marked sample books to your own dev database (MONGODB_DATABASE in .env):

    python3 scripts/seed.py           # add or refresh the samples (safe to run again)
    python3 scripts/seed.py --remove  # remove the samples, and nothing else
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    command = ["uv", "run", "python", "-m", "trove.books.seed", *sys.argv[1:]]
    sys.exit(subprocess.run(command, cwd=ROOT / "api").returncode)
