#!/usr/bin/env python3
"""Run the FoundersCircle backend and frontend together for local development."""

import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / "bin" / "python"


def main() -> int:
    if not PYTHON.exists():
        print("Missing .venv. Follow the README setup steps first.", file=sys.stderr)
        return 1

    commands = [
        [str(PYTHON), "-m", "uvicorn", "main:app", "--app-dir", "backend", "--reload", "--reload-dir", "backend", "--host", "127.0.0.1", "--port", "8000"],
        ["npm", "--prefix", "frontend", "run", "dev", "--", "--host", "127.0.0.1"],
    ]
    processes: list[subprocess.Popen] = []
    try:
        for command in commands:
            processes.append(subprocess.Popen(command, cwd=ROOT))

        print("\nFoundersCircle is starting:")
        print("  App:      http://127.0.0.1:5173")
        print("  API docs: http://127.0.0.1:8000/docs")
        print("Press Ctrl+C to stop both.\n")

        while True:
            for process in processes:
                return_code = process.poll()
                if return_code is not None:
                    return return_code
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
    raise SystemExit(main())
