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


def test_new_checkout_email_quotes_the_readers_note():
    from trove.notifications.templates import checkout_requested

    subject, text, html = checkout_requested(
        "Sam Lee", "My book", "<b>Hello</b>", "http://app/checkouts", 7
    ).render("http://unsubscribe")
    assert subject == "Sam Lee would like to check out your book"
    assert '"<b>Hello</b>"' in text
    assert "<b>Hello</b>" not in html
    assert "http://app/checkouts" in text
    assert "within 7 days" in text


def test_accepted_emails_link_to_trove_without_contact_details():
    from trove.notifications.templates import checkout_accepted_for_author, checkout_accepted_for_reader

    subject, text, _ = checkout_accepted_for_reader("Maya Lee", "My book", "http://app/checkouts").render(
        "http://u"
    )
    assert subject == "Maya Lee said yes"
    assert "http://app/checkouts" in text
    subject, text, _ = checkout_accepted_for_author("Sam Lee", "My book", "http://app/checkouts").render(
        "http://u"
    )
    assert subject == "You said yes to Sam Lee"
    assert "@" not in text.replace("http://u", "")


async def test_accepted_emails_respect_each_persons_email_switch(database, capsys):
    from trove.notifications.service import notify_checkout_accepted

    await database.users.insert_many(
        [
            {"_id": "reader-1", "email": "sam@example.com", "is_active": True, "email_notifications": False},
            {"_id": "author-1", "email": "maya@example.com", "is_active": True},
        ]
    )
    await notify_checkout_accepted(
        database,
        checkout_id="c1",
        reader_id="reader-1",
        author_id="author-1",
        reader_name="Sam Lee",
        author_name="Maya Lee",
        book_title="My book",
    )
    printed = capsys.readouterr().out
    # Without SMTP, emails are printed instead of sent: only the author's went out.
    assert "To user author-1: You said yes to Sam Lee" in printed
    assert "reader-1" not in printed
