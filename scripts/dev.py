#!/usr/bin/env python3
"""Run the API and the web app together for local development: python3 scripts/dev.py"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if shutil.which("uv") is None:
        print("Install uv first: https://docs.astral.sh/uv/", file=sys.stderr)
        return 1
    if not (ROOT / "web" / "node_modules").exists():
        print("Run `npm --prefix web install` first.", file=sys.stderr)
        return 1

    commands = [
        (["uv", "run", "uvicorn", "trove.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"], ROOT / "api"),
        (["npm", "run", "dev"], ROOT / "web"),
    ]
    processes = [subprocess.Popen(command, cwd=cwd) for command, cwd in commands]
    print("\nTrove is starting:")
    print("  App:      http://127.0.0.1:5173")
    print("  API docs: http://127.0.0.1:8000/docs")
    print("Press Ctrl+C to stop both.\n")
    try:
        while True:
            for process in processes:
                if (code := process.poll()) is not None:
                    return code
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 0
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    sys.exit(main())
