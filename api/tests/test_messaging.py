from datetime import UTC, datetime, timedelta

import pytest

from tests.test_checkouts import check_out, member
from trove.checkouts import router as checkouts_router
from trove.messaging import service as messaging_service
from trove.messaging.service import checkouts_with_new_messages, email_new_message, post_note


@pytest.fixture(autouse=True)
def quiet_checkout_emails(monkeypatch):
    async def nothing(database, **details):
        return None

    monkeypatch.setattr(checkouts_router, "notify_checkout_requested", nothing)
    monkeypatch.setattr(checkouts_router, "notify_checkout_accepted", nothing)


@pytest.fixture
def emailed(monkeypatch):
    """Records the messages the router asks to email about, instead of emailing."""
    calls = []

    async def record(database, message):
        calls.append(message)

    monkeypatch.setattr(messaging_service, "email_new_message", record)
    return calls


async def accepted_checkout(client, database):
    """Maya's book, checked out by Sam and accepted. Returns (checkout id, maya, sam) with headers."""
    maya_id, maya = await member(client, database, "Maya")
    sam_id, sam = await member(client, database, "Sam")
    checkout_id = (await check_out(client, sam, "book-of-maya", message="Hi Maya!")).json()["id"]
    await client.post(f"/checkouts/{checkout_id}/accept", headers=maya)
    return checkout_id, (maya_id, maya), (sam_id, sam)


async def send(client, headers, checkout_id, text):
    return await client.post(f"/messages/{checkout_id}", json={"text": text}, headers=headers)


async def test_messages_require_sign_in(client):
    assert (await client.get("/messages/c1")).status_code == 401
    assert (await client.post("/messages/c1", json={"text": "Hi"})).status_code == 401
    assert (await client.post("/messages/c1/read")).status_code == 401


async def test_the_thread_opens_when_the_author_accepts(client, database, emailed):
    _, maya = await member(client, database, "Maya")
    _, sam = await member(client, database, "Sam")
    checkout_id = (await check_out(client, sam, "book-of-maya", message="Hi Maya!")).json()["id"]

    # While it waits, there is no conversation: the note is the whole ask.
    assert (await client.get(f"/messages/{checkout_id}", headers=sam)).status_code == 404
    assert (await send(client, sam, checkout_id, "Any news?")).status_code == 404

    await client.post(f"/checkouts/{checkout_id}/accept", headers=maya)
    thread = (await client.get(f"/messages/{checkout_id}", headers=sam)).json()
    assert thread["book_title"] == "Maya's book"
    assert thread["other_name"] == "Maya Lee"
    assert thread["can_write"] is True
    assert [(m["kind"], m["text"], m["from_me"]) for m in thread["messages"]] == [
        ("checkout_note", "Hi Maya!", True)
    ]


async def test_both_people_write_and_read_in_order(client, database, emailed):
    checkout_id, (_, maya), (_, sam) = await accepted_checkout(client, database)
    first = await send(client, maya, checkout_id, "  Happy to talk!  ")
    assert first.status_code == 201
    assert first.json()["text"] == "Happy to talk!"
    assert (await send(client, sam, checkout_id, "Great, thank you.")).status_code == 201

    messages = (await client.get(f"/messages/{checkout_id}", headers=maya)).json()["messages"]
    assert [(m["kind"], m["sender_name"], m["text"], m["from_me"]) for m in messages] == [
        ("checkout_note", "Sam Lee", "Hi Maya!", False),
        ("message", "Maya Lee", "Happy to talk!", True),
        ("message", "Sam Lee", "Great, thank you.", False),
    ]
    assert [message["text"] for message in emailed] == ["Happy to talk!", "Great, thank you."]


async def test_nobody_else_can_see_or_write(client, database, emailed):
    checkout_id, _, _ = await accepted_checkout(client, database)
    _, ana = await member(client, database, "Ana")
    assert (await client.get(f"/messages/{checkout_id}", headers=ana)).status_code == 404
    assert (await send(client, ana, checkout_id, "Hello")).status_code == 404
    assert (await client.post(f"/messages/{checkout_id}/read", headers=ana)).status_code == 404
    assert await database.messages.count_documents({}) == 0


async def test_no_conversation_after_a_decline(client, database, emailed):
    _, maya = await member(client, database, "Maya")
    _, sam = await member(client, database, "Sam")
    checkout_id = (await check_out(client, sam, "book-of-maya")).json()["id"]
    await client.post(f"/checkouts/{checkout_id}/decline", headers=maya)
    assert (await client.get(f"/messages/{checkout_id}", headers=maya)).status_code == 404
    assert await post_note(database, checkout_id, "Confirmed") is None


async def test_messages_are_required_and_at_most_2000_characters(client, database, emailed):
    checkout_id, (_, maya), _ = await accepted_checkout(client, database)
    assert (await send(client, maya, checkout_id, "   ")).status_code == 422
    assert (await send(client, maya, checkout_id, "x" * 2001)).status_code == 422
    assert (await send(client, maya, checkout_id, "x" * 2000)).status_code == 201


async def test_at_most_30_messages_an_hour_per_person(client, database, emailed):
    checkout_id, (maya_id, maya), (_, sam) = await accepted_checkout(client, database)
    now = datetime.now(UTC)
    await database.messages.insert_many(
        [
            {
                "_id": f"m{n}",
                "checkout_id": checkout_id,
                "participants": [],
                "sender_id": maya_id,
                "text": "Hi",
                "sent_at": now - timedelta(minutes=n),
            }
            for n in range(30)
        ]
    )
    response = await send(client, maya, checkout_id, "One more")
    assert response.status_code == 429
    # The other person isn't held back, and older messages stop counting.
    assert (await send(client, sam, checkout_id, "Hello!")).status_code == 201
    await database.messages.update_many(
        {"sender_id": maya_id}, {"$set": {"sent_at": now - timedelta(hours=2)}}
    )
    assert (await send(client, maya, checkout_id, "One more")).status_code == 201


async def test_new_message_marker_is_private_to_each_person(client, database, emailed):
    checkout_id, (maya_id, maya), (sam_id, sam) = await accepted_checkout(client, database)

    def marker(listing, key):
        return [item["new_messages"] for item in listing.json()[key]]

    assert marker(await client.get("/checkouts", headers=sam), "reading") == [False]
    await send(client, maya, checkout_id, "Hi Sam")
    assert marker(await client.get("/checkouts", headers=sam), "reading") == [True]
    # Writing it isn't news to you.
    assert marker(await client.get("/checkouts", headers=maya), "lending") == [False]

    await client.post(f"/messages/{checkout_id}/read", headers=sam)
    assert marker(await client.get("/checkouts", headers=sam), "reading") == [False]

    # An app note is new for both people.
    note = await post_note(database, checkout_id, "Ana confirmed\nTuesday at 3pm")
    assert note["text"] == "Ana confirmed Tuesday at 3pm"
    assert await checkouts_with_new_messages(database, sam_id, [checkout_id]) == {checkout_id}
    assert await checkouts_with_new_messages(database, maya_id, [checkout_id]) == {checkout_id}
    shown = (await client.get(f"/messages/{checkout_id}", headers=sam)).json()["messages"][-1]
    assert (shown["kind"], shown["sender_name"], shown["from_me"]) == ("note", "", False)


async def test_new_message_emails_wait_10_minutes_per_person(client, database, monkeypatch, emailed):
    # `emailed` stops the router's own background email, so only the calls below send anything.
    checkout_id, (maya_id, maya), (sam_id, sam) = await accepted_checkout(client, database)
    sent = []

    async def record(database, **details):
        sent.append((details["recipient_id"], details["sender_name"]))

    monkeypatch.setattr(messaging_service, "notify_new_message", record)

    async def write(headers, text):
        await send(client, headers, checkout_id, text)
        return await database.messages.find_one({"text": text})

    await email_new_message(database, await write(maya, "One"))
    await email_new_message(database, await write(maya, "Two"))
    assert sent == [(sam_id, "Maya Lee")]  # the second came within 10 minutes

    await email_new_message(database, await write(sam, "Reply"))
    assert sent[-1] == (maya_id, "Sam Lee")  # Maya's own gap is separate

    await database.message_threads.update_one(
        {"_id": checkout_id}, {"$set": {f"emailed.{sam_id}": datetime.now(UTC) - timedelta(minutes=11)}}
    )
    await email_new_message(database, await write(maya, "Three"))
    assert sent[-1] == (sam_id, "Maya Lee")

    # A note goes to both people (each still within their own gap here, so set them back first).
    await database.message_threads.update_one({"_id": checkout_id}, {"$unset": {"emailed": ""}})
    await email_new_message(database, await post_note(database, checkout_id, "Confirmed"))
    assert sorted(sent[-2:]) == sorted([(sam_id, ""), (maya_id, "")])


async def test_deleting_an_account_removes_its_conversations(client, database, emailed):
    checkout_id, (_, maya), (_, sam) = await accepted_checkout(client, database)
    await send(client, maya, checkout_id, "Hi")
    response = await client.request("DELETE", "/auth/me", json={"email": "sam@example.com"}, headers=sam)
    assert response.status_code == 204
    assert await database.messages.count_documents({}) == 0
    assert await database.message_threads.count_documents({}) == 0


async def test_a_long_thread_keeps_its_newest_messages(client, database, emailed):
    checkout_id, (maya_id, maya), _ = await accepted_checkout(client, database)
    start = datetime.now(UTC) - timedelta(days=30)
    await database.messages.insert_many(
        [
            {
                "_id": f"m{n:03}",
                "checkout_id": checkout_id,
                "participants": [],
                "sender_id": maya_id,
                "text": f"Message {n}",
                "sent_at": start + timedelta(minutes=n),
            }
            for n in range(messaging_service.THREAD_LIMIT + 5)
        ]
    )
    texts = [
        m["text"] for m in (await client.get(f"/messages/{checkout_id}", headers=maya)).json()["messages"]
    ]
    assert texts[0] == "Hi Maya!"  # the checkout note always comes first
    assert texts[1] == "Message 5"  # the five oldest dropped
    assert texts[-1] == f"Message {messaging_service.THREAD_LIMIT + 4}"
