"""Add the sample books to your own dev database. Run it with `python3 scripts/seed.py [--remove]`."""

import asyncio
import sys

from trove.books.samples import remove_samples, seed_samples
from trove.books.service import ensure_indexes
from trove.core.config import get_settings
from trove.core.database import connect


async def main(remove: bool) -> int:
    settings = get_settings()
    if not settings.mongodb_uri:
        print("Set MONGODB_URI in .env first.", file=sys.stderr)
        return 1
    # Samples belong only in a developer's own database, never a shared or production one.
    if not settings.mongodb_database.startswith("trove_dev"):
        print("Refusing to seed: MONGODB_DATABASE must start with trove_dev.", file=sys.stderr)
        return 1
    client = connect(settings.mongodb_uri)
    try:
        database = client[settings.mongodb_database]
        if remove:
            print(f"Removed {await remove_samples(database)} sample books.")
        else:
            await ensure_indexes(database)
            print(f"Seeded {await seed_samples(database)} sample books.")
    finally:
        await client.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(remove="--remove" in sys.argv)))
