#!/usr/bin/env python3
"""Give a member the question after a reading, so it can be walked before "Did you meet?" exists.
Only runs on a trove_dev database:

    python3 scripts/ask_after_reading.py member@case.edu
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    command = ["uv", "run", "python", "-m", "trove.interview.dev_reading", *sys.argv[1:]]
    sys.exit(subprocess.run(command, cwd=ROOT / "api").returncode)
