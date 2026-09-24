import unittest
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient
from pymongo import ReturnDocument
from pymongo.errors import ConnectionFailure

from auth import get_current_user
from database import get_database
from main import app
from sample_data import profiles


class ProfileCrudTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch("database.database_settings", return_value=("", "test"))
        self.settings.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.document = deepcopy(profiles[0])
        self.payload = {key: value for key, value in self.document.items() if key != "_id"}
        self.database = MagicMock()
        self.collection = self.database.profiles
        self.collection.insert_one = AsyncMock()
        self.collection.find_one = AsyncMock(return_value=self.document)
        self.collection.find_one_and_update = AsyncMock(return_value=self.document)
        self.collection.delete_one = AsyncMock(return_value=SimpleNamespace(deleted_count=1))
        app.dependency_overrides[get_database] = lambda: self.database
        app.dependency_overrides[get_current_user] = lambda: {"_id": "test-user"}

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def test_create_persists_validated_profile_with_generated_id(self):
        response = self.client.post("/profiles", json={**self.payload, "name": "  Alex  "})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(UUID(data["id"]).version, 4)
        self.assertEqual(data["name"], "Alex")
        self.assertNotIn("_id", data)
        self.collection.insert_one.assert_awaited_once_with({
            **self.payload, "name": "Alex", "_id": data["id"], "owner_user_id": "test-user",
        })

    def test_create_assigns_distinct_ids(self):
        first = self.client.post("/profiles", json=self.payload).json()
        app.dependency_overrides[get_current_user] = lambda: {"_id": "second-user"}
        second = self.client.post("/profiles", json=self.payload).json()
        self.assertNotEqual(first["id"], second["id"])

    def test_invalid_create_does_not_write_to_database(self):
        for body in ({}, {**self.payload, "name": " "}, {**self.payload, "id": "chosen"},
                     {**self.payload, "_id": "chosen"}, {**self.payload, "expertise": "wrong"}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/profiles", json=body).status_code, 422)
        self.collection.insert_one.assert_not_awaited()

    def test_get_uses_exact_id_and_returns_public_fields(self):
        self.document["private_note"] = "not public"
        response = self.client.get("/profiles/sample-alex")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {**self.payload, "id": "sample-alex"})
        self.assertEqual(self.collection.find_one.call_args.args[0], {"_id": "sample-alex"})

    def test_missing_get_returns_404(self):
        self.collection.find_one.return_value = None
        self.assertEqual(self.client.get("/profiles/missing").status_code, 404)

    def test_sample_route_is_not_treated_as_id(self):
        response = self.client.get("/profiles/sample")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.collection.find_one.call_args.args[0], {"_id": "sample-alex"})

    def test_patch_changes_only_supplied_fields_atomically(self):
        self.collection.find_one_and_update.return_value = {**self.document, "location": "Boston"}
        response = self.client.patch("/profiles/sample-alex", json={"location": " Boston "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {**self.payload, "location": "Boston", "id": "sample-alex"})
        call = self.collection.find_one_and_update.call_args
        self.assertEqual(call.args, (
            {"_id": "sample-alex", "owner_user_id": "test-user"}, {"$set": {"location": "Boston"}},
        ))
        self.assertEqual(call.kwargs["return_document"], ReturnDocument.AFTER)
        self.assertFalse(call.kwargs.get("upsert", False))

    def test_patch_can_clear_lists(self):
        self.collection.find_one_and_update.return_value = {**self.document, "expertise": [], "interests": []}
        response = self.client.patch("/profiles/sample-alex", json={"expertise": [], "interests": []})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["expertise"], [])
        self.assertEqual(self.collection.find_one_and_update.call_args.args[1], {
            "$set": {"expertise": [], "interests": []},
        })

    def test_invalid_patch_never_writes(self):
        invalid = [{}, {"name": " "}, {"expertise": "mentoring"}, {"interests": [123]},
                   {"id": "new"}, {"_id": "new"}, {"$set": {"name": "bad"}}]
        invalid.extend({field: None} for field in self.payload)
        for body in invalid:
            with self.subTest(body=body):
                response = self.client.patch("/profiles/sample-alex", json=body)
                self.assertEqual(response.status_code, 422)
        self.collection.find_one_and_update.assert_not_awaited()

    def test_missing_patch_returns_404(self):
        self.collection.find_one_and_update.return_value = None
        self.assertEqual(self.client.patch("/profiles/missing", json={"name": "Alex"}).status_code, 404)

    def test_delete_targets_one_id_and_returns_empty_204(self):
        response = self.client.delete("/profiles/sample-alex")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")
        self.collection.delete_one.assert_awaited_once_with({"_id": "sample-alex", "owner_user_id": "test-user"})

    def test_missing_delete_returns_404(self):
        self.collection.delete_one.return_value.deleted_count = 0
        self.assertEqual(self.client.delete("/profiles/missing").status_code, 404)

    def test_database_failures_return_503_for_each_operation(self):
        for method in ("insert_one", "find_one", "find_one_and_update", "delete_one"):
            getattr(self.collection, method).side_effect = ConnectionFailure("private-details")
        for method, path, body in [
            ("POST", "/profiles", self.payload),
            ("GET", "/profiles/sample-alex", None),
            ("PATCH", "/profiles/sample-alex", {"name": "Alex"}),
            ("DELETE", "/profiles/sample-alex", None),
        ]:
            with self.subTest(method=method):
                response = self.client.request(method, path, json=body)
                self.assertEqual(response.status_code, 503)
                self.assertNotIn("private-details", response.text)

    def test_write_routes_require_database_configuration(self):
        app.dependency_overrides.clear()
        app.dependency_overrides[get_current_user] = lambda: {"_id": "test-user"}
        for method, path, body in [
            ("POST", "/profiles", self.payload),
            ("PATCH", "/profiles/sample-alex", {"name": "Alex"}),
            ("DELETE", "/profiles/sample-alex", None),
        ]:
            with self.subTest(method=method):
                self.assertEqual(self.client.request(method, path, json=body).status_code, 503)

    def test_openapi_exposes_crud_models_and_statuses(self):
        paths = self.client.get("/openapi.json").json()["paths"]
        self.assertIn("201", paths["/profiles"]["post"]["responses"])
        operations = paths["/profiles/{profile_id}"]
        self.assertTrue({"get", "patch", "delete"}.issubset(operations))
        self.assertNotIn("content", operations["delete"]["responses"]["204"])
