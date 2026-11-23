#!/usr/bin/env python3
"""Run the API and the web app together for local development: python3 scripts/dev.py

A second copy can run beside the first, on the free scripted AI and its own database:

    MONGODB_DATABASE=trove_dev_qc python3 scripts/dev.py --api-port 8100 --web-port 5273 --scripted-ai

With no ANTHROPIC_API_KEY in .env it uses the scripted AI on its own, and says so.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# The same list the API checks (api/trove/ai/scripted.py), so dev.py stops before the API would refuse.
DEV_ENVIRONMENTS = {"development", "dev", "local", "test"}


def api_settings(env: dict[str, str]) -> dict | None:
    """The AI settings as the API itself reads .env and the environment, so the two never disagree."""
    code = (
        "import json; from trove.core.config import get_settings as g; s = g(); "
        "print(json.dumps({'key': bool(s.anthropic_api_key), 'mode': s.ai_mode, "
        "'database': s.mongodb_database, 'model': s.anthropic_model, 'environment': s.environment}))"
    )
    result = subprocess.run(
        ["uv", "run", "--quiet", "python", "-c", code],
        cwd=ROOT / "api",
        env=env,
        capture_output=True,
        text=True,
    )
    try:
        return json.loads(result.stdout.strip().splitlines()[-1]) if result.returncode == 0 else None
    except (ValueError, IndexError):
        return None


def choose_ai(settings: dict, asked_scripted: bool) -> tuple[bool, str, str | None]:
    """Whether to run the scripted AI, the line that says which AI runs, and why it can't start, if it can't.

    With no key the real AI can only refuse, so the interview would fail on its first question. The scripted
    AI works without one, and saying so keeps a missing key from looking like a broken app."""
    fallback = not settings["key"] and not asked_scripted and settings["mode"] != "scripted"
    if settings["key"] and not asked_scripted and settings["mode"] != "scripted":
        return False, f"real ({settings['model']})", None

    # The API refuses canned replies outside development or on any other database: stop here with the fix.
    database, environment = settings["database"], settings.get("environment", "development")
    why = (
        "There's no ANTHROPIC_API_KEY in .env, so the interview would use the scripted AI, which"
        if fallback
        else "The scripted AI"
    )
    problem = None
    if environment.lower() not in DEV_ENVIRONMENTS:
        problem = (
            f"{why} only runs in development, and ENVIRONMENT is {environment}. Remove ENVIRONMENT from .env."
        )
    elif not database.startswith("trove_dev"):
        problem = (
            f"{why} only runs on a trove_dev database, and MONGODB_DATABASE is {database}. "
            f"{'Add a key, or set' if fallback else 'Set'} MONGODB_DATABASE=trove_dev_<yourname> in .env."
        )
    if fallback:
        return (
            True,
            "scripted, because .env has no ANTHROPIC_API_KEY (no cost). Add a key for the real AI.",
            problem,
        )
    return True, "scripted (canned replies, no key, no cost)", problem


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
    settings = api_settings(env)
    if settings is None:
        ai = "unknown: couldn't read the API's settings (run `uv sync --directory api`)"
    else:
        scripted, ai, problem = choose_ai(settings, args.scripted_ai)
        if problem:
            print(problem, file=sys.stderr)
            return 1
        if scripted:
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
    print(f"  AI:       {ai}")
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
