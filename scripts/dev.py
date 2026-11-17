#!/usr/bin/env python3
"""Run the API and the web app together for local development: python3 scripts/dev.py

A second copy can run beside the first, on the free scripted AI and its own database:

    MONGODB_DATABASE=trove_dev_qc python3 scripts/dev.py --api-port 8100 --web-port 5273 --scripted-ai
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the API and the web app together.")
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--web-port", type=int, default=5173)
    parser.add_argument("--scripted-ai", action="store_true", help="Canned AI replies: no key, no cost.")
    args = parser.parse_args()

    if shutil.which("uv") is None:
        print("Install uv first: https://docs.astral.sh/uv/", file=sys.stderr)
        return 1
    if not (ROOT / "web" / "node_modules").exists():
        print("Run `npm --prefix web install` first.", file=sys.stderr)
        return 1

    api = f"http://127.0.0.1:{args.api_port}"
    web = f"http://127.0.0.1:{args.web_port}"
    # Real environment variables win over .env, so links in emails point at this copy of the app.
    env = {**os.environ, "API_URL": api, "FRONTEND_URL": web, "TROVE_API_PORT": str(args.api_port)}
    if args.scripted_ai:
        env["AI_MODE"] = "scripted"
    uvicorn = ["uv", "run", "uvicorn", "trove.main:app", "--reload", "--host", "127.0.0.1"]
    commands = [
        ([*uvicorn, "--port", str(args.api_port)], ROOT / "api"),
        # Fail rather than quietly take the next port, which the first copy's links wouldn't match.
        (["npm", "run", "dev", "--", "--port", str(args.web_port), "--strictPort"], ROOT / "web"),
    ]
    processes = [subprocess.Popen(command, cwd=cwd, env=env) for command, cwd in commands]
    print("\nTrove is starting:")
    print(f"  App:      {web}")
    print(f"  API docs: {api}/docs")
    if args.scripted_ai:
        print("  AI:       scripted (no key, no cost)")
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
