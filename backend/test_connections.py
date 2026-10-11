import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from auth import get_current_user
from database import get_database
from main import app

ME = {"name": "Alex Morgan", "affiliation": "CWRU alumni", "location": "Cleveland, Ohio",
      "expertise": ["Software engineering"], "interests": ["Healthcare technology"]}
THEM = {"name": "Taylor Rivera", "affiliation": "CWRU alumni", "location": "Cleveland, Ohio",
        "expertise": ["Medical devices"], "interests": ["Healthcare technology"]}


class ConnectionTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch("database.database_settings", return_value=("", "test"))
        self.settings.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.mine = {"_id": "profile-me", "owner_user_id": "user-me", **ME}
        self.theirs = {"_id": "profile-them", "owner_user_id": "user-them", **THEM}
        self.database = MagicMock()

        async def find_profile(query, projection=None):
            if query.get("owner_user_id") == "user-me" or query.get("_id") == "profile-me":
                return self.mine
            if query.get("owner_user_id") == "user-them" or query.get("_id") == "profile-them":
                return self.theirs
            return self.demo if query.get("_id") == "sample-alex" else None

        self.demo = {"_id": "sample-alex", **ME}  # a demo profile has no owner
        self.database.profiles.find_one = AsyncMock(side_effect=find_profile)
        self.database.connections.insert_one = AsyncMock()
        self.database.connections.find_one_and_update = AsyncMock(return_value=None)
        app.dependency_overrides[get_database] = lambda: self.database
        app.dependency_overrides[get_current_user] = lambda: {"_id": "user-me"}
        self.notify_request = patch("connections.notify_connection_request", new=AsyncMock())
        self.notify_accept = patch("connections.notify_connection_accepted", new=AsyncMock())
        self.sent = self.notify_request.start()
        self.accepted = self.notify_accept.start()

    def tearDown(self):
        self.notify_request.stop()
        self.notify_accept.stop()
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def pending(self, **changes):
        return {
            "_id": "conn-1", "pair_key": "user-me|user-them", "sender_user_id": "user-them",
            "recipient_user_id": "user-me", "status": "pending", "message": None,
            "created_at": datetime.now(timezone.utc), "responded_at": None, **changes,
        }

    def test_send_request_stores_pair_and_queues_one_email(self):
        response = self.client.post("/connections", json={"profile_id": "profile-them", "message": " Hi! "})
        self.assertEqual(response.status_code, 201)
        stored = self.database.connections.insert_one.call_args.args[0]
        self.assertEqual(stored["pair_key"], "user-me|user-them")
        self.assertEqual((stored["sender_user_id"], stored["recipient_user_id"]), ("user-me", "user-them"))
        self.assertEqual((stored["status"], stored["message"]), ("pending", "Hi!"))
        data = response.json()
        self.assertEqual((data["direction"], data["status"]), ("outgoing", "pending"))
        self.assertEqual(data["profile"]["id"], "profile-them")
        self.assertNotIn("owner_user_id", response.text)
        self.assertNotIn("user-them", response.text)
        self.sent.assert_awaited_once_with(self.database, stored["_id"])

    def test_pair_key_is_the_same_in_both_directions(self):
        from connections import pair_key
        self.assertEqual(pair_key("a", "b"), pair_key("b", "a"))

    def test_sender_needs_their_own_profile(self):
        self.mine = None
        self.assertEqual(self.client.post("/connections", json={"profile_id": "profile-them"}).status_code, 409)
        self.database.connections.insert_one.assert_not_awaited()

    def test_unknown_demo_and_own_profiles_are_rejected(self):
        for profile_id, status in [("missing", 404), ("sample-alex", 409), ("profile-me", 400)]:
            with self.subTest(profile_id=profile_id):
                response = self.client.post("/connections", json={"profile_id": profile_id})
                self.assertEqual(response.status_code, status)
        self.database.connections.insert_one.assert_not_awaited()
        self.sent.assert_not_awaited()

    def test_duplicate_pair_returns_409_and_sends_no_email(self):
        self.database.connections.insert_one.side_effect = DuplicateKeyError("pair")
        self.assertEqual(self.client.post("/connections", json={"profile_id": "profile-them"}).status_code, 409)
        self.sent.assert_not_awaited()

    def test_invalid_bodies_never_write(self):
        for body in ({}, {"profile_id": " "}, {"profile_id": "profile-them", "message": " "},
                     {"profile_id": "profile-them", "message": "x" * 301},
                     {"profile_id": "profile-them", "sender_user_id": "other"},
                     {"profile_id": "profile-them", "status": "accepted"}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/connections", json=body).status_code, 422)
        self.database.connections.insert_one.assert_not_awaited()

    def test_list_shows_direction_and_the_other_persons_public_profile(self):
        documents = [self.pending(), self.pending(
            _id="conn-2", sender_user_id="user-me", recipient_user_id="user-them", status="accepted",
        )]
        cursor = self.database.connections.find.return_value.sort.return_value.limit.return_value
        cursor.to_list = AsyncMock(return_value=documents)
        self.database.profiles.find.return_value.to_list = AsyncMock(return_value=[self.theirs])
        response = self.client.get("/connections", params={"status": "pending"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([(c["id"], c["direction"]) for c in response.json()],
                         [("conn-1", "incoming"), ("conn-2", "outgoing")])
        self.assertEqual(response.json()[0]["profile"]["name"], "Taylor Rivera")
        self.assertNotIn("user-them", response.text)
        query = self.database.connections.find.call_args.args[0]
        self.assertEqual(query["status"], "pending")
        self.assertEqual(query["$or"], [{"sender_user_id": "user-me"}, {"recipient_user_id": "user-me"}])

    def test_empty_list_skips_profile_lookup(self):
        cursor = self.database.connections.find.return_value.sort.return_value.limit.return_value
        cursor.to_list = AsyncMock(return_value=[])
        self.assertEqual(self.client.get("/connections").json(), [])
        self.database.profiles.find.assert_not_called()

    def test_accept_updates_only_my_pending_request_and_emails_the_sender(self):
        self.database.connections.find_one_and_update.return_value = self.pending(status="accepted")
        response = self.client.patch("/connections/conn-1", json={"status": "accepted"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "accepted")
        call = self.database.connections.find_one_and_update.call_args
        self.assertEqual(call.args[0], {"_id": "conn-1", "recipient_user_id": "user-me", "status": "pending"})
        self.assertEqual(call.args[1]["$set"]["status"], "accepted")
        self.assertEqual(call.kwargs["return_document"], ReturnDocument.AFTER)
        self.accepted.assert_awaited_once_with(self.database, "conn-1")

    def test_decline_sends_no_email(self):
        self.database.connections.find_one_and_update.return_value = self.pending(status="declined")
        self.assertEqual(self.client.patch("/connections/conn-1", json={"status": "declined"}).status_code, 200)
        self.accepted.assert_not_awaited()

    def test_responding_to_someone_elses_or_settled_request_returns_404(self):
        response = self.client.patch("/connections/conn-1", json={"status": "accepted"})
        self.assertEqual(response.status_code, 404)
        self.accepted.assert_not_awaited()

    def test_only_accepted_or_declined_are_valid_responses(self):
        for body in ({}, {"status": "pending"}, {"status": "withdrawn"}, {"status": "accepted", "x": 1}):
            with self.subTest(body=body):
                self.assertEqual(self.client.patch("/connections/conn-1", json=body).status_code, 422)
        self.database.connections.find_one_and_update.assert_not_awaited()
