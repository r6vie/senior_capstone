import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

import linkedin_auth
from auth import SESSION_SECONDS, token_digest
from database import get_database
from main import app

SETTINGS = {
    "client_id": "client-id", "client_secret": "client-secret",
    "redirect_uri": "http://127.0.0.1:5173/api/auth/linkedin/callback",
    "frontend_url": "http://127.0.0.1:5173",
}
MEMBER = {
    "sub": "linkedin-sub-1", "name": "Jane Founder", "given_name": "Jane", "family_name": "Founder",
    "email": "Jane@Example.com", "email_verified": True, "picture": "https://media.licdn.com/jane.jpg",
    "locale": {"country": "US", "language": "en"},
}


def location_query(response):
    return parse_qs(urlparse(response.headers["location"]).query)


class LinkedInSignInTests(unittest.TestCase):
    def setUp(self):
        patches = [
            patch("database.database_settings", return_value=("", "test")),
            patch("linkedin_auth.linkedin_settings", return_value=dict(SETTINGS)),
            patch("linkedin_auth.notify_welcome", new=AsyncMock()),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        self.client = TestClient(app, follow_redirects=False)
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)
        self.addCleanup(app.dependency_overrides.clear)

        self.database = MagicMock()
        self.database.auth_attempts.find_one_and_update = AsyncMock(return_value={"count": 1})
        self.database.oauth_states.insert_one = AsyncMock()
        self.database.oauth_states.find_one_and_delete = AsyncMock(return_value={"_id": "saved"})
        self.database.login_codes.insert_one = AsyncMock()
        self.database.login_codes.find_one_and_delete = AsyncMock(return_value=None)
        self.database.users.find_one = AsyncMock(return_value=None)
        self.database.users.insert_one = AsyncMock()
        self.database.users.update_one = AsyncMock()
        self.database.sessions.insert_one = AsyncMock()
        app.dependency_overrides[get_database] = lambda: self.database

    def sign_in(self, member=MEMBER, state="state-value"):
        """Run the callback as if LinkedIn returned `member` for a valid sign-in attempt."""
        self.client.cookies.set(linkedin_auth.STATE_COOKIE, state)
        with patch("linkedin_auth.fetch_linkedin_member", AsyncMock(return_value=member)):
            return self.client.get("/auth/linkedin/callback", params={"code": "abc", "state": state})

    def assertFailed(self, response, error):
        self.assertEqual(response.status_code, 303)
        self.assertTrue(response.headers["location"].startswith("http://127.0.0.1:5173/signup?"))
        self.assertEqual(location_query(response)["error"], [error])

    # --- starting ---------------------------------------------------------------------------

    def test_start_redirects_to_linkedin_with_state_bound_to_a_cookie(self):
        response = self.client.get("/auth/linkedin/start")
        self.assertEqual(response.status_code, 303)
        target = urlparse(response.headers["location"])
        self.assertEqual(f"{target.scheme}://{target.netloc}{target.path}", linkedin_auth.AUTHORIZE_URL)
        query = location_query(response)
        self.assertEqual(query["client_id"], ["client-id"])
        self.assertEqual(query["response_type"], ["code"])
        self.assertEqual(query["scope"], ["openid profile email"])
        self.assertEqual(query["redirect_uri"], [SETTINGS["redirect_uri"]])
        state = query["state"][0]
        self.assertGreaterEqual(len(state), 32)
        self.assertEqual(self.client.cookies.get(linkedin_auth.STATE_COOKIE), state)
        cookie = response.headers["set-cookie"].lower()
        self.assertIn("httponly", cookie)
        self.assertIn("samesite=lax", cookie)
        stored = self.database.oauth_states.insert_one.call_args.args[0]
        self.assertEqual(stored["_id"], token_digest(state))
        self.assertNotIn(state, str(stored))
        self.assertNotIn("client-secret", response.headers["location"])

    def test_start_without_linkedin_credentials_explains_instead_of_redirecting_away(self):
        with patch("linkedin_auth.linkedin_settings", return_value={**SETTINGS, "client_id": "", "client_secret": ""}):
            self.assertFailed(self.client.get("/auth/linkedin/start"), "not_configured")
        self.database.oauth_states.insert_one.assert_not_awaited()

    def test_start_is_rate_limited(self):
        self.database.auth_attempts.find_one_and_update.return_value = {"count": 21}
        self.assertFailed(self.client.get("/auth/linkedin/start"), "too_many_attempts")
        self.database.oauth_states.insert_one.assert_not_awaited()

    # --- callback: forged or stale requests --------------------------------------------------

    def test_callback_rejects_missing_or_mismatched_state_cookie(self):
        self.client.cookies.clear()
        with patch("linkedin_auth.fetch_linkedin_member", AsyncMock()) as fetch:
            self.assertFailed(self.client.get("/auth/linkedin/callback", params={"code": "abc", "state": "s"}), "invalid_state")
            self.client.cookies.set(linkedin_auth.STATE_COOKIE, "other-browser")
            self.assertFailed(self.client.get("/auth/linkedin/callback", params={"code": "abc", "state": "s"}), "invalid_state")
            fetch.assert_not_awaited()
        self.database.users.insert_one.assert_not_awaited()

    def test_callback_rejects_unknown_expired_or_reused_state(self):
        self.database.oauth_states.find_one_and_delete.return_value = None
        with patch("linkedin_auth.fetch_linkedin_member", AsyncMock()) as fetch:
            self.client.cookies.set(linkedin_auth.STATE_COOKIE, "state-value")
            self.assertFailed(self.client.get("/auth/linkedin/callback", params={"code": "abc", "state": "state-value"}), "invalid_state")
            fetch.assert_not_awaited()
        query = self.database.oauth_states.find_one_and_delete.call_args.args[0]
        self.assertEqual(query["_id"], token_digest("state-value"))
        self.assertIn("$gt", query["expires_at"])

    def test_declined_consent_reports_cancellation(self):
        self.client.cookies.set(linkedin_auth.STATE_COOKIE, "state-value")
        response = self.client.get("/auth/linkedin/callback", params={"error": "user_cancelled_login", "state": "state-value"})
        self.assertFailed(response, "cancelled")
        self.database.users.insert_one.assert_not_awaited()

    def test_linkedin_failures_never_leak_details(self):
        self.client.cookies.set(linkedin_auth.STATE_COOKIE, "state-value")
        failure = AsyncMock(side_effect=linkedin_auth.LinkedInError("linkedin_failed"))
        with patch("linkedin_auth.fetch_linkedin_member", failure):
            response = self.client.get("/auth/linkedin/callback", params={"code": "abc", "state": "state-value"})
        self.assertFailed(response, "linkedin_failed")
        self.assertNotIn("client-secret", response.headers["location"])

    # --- callback: accounts ------------------------------------------------------------------

    def test_first_sign_in_creates_an_account_without_a_password(self):
        response = self.sign_in()
        self.assertEqual(response.status_code, 303)
        user = self.database.users.insert_one.call_args.args[0]
        self.assertEqual(user["email"], "jane@example.com")
        self.assertEqual(user["name"], "Jane Founder")
        self.assertEqual(user["linkedin_sub"], "linkedin-sub-1")
        self.assertTrue(user["is_active"])
        self.assertNotIn("password_hash", user)
        # The details LinkedIn shared are kept, to build AI-written profiles later.
        self.assertEqual(user["linkedin"]["picture"], MEMBER["picture"])
        self.assertEqual(user["linkedin"]["given_name"], "Jane")
        self.assertIs(user["linkedin"]["email_verified"], True)
        code = location_query(response)["code"][0]
        self.assertTrue(response.headers["location"].startswith("http://127.0.0.1:5173/auth/linkedin?"))
        saved = self.database.login_codes.insert_one.call_args.args[0]
        self.assertEqual(saved["_id"], token_digest(code))
        self.assertNotIn(code, str(saved))
        self.assertEqual((saved["user_id"], saved["is_new"]), (user["_id"], True))
        self.assertNotIn("access_token", response.headers["location"])
        self.assertEqual(response.headers["cache-control"], "no-store")

    def test_returning_member_is_found_by_linkedin_id_and_details_refreshed(self):
        existing = {"_id": "user-1", "email": "jane@example.com", "linkedin_sub": "linkedin-sub-1", "is_active": True}
        self.database.users.find_one.return_value = existing
        response = self.sign_in()
        self.assertEqual(self.database.users.find_one.call_args.args[0], {"linkedin_sub": "linkedin-sub-1"})
        self.database.users.insert_one.assert_not_awaited()
        update = self.database.users.update_one.call_args
        self.assertEqual(update.args[0], {"_id": "user-1"})
        self.assertNotIn("linkedin_sub", update.args[1]["$set"])
        saved = self.database.login_codes.insert_one.call_args.args[0]
        self.assertEqual((saved["user_id"], saved["is_new"]), ("user-1", False))
        self.assertIn("code", location_query(response))

    def test_existing_password_account_is_linked_by_verified_email(self):
        existing = {"_id": "user-1", "email": "jane@example.com", "password_hash": "x", "is_active": True}
        self.database.users.find_one.side_effect = [None, existing]
        self.sign_in()
        self.assertEqual(self.database.users.find_one.call_args_list[1].args[0], {"email": "jane@example.com"})
        self.database.users.insert_one.assert_not_awaited()
        self.assertEqual(self.database.users.update_one.call_args.args[1]["$set"]["linkedin_sub"], "linkedin-sub-1")
        self.assertIs(self.database.login_codes.insert_one.call_args.args[0]["is_new"], False)

    def test_unverified_email_is_never_used_to_claim_an_existing_account(self):
        response = self.sign_in({**MEMBER, "email_verified": False})
        self.assertFailed(response, "email_unverified")
        self.assertEqual(self.database.users.find_one.await_count, 1)
        self.database.users.update_one.assert_not_awaited()
        self.database.users.insert_one.assert_not_awaited()

    def test_disabled_accounts_cannot_sign_in(self):
        self.database.users.find_one.return_value = {"_id": "user-1", "linkedin_sub": "linkedin-sub-1", "is_active": False}
        self.assertFailed(self.sign_in(), "account_disabled")
        self.database.login_codes.insert_one.assert_not_awaited()

    def test_member_without_an_email_cannot_sign_up(self):
        self.assertFailed(self.sign_in({k: v for k, v in MEMBER.items() if k != "email"}), "missing_email")
        self.assertFailed(self.sign_in({k: v for k, v in MEMBER.items() if k != "sub"}), "missing_email")
        self.database.users.insert_one.assert_not_awaited()

    def test_missing_name_falls_back_to_the_email_prefix(self):
        self.sign_in({k: v for k, v in MEMBER.items() if k != "name"})
        self.assertEqual(self.database.users.insert_one.call_args.args[0]["name"], "jane")

    def test_race_creating_the_same_account_fails_cleanly(self):
        self.database.users.insert_one.side_effect = DuplicateKeyError("duplicate")
        self.assertFailed(self.sign_in(), "linkedin_failed")

    # --- exchanging the one-time code ------------------------------------------------------

    def test_exchange_turns_a_one_time_code_into_a_session(self):
        self.database.login_codes.find_one_and_delete.return_value = {"user_id": "user-1", "is_new": True}
        self.database.users.find_one.return_value = {"_id": "user-1"}
        response = self.client.post("/auth/linkedin/exchange", json={"code": "one-time"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["is_new"], True)
        self.assertEqual(data["token_type"], "bearer")
        self.assertEqual(data["expires_in"], SESSION_SECONDS)
        self.assertEqual(response.headers["cache-control"], "no-store")
        query = self.database.login_codes.find_one_and_delete.call_args.args[0]
        self.assertEqual(query["_id"], token_digest("one-time"))
        self.assertIn("$gt", query["expires_at"])
        stored = self.database.sessions.insert_one.call_args.args[0]
        self.assertEqual(stored["token_hash"], token_digest(data["access_token"]))
        self.assertEqual(stored["user_id"], "user-1")
        self.assertGreater(stored["expires_at"], datetime.now(timezone.utc))

    def test_exchange_rejects_unknown_expired_or_used_codes(self):
        response = self.client.post("/auth/linkedin/exchange", json={"code": "used"})
        self.assertEqual(response.status_code, 400)
        self.database.sessions.insert_one.assert_not_awaited()

    def test_exchange_rejects_codes_for_deactivated_users(self):
        self.database.login_codes.find_one_and_delete.return_value = {"user_id": "user-1", "is_new": False}
        self.database.users.find_one.return_value = None
        self.assertEqual(self.client.post("/auth/linkedin/exchange", json={"code": "one-time"}).status_code, 400)
        self.database.sessions.insert_one.assert_not_awaited()

    def test_exchange_validates_and_throttles(self):
        for body in ({}, {"code": ""}, {"code": 5}, {"code": "x" * 257}, {"code": "a", "extra": 1}):
            self.assertEqual(self.client.post("/auth/linkedin/exchange", json=body).status_code, 422)
        self.database.auth_attempts.find_one_and_update.return_value = {"count": 21}
        self.assertEqual(self.client.post("/auth/linkedin/exchange", json={"code": "a"}).status_code, 429)
        self.database.login_codes.find_one_and_delete.assert_not_awaited()


class LinkedInRequestTests(unittest.IsolatedAsyncioTestCase):
    """The two calls to LinkedIn, with its servers replaced by canned answers."""

    async def run_flow(self, handler):
        import httpx

        transport = httpx.MockTransport(handler)
        real = httpx.AsyncClient
        with patch("linkedin_auth.httpx.AsyncClient", lambda **kw: real(transport=transport, **kw)):
            return await linkedin_auth.fetch_linkedin_member("the-code", SETTINGS)

    async def test_code_is_traded_for_member_details(self):
        import httpx

        seen = {}

        def handler(request):
            if request.url.path.endswith("/accessToken"):
                seen["form"] = parse_qs(request.content.decode())
                return httpx.Response(200, json={"access_token": "member-token"})
            seen["authorization"] = request.headers["authorization"]
            return httpx.Response(200, json=MEMBER)

        self.assertEqual(await self.run_flow(handler), MEMBER)
        self.assertEqual(seen["form"]["grant_type"], ["authorization_code"])
        self.assertEqual(seen["form"]["code"], ["the-code"])
        self.assertEqual(seen["form"]["redirect_uri"], [SETTINGS["redirect_uri"]])
        self.assertEqual(seen["authorization"], "Bearer member-token")

    async def test_linkedin_errors_become_a_generic_failure(self):
        import httpx

        for handler in (
            lambda request: httpx.Response(401, json={"error": "invalid_client", "secret": "client-secret"}),
            lambda request: httpx.Response(200, json={"unexpected": True}),
            lambda request: httpx.Response(200, text="not json"),
        ):
            with self.assertRaises(linkedin_auth.LinkedInError) as caught:
                await self.run_flow(handler)
            self.assertEqual(caught.exception.code, "linkedin_failed")


if __name__ == "__main__":
    unittest.main()
