from datetime import UTC, datetime, timedelta

import pytest

from trove.checkouts import router as checkouts_router
from trove.checkouts.service import fully_checked_out, get_checkout_for

NOW = datetime.now(UTC).replace(microsecond=0)
UNAVAILABLE = "This book isn't available right now."
PASSWORD = "a long test passphrase"


def book(book_id: str, author_id: str, **fields) -> dict:
    return {
        "_id": book_id,
        "author_id": author_id,
        "author_name": "Jordan Lee",
        "title": f"The book {book_id}",
        "cover_style": "cover-1",
        "blurb": None,
        "chapters": [{"id": "c1", "title": "One thing", "summary": "About it.", "quotes": ["My words."]}],
        "copies": 3,
        "status": "on_shelf",
        "published_at": NOW,
        "created_at": NOW,
        "updated_at": NOW,
        **fields,
    }


async def member(client, database, name: str, *, with_book: bool = True) -> tuple[str, dict]:
    """Sign up `name` and give them a book on the shelf; returns (user id, auth headers)."""
    email = f"{name.lower()}@example.com"
    account = (
        await client.post(
            "/auth/signup",
            json={"first_name": name, "last_name": "Lee", "email": email, "password": PASSWORD},
        )
    ).json()
    login = await client.post("/auth/login", json={"email": email, "password": PASSWORD})
    if with_book:
        await database.books.insert_one(
            book(f"book-of-{name.lower()}", account["id"], title=f"{name}'s book")
        )
    return account["id"], {"Authorization": f"Bearer {login.json()['access_token']}"}


async def check_out(client, headers, book_id: str, message: str = "I'd love to hear about this."):
    return await client.post("/checkouts", json={"book_id": book_id, "message": message}, headers=headers)


@pytest.fixture
def sent(monkeypatch):
    """Records the new-checkout emails instead of sending them."""
    calls = []

    async def record(database, **details):
        calls.append(details)

    monkeypatch.setattr(checkouts_router, "notify_checkout_requested", record)
    return calls


async def test_checkouts_require_sign_in(client):
    assert (await client.get("/checkouts")).status_code == 401
    assert (await client.post("/checkouts", json={"book_id": "b", "message": "Hi"})).status_code == 401
    assert (await client.post("/checkouts/x/accept")).status_code == 401


async def test_check_out_then_author_accepts(client, database, sent):
    author_id, author = await member(client, database, "Maya")
    _, reader = await member(client, database, "Sam")

    response = await check_out(client, reader, "book-of-maya")
    assert response.status_code == 201
    checkout = response.json()
    assert checkout["status"] == "waiting"
    assert checkout["book_title"] == "Maya's book"
    assert checkout["author_name"] == "Maya Lee"
    assert checkout["expires_at"] is not None
    assert sent == [
        {
            "checkout_id": checkout["id"],
            "author_id": author_id,
            "reader_name": "Sam Lee",
            "book_title": "Maya's book",
            "message": "I'd love to hear about this.",
        }
    ]

    lending = (await client.get("/checkouts", headers=author)).json()["lending"]
    assert [item["reader_name"] for item in lending] == ["Sam Lee"]
    assert lending[0]["reader_book"] == {"id": "book-of-sam", "title": "Sam's book"}
    assert lending[0]["status"] == "waiting"

    accepted = await client.post(f"/checkouts/{checkout['id']}/accept", headers=author)
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"
    reading = (await client.get("/checkouts", headers=reader)).json()["reading"]
    assert reading[0]["status"] == "accepted"
    assert reading[0]["expires_at"] is None

    # Answering twice is refused, and only the author can answer.
    assert (await client.post(f"/checkouts/{checkout['id']}/accept", headers=author)).status_code == 409
    assert (await client.post(f"/checkouts/{checkout['id']}/decline", headers=reader)).status_code == 404


async def test_you_need_a_book_of_your_own(client, database, sent):
    await member(client, database, "Maya")
    _, reader = await member(client, database, "Sam", with_book=False)
    response = await check_out(client, reader, "book-of-maya")
    assert response.status_code == 403
    assert sent == []


async def test_a_draft_isnt_enough(client, database, sent):
    await member(client, database, "Maya")
    reader_id, reader = await member(client, database, "Sam", with_book=False)
    await database.books.insert_one(book("sams-draft", reader_id, status="draft"))
    response = await check_out(client, reader, "book-of-maya")
    assert response.status_code == 403
    assert "on the shelf" in response.json()["detail"]


async def test_you_cant_check_out_your_own_book(client, database, sent):
    _, maya = await member(client, database, "Maya")
    assert (await check_out(client, maya, "book-of-maya")).status_code == 409


async def test_books_off_the_shelf_are_unavailable(client, database, sent):
    await database.books.insert_one(book("draft", "author-1", status="draft"))
    _, reader = await member(client, database, "Sam")
    for book_id in ("draft", "no-such-book"):
        response = await check_out(client, reader, book_id)
        assert response.status_code == 404
        assert response.json()["detail"] == UNAVAILABLE


async def test_one_open_checkout_per_book(client, database, sent):
    await member(client, database, "Maya")
    _, reader = await member(client, database, "Sam")
    assert (await check_out(client, reader, "book-of-maya")).status_code == 201
    assert (await check_out(client, reader, "book-of-maya")).status_code == 409


async def test_a_reader_can_have_three_open_checkouts(client, database, sent):
    await database.books.insert_many([book(f"b{number}", f"author-{number}") for number in range(4)])
    _, reader = await member(client, database, "Sam")
    for number in range(3):
        assert (await check_out(client, reader, f"b{number}")).status_code == 201
    fourth = await check_out(client, reader, "b3")
    assert fourth.status_code == 409
    assert "3 open checkouts" in fourth.json()["detail"]


async def test_a_book_leaves_the_shelf_when_every_copy_is_out(client, database, sent):
    await database.books.insert_one(book("one-copy", "author-1", copies=1))
    _, sam = await member(client, database, "Sam")
    _, ana = await member(client, database, "Ana")

    assert await fully_checked_out(database, [{"_id": "one-copy", "copies": 1}]) == set()
    assert (await check_out(client, sam, "one-copy")).status_code == 201
    assert await fully_checked_out(database, [{"_id": "one-copy", "copies": 1}]) == {"one-copy"}

    # The next reader is told only that it isn't available: no counts, no "fully booked".
    response = await check_out(client, ana, "one-copy")
    assert response.status_code == 409
    assert response.json()["detail"] == UNAVAILABLE


async def test_a_decline_looks_like_unavailable_and_waits_30_days(client, database, sent):
    _, author = await member(client, database, "Maya")
    _, reader = await member(client, database, "Sam")
    checkout_id = (await check_out(client, reader, "book-of-maya")).json()["id"]

    assert (await client.post(f"/checkouts/{checkout_id}/decline", headers=author)).status_code == 204
    reading = (await client.get("/checkouts", headers=reader)).json()["reading"]
    assert reading[0]["status"] == "unavailable"
    assert (await client.get("/checkouts", headers=author)).json()["lending"] == []
    assert await fully_checked_out(database, [{"_id": "book-of-maya", "copies": 1}]) == set()

    again = await check_out(client, reader, "book-of-maya")
    assert again.status_code == 409
    assert again.json()["detail"] == UNAVAILABLE

    await database.checkouts.update_one(
        {"_id": checkout_id}, {"$set": {"closed_at": NOW - timedelta(days=31)}}
    )
    assert (await check_out(client, reader, "book-of-maya")).status_code == 201


async def test_unanswered_checkouts_expire_after_7_days(client, database, sent):
    _, author = await member(client, database, "Maya")
    _, reader = await member(client, database, "Sam")
    checkout_id = (await check_out(client, reader, "book-of-maya")).json()["id"]
    saved = await database.checkouts.find_one({"_id": checkout_id})
    assert saved["expires_at"] - saved["created_at"] == timedelta(days=7)

    await database.checkouts.update_one(
        {"_id": checkout_id}, {"$set": {"expires_at": NOW - timedelta(minutes=1)}}
    )
    assert (await client.get("/checkouts", headers=reader)).json()["reading"][0]["status"] == "unavailable"
    assert (await client.get("/checkouts", headers=author)).json()["lending"] == []
    assert (await client.post(f"/checkouts/{checkout_id}/accept", headers=author)).status_code == 409
    # Same 30-day wait as a decline.
    assert (await check_out(client, reader, "book-of-maya")).json()["detail"] == UNAVAILABLE


async def test_a_reader_can_cancel_before_an_answer(client, database, sent):
    _, author = await member(client, database, "Maya")
    _, reader = await member(client, database, "Sam")
    checkout_id = (await check_out(client, reader, "book-of-maya")).json()["id"]

    assert (await client.post(f"/checkouts/{checkout_id}/cancel", headers=author)).status_code == 404
    cancelled = await client.post(f"/checkouts/{checkout_id}/cancel", headers=reader)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    # Cancelling frees the slot at once; there's no 30-day wait.
    second = await check_out(client, reader, "book-of-maya")
    assert second.status_code == 201

    await client.post(f"/checkouts/{second.json()['id']}/accept", headers=author)
    assert (await client.post(f"/checkouts/{second.json()['id']}/cancel", headers=reader)).status_code == 409


async def test_get_checkout_for_only_its_reader_and_author(client, database, sent):
    author_id, _ = await member(client, database, "Maya")
    reader_id, reader = await member(client, database, "Sam")
    checkout_id = (await check_out(client, reader, "book-of-maya")).json()["id"]

    assert (await get_checkout_for(database, checkout_id, reader_id))["_id"] == checkout_id
    assert (await get_checkout_for(database, checkout_id, author_id))["_id"] == checkout_id
    assert await get_checkout_for(database, checkout_id, "someone-else") is None


async def test_the_message_is_required_and_short(client, database, sent):
    await member(client, database, "Maya")
    _, reader = await member(client, database, "Sam")
    assert (await check_out(client, reader, "book-of-maya", message="   ")).status_code == 422
    assert (await check_out(client, reader, "book-of-maya", message="x" * 1001)).status_code == 422
    assert sent == []
