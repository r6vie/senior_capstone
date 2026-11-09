"""Shared fixtures.

Tests that touch the database use a real MongoDB: a throwaway database named trove_test_<random>
on TROVE_TEST_MONGODB_URI (or, if unset, the MONGODB_URI in .env). It is dropped afterwards.
Without either, database tests are skipped. CI runs a local MongoDB container.
"""

import os
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from tests.fakes import FakeClaude
from trove.ai.client import get_claude
from trove.core.config import get_settings
from trove.core.database import connect, get_database, setup_indexes
from trove.main import INDEX_SETUPS, app


@pytest.fixture(autouse=True)
def no_real_email(monkeypatch):
    # Never send real email from tests: without SMTP_HOST, emails are printed instead.
    monkeypatch.setenv("SMTP_HOST", "")
    monkeypatch.delenv("SMTP_HOST")
    get_settings.cache_clear()
    monkeypatch.setattr(get_settings(), "smtp_host", "")
    # Tests never write to the real spending ledger, and never run on the scripted AI by accident.
    monkeypatch.setattr(get_settings(), "ai_usage_log", "")
    # Tests never hold the real key either, so a route that needs Claude fails here as it does on CI,
    # where there is no .env, unless the test installs fake_claude.
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "")
    monkeypatch.setattr(get_settings(), "ai_mode", "real")
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
async def mongo_database():
    uri = os.environ.get("TROVE_TEST_MONGODB_URI") or get_settings().mongodb_uri
    if not uri:
        pytest.skip("Set TROVE_TEST_MONGODB_URI (or MONGODB_URI in .env) to run database tests.")
    client = connect(uri)
    database = client[f"trove_test_{uuid4().hex[:12]}"]
    await setup_indexes(database, INDEX_SETUPS)
    yield database
    await client.drop_database(database.name)
    await client.close()


@pytest.fixture
async def database(mongo_database):
    """The test database, emptied after each test."""
    yield mongo_database
    for name in await mongo_database.list_collection_names():
        await mongo_database[name].delete_many({})


@pytest.fixture
def fake_claude():
    claude = FakeClaude()
    app.dependency_overrides[get_claude] = lambda: claude
    yield claude
    app.dependency_overrides.pop(get_claude, None)


async def http_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http:
        yield http


@pytest.fixture
async def client(database):
    """An HTTP client for the app, wired to the test database."""
    app.dependency_overrides[get_database] = lambda: database
    async for http in http_client():
        yield http
    app.dependency_overrides.pop(get_database, None)


@pytest.fixture
async def client_without_database():
    """An HTTP client for the app as it behaves while MongoDB is unreachable."""
    app.state.database = None
    app.state.database_ready = False
    async for http in http_client():
        yield http
