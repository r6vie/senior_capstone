import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from auth import get_current_user
from connection_models import REQUEST_TYPE_LABELS
from connections import MAX_MESSAGES_PER_THREAD, MAX_REQUESTS_PER_DAY
from database import get_database
from main import app

ME = {"name": "Alex Morgan", "affiliation": "CWRU alumni", "location": "Cleveland, Ohio",
      "expertise": ["Software engineering"], "interests": ["Healthcare technology"]}
THEM = {"name": "Taylor Rivera", "affiliation": "CWRU alumni", "location": "Cleveland, Ohio",
        "expertise": ["Medical devices"], "interests": ["Healthcare technology"]}


class ApiCase(unittest.TestCase):
    """Shared setup: signed in as user-me, with a mocked database."""

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
        self.database.connections.count_documents = AsyncMock(return_value=0)
        self.database.connections.find_one = AsyncMock(return_value=None)
        self.database.connections.find_one_and_update = AsyncMock(return_value=None)
        self.database.messages.insert_one = AsyncMock()
        self.database.messages.count_documents = AsyncMock(return_value=0)
        self.database.messages.find_one = AsyncMock(return_value=None)
        self.database.users.find_one = AsyncMock(return_value={"_id": "user-them", "email": "taylor@example.com"})
        app.dependency_overrides[get_database] = lambda: self.database
        app.dependency_overrides[get_current_user] = lambda: {"_id": "user-me"}
        self.patches = [
            patch("connections.notify_connection_request", new=AsyncMock()),
            patch("connections.notify_connection_accepted", new=AsyncMock()),
            patch("connections.notify_new_message", new=AsyncMock()),
        ]
        self.sent, self.accepted, self.messaged = [p.start() for p in self.patches]

    def tearDown(self):
        for p in self.patches:
            p.stop()
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def body(self, **changes):
        return {"profile_id": "profile-them", "type": "mentorship",
                "message": "Could you mentor me this semester?", **changes}

    def pending(self, **changes):
        """By default Taylor (user-them) asked me (user-me)."""
        return {
            "_id": "conn-1", "pair_key": "user-me|user-them", "sender_user_id": "user-them",
            "recipient_user_id": "user-me", "status": "pending", "type": "mentorship",
            "message": "Please mentor me", "created_at": datetime.now(timezone.utc),
            "responded_at": None, **changes,
        }

    def i_asked(self, **changes):
        return self.pending(sender_user_id="user-me", recipient_user_id="user-them", **changes)


class ConnectionTests(ApiCase):
    # ---- sending --------------------------------------------------------------------------

    def test_send_request_stores_type_and_message_and_queues_one_email(self):
        response = self.client.post("/connections", json=self.body(message="  Hi! Mentor me?  "))
        self.assertEqual(response.status_code, 201)
        stored = self.database.connections.insert_one.call_args.args[0]
        self.assertEqual(stored["pair_key"], "user-me|user-them")
        self.assertEqual((stored["sender_user_id"], stored["recipient_user_id"]), ("user-me", "user-them"))
        self.assertEqual((stored["status"], stored["type"], stored["message"]), ("pending", "mentorship", "Hi! Mentor me?"))
        data = response.json()
        self.assertEqual((data["direction"], data["status"], data["type"]), ("outgoing", "pending", "mentorship"))
        self.assertEqual(data["profile"]["id"], "profile-them")
        self.assertIsNone(data["contact_email"])
        self.assertNotIn("owner_user_id", response.text)
        self.assertNotIn("user-them", response.text)
        self.assertNotIn("taylor@example.com", response.text)
        self.sent.assert_awaited_once_with(self.database, stored["_id"])

    def test_every_listed_type_can_be_sent(self):
        for value in REQUEST_TYPE_LABELS:
            with self.subTest(type=value):
                self.assertEqual(self.client.post("/connections", json=self.body(type=value)).status_code, 201)

    def test_pair_key_is_the_same_in_both_directions(self):
        from connections import pair_key
        self.assertEqual(pair_key("a", "b"), pair_key("b", "a"))

    def test_sender_needs_their_own_profile(self):
        self.mine = None
        self.assertEqual(self.client.post("/connections", json=self.body()).status_code, 409)
        self.database.connections.insert_one.assert_not_awaited()

    def test_unknown_demo_and_own_profiles_are_rejected(self):
        for profile_id, status in [("missing", 404), ("sample-alex", 409), ("profile-me", 400)]:
            with self.subTest(profile_id=profile_id):
                self.assertEqual(self.client.post("/connections", json=self.body(profile_id=profile_id)).status_code, status)
        self.database.connections.insert_one.assert_not_awaited()
        self.sent.assert_not_awaited()

    def test_duplicate_pair_returns_409_and_sends_no_email(self):
        self.database.connections.insert_one.side_effect = DuplicateKeyError("pair")
        self.assertEqual(self.client.post("/connections", json=self.body()).status_code, 409)
        self.sent.assert_not_awaited()

    def test_type_and_message_are_required_and_checked(self):
        bad = [
            {"profile_id": "profile-them", "message": "Hi"},                    # no type
            {"profile_id": "profile-them", "type": "mentorship"},               # no message
            self.body(type="friendship"), self.body(type=None), self.body(type=1),
            self.body(message=" "), self.body(message=""), self.body(message="x" * 1001),
            self.body(message=None), self.body(profile_id=" "),
            self.body(sender_user_id="other"), self.body(status="accepted"),
        ]
        for body in bad:
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/connections", json=body).status_code, 422)
        self.assertEqual(self.client.post("/connections", json={}).status_code, 422)
        self.database.connections.insert_one.assert_not_awaited()

    def test_message_of_exactly_the_maximum_length_is_accepted(self):
        self.assertEqual(self.client.post("/connections", json=self.body(message="x" * 1000)).status_code, 201)

    def test_daily_cap_blocks_the_next_request_before_writing(self):
        self.database.connections.count_documents.return_value = MAX_REQUESTS_PER_DAY
        response = self.client.post("/connections", json=self.body())
        self.assertEqual(response.status_code, 429)
        self.assertIn("per day", response.json()["detail"])
        query = self.database.connections.count_documents.call_args.args[0]
        self.assertEqual(query["sender_user_id"], "user-me")
        self.assertAlmostEqual(
            query["created_at"]["$gte"].timestamp(), (datetime.now(timezone.utc) - timedelta(days=1)).timestamp(), delta=30,
        )
        self.database.connections.insert_one.assert_not_awaited()
        self.sent.assert_not_awaited()

    def test_requests_just_under_the_cap_still_go_through(self):
        self.database.connections.count_documents.return_value = MAX_REQUESTS_PER_DAY - 1
        self.assertEqual(self.client.post("/connections", json=self.body()).status_code, 201)

    # ---- types ----------------------------------------------------------------------------

    def test_types_endpoint_lists_the_dropdown_options_in_order(self):
        response = self.client.get("/connections/types")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0], {"value": "mentorship", "label": "Mentorship"})
        self.assertEqual([item["value"] for item in response.json()], list(REQUEST_TYPE_LABELS))

    # ---- listing --------------------------------------------------------------------------

    def list_cursor(self, documents):
        cursor = self.database.connections.find.return_value.sort.return_value.limit.return_value
        cursor.to_list = AsyncMock(return_value=documents)
        self.database.profiles.find.return_value.to_list = AsyncMock(return_value=[self.theirs])
        self.database.users.find.return_value.to_list = AsyncMock(
            return_value=[{"_id": "user-them", "email": "taylor@example.com"}],
        )

    def test_list_shows_type_direction_and_the_other_persons_public_profile(self):
        self.list_cursor([self.pending(), self.pending(
            _id="conn-2", sender_user_id="user-me", recipient_user_id="user-them", status="accepted", type="career_advice",
        )])
        response = self.client.get("/connections", params={"status": "pending"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([(c["id"], c["direction"], c["type"]) for c in response.json()],
                         [("conn-1", "incoming", "mentorship"), ("conn-2", "outgoing", "career_advice")])
        self.assertEqual(response.json()[0]["message"], "Please mentor me")
        self.assertEqual(response.json()[0]["profile"]["name"], "Taylor Rivera")
        self.assertNotIn("user-them", response.text)
        query = self.database.connections.find.call_args.args[0]
        self.assertEqual(query["status"], "pending")
        self.assertEqual(query["$or"], [{"sender_user_id": "user-me"}, {"recipient_user_id": "user-me"}])

    def test_list_shares_an_email_only_for_accepted_requests(self):
        self.list_cursor([self.pending(), self.pending(_id="conn-2", status="accepted"),
                          self.pending(_id="conn-3", status="declined")])
        emails = {c["id"]: c["contact_email"] for c in self.client.get("/connections").json()}
        self.assertEqual(emails, {"conn-1": None, "conn-2": "taylor@example.com", "conn-3": None})
        lookup = self.database.users.find.call_args.args
        self.assertEqual(lookup[0], {"_id": {"$in": ["user-them"]}, "is_active": True})
        self.assertEqual(lookup[1], {"email": 1})

    def test_no_email_lookup_when_nothing_is_accepted(self):
        self.list_cursor([self.pending()])
        self.client.get("/connections")
        self.database.users.find.assert_not_called()

    def test_requests_saved_before_types_existed_show_as_other(self):
        old = self.pending()
        del old["type"]
        self.list_cursor([old])
        self.assertEqual(self.client.get("/connections").json()[0]["type"], "other")

    def test_list_can_be_filtered_by_type(self):
        self.list_cursor([])
        self.client.get("/connections", params={"type": "mentorship"})
        self.assertEqual(self.database.connections.find.call_args.args[0]["type"], "mentorship")
        self.client.get("/connections", params={"type": "other"})
        self.assertEqual(self.database.connections.find.call_args.args[0]["type"], {"$in": ["other", None]})
        self.client.get("/connections")
        self.assertNotIn("type", self.database.connections.find.call_args.args[0])
        self.assertEqual(self.client.get("/connections", params={"type": "bogus"}).status_code, 422)

    def test_empty_list_skips_profile_lookup(self):
        cursor = self.database.connections.find.return_value.sort.return_value.limit.return_value
        cursor.to_list = AsyncMock(return_value=[])
        self.assertEqual(self.client.get("/connections").json(), [])
        self.database.profiles.find.assert_not_called()

    # ---- responding -----------------------------------------------------------------------

    def test_accept_updates_only_my_pending_request_emails_the_sender_and_shares_their_address(self):
        self.database.connections.find_one_and_update.return_value = self.pending(status="accepted")
        response = self.client.patch("/connections/conn-1", json={"status": "accepted"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.json()["status"], response.json()["type"]), ("accepted", "mentorship"))
        self.assertEqual(response.json()["contact_email"], "taylor@example.com")
        call = self.database.connections.find_one_and_update.call_args
        self.assertEqual(call.args[0], {"_id": "conn-1", "recipient_user_id": "user-me", "status": "pending"})
        self.assertEqual(call.args[1]["$set"]["status"], "accepted")
        self.assertEqual(call.kwargs["return_document"], ReturnDocument.AFTER)
        self.accepted.assert_awaited_once_with(self.database, "conn-1")
        self.assertEqual(self.database.users.find_one.call_args.args[0], {"_id": "user-them", "is_active": True})

    def test_decline_shares_nothing_and_sends_no_email(self):
        self.database.connections.find_one_and_update.return_value = self.pending(status="declined")
        response = self.client.patch("/connections/conn-1", json={"status": "declined"})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["contact_email"])
        self.accepted.assert_not_awaited()
        self.database.users.find_one.assert_not_awaited()

    def test_responding_to_someone_elses_or_settled_request_returns_404(self):
        response = self.client.patch("/connections/conn-1", json={"status": "accepted"})
        self.assertEqual(response.status_code, 404)
        self.accepted.assert_not_awaited()

    def test_only_accepted_or_declined_are_valid_responses(self):
        for body in ({}, {"status": "pending"}, {"status": "withdrawn"}, {"status": "accepted", "x": 1}):
            with self.subTest(body=body):
                self.assertEqual(self.client.patch("/connections/conn-1", json=body).status_code, 422)
        self.database.connections.find_one_and_update.assert_not_awaited()


class ConversationTests(ApiCase):
    def thread_cursor(self, replies):
        cursor = self.database.messages.find.return_value.sort.return_value.limit.return_value
        cursor.to_list = AsyncMock(return_value=replies)

    def reply(self, **changes):
        return {"_id": "m-1", "connection_id": "conn-1", "sender_user_id": "user-me", "body": "Happy to help!",
                "created_at": datetime.now(timezone.utc), **changes}

    def post(self, body="Thanks for reaching out!"):
        return self.client.post("/connections/conn-1/messages", json={"body": body})

    # ---- who can see a conversation -------------------------------------------------------

    def test_strangers_get_404_everywhere(self):
        self.database.connections.find_one.return_value = None
        for method, path, body in [
            ("GET", "/connections/conn-1", None), ("GET", "/connections/conn-1/messages", None),
            ("POST", "/connections/conn-1/messages", {"body": "hi"}),
        ]:
            with self.subTest(path=path, method=method):
                self.assertEqual(self.client.request(method, path, json=body).status_code, 404)
        query = self.database.connections.find_one.call_args.args[0]
        self.assertEqual(query["$or"], [{"sender_user_id": "user-me"}, {"recipient_user_id": "user-me"}])
        self.database.messages.insert_one.assert_not_awaited()

    def test_thread_starts_with_the_original_request_then_the_replies(self):
        self.database.connections.find_one.return_value = self.pending()
        self.thread_cursor([self.reply()])
        data = self.client.get("/connections/conn-1/messages").json()
        self.assertEqual([(m["id"], m["from_me"], m["body"]) for m in data],
                         [("request", False, "Please mentor me"), ("m-1", True, "Happy to help!")])
        self.assertNotIn("user-", str(data))

    def test_a_single_request_can_be_read_by_either_person(self):
        self.database.connections.find_one.return_value = self.pending()
        data = self.client.get("/connections/conn-1").json()
        self.assertEqual((data["id"], data["direction"], data["profile"]["name"]), ("conn-1", "incoming", "Taylor Rivera"))
        self.assertIsNone(data["contact_email"])
        self.database.users.find_one.assert_not_awaited()

    # ---- contact sharing ------------------------------------------------------------------

    def test_the_other_persons_email_appears_only_after_acceptance(self):
        self.database.connections.find_one.return_value = self.pending(status="accepted")
        data = self.client.get("/connections/conn-1").json()
        self.assertEqual(data["contact_email"], "taylor@example.com")
        self.assertEqual(self.database.users.find_one.call_args.args[0], {"_id": "user-them", "is_active": True})
        for status in ("pending", "declined"):
            self.database.connections.find_one.return_value = self.pending(status=status)
            self.assertIsNone(self.client.get("/connections/conn-1").json()["contact_email"])

    def test_the_email_belongs_to_the_other_person_whichever_side_i_am_on(self):
        self.database.connections.find_one.return_value = self.i_asked(status="accepted")
        self.client.get("/connections/conn-1")
        self.assertEqual(self.database.users.find_one.call_args.args[0]["_id"], "user-them")

    # ---- replying -------------------------------------------------------------------------

    def test_the_person_asked_can_reply_while_the_request_is_pending(self):
        self.database.connections.find_one.return_value = self.pending()
        response = self.post("  Happy to help!  ")
        self.assertEqual(response.status_code, 201)
        stored = self.database.messages.insert_one.call_args.args[0]
        self.assertEqual((stored["connection_id"], stored["sender_user_id"], stored["body"]),
                         ("conn-1", "user-me", "Happy to help!"))
        self.assertEqual((response.json()["from_me"], response.json()["body"]), (True, "Happy to help!"))
        self.messaged.assert_awaited_once_with(self.database, "conn-1", stored["_id"])

    def test_the_person_asked_can_reply_several_times_in_a_row(self):
        self.database.connections.find_one.return_value = self.pending()
        self.database.messages.find_one.return_value = {"sender_user_id": "user-me"}
        self.assertEqual(self.post().status_code, 201)

    def test_the_requester_must_wait_for_a_reply_before_writing_again(self):
        self.database.connections.find_one.return_value = self.i_asked()
        # Nothing but the original request so far, or their own last message: blocked.
        for last in (None, {"sender_user_id": "user-me"}):
            with self.subTest(last=last):
                self.database.messages.find_one.return_value = last
                response = self.post()
                self.assertEqual(response.status_code, 409)
                self.assertIn("wait for a reply", response.json()["detail"])
        self.database.messages.insert_one.assert_not_awaited()
        self.messaged.assert_not_awaited()

    def test_the_requester_can_write_again_after_the_other_person_replies(self):
        self.database.connections.find_one.return_value = self.i_asked()
        self.database.messages.find_one.return_value = {"sender_user_id": "user-them"}
        self.assertEqual(self.post().status_code, 201)
        self.assertEqual(self.database.messages.find_one.call_args.kwargs["sort"], [("created_at", -1)])

    def test_either_person_can_write_freely_once_accepted(self):
        for connection in (self.pending(status="accepted"), self.i_asked(status="accepted")):
            with self.subTest(direction=connection["sender_user_id"]):
                self.database.connections.find_one.return_value = connection
                self.database.messages.find_one.return_value = {"sender_user_id": "user-me"}
                self.assertEqual(self.post().status_code, 201)

    def test_a_declined_request_is_closed(self):
        self.database.connections.find_one.return_value = self.pending(status="declined")
        response = self.post()
        self.assertEqual(response.status_code, 409)
        self.assertIn("closed", response.json()["detail"])
        self.database.messages.insert_one.assert_not_awaited()

    def test_a_full_conversation_stops_taking_messages(self):
        self.database.connections.find_one.return_value = self.pending(status="accepted")
        self.database.messages.count_documents.return_value = MAX_MESSAGES_PER_THREAD
        self.assertEqual(self.post().status_code, 409)
        self.database.messages.insert_one.assert_not_awaited()

    def test_bad_messages_never_write(self):
        self.database.connections.find_one.return_value = self.pending()
        for body in ({}, {"body": ""}, {"body": "   "}, {"body": "x" * 1001}, {"body": None}, {"body": 5},
                     {"body": "hi", "sender_user_id": "other"}):
            with self.subTest(body=body):
                self.assertEqual(self.client.post("/connections/conn-1/messages", json=body).status_code, 422)
        self.database.messages.insert_one.assert_not_awaited()
        self.assertEqual(self.post("x" * 1000).status_code, 201)
