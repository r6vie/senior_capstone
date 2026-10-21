import unittest
from typing import get_args
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from pymongo.errors import DuplicateKeyError

import notifications
from connection_models import REQUEST_TYPE_LABELS, RequestType
from database import get_database
from email_templates import (
    REQUEST_WORDING, Suggestion, connection_accepted, connection_request, match_digest, new_message, verify_email,
    welcome,
)
from main import app
from notifications import (
    clean_header, notify_once, unsubscribe_token, user_id_from_token, verification_token, verification_user_id,
)

ALEX = {"_id": "p-alex", "name": "Alex Morgan", "affiliation": "CWRU alumni", "location": "Cleveland, Ohio",
        "expertise": ["Software engineering", "Startup mentoring"],
        "interests": ["Healthcare technology", "Entrepreneurship"]}
TAYLOR = {"_id": "p-taylor", "name": "Taylor Rivera", "affiliation": "CWRU alumni", "location": "Cleveland, Ohio",
          "expertise": ["Medical devices"], "interests": ["Healthcare technology", "Product development"]}
JORDAN = {"_id": "p-jordan", "name": "Jordan Lee", "affiliation": "Other", "location": "New York, New York",
          "expertise": ["Fundraising"], "interests": []}


class TemplateTests(unittest.TestCase):
    def test_connection_request_shows_who_asked_their_note_and_profile_summary(self):
        subject, text, html = connection_request(TAYLOR, ALEX, "Let's talk!", [], "http://app").render("http://api/unsub")
        self.assertEqual(subject, "Alex wants to connect with you on FoundersCircle")
        for body in (text, html):
            self.assertIn("Alex Morgan", body)
            self.assertIn("Expertise: Software engineering, Startup mentoring", body)
            self.assertIn("http://api/unsub", body)
            self.assertIn("http://app", body)
        self.assertIn("Let's talk!", text)
        self.assertIn("Let&#x27;s talk!", html)
        self.assertNotIn("Why it could be a good fit", text)

    def test_wording_exists_for_exactly_the_request_types_the_api_accepts(self):
        self.assertEqual(set(REQUEST_WORDING), set(get_args(RequestType)))
        self.assertEqual(set(REQUEST_TYPE_LABELS), set(get_args(RequestType)))

    def test_each_request_type_gets_its_own_subject_and_says_what_was_asked(self):
        subjects = {}
        for request_type, (_, _, what, _) in REQUEST_WORDING.items():
            subject, text, html = connection_request(
                TAYLOR, ALEX, "Could you help me?", [], "http://app", request_type=request_type,
            ).render("u")
            subjects[request_type] = subject
            self.assertIn("Alex", subject)
            self.assertIn(f"sent you {what}.", text)
            self.assertIn("Could you help me?", html)
        self.assertEqual(len(set(subjects.values())), len(subjects))
        self.assertEqual(subjects["mentorship"], "Alex would like you as a mentor")

    def test_an_unknown_or_missing_type_falls_back_to_a_plain_connection_request(self):
        subject, _, _ = connection_request(TAYLOR, ALEX, None, [], "http://app", request_type="bogus").render("u")
        self.assertEqual(subject, "Alex wants to connect with you on FoundersCircle")

    def test_accepted_email_shares_the_accepters_address_only_when_given_one(self):
        _, text, html = connection_accepted(
            ALEX, TAYLOR, [], "http://app", request_type="mentorship", contact_email="taylor@example.com",
        ).render("u")
        self.assertIn("How to reach Taylor:\n- taylor@example.com", text)
        self.assertIn("taylor@example.com", html)
        _, text, _ = connection_accepted(ALEX, TAYLOR, [], "http://app").render("u")
        self.assertNotIn("How to reach", text)

    def test_new_message_email_quotes_the_message_and_escapes_it(self):
        subject, text, html = new_message(ALEX, TAYLOR, "Happy to help! <b>Call me</b>", "http://app").render("u")
        self.assertEqual(subject, "Taylor sent you a message on FoundersCircle")
        self.assertIn('"Happy to help! <b>Call me</b>"', text)
        self.assertIn("Reply: http://app", text)
        self.assertNotIn("<b>Call me</b>", html)
        self.assertIn("&lt;b&gt;Call me&lt;/b&gt;", html)

    def test_accepted_email_names_what_was_accepted(self):
        subject, _, _ = connection_accepted(ALEX, TAYLOR, [], "http://app", request_type="mentorship").render("u")
        self.assertEqual(subject, "Taylor accepted your mentorship request")

    def test_reasons_from_the_matching_code_appear_when_given(self):
        _, text, html = connection_request(TAYLOR, ALEX, None, ["You both care about X"], "http://app").render("u")
        self.assertIn("Why it could be a good fit:\n- You both care about X", text)
        self.assertIn("You both care about X", html)

    def test_member_text_is_escaped_in_html_but_not_in_plain_text(self):
        evil = {**ALEX, "name": "<script>alert(1)</script> Sam", "affiliation": "<b>x</b>"}
        _, text, html = connection_request(TAYLOR, evil, "<img src=x>", ["<i>why</i>"], "http://app").render("u")
        for dangerous in ("<script>", "<img", "<b>x", "<i>why"):
            self.assertNotIn(dangerous, html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("<img src=x>", text)

    def test_profiles_without_tags_still_make_a_valid_email(self):
        bare = {**ALEX, "expertise": [], "interests": []}
        subject, text, _ = connection_request(TAYLOR, bare, None, [], "http://app").render("u")
        self.assertNotIn("About", text)
        self.assertIn("View request: http://app", text)

    def test_accepted_email_names_the_accepter_and_shows_their_profile(self):
        subject, text, _ = connection_accepted(ALEX, TAYLOR, [], "http://app").render("u")
        self.assertEqual(subject, "Taylor accepted your connection request")
        self.assertIn("You're now connected with Taylor Rivera.", text)
        self.assertIn("Expertise: Medical devices", text)

    def test_welcome_points_to_profile_creation(self):
        subject, text, html = welcome("Sam Quinn", "http://app").render("http://api/unsub")
        self.assertEqual(subject, "Welcome to FoundersCircle")
        self.assertIn("Create your profile: http://app", text)
        self.assertIn("http://api/unsub", html)

    def test_digest_template_displays_whatever_suggestions_it_is_given(self):
        email = match_digest(ALEX, [Suggestion(TAYLOR, ["Reason one"]), Suggestion(JORDAN)], "http://app")
        subject, text, html = email.render("u")
        self.assertEqual(subject, "Taylor could be a great connection (plus 1 more)")
        self.assertIn("Taylor Rivera (CWRU alumni, Cleveland, Ohio):\n- Reason one", text)
        self.assertIn("Jordan Lee (Other, New York, New York)", html)

    def test_verification_email_has_the_link_and_no_unsubscribe(self):
        subject, text, html = verify_email("Sam Quinn", "http://api/auth/verify?token=t").render("http://api/unsub")
        self.assertEqual(subject, "Confirm your email for FoundersCircle")
        self.assertIn("Confirm email: http://api/auth/verify?token=t", text)
        self.assertIn("24 hours", text)
        for body in (text, html):
            self.assertNotIn("unsub", body.lower())

    def test_empty_digest_is_refused(self):
        with self.assertRaises(ValueError):
            match_digest(ALEX, [], "http://app")


class UnsubscribeTokenTests(unittest.TestCase):
    def test_token_round_trips_and_rejects_tampering(self):
        token = unsubscribe_token("user-1")
        self.assertEqual(user_id_from_token(token), "user-1")
        self.assertIsNone(user_id_from_token(token.replace("user-1", "user-2")))
        self.assertIsNone(user_id_from_token("user-1.deadbeef"))
        self.assertIsNone(user_id_from_token("no-dot"))
        self.assertIsNone(user_id_from_token("user-1.é"))  # non-ASCII must not crash

    def test_verification_token_round_trips_and_expires_after_24_hours(self):
        token = verification_token("user-1", now=1_000_000)
        self.assertEqual(verification_user_id(token, now=1_000_000 + 23 * 3600), "user-1")
        self.assertIsNone(verification_user_id(token, now=1_000_000 + 24 * 3600 + 1))

    def test_verification_token_rejects_tampering_and_other_kinds_of_link(self):
        token = verification_token("user-1")
        user_id, expires, signature = token.rsplit(".", 2)
        for bad in (token.replace("user-1", "user-2"), f"{user_id}.{int(expires) + 99999}.{signature}",
                    f"{user_id}.notanumber.{signature}", f"{user_id}.{expires}.é", "junk", "",
                    unsubscribe_token("user-1")):
            with self.subTest(token=bad):
                self.assertIsNone(verification_user_id(bad))
        self.assertIsNone(user_id_from_token(token))  # a confirmation link cannot unsubscribe anyone

    def test_header_values_lose_newlines(self):
        self.assertEqual(clean_header("Hi\r\nBcc: x@example.com"), "Hi Bcc: x@example.com")


class SmtpTests(unittest.TestCase):
    def test_message_is_multipart_with_clean_headers_and_logs_in(self):
        config = {"EMAIL_FROM": "FoundersCircle <noreply@example.com>", "SMTP_HOST": "smtp.example.com",
                  "SMTP_PORT": "587", "SMTP_USER": "user", "SMTP_PASSWORD": "secret"}
        with patch("notifications.smtplib.SMTP") as smtp:
            server = smtp.return_value.__enter__.return_value
            notifications._send_sync(config, "to@example.com", "Hi\r\nBcc: evil@example.com", "plain", "<p>html</p>")
        smtp.assert_called_once_with("smtp.example.com", 587, timeout=10)
        server.starttls.assert_called_once()
        server.login.assert_called_once_with("user", "secret")
        message = server.send_message.call_args.args[0]
        self.assertEqual(message["Subject"], "Hi Bcc: evil@example.com")
        self.assertIsNone(message["Bcc"])
        self.assertEqual(message["To"], "to@example.com")
        self.assertEqual(message.get_content_type(), "multipart/alternative")
        self.assertEqual([part.get_content_type() for part in message.iter_parts()], ["text/plain", "text/html"])


class NotifyOnceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.database = MagicMock()
        self.database.users.find_one = AsyncMock(return_value={"_id": "u1", "email": "u1@example.com"})
        self.database.notifications.insert_one = AsyncMock()
        self.database.notifications.update_one = AsyncMock()
        self.database.notifications.find_one_and_update = AsyncMock(return_value=None)
        self.smtp = patch("notifications.smtp_configured", return_value=True)
        self.smtp.start()
        self.send = patch("notifications.send_email", new=AsyncMock())
        self.mock_send = self.send.start()
        self.make = lambda unsubscribe: ("Subject", "Body " + unsubscribe, "<p>x</p>")
        profiles = {"u-alex": ALEX, "u-taylor": TAYLOR}
        self.database.profiles.find_one = AsyncMock(side_effect=lambda q, p=None: profiles[q["owner_user_id"]])

    def tearDown(self):
        self.smtp.stop()
        self.send.stop()

    async def test_sends_once_and_records_the_outcome(self):
        self.assertEqual(await notify_once(self.database, "k1", "u1", self.make), "sent")
        args = self.mock_send.await_args.args
        self.assertEqual(args[0], "u1@example.com")
        self.assertIn("/notifications/unsubscribe?token=", args[2])
        self.database.notifications.update_one.assert_awaited_once_with({"_id": "k1"}, {"$set": {"status": "sent"}})

    async def test_second_call_with_same_key_sends_nothing(self):
        self.database.notifications.insert_one.side_effect = DuplicateKeyError("dup")
        self.assertEqual(await notify_once(self.database, "k1", "u1", self.make), "duplicate")
        self.mock_send.assert_not_awaited()

    async def test_failed_send_is_recorded_not_raised_and_can_be_retried(self):
        self.mock_send.side_effect = OSError("smtp down")
        self.assertEqual(await notify_once(self.database, "k1", "u1", self.make), "failed")
        self.database.notifications.update_one.assert_awaited_with({"_id": "k1"}, {"$set": {"status": "failed"}})
        self.mock_send.side_effect = None
        self.database.notifications.insert_one.side_effect = DuplicateKeyError("dup")
        self.database.notifications.find_one_and_update.return_value = {"_id": "k1"}
        self.assertEqual(await notify_once(self.database, "k1", "u1", self.make), "sent")

    async def test_inactive_or_opted_out_members_get_nothing(self):
        self.database.users.find_one.return_value = None
        self.assertEqual(await notify_once(self.database, "k1", "u1", self.make), "skipped")
        self.database.users.find_one.return_value = {"_id": "u1", "email": "a@b.co", "email_notifications": False}
        self.assertEqual(await notify_once(self.database, "k1", "u1", self.make), "skipped")
        self.database.notifications.insert_one.assert_not_awaited()
        self.mock_send.assert_not_awaited()

    async def test_without_smtp_the_email_is_printed_and_nothing_is_recorded(self):
        with patch("notifications.smtp_configured", return_value=False), patch("builtins.print") as printed:
            self.assertEqual(await notify_once(self.database, "k1", "u1", self.make), "logged")
        printed.assert_called()
        self.database.notifications.insert_one.assert_not_awaited()
        self.mock_send.assert_not_awaited()

    async def test_confirmation_email_is_sent_even_to_members_who_unsubscribed(self):
        self.database.users.find_one.return_value = {"_id": "u1", "email": "u1@example.com", "email_notifications": False}
        self.assertEqual(await notifications.notify_verification(self.database, "u1", "Sam Quinn"), "sent")
        self.assertEqual(self.mock_send.await_args.args[1], "Confirm your email for FoundersCircle")
        self.assertIn("/auth/verify?token=u1.", self.mock_send.await_args.args[2])
        self.assertTrue(self.database.notifications.insert_one.await_args.args[0]["_id"].startswith("verify:u1:"))

    async def test_a_repeat_confirmation_within_five_minutes_sends_nothing_new(self):
        self.database.notifications.insert_one.side_effect = DuplicateKeyError("dup")
        self.assertEqual(await notifications.notify_verification(self.database, "u1", "Sam Quinn"), "duplicate")
        self.mock_send.assert_not_awaited()

    async def test_welcome_hook_greets_the_new_member_once(self):
        self.assertEqual(await notifications.notify_welcome(self.database, "u1", "Sam Quinn"), "sent")
        self.assertEqual(self.database.notifications.insert_one.await_args.args[0]["_id"], "welcome:u1")
        self.assertEqual(self.mock_send.await_args.args[1], "Welcome to FoundersCircle")

    async def test_connection_request_hook_emails_the_recipient(self):
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "u-alex", "recipient_user_id": "u-taylor", "message": "Hello",
        })
        self.assertEqual(await notifications.notify_connection_request(self.database, "c1"), "sent")
        self.assertEqual(self.database.users.find_one.await_args.args[0]["_id"], "u-taylor")
        self.assertEqual(self.database.notifications.insert_one.await_args.args[0]["_id"], "connection-request:c1")
        self.assertEqual(self.mock_send.await_args.args[1], "Alex wants to connect with you on FoundersCircle")
        self.assertIn("Hello", self.mock_send.await_args.args[2])

    async def test_request_hook_uses_the_requests_type_and_message(self):
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "u-alex", "recipient_user_id": "u-taylor",
            "type": "mentorship", "message": "Please mentor me",
        })
        self.assertEqual(await notifications.notify_connection_request(self.database, "c1"), "sent")
        self.assertEqual(self.mock_send.await_args.args[1], "Alex would like you as a mentor")
        self.assertIn("Please mentor me", self.mock_send.await_args.args[2])

    async def test_accepted_hook_emails_the_original_sender(self):
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "u-alex", "recipient_user_id": "u-taylor",
        })
        self.assertEqual(await notifications.notify_connection_accepted(self.database, "c1"), "sent")
        self.assertEqual(self.database.users.find_one.await_args.args[0]["_id"], "u-alex")
        self.assertEqual(self.mock_send.await_args.args[1], "Taylor accepted your connection request")

    async def test_accepted_hook_gives_the_sender_the_accepters_address(self):
        accounts = {"u-alex": {"_id": "u-alex", "email": "alex@example.com"},
                    "u-taylor": {"_id": "u-taylor", "email": "taylor@example.com"}}
        self.database.users.find_one = AsyncMock(side_effect=lambda query, projection=None: accounts[query["_id"]])
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "u-alex", "recipient_user_id": "u-taylor", "type": "mentorship",
        })
        self.assertEqual(await notifications.notify_connection_accepted(self.database, "c1"), "sent")
        self.assertEqual(self.mock_send.await_args.args[0], "alex@example.com")  # goes to the original sender
        self.assertIn("How to reach Taylor:\n- taylor@example.com", self.mock_send.await_args.args[2])
        self.assertNotIn("alex@example.com", self.mock_send.await_args.args[2])  # not their own address back

    async def test_new_message_hook_emails_the_other_person(self):
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "u-alex", "recipient_user_id": "u-taylor",
        })
        self.database.messages.find_one = AsyncMock(return_value={
            "_id": "m1", "connection_id": "c1", "sender_user_id": "u-taylor", "body": "Happy to help!",
        })
        self.assertEqual(await notifications.notify_new_message(self.database, "c1", "m1"), "sent")
        self.assertEqual(self.database.users.find_one.await_args.args[0]["_id"], "u-alex")  # the requester hears back
        self.assertEqual(self.mock_send.await_args.args[1], "Taylor sent you a message on FoundersCircle")
        self.assertIn("Happy to help!", self.mock_send.await_args.args[2])
        self.assertTrue(self.database.notifications.insert_one.await_args.args[0]["_id"].startswith("message:c1:u-alex:"))

        self.database.messages.find_one.return_value = {
            "_id": "m2", "connection_id": "c1", "sender_user_id": "u-alex", "body": "Great, thanks!",
        }
        await notifications.notify_new_message(self.database, "c1", "m2")
        self.assertEqual(self.database.users.find_one.await_args.args[0]["_id"], "u-taylor")  # and the other way round

    async def test_a_burst_of_messages_sends_only_one_email_per_ten_minutes(self):
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "u-alex", "recipient_user_id": "u-taylor",
        })
        self.database.messages.find_one = AsyncMock(return_value={
            "_id": "m1", "connection_id": "c1", "sender_user_id": "u-taylor", "body": "One",
        })
        self.database.notifications.insert_one.side_effect = DuplicateKeyError("same window")
        self.assertEqual(await notifications.notify_new_message(self.database, "c1", "m1"), "duplicate")
        self.mock_send.assert_not_awaited()

    async def test_new_message_hook_does_nothing_when_the_records_are_gone(self):
        self.database.connections.find_one = AsyncMock(return_value=None)
        self.database.messages.find_one = AsyncMock(return_value=None)
        self.assertIsNone(await notifications.notify_new_message(self.database, "c1", "m1"))
        self.mock_send.assert_not_awaited()

    async def test_accepted_hook_names_the_type_of_request(self):
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "u-alex", "recipient_user_id": "u-taylor", "type": "mentorship",
        })
        await notifications.notify_connection_accepted(self.database, "c1")
        self.assertEqual(self.mock_send.await_args.args[1], "Taylor accepted your mentorship request")

    async def test_matching_reasons_are_included_when_the_matching_code_provides_them(self):
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "u-alex", "recipient_user_id": "u-taylor",
        })
        with patch("notifications.match_reasons", return_value=["Because science"]) as reasons:
            await notifications.notify_connection_request(self.database, "c1")
        reasons.assert_called_once_with(TAYLOR, ALEX)  # (recipient, sender): why Taylor would want Alex
        self.assertIn("Because science", self.mock_send.await_args.args[2])

    async def test_a_matching_bug_does_not_stop_the_email(self):
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "u-alex", "recipient_user_id": "u-taylor",
        })
        with patch("notifications.match_reasons", side_effect=RuntimeError("bug")):
            self.assertEqual(await notifications.notify_connection_request(self.database, "c1"), "sent")
        self.assertNotIn("Why it could be a good fit", self.mock_send.await_args.args[2])

    async def test_hooks_do_nothing_when_the_connection_or_a_profile_is_gone(self):
        self.database.connections.find_one = AsyncMock(return_value=None)
        self.assertIsNone(await notifications.notify_connection_request(self.database, "c1"))
        self.database.connections.find_one = AsyncMock(return_value={
            "_id": "c1", "sender_user_id": "a", "recipient_user_id": "b",
        })
        self.database.profiles.find_one = AsyncMock(return_value=None)
        self.assertIsNone(await notifications.notify_connection_accepted(self.database, "c1"))
        self.database.notifications.insert_one.assert_not_awaited()


class UnsubscribePageTests(unittest.TestCase):
    def setUp(self):
        self.settings = patch("database.database_settings", return_value=("", "test"))
        self.settings.start()
        self.client = TestClient(app)
        self.client.__enter__()
        self.database = MagicMock()
        self.database.users.update_one = AsyncMock()
        app.dependency_overrides[get_database] = lambda: self.database

    def tearDown(self):
        app.dependency_overrides.clear()
        self.client.__exit__(None, None, None)
        self.settings.stop()

    def test_opening_the_link_changes_nothing_until_the_button_is_pressed(self):
        token = unsubscribe_token("user-1")
        page = self.client.get("/notifications/unsubscribe", params={"token": token})
        self.assertEqual(page.status_code, 200)
        self.assertIn("method='post'", page.text)
        self.database.users.update_one.assert_not_awaited()

    def test_posting_a_valid_token_turns_off_emails_for_that_account_only(self):
        response = self.client.post("/notifications/unsubscribe", params={"token": unsubscribe_token("user-1")})
        self.assertEqual(response.status_code, 200)
        self.database.users.update_one.assert_awaited_once_with(
            {"_id": "user-1"}, {"$set": {"email_notifications": False}},
        )

    def test_forged_tokens_are_rejected(self):
        for method in ("get", "post"):
            response = getattr(self.client, method)("/notifications/unsubscribe", params={"token": "user-1.forged"})
            self.assertEqual(response.status_code, 400)
        self.database.users.update_one.assert_not_awaited()
