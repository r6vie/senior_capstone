from datetime import UTC, datetime, timedelta

import pytest

from tests.test_checkouts import check_out, member
from trove.checkouts import router as checkouts_router
from trove.checkouts.service import fully_checked_out, past_meets

NOW = datetime.now(UTC)


@pytest.fixture(autouse=True)
def quiet_checkout_emails(monkeypatch):
    async def nothing(database, **details):
        return None

    monkeypatch.setattr(checkouts_router, "notify_checkout_requested", nothing)
    monkeypatch.setattr(checkouts_router, "notify_checkout_accepted", nothing)


async def reading(client, database, *, accepted_days_ago: float = 15, copies: int = 3):
    """Maya's book, checked out by Sam and accepted `accepted_days_ago` days ago (no meeting time)."""
    maya_id, maya = await member(client, database, "Maya")
    sam_id, sam = await member(client, database, "Sam")
    await database.books.update_one({"_id": "book-of-maya"}, {"$set": {"copies": copies}})
    checkout_id = (await check_out(client, sam, "book-of-maya")).json()["id"]
    await client.post(f"/checkouts/{checkout_id}/accept", headers=maya)
    await database.checkouts.update_one(
        {"_id": checkout_id}, {"$set": {"answered_at": NOW - timedelta(days=accepted_days_ago)}}
    )
    return checkout_id, (maya_id, maya), (sam_id, sam)


async def answer(client, headers, checkout_id, value):
    return await client.post(f"/checkouts/{checkout_id}/met", json={"answer": value}, headers=headers)


async def mine(client, headers, key="reading"):
    return (await client.get("/checkouts", headers=headers)).json()[key]


async def test_not_asked_before_the_meeting_time(client, database):
    checkout_id, (_, maya), (_, sam) = await reading(client, database, accepted_days_ago=2)
    assert (await mine(client, sam))[0]["did_you_meet"] is None
    assert (await mine(client, maya, "lending"))[0]["did_you_meet"] is None
    response = await answer(client, sam, checkout_id, "met")
    assert response.status_code == 409
    assert "meeting time has passed" in response.json()["detail"]


async def test_asked_once_the_confirmed_meeting_is_over(client, database):
    checkout_id, _, (_, sam) = await reading(client, database, accepted_days_ago=1)
    await database.meetings.insert_one({"_id": checkout_id, "start": NOW + timedelta(hours=2)})
    assert (await mine(client, sam))[0]["did_you_meet"] is None
    await database.meetings.update_one({"_id": checkout_id}, {"$set": {"start": NOW - timedelta(hours=1)}})
    assert (await mine(client, sam))[0]["did_you_meet"] == {"can_answer": True, "my_answer": None}


async def test_a_later_meeting_time_moves_the_question_and_the_return(client, database):
    # Accepted long ago, but a time was confirmed for later: nothing is asked or returned yet.
    checkout_id, _, (_, sam) = await reading(client, database, accepted_days_ago=40)
    await database.meetings.insert_one({"_id": checkout_id, "start": NOW + timedelta(days=1)})
    item = (await mine(client, sam))[0]
    assert (item["status"], item["did_you_meet"]) == ("accepted", None)


async def test_asked_14_days_after_the_yes_without_a_time(client, database):
    _, _, (_, sam) = await reading(client, database, accepted_days_ago=13.9)
    assert (await mine(client, sam))[0]["did_you_meet"] is None
    await database.checkouts.update_many({}, {"$set": {"answered_at": NOW - timedelta(days=14, minutes=1)}})
    assert (await mine(client, sam))[0]["did_you_meet"]["can_answer"] is True


async def test_met_returns_the_copy_and_makes_a_past_meet_for_both(client, database):
    checkout_id, (maya_id, maya), (sam_id, sam) = await reading(client, database, copies=1)
    await client.put("/auth/me/contact", json={"phone": "216-555-0142"}, headers=maya)
    assert await fully_checked_out(database, [{"_id": "book-of-maya", "copies": 1}]) == {"book-of-maya"}

    response = await answer(client, sam, checkout_id, "met")
    assert response.status_code == 200
    assert response.json() == {"can_answer": False, "my_answer": "met"}

    # The copy is back, so the book returns to the shelf; Sam's slot is free; Maya's list moves on.
    assert await fully_checked_out(database, [{"_id": "book-of-maya", "copies": 1}]) == set()
    assert (await mine(client, sam))[0]["status"] == "returned"
    assert await mine(client, maya, "lending") == []

    sams = (await client.get("/checkouts/past-meets", headers=sam)).json()
    assert [(m["other_name"], m["you_were"], m["book_title"]) for m in sams] == [
        ("Maya Lee", "reader", "Maya's book")
    ]
    assert sams[0]["contact"]["phone"] == "216-555-0142"
    assert sams[0]["met_on"].endswith(
        ("Z", "+00:00")
    )  # a real moment, so every time zone shows the right day
    assert sams[0]["other_book"] == {"id": "book-of-maya", "title": "Maya's book"}
    mayas = (await client.get("/checkouts/past-meets", headers=maya)).json()
    assert [(m["other_name"], m["you_were"]) for m in mayas] == [("Sam Lee", "author")]
    assert mayas[0]["contact"]["email"] == "sam@example.com"
    # Maya hasn't answered herself, and never sees Sam's answer.
    assert mayas[0]["did_you_meet"] == {"can_answer": True, "my_answer": None}

    # Each reading grows the book (I6): the author gets one question.
    assert (
        await database.reading_questions.count_documents({"checkout_id": checkout_id, "author_id": maya_id})
        == 1
    )
    # The conversation is read-only history now.
    thread = await client.get(f"/messages/{checkout_id}", headers=sam)
    assert thread.status_code == 200 and thread.json()["can_write"] is False
    assert (
        await client.post(f"/messages/{checkout_id}", json={"text": "Hi"}, headers=sam)
    ).status_code == 409

    assert await past_meets(database, sam_id) == [
        {"checkout_id": checkout_id, "other_id": maya_id, "other_name": "Maya Lee", "book_id": "book-of-maya"}
    ]


async def test_not_yet_keeps_the_checkout_open(client, database):
    checkout_id, _, (_, sam) = await reading(client, database, copies=1)
    response = await answer(client, sam, checkout_id, "not_yet")
    assert response.json() == {"can_answer": True, "my_answer": "not_yet"}
    assert (await mine(client, sam))[0]["status"] == "accepted"
    assert await fully_checked_out(database, [{"_id": "book-of-maya", "copies": 1}]) == {"book-of-maya"}
    assert (await answer(client, sam, checkout_id, "met")).status_code == 200


async def test_no_returns_the_copy_without_a_past_meet(client, database):
    checkout_id, (_, maya), (_, sam) = await reading(client, database)
    assert (await answer(client, maya, checkout_id, "no")).status_code == 200
    assert (await mine(client, sam))[0]["status"] == "returned"
    assert (await client.get("/checkouts/past-meets", headers=sam)).json() == []
    # Contact details go when there was no meeting, and the author gets no question.
    assert (await mine(client, sam))[0]["author_contact"] is None
    assert await database.reading_questions.count_documents({}) == 0


async def test_disagreeing_answers_are_not_a_past_meet(client, database):
    checkout_id, (_, maya), (_, sam) = await reading(client, database)
    await answer(client, sam, checkout_id, "met")
    assert len((await client.get("/checkouts/past-meets", headers=maya)).json()) == 1
    assert (await answer(client, maya, checkout_id, "no")).status_code == 200
    assert (await client.get("/checkouts/past-meets", headers=maya)).json() == []
    assert (await client.get("/checkouts/past-meets", headers=sam)).json() == []


async def test_one_final_answer_each(client, database):
    checkout_id, (_, maya), (_, sam) = await reading(client, database)
    await answer(client, sam, checkout_id, "met")
    assert (await answer(client, sam, checkout_id, "no")).status_code == 409
    assert (await answer(client, maya, checkout_id, "not_yet")).status_code == 409
    assert (await answer(client, maya, checkout_id, "met")).status_code == 200
    assert (await answer(client, maya, checkout_id, "met")).status_code == 409


async def test_unanswered_copies_return_14_days_after_the_question(client, database):
    checkout_id, _, (sam_id, sam) = await reading(client, database, accepted_days_ago=27.9, copies=1)
    assert (await mine(client, sam))[0]["status"] == "accepted"  # asked 13.9 days ago
    await database.checkouts.update_many({}, {"$set": {"answered_at": NOW - timedelta(days=28, minutes=1)}})
    assert await fully_checked_out(database, [{"_id": "book-of-maya", "copies": 1}]) == set()
    saved = await database.checkouts.find_one({"_id": checkout_id})
    assert (saved["status"], saved["returned_by"], saved["met"]) == ("returned", "no_answer", False)
    # Returned on time (28 days after the yes), not when someone next looked.
    returned_at = saved["returned_at"].replace(tzinfo=UTC)
    assert abs(returned_at - (NOW - timedelta(minutes=1))) < timedelta(minutes=2)
    assert await past_meets(database, sam_id) == []
    # They can still say they met afterwards.
    assert (await answer(client, sam, checkout_id, "met")).status_code == 200
    assert len(await past_meets(database, sam_id)) == 1


async def test_only_the_two_people_can_answer(client, database):
    checkout_id, _, _ = await reading(client, database)
    _, ana = await member(client, database, "Ana")
    assert (await answer(client, ana, checkout_id, "met")).status_code == 404
    assert (
        await client.post(f"/checkouts/{checkout_id}/met", json={"answer": "maybe"}, headers=ana)
    ).status_code == 422
    assert (await client.post("/checkouts/x/met", json={"answer": "met"})).status_code == 401
    assert (await client.get("/checkouts/past-meets")).status_code == 401


async def test_a_waiting_or_declined_checkout_cant_be_answered(client, database):
    _, maya = await member(client, database, "Maya")
    _, sam = await member(client, database, "Sam")
    checkout_id = (await check_out(client, sam, "book-of-maya")).json()["id"]
    assert (await answer(client, sam, checkout_id, "met")).status_code == 404
    await client.post(f"/checkouts/{checkout_id}/decline", headers=maya)
    assert (await answer(client, sam, checkout_id, "met")).status_code == 404
