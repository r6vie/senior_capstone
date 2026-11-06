"""The MongoDB connection: connect in the background, keep retrying, and hand routes the database."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager, suppress

import certifi
from fastapi import FastAPI, HTTPException, Request
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import PyMongoError

from trove.core.config import get_settings

logger = logging.getLogger(__name__)
RECONNECT_SECONDS = 5

# Each feature that owns collections exposes one of these; main.py lists them.
IndexSetup = Callable[[AsyncDatabase], Awaitable[None]]


def connect(uri: str) -> AsyncMongoClient:
    # Atlas (mongodb+srv) uses TLS; python.org builds of Python on macOS ship without root
    # certificates, so verify against certifi's bundle instead.
    tls = {"tlsCAFile": certifi.where()} if uri.startswith("mongodb+srv://") else {}
    return AsyncMongoClient(uri, timeoutMS=10000, serverSelectionTimeoutMS=5000, **tls)


async def setup_indexes(database: AsyncDatabase, index_setups: list[IndexSetup]) -> None:
    for setup in index_setups:
        await setup(database)


def make_lifespan(index_setups: list[IndexSetup]):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.database = None
        app.state.database_ready = False
        settings = get_settings()
        if not settings.mongodb_uri:
            # Keep the API docs available while MongoDB is being set up.
            logger.warning("MONGODB_URI is not set; database routes return 503.")
            yield
            return
        try:
            client = connect(settings.mongodb_uri)
        except ValueError:
            logger.warning("MONGODB_URI is invalid; database routes return 503.")
            yield
            return

        app.state.database = client[settings.mongodb_database]
        stop = asyncio.Event()
        # Connecting happens in the background so a temporary outage never stops FastAPI starting.
        task = asyncio.create_task(_initialize(app, index_setups, stop), name="mongodb-initializer")
        try:
            yield
        finally:
            stop.set()
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            await client.close()

    return lifespan


async def _initialize(app: FastAPI, index_setups: list[IndexSetup], stop: asyncio.Event) -> None:
    database = app.state.database
    while not stop.is_set():
        try:
            await database.command("ping")
            await setup_indexes(database, index_setups)
        except (PyMongoError, ValueError):
            # Connection errors can contain private connection details; never log them.
            app.state.database_ready = False
            logger.warning("MongoDB is unavailable; retrying in %s seconds.", RECONNECT_SECONDS)
            try:
                await asyncio.wait_for(stop.wait(), timeout=RECONNECT_SECONDS)
            except TimeoutError:
                continue
        else:
            app.state.database_ready = True
            logger.info("MongoDB is ready (database %s).", database.name)
            return


def get_database(request: Request) -> AsyncDatabase:
    """FastAPI dependency: the database, or 503 while it is unavailable."""
    database = request.app.state.database
    if database is None or not request.app.state.database_ready:
        raise HTTPException(
            status_code=503,
            detail="The database is temporarily unavailable. The API reconnects automatically.",
        )
    return database
