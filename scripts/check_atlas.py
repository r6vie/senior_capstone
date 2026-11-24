#!/usr/bin/env python3
"""Check that an Atlas cluster is ready to host Trove, before putting its connection string in Render.

Run it in your own terminal (it asks for the string with hidden input, so the secret is never printed,
saved or left in your shell history):

    cd api && python -m uv run python ../scripts/check_atlas.py

It connects, writes and removes one scratch document, and makes and removes one index in the `trove_prod`
database, which is everything the app does at startup. It shows the cluster's host name, so you can see
it is your cluster and not a teammate's. It never shows the user name or password.
"""

import asyncio
import getpass
import re
import sys
from pathlib import Path

# The `trove` package lives in api/, and Python only looks beside the script, so say where it is.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "api"))

DATABASE = "trove_prod"


async def check(uri: str) -> int:
    from trove.core.database import connect

    host = re.search(r"@([^/?]+)", uri)
    print(f"Cluster host: {host.group(1) if host else '(could not read one)'}")
    print(f"Database:     {DATABASE}")
    client = connect(uri)
    try:
        await client.admin.command("ping")
        print("PASS  connected")
        database = client[DATABASE]
        await database.atlas_check.insert_one({"_id": "check"})
        await database.atlas_check.create_index("when", expireAfterSeconds=60, name="check_expiry")
        print("PASS  can write and make indexes in trove_prod")
        await database.drop_collection("atlas_check")
        print("PASS  cleaned up")
        return 0
    except Exception as error:  # the message can include the host, never the password
        print(f"FAIL  {type(error).__name__}: {str(error)[:300]}")
        return 1
    finally:
        await client.close()


def main() -> int:
    uri = getpass.getpass("Atlas connection string (hidden): ").strip()
    if not uri.startswith(("mongodb+srv://", "mongodb://")):
        print("That doesn't look like a connection string. It starts with mongodb+srv://")
        return 1
    if "<password>" in uri or "<db_password>" in uri:
        print("Replace <password> (or <db_password>) with the database user's password first.")
        return 1
    return asyncio.run(check(uri))


if __name__ == "__main__":
    sys.exit(main())
