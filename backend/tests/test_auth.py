import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

from auth import SESSION_SECONDS, get_current_user, limit_attempts, password_hasher, token_digest
from database import ensure_indexes, get_database
from main import app
from sample_data import profiles


class AuthenticationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = "example-test-passphrase"
        cls.password_hash = password_hasher.hash(cls.password)

    def setUp(self):
        self.settings = patch("database.database_settings", return_value=("", "test"))
        self.settings.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.database = MagicMock()
        self.user = {
            "_id": "user-one", "name": "Example User", "email": "user@example.com",
            "password_hash": self.password_hash, "is_active": True,
            "created_at": datetime.now(timezone.utc),
        }
        self.database.users.find_one = AsyncMock(return_value=self.user)
        self.database.users.insert_one = AsyncMock()
        self.database.sessions.find_one = AsyncMock(return_value={
            "user_id": self.user["_id"], "expires_at": datetime.now(timezone.utc) + timedelta(hours=1),
        })
        self.database.sessions.insert_one = AsyncMock()
        self.database.sessions.delete_one = AsyncMock()
        self.database.auth_attempts.find_one_and_update = AsyncMock(return_value={"count": 1})
        self.database.profiles.insert_one = AsyncMock()
        self.database.profiles.find_one = AsyncMock(return_value=None)
        self.database.profiles.find_one_and_update = AsyncMock(return_value=None)
        self.database.profiles.delete_one = AsyncMock(return_value=SimpleNamespace(deleted_count=0))
        app.dependency_overrides[get_database] = lambda: self.database
        self.headers = {"Authorization": "Bearer test-session-token"}
        self.signup_data = {"email": "user@example.com", "password": self.password, "name": "Example User"}
        self.profile = {k: v for k, v in profiles[0].items() if k != "_id"}

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def test_signup_hashes_password_and_never_returns_secrets(self):
        response = self.client.post("/auth/signup", json={**self.signup_data, "email": "USER@example.com"})
        self.assertEqual(response.status_code, 201)
        stored = self.database.users.insert_one.call_args.args[0]
        self.assertEqual(stored["email"], "user@example.com")
        self.assertTrue(stored["password_hash"].startswith("$argon2id$"))
        self.assertTrue(password_hasher.verify(self.password, stored["password_hash"]))
        self.assertNotIn("password", stored)
        self.assertEqual(set(response.json()), {"id", "name", "email", "created_at"})
        self.assertNotIn(self.password, response.text)
        self.assertNotIn(stored["password_hash"], response.text)

    def test_duplicate_signup_returns_409(self):
        self.database.users.insert_one.side_effect = DuplicateKeyError("duplicate")
        self.assertEqual(self.client.post("/auth/signup", json=self.signup_data).status_code, 409)

    def test_invalid_signup_and_escalation_fields_are_rejected_without_echoing_password(self):
        cases = [
            {"password": "too-short"}, {"password": " " * 12}, {"password": "x" * 129},
            {"password": 123}, {"email": "not-email"}, {"name": " "},
            {"is_active": True}, {"role": "admin"}, {"_id": "chosen"},
        ]
        for changes in cases:
            with self.subTest(changes=changes):
                response = self.client.post("/auth/signup", json={**self.signup_data, **changes})
                self.assertEqual(response.status_code, 422)
                self.assertNotIn('"input"', response.text)
                self.assertNotIn(self.password, response.text)
        self.database.users.insert_one.assert_not_awaited()

    def test_login_issues_token_but_stores_only_its_hash(self):
        response = self.client.post("/auth/login", json={"email": "USER@example.com", "password": self.password})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        token = data["access_token"]
        self.assertEqual(len(token), 43)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["expires_in"], SESSION_SECONDS)
        self.assertEqual(response.headers["cache-control"], "no-store")
        stored = self.database.sessions.insert_one.call_args.args[0]
        self.assertEqual(stored["token_hash"], token_digest(token))
        self.assertNotIn(token, str(stored))
        self.assertEqual(stored["user_id"], self.user["_id"])
        self.assertGreater(stored["expires_at"], datetime.now(timezone.utc))
        self.database.users.find_one.assert_awaited_once_with({"email": "user@example.com"})

    def test_wrong_password_unknown_email_and_disabled_account_share_error(self):
        responses = []
        responses.append(self.client.post("/auth/login", json={"email": "user@example.com", "password": "wrong"}))
        self.database.users.find_one.return_value = None
        responses.append(self.client.post("/auth/login", json={"email": "missing@example.com", "password": self.password}))
        self.database.users.find_one.return_value = {**self.user, "is_active": False}
        responses.append(self.client.post("/auth/login", json={"email": "user@example.com", "password": self.password}))
        for response in responses:
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json(), responses[0].json())
        self.database.sessions.insert_one.assert_not_awaited()

    def test_all_platform_routes_reject_anonymous_requests(self):
        for method, path, data in [
            ("GET", "/profiles", None), ("GET", "/profiles/sample", None),
            ("GET", "/profiles/me", None), ("GET", "/profiles/sample-alex", None),
            ("POST", "/profiles", self.profile), ("POST", "/profiles/validate", self.profile),
            ("PATCH", "/profiles/sample-alex", {"name": "Changed"}),
            ("DELETE", "/profiles/sample-alex", None), ("GET", "/health/database", None),
            ("GET", "/auth/me", None), ("POST", "/auth/logout", None),
        ]:
            with self.subTest(method=method, path=path):
                response = self.client.request(method, path, json=data)
                self.assertEqual(response.status_code, 401)
                self.assertEqual(response.headers["www-authenticate"], "Bearer")
        self.database.sessions.find_one.assert_not_awaited()

    def test_anonymous_requests_fail_before_missing_database_configuration(self):
        app.dependency_overrides.clear()
        self.assertEqual(self.client.get("/profiles").status_code, 401)

    def test_public_home_and_docs_remain_accessible(self):
        for path in ("/", "/docs", "/openapi.json"):
            self.assertEqual(self.client.get(path).status_code, 200)

    def test_invalid_or_expired_token_returns_401(self):
        self.database.sessions.find_one.return_value = None
        response = self.client.get("/auth/me", headers=self.headers)
        self.assertEqual(response.status_code, 401)
        query = self.database.sessions.find_one.call_args.args[0]
        self.assertEqual(query["token_hash"], token_digest("test-session-token"))
        self.assertIn("$gt", query["expires_at"])
        self.database.users.find_one.assert_not_awaited()

    def test_wrong_scheme_and_oversized_tokens_are_rejected(self):
        for authorization in ("Basic credentials", "Bearer " + "x" * 257):
            self.assertEqual(self.client.get("/auth/me", headers={"Authorization": authorization}).status_code, 401)
        self.database.sessions.find_one.assert_not_awaited()

    def test_valid_session_requires_an_existing_active_account(self):
        self.database.users.find_one.return_value = None
        self.assertEqual(self.client.get("/auth/me", headers=self.headers).status_code, 401)
        self.assertEqual(self.database.users.find_one.call_args.args[0], {"_id": "user-one", "is_active": True})

    def test_me_excludes_private_account_fields(self):
        response = self.client.get("/auth/me", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(set(response.json()), {"id", "name", "email", "created_at"})

    def test_logout_revokes_only_current_session(self):
        response = self.client.post("/auth/logout", headers=self.headers)
        self.assertEqual(response.status_code, 204)
        self.database.sessions.delete_one.assert_awaited_once_with({
            "token_hash": token_digest("test-session-token"), "user_id": "user-one",
        })
        self.database.sessions.find_one.return_value = None
        self.assertEqual(self.client.get("/auth/me", headers=self.headers).status_code, 401)

    def test_new_profile_belongs_to_authenticated_user(self):
        response = self.client.post("/profiles", json=self.profile, headers=self.headers)
        self.assertEqual(response.status_code, 201)
        stored = self.database.profiles.insert_one.call_args.args[0]
        self.assertEqual(stored["owner_user_id"], "user-one")
        self.assertNotIn("owner_user_id", response.json())

    def test_client_cannot_assign_or_change_ownership(self):
        for method, path, data in [
            ("POST", "/profiles", {**self.profile, "owner_user_id": "user-two"}),
            ("PATCH", "/profiles/target", {"owner_user_id": "user-two"}),
        ]:
            self.assertEqual(self.client.request(method, path, json=data, headers=self.headers).status_code, 422)
        self.database.profiles.insert_one.assert_not_awaited()
        self.database.profiles.find_one_and_update.assert_not_awaited()

    def test_duplicate_owned_profile_returns_409(self):
        self.database.profiles.insert_one.side_effect = DuplicateKeyError("duplicate owner")
        self.assertEqual(self.client.post("/profiles", json=self.profile, headers=self.headers).status_code, 409)

    def test_update_and_delete_are_scoped_to_current_owner(self):
        response = self.client.patch("/profiles/other-profile", json={"name": "Changed"}, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.database.profiles.find_one_and_update.call_args.args[0], {
            "_id": "other-profile", "owner_user_id": "user-one",
        })
        response = self.client.delete("/profiles/other-profile", headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.database.profiles.delete_one.assert_awaited_once_with({
            "_id": "other-profile", "owner_user_id": "user-one",
        })

    def test_me_profile_looks_up_owner_not_literal_me_id(self):
        self.database.profiles.find_one.return_value = profiles[0]
        response = self.client.get("/profiles/me", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.database.profiles.find_one.call_args.args[0], {"owner_user_id": "user-one"})

    def test_me_profile_reports_missing_profile(self):
        self.assertEqual(self.client.get("/profiles/me", headers=self.headers).status_code, 404)

    def test_throttling_blocks_login_before_password_verification(self):
        self.database.auth_attempts.find_one_and_update.return_value = {"count": 11}
        response = self.client.post("/auth/login", json={"email": "user@example.com", "password": self.password})
        self.assertEqual(response.status_code, 429)
        self.assertGreater(int(response.headers["retry-after"]), 0)
        self.database.users.find_one.assert_not_awaited()
        self.database.sessions.insert_one.assert_not_awaited()

    def test_throttling_blocks_signup_before_hashing(self):
        self.database.auth_attempts.find_one_and_update.return_value = {"count": 6}
        self.assertEqual(self.client.post("/auth/signup", json=self.signup_data).status_code, 429)
        self.database.users.insert_one.assert_not_awaited()

    def test_swagger_marks_every_platform_endpoint_protected(self):
        schema = self.client.get("/openapi.json").json()
        self.assertEqual(schema["components"]["securitySchemes"]["HTTPBearer"]["scheme"], "bearer")
        for path, operations in schema["paths"].items():
            for method, operation in operations.items():
                if path.startswith("/profiles") or path in ("/health/database", "/auth/me", "/auth/logout"):
                    with self.subTest(path=path, method=method):
                        self.assertEqual(operation["security"], [{"HTTPBearer": []}])
        self.assertNotIn("security", schema["paths"]["/auth/signup"]["post"])


class IndexTests(unittest.IsolatedAsyncioTestCase):
    async def test_indexes_enforce_uniqueness_and_expiry_without_claiming_seed_profiles(self):
        database = MagicMock()
        for name in ("users", "sessions", "auth_attempts", "profiles"):
            getattr(database, name).create_index = AsyncMock()
        await ensure_indexes(database)
        database.users.create_index.assert_awaited_once_with("email", unique=True, name="users_email_unique")
        database.sessions.create_index.assert_any_await("expires_at", expireAfterSeconds=0, name="sessions_expiry")
        database.profiles.create_index.assert_awaited_once_with(
            "owner_user_id", unique=True, name="profiles_owner_unique",
            partialFilterExpression={"owner_user_id": {"$type": "string"}},
        )

    async def test_concurrent_rate_counter_creation_is_retried(self):
        database = MagicMock()
        database.auth_attempts.find_one_and_update = AsyncMock(side_effect=[DuplicateKeyError("race"), {"count": 2}])
        request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
        await limit_attempts(request, database, "login", 10, 900)
        self.assertEqual(database.auth_attempts.find_one_and_update.await_count, 2)
