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


def extracted(*profiles: tuple[str, list[dict]]) -> str:
    return json.dumps(
        {"profiles": [{"book_id": book_id, "signals": signals} for book_id, signals in profiles]}
    )


def signal(kind: str, label: str, evidence: str, *broader: str) -> dict:
    return {"kind": kind, "label": label, "broader": list(broader), "evidence": evidence}


async def test_recommendation_requires_sign_in(client):
    assert (await client.get("/discovery/recommendation")).status_code == 401
    assert (await client.get("/discovery/search", params={"q": "career"})).status_code == 401


async def test_searches_public_book_text_and_author_names(client, database):
    _, headers = await sign_in(client)
    matching = book("career-change", "maya-chen", title="Leaving the Laboratory")
    matching["author_name"] = "Maya Chen"
    matching["blurb"] = "A move from research into public-interest teaching."
    matching["chapters"][0]["title"] = "The final experiment"
    matching["chapters"][0]["summary"] = "How a difficult semester clarified the next direction."
    other = book("other", "other-author", title="Growing a Neighborhood Garden")
    other["blurb"] = "Neighbors share seeds and seasonal harvests."
    other["chapters"][0]["title"] = "The first tomato"
    other["chapters"][0]["summary"] = "Choosing a sunny plot and preparing the soil."
    await database.books.insert_many(
        [
            matching,
            other,
            book("hidden", "hidden-author", status="off_shelf", title="Leaving Another Laboratory"),
        ]
    )

    for query in ("labor", "Maya", "public teaching", "final experiment", "difficult direction"):
        response = await client.get("/discovery/search", params={"q": query}, headers=headers)
        assert [result["book"]["id"] for result in response.json()["results"]] == ["career-change"]
        assert "Private grounding words" not in response.text

    assert (await client.get("/discovery/search", params={"q": "Private"}, headers=headers)).json() == {
        "results": []
    }


async def test_search_is_partial_ranked_and_returns_a_public_excerpt(client, database):
    _, headers = await sign_in(client)
    title_match = book("title", "author-one", title="Engineering a Career Change")
    title_match["blurb"] = "A practical account of starting over."
    summary_match = book("summary", "author-two", title="A Different Path")
    summary_match["chapters"][0]["summary"] = "What engineering taught me about career changes."
    await database.books.insert_many([summary_match, title_match])

    results = (await client.get("/discovery/search", params={"q": "engi career"}, headers=headers)).json()[
        "results"
    ]
    assert [result["book"]["id"] for result in results] == ["title", "summary"]
    assert results[0]["excerpt"] == "Engineering a Career Change"
    assert "engineering" in results[1]["excerpt"].lower()


async def test_search_waits_for_two_characters(client, database):
    _, headers = await sign_in(client)
    await database.books.insert_one(book("one", "author-one", title="A Book"))
    assert (await client.get("/discovery/search", params={"q": "a"}, headers=headers)).json() == {
        "results": []
    }


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
            extracted(
                ("mine", [signal("experience", "changing direction", "changing direction")]),
                (
                    "recommended",
                    [signal("experience", "changing direction", "changing direction")],
                ),
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
        "reason": "You and Author One both write about changing direction, giving you a concrete place to start.",
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
        text_message(
            extracted(
                ("mine", [signal("experience", "changing direction", "changing direction")]),
                ("candidate", [signal("experience", "changing direction", "changing direction")]),
            )
        )
    )

    first = await client.get("/discovery/recommendation", headers=headers)
    second = await client.get("/discovery/recommendation", headers=headers)
    assert first.json() == second.json()
    assert first.json()["reason"] == (
        "You and Author One both write about changing direction, giving you a concrete place to start."
    )
    assert len(fake_claude.requests) == 1
    cache = await database.recommendations.find_one({"user_id": account["id"]})
    assert timedelta(days=6, hours=23) < cache["expires_at"].replace(tzinfo=UTC) - datetime.now(UTC)

    await database.books.update_one({"_id": "mine"}, {"$set": {"title": "A changed story"}})
    fake_claude.responses.append(
        text_message(extracted(("mine", [signal("experience", "changing direction", "changing direction")])))
    )
    changed = await client.get("/discovery/recommendation", headers=headers)
    assert changed.json()["book"]["id"] == "candidate"
    assert len(fake_claude.requests) == 2
    assert "candidate" not in fake_claude.requests[1]["messages"][0]["content"]

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
        text_message(
            extracted(("hidden", [signal("experience", "changing direction", "changing direction")]))
        )
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


async def test_matching_is_deterministic_and_prefers_an_exact_interest(client, database, fake_claude):
    account, headers = await sign_in(client)
    own = book("mine", account["id"], title="What tennis taught me")
    exact = book("exact", "exact-author", title="Tennis after work")
    related = book("related", "related-author", title="A football team from scratch")
    await database.books.insert_many([own, related, exact])
    fake_claude.responses.append(
        text_message(
            extracted(
                ("mine", [signal("interest", "tennis", "tennis", "racket sports", "sports")]),
                ("related", [signal("interest", "football", "football", "team sports", "sports")]),
                ("exact", [signal("interest", "tennis", "Tennis", "racket sports", "sports")]),
            )
        )
    )

    response = await client.get("/discovery/recommendation", headers=headers)

    assert response.json()["book"]["id"] == "exact"
    assert response.json()["reason"] == (
        "You and Exact Author both write about tennis, giving you a concrete place to start."
    )
    stored = await database.match_profiles.find_one({"_id": "mine"})
    assert stored["profile"]["signals"][0]["broader"] == ["racket sports", "sports"]


async def test_matching_connects_different_interests_through_a_broader_concept(client, database, fake_claude):
    account, headers = await sign_in(client)
    own = book("mine", account["id"], title="What tennis taught me")
    candidate = book("candidate", "maya-chen", title="A football team from scratch")
    await database.books.insert_many([own, candidate])
    fake_claude.responses.append(
        text_message(
            extracted(
                ("mine", [signal("interest", "tennis", "tennis", "racket sports", "sports")]),
                (
                    "candidate",
                    [signal("interest", "football", "football", "team sports", "sports")],
                ),
            )
        )
    )

    response = await client.get("/discovery/recommendation", headers=headers)

    assert response.json()["reason"] == (
        "Your book's tennis connects with Maya Chen's football through sports."
    )


async def test_matching_uses_complementary_goals_and_knowledge(client, database, fake_claude):
    account, headers = await sign_in(client)
    own = book("mine", account["id"], title="Learning to fund a first company")
    candidate = book("candidate", "maya-chen", title="Raising a seed round")
    await database.books.insert_many([own, candidate])
    fake_claude.responses.append(
        text_message(
            extracted(
                ("mine", [signal("goal", "startup fundraising", "fund a first company")]),
                ("candidate", [signal("knowledge", "startup fundraising", "Raising a seed round")]),
            )
        )
    )

    response = await client.get("/discovery/recommendation", headers=headers)

    assert response.json()["book"]["id"] == "candidate"
    assert response.json()["reason"] == (
        "Maya Chen's experience with startup fundraising complements your goal around startup fundraising."
    )


async def test_an_extracted_signal_must_be_grounded_in_public_book_text(client, database, fake_claude):
    account, headers = await sign_in(client)
    await database.books.insert_many([book("mine", account["id"]), book("candidate", "author-one")])
    fake_claude.responses.append(
        text_message(
            extracted(
                ("mine", [signal("interest", "secret hobby", "Private grounding words")]),
                ("candidate", [signal("interest", "secret hobby", "Private grounding words")]),
            )
        )
    )

    response = await client.get("/discovery/recommendation", headers=headers)

    assert response.json() == {"state": "unavailable", "book": None, "reason": None}
    stored = await database.match_profiles.find_one({"_id": "mine"})
    assert stored["profile"]["signals"] == []
