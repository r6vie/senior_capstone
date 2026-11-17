"""Development only: `scripts/ask_after_reading.py`. Nothing in the app calls this."""

import asyncio
import sys
from uuid import uuid4

from trove.auth.service import user_id_by_email
from trove.core.config import get_settings
from trove.core.database import connect
from trove.interview.service import ask_after_reading


async def main(email: str) -> int:
    settings = get_settings()
    if not settings.mongodb_database.startswith("trove_dev"):
        print(
            f"Refusing to run on {settings.mongodb_database}: this is for trove_dev databases.",
            file=sys.stderr,
        )
        return 1
    client = connect(settings.mongodb_uri)
    try:
        database = client[settings.mongodb_database]
        author_id = await user_id_by_email(database, email)
        if author_id is None:
            print(f"No member with the email {email} in {database.name}.", file=sys.stderr)
            return 1
        await ask_after_reading(database, author_id, f"dev-{uuid4()}")
        print(f"{email} now has the question after a reading.")
        return 0
    finally:
        await client.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: scripts/ask_after_reading.py member@case.edu", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(asyncio.run(main(sys.argv[1])))
