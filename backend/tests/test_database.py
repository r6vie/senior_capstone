import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from pymongo.errors import ConnectionFailure

from auth import get_current_user
from database import database_connection, get_database
from main import app
from seed import seed_profiles


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch("database.database_settings", return_value=("", "founderscircle"))
        self.settings.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.database = MagicMock()
        self.database.name = "founderscircle"
        self.database.command = AsyncMock(return_value={"ok": 1})
        app.dependency_overrides[get_current_user] = lambda: {"_id": "test-user"}

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def use_database(self):
        app.dependency_overrides[get_database] = lambda: self.database

    def test_missing_configuration_keeps_docs_but_blocks_database_routes(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/docs").status_code, 200)
        for path in ("/profiles", "/profiles/sample", "/health/database"):
            self.assertEqual(self.client.get(path).status_code, 503)

    def test_health_pings_database(self):
        self.use_database()
        self.assertEqual(self.client.get("/health/database").json(), {
            "status": "connected", "database": "founderscircle",
        })
        self.database.command.assert_awaited_once_with("ping")

    def test_database_failure_does_not_expose_connection_details(self):
        self.use_database()
        self.database.command.side_effect = ConnectionFailure("private-connection-details")
        response = self.client.get("/health/database")
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("private-connection-details", response.text)

    def test_missing_sample_returns_not_found(self):
        self.use_database()
        self.database.profiles.find_one = AsyncMock(return_value=None)
        self.assertEqual(self.client.get("/profiles/sample").status_code, 404)

    def test_filter_escapes_regex_and_hides_internal_id(self):
        self.use_database()
        cursor = self.database.profiles.find.return_value
        cursor.sort.return_value.limit.return_value.to_list = AsyncMock(return_value=[])
        response = self.client.get("/profiles", params={"expertise": "  C++  "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        self.database.profiles.find.assert_called_once_with(
            {"expertise": {"$regex": r"C\+\+", "$options": "i"}},
            {"_id": 1, "name": 1, "affiliation": 1, "location": 1, "expertise": 1, "interests": 1},
        )


class ConnectionAndSeedTests(unittest.IsolatedAsyncioTestCase):
    async def test_client_is_closed_after_failure(self):
        client = MagicMock()
        client.close = AsyncMock()
        with patch("database.database_settings", return_value=("mongodb://localhost", "test")):
            with patch("database.AsyncMongoClient", return_value=client):
                with self.assertRaisesRegex(RuntimeError, "MongoDB connection failed"):
                    async with database_connection():
                        raise ConnectionFailure("private-connection-details")
        client.close.assert_awaited_once()

    async def test_reseeding_preserves_existing_records(self):
        # Simulate $setOnInsert to check seed behavior without an Atlas account.
        records = {}

        async def update_one(query, update, upsert):
            key = query["_id"]
            if key in records:
                return SimpleNamespace(upserted_id=None)
            records[key] = deepcopy(update["$setOnInsert"])
            return SimpleNamespace(upserted_id=key)

        database = MagicMock()
        database.profiles.update_one = AsyncMock(side_effect=update_one)
        self.assertEqual(await seed_profiles(database), 3)
        records["sample-alex"]["location"] = "Edited location"
        self.assertEqual(await seed_profiles(database), 0)
        self.assertEqual(len(records), 3)
        self.assertEqual(records["sample-alex"]["location"], "Edited location")
