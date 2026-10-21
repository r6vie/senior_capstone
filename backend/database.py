"""Read private settings and maintain a recoverable MongoDB connection."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

import certifi
from dotenv import dotenv_values
from fastapi import HTTPException, Request
from pymongo import AsyncMongoClient
from pymongo.errors import PyMongoError


logger = logging.getLogger(__name__)
RECONNECT_SECONDS = 5


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
        # Atlas (mongodb+srv) uses TLS; python.org builds of Python on macOS ship
        # without root certificates, so verify against certifi's bundle instead.
        tls = {"tlsCAFile": certifi.where()} if uri.startswith("mongodb+srv://") else {}
        client = AsyncMongoClient(uri, timeoutMS=10000, serverSelectionTimeoutMS=5000, **tls)
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
    app.state.database_ready = False
    uri, name = database_settings()
    if not uri:
        # Keep the home page and API docs available while Atlas is being set up.
        yield
        return

    stop_event = asyncio.Event()
    try:
        # Creating a client is non-blocking. Connection and index setup happen in
        # the background so a temporary Atlas outage never terminates FastAPI.
        tls = {"tlsCAFile": certifi.where()} if uri.startswith("mongodb+srv://") else {}
        client = AsyncMongoClient(uri, timeoutMS=10000, serverSelectionTimeoutMS=5000, **tls)
        database = client[name]
    except ValueError:
        logger.warning("MongoDB configuration is invalid; database routes are unavailable.")
        yield
        return

    app.state.database = database
    retry_task = asyncio.create_task(
        initialize_database(app, database, stop_event),
        name="mongodb-initializer",
    )
    try:
        yield
    finally:
        stop_event.set()
        retry_task.cancel()
        try:
            await retry_task
        except asyncio.CancelledError:
            pass
        await client.close()


async def initialize_database(app, database, stop_event: asyncio.Event):
    """Retry Atlas until it is ready, without exposing connection details."""
    while not stop_event.is_set():
        try:
            await database.command("ping")
            await ensure_indexes(database)
        except (PyMongoError, ValueError):
            app.state.database_ready = False
            logger.warning("MongoDB is unavailable; retrying in %s seconds.", RECONNECT_SECONDS)
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=RECONNECT_SECONDS)
            except TimeoutError:
                continue
        else:
            app.state.database_ready = True
            logger.info("MongoDB connection is ready.")
            return


async def ensure_indexes(database):
    # Unique indexes prevent duplicates even when requests arrive concurrently.
    await database.users.create_index("email", unique=True, name="users_email_unique")
    # LinkedIn members are looked up by their stable LinkedIn ID; password-only accounts lack one.
    await database.users.create_index(
        "linkedin_sub", unique=True, name="users_linkedin_sub_unique",
        partialFilterExpression={"linkedin_sub": {"$type": "string"}},
    )
    await database.oauth_states.create_index("expires_at", expireAfterSeconds=0, name="oauth_states_expiry")
    await database.login_codes.create_index("expires_at", expireAfterSeconds=0, name="login_codes_expiry")
    await database.sessions.create_index("token_hash", unique=True, name="sessions_token_unique")
    await database.sessions.create_index("expires_at", expireAfterSeconds=0, name="sessions_expiry")
    await database.auth_attempts.create_index("expires_at", expireAfterSeconds=0, name="attempts_expiry")
    await database.profiles.create_index(
        "owner_user_id", unique=True, name="profiles_owner_unique",
        partialFilterExpression={"owner_user_id": {"$type": "string"}},
    )
    await database.facts.create_index([("user_id", 1), ("created_at", 1)], name="facts_by_member")
    await database.facts.create_index("links", name="facts_link_keys")
    await database.interview_sessions.create_index("user_id", unique=True, name="interviews_one_per_member")
    # One request per pair of people, in either direction.
    await database.connections.create_index("pair_key", unique=True, name="connections_pair_unique")
    await database.connections.create_index("sender_user_id", name="connections_sender")
    await database.connections.create_index("recipient_user_id", name="connections_recipient")
    await database.notifications.create_index("user_id", name="notifications_user")
    await database.messages.create_index([("connection_id", 1), ("created_at", 1)], name="messages_thread")


def get_database(request: Request):
    database = request.app.state.database
    if database is None or not getattr(request.app.state, "database_ready", False):
        raise HTTPException(
            status_code=503,
            detail="MongoDB is temporarily unavailable. The backend will reconnect automatically.",
        )
    return database
