#!/usr/bin/env python3
"""Regenerate the frontend's typed API client from the backend.

Run after any change to a route or a request/response model:

    python3 scripts/generate_api_client.py

Writes api/openapi.json and web/src/api/schema.ts. Commit both. CI fails if they are stale.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DUMP = "import json; from trove.main import app; print(json.dumps(app.openapi(), indent=2))"


def main() -> int:
    schema = subprocess.run(
        ["uv", "run", "python", "-c", DUMP],
        cwd=ROOT / "api", capture_output=True, text=True, check=True,
    ).stdout
    (ROOT / "api" / "openapi.json").write_text(schema, encoding="utf-8")
    subprocess.run(["npm", "--prefix", "web", "run", "--silent", "api:generate"], cwd=ROOT, check=True)
    print("Updated api/openapi.json and web/src/api/schema.ts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
