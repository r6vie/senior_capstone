"""Run once to save the fictional profiles in MongoDB. Safe to run again."""

import asyncio

from database import database_connection
from sample_data import profiles


async def seed_profiles(database) -> int:
    inserted = 0
    for profile in profiles:
        result = await database.profiles.update_one(
            {"_id": profile["_id"]},
            {"$setOnInsert": profile},
            upsert=True,
        )
        inserted += result.upserted_id is not None
    return inserted


async def main():
    async with database_connection() as database:
        await database.command("ping")
        inserted = await seed_profiles(database)
        print(f"Connected to MongoDB. Added {inserted} fictional profiles.")
        print("Existing profiles were left unchanged.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
