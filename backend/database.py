"""Read our private settings and manage the MongoDB connection."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import dotenv_values
from fastapi import HTTPException, Request
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError


def database_settings() -> tuple[str, str]:
    # Use the project's .env even when Python is started from another folder.
    settings = {**dotenv_values(Path(__file__).resolve().parent.parent / ".env"), **os.environ}
    return (
        (settings.get("MONGODB_URI") or "").strip(),
        (settings.get("MONGODB_DATABASE") or "founderscircle").strip(),
    )


@asynccontextmanager
async def database_connection():
    uri, name = database_settings()
    if not uri:
        raise RuntimeError("Add MONGODB_URI to the project's .env file first.")
    client = None
    try:
        client = AsyncMongoClient(uri, timeoutMS=10000, serverSelectionTimeoutMS=5000)
        yield client[name]
    except (PyMongoError, ValueError):
        # Connection errors can contain private connection details; don't print them.
        raise RuntimeError(
            "MongoDB connection failed. Check the .env connection string, database "
            "user, Atlas IP access list, and internet connection."
        ) from None
    finally:
        if client is not None:
            await client.close()


@asynccontextmanager
async def lifespan(app):
    app.state.database = None
    uri, _ = database_settings()
    if not uri:
        # Keep the home page and API docs available while Atlas is being set up.
        yield
        return
    async with database_connection() as database:
        await ensure_indexes(database)
        app.state.database = database
        yield


async def ensure_indexes(database):
    # Unique indexes prevent duplicates even when requests arrive concurrently.
    await database.users.create_index("email", unique=True, name="users_email_unique")
    await database.sessions.create_index("token_hash", unique=True, name="sessions_token_unique")
    await database.sessions.create_index("expires_at", expireAfterSeconds=0, name="sessions_expiry")
    await database.auth_attempts.create_index("expires_at", expireAfterSeconds=0, name="attempts_expiry")
    await database.profiles.create_index(
        "owner_user_id", unique=True, name="profiles_owner_unique",
        partialFilterExpression={"owner_user_id": {"$type": "string"}},
    )


def get_database(request: Request):
    database = request.app.state.database
    if database is None:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is not configured. Add MONGODB_URI to .env and restart the backend.",
        )
    return database
