from trove.notifications.email import Email
from trove.notifications.links import unsubscribe_token, user_id_from_unsubscribe_token
from trove.notifications.templates import welcome


def test_member_text_is_escaped_in_html():
    email = Email(
        subject="Hi",
        heading="Hi",
        paragraphs=["<script>x</script>"],
        button_text="Go",
        button_url="https://example.com",
    )
    _, text, html = email.render("https://example.com/unsubscribe")
    assert "<script>" in text
    assert "<script>" not in html
    assert "Unsubscribe" in html


def test_unsubscribe_tokens_cannot_be_forged():
    token = unsubscribe_token("user-1")
    assert user_id_from_unsubscribe_token(token) == "user-1"
    assert user_id_from_unsubscribe_token(token.replace("user-1", "user-2")) is None
    assert user_id_from_unsubscribe_token("garbage") is None


def test_welcome_email_uses_first_name():
    subject, text, _ = welcome("Maya", "http://app").render("http://unsubscribe")
    assert subject == "Welcome to Trove"
    assert "Hi Maya," in text


async def test_unsubscribe_link_turns_off_email(client, database):
    await database.users.insert_one({"_id": "user-1", "email": "a@example.com", "is_active": True})
    token = unsubscribe_token("user-1")
    page = await client.get("/notifications/unsubscribe", params={"token": token})
    assert page.status_code == 200
    assert (await database.users.find_one({"_id": "user-1"})).get("email_notifications") is None

    done = await client.post("/notifications/unsubscribe", params={"token": token})
    assert done.status_code == 200
    assert (await database.users.find_one({"_id": "user-1"}))["email_notifications"] is False
