import json
from datetime import UTC, datetime, timedelta

from tests.fakes import text_message

NOW = datetime.now(UTC).replace(microsecond=0)
SIGNUP = {
    "first_name": "Maya",
    "last_name": "Okafor",
    "email": "maya-discovery@example.com",
    "password": "a long test passphrase",
}


async def sign_in(client) -> tuple[dict, dict[str, str]]:
    account = (await client.post("/auth/signup", json=SIGNUP)).json()
    login = await client.post("/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]})
    return account, {"Authorization": f"Bearer {login.json()['access_token']}"}


def book(book_id: str, author_id: str, *, status: str = "on_shelf", title: str | None = None) -> dict:
    return {
        "_id": book_id,
        "author_id": author_id,
        "author_name": author_id.replace("-", " ").title(),
        "title": title or book_id.replace("-", " ").title(),
        "cover_style": "cover-1",
        "blurb": "A public account of changing direction.",
        "chapters": [
            {
                "id": "chapter-1",
                "title": "The turning point",
                "summary": "How a difficult choice became a new direction.",
                "quotes": ["Private grounding words."],
            }
        ],
        "copies": 3,
        "status": status,
        "published_at": NOW if status != "draft" else None,
        "created_at": NOW,
        "updated_at": NOW,
    }


async def test_recommendation_requires_sign_in(client):
    assert (await client.get("/discovery/recommendation")).status_code == 401


async def test_members_are_invited_to_create_or_finish_their_book(client, database, fake_claude):
    account, headers = await sign_in(client)
    response = await client.get("/discovery/recommendation", headers=headers)
    assert response.json() == {"state": "create_book", "book": None, "reason": None}

    await database.books.insert_one(book("mine", account["id"], status="draft"))
    response = await client.get("/discovery/recommendation", headers=headers)
    assert response.json() == {"state": "finish_book", "book": None, "reason": None}
    assert fake_claude.requests == []


async def test_an_off_shelf_book_can_shape_its_owners_recommendation(client, database, fake_claude):
    account, headers = await sign_in(client)
    await database.books.insert_many(
        [
            book("mine", account["id"], status="off_shelf", title="Leaving the laboratory"),
            book("recommended", "author-one", title="Building a classroom after research"),
            book("hidden", "author-two", status="off_shelf", title="Nobody should receive this"),
        ]
    )
    fake_claude.responses.append(
        text_message(
            json.dumps(
                {
                    "book_id": "recommended",
                    "reason": "You both turned research experience into work centered on other people.",
                }
            )
        )
    )

    response = await client.get("/discovery/recommendation", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "state": "recommendation",
        "book": {
            "id": "recommended",
            "title": "Building a classroom after research",
            "author_name": "Author One",
            "cover_style": "cover-1",
            "blurb": "A public account of changing direction.",
        },
        "reason": "You both turned research experience into work centered on other people.",
    }
    sent = fake_claude.requests[0]["messages"][0]["content"]
    assert "Leaving the laboratory" in sent
    assert "Building a classroom after research" in sent
    assert "Nobody should receive this" not in sent
    assert "Private grounding words" not in sent


async def test_the_pick_is_cached_until_a_book_changes(client, database, fake_claude):
    account, headers = await sign_in(client)
    await database.books.insert_many([book("mine", account["id"]), book("candidate", "author-one")])
    fake_claude.responses.append(
        text_message(json.dumps({"book_id": "candidate", "reason": "  You both rebuilt a path.  "}))
    )

    first = await client.get("/discovery/recommendation", headers=headers)
    second = await client.get("/discovery/recommendation", headers=headers)
    assert first.json() == second.json()
    assert first.json()["reason"] == "You both rebuilt a path."
    assert len(fake_claude.requests) == 1
    cache = await database.recommendations.find_one({"user_id": account["id"]})
    assert timedelta(days=6, hours=23) < cache["expires_at"].replace(tzinfo=UTC) - datetime.now(UTC)

    await database.books.update_one({"_id": "mine"}, {"$set": {"title": "A changed story"}})
    fake_claude.responses.append(
        text_message(json.dumps({"book_id": "candidate", "reason": "Your changed stories connect."}))
    )
    changed = await client.get("/discovery/recommendation", headers=headers)
    assert changed.json()["reason"] == "Your changed stories connect."
    assert len(fake_claude.requests) == 2

    await database.books.update_one({"_id": "candidate"}, {"$set": {"status": "off_shelf"}})
    assert (await client.get("/discovery/recommendation", headers=headers)).json() == {
        "state": "empty_shelf",
        "book": None,
        "reason": None,
    }


async def test_a_stale_or_invalid_pick_is_never_returned(client, database, fake_claude):
    account, headers = await sign_in(client)
    await database.books.insert_many([book("mine", account["id"]), book("candidate", "author-one")])
    fake_claude.responses.append(
        text_message(json.dumps({"book_id": "hidden", "reason": "This id was not offered."}))
    )
    assert (await client.get("/discovery/recommendation", headers=headers)).json() == {
        "state": "unavailable",
        "book": None,
        "reason": None,
    }

    await database.books.update_one({"_id": "candidate"}, {"$set": {"status": "off_shelf"}})
    assert (await client.get("/discovery/recommendation", headers=headers)).json() == {
        "state": "empty_shelf",
        "book": None,
        "reason": None,
    }


async def test_ai_not_set_up_leaves_the_shelf_available(client, database):
    account, headers = await sign_in(client)
    await database.books.insert_many([book("mine", account["id"]), book("candidate", "author-one")])
    assert (await client.get("/discovery/recommendation", headers=headers)).json() == {
        "state": "unavailable",
        "book": None,
        "reason": None,
    }
