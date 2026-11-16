from datetime import UTC, datetime, timedelta

from tests.test_checkouts import check_out, member
from trove.meetings import router as meetings_router
from trove.meetings.service import calendar_invite
from trove.notifications.service import notify_meeting_reminder


def slot(days: int, hour: int = 15, minute: int = 0) -> datetime:
    """A start time `days` from now, on the clock time given (UTC)."""
    day = datetime.now(UTC) + timedelta(days=days)
    return day.replace(hour=hour, minute=minute, second=0, microsecond=0)


def iso(*times: datetime) -> list[str]:
    return [t.isoformat() for t in times]


async def accepted_pair(client, database):
    """Maya (author) and Sam (reader) with an accepted checkout; returns (checkout id, maya, sam)."""
    _, maya = await member(client, database, "Maya")
    _, sam = await member(client, database, "Sam")
    checkout = (await check_out(client, sam, "book-of-maya")).json()
    await client.post(f"/checkouts/{checkout['id']}/accept", headers=maya)
    return checkout["id"], maya, sam


async def test_meetings_require_sign_in(client):
    assert (await client.get("/meetings/x")).status_code == 401
    assert (await client.put("/meetings/x/times", json={"times": []})).status_code == 401
    assert (await client.get("/meetings/x/invite.ics")).status_code == 401


async def test_only_the_two_people_on_an_accepted_checkout_can_see_it(client, database):
    _, maya = await member(client, database, "Maya")
    _, sam = await member(client, database, "Sam")
    _, ivy = await member(client, database, "Ivy")
    checkout = (await check_out(client, sam, "book-of-maya")).json()

    # Waiting for an answer: nothing to arrange yet.
    assert (await client.get(f"/meetings/{checkout['id']}", headers=sam)).status_code == 404

    await client.post(f"/checkouts/{checkout['id']}/accept", headers=maya)
    for headers in (maya, sam):
        assert (await client.get(f"/meetings/{checkout['id']}", headers=headers)).status_code == 200
    # A third member can't tell the checkout exists, and can't change anything.
    assert (await client.get(f"/meetings/{checkout['id']}", headers=ivy)).status_code == 404
    offer = {"times": iso(slot(3))}
    assert (await client.put(f"/meetings/{checkout['id']}/times", json=offer, headers=ivy)).status_code == 404
    confirm = {"start": slot(3).isoformat()}
    assert (
        await client.put(f"/meetings/{checkout['id']}/confirm", json=confirm, headers=ivy)
    ).status_code == 404
    assert (await client.get(f"/meetings/{checkout['id']}/invite.ics", headers=ivy)).status_code == 404


async def test_a_declined_checkout_has_no_meeting(client, database):
    _, maya = await member(client, database, "Maya")
    _, sam = await member(client, database, "Sam")
    checkout = (await check_out(client, sam, "book-of-maya")).json()
    await client.post(f"/checkouts/{checkout['id']}/decline", headers=maya)
    assert (await client.get(f"/meetings/{checkout['id']}", headers=sam)).status_code == 404


async def test_offered_times_show_where_they_overlap(client, database):
    checkout_id, maya, sam = await accepted_pair(client, database)
    empty = (await client.get(f"/meetings/{checkout_id}", headers=sam)).json()
    assert empty["other_name"] == "Maya Lee"
    assert empty["book_title"] == "Maya's book"
    assert (empty["my_times"], empty["their_times"], empty["shared_times"]) == ([], [], [])

    await client.put(
        f"/meetings/{checkout_id}/times", json={"times": iso(slot(2), slot(3), slot(4))}, headers=maya
    )
    after = await client.put(
        f"/meetings/{checkout_id}/times", json={"times": iso(slot(3), slot(4, 15, 30), slot(5))}, headers=sam
    )
    body = after.json()
    assert len(body["my_times"]) == 3
    assert len(body["their_times"]) == 3
    # Only the day-3 time is on both lists.
    assert [datetime.fromisoformat(t) for t in body["shared_times"]] == [slot(3)]

    # Sending a new list replaces the old one; an empty list takes them all back.
    cleared = (await client.put(f"/meetings/{checkout_id}/times", json={"times": []}, headers=sam)).json()
    assert cleared["my_times"] == []
    assert cleared["shared_times"] == []
    assert len((await client.get(f"/meetings/{checkout_id}", headers=maya)).json()["my_times"]) == 3


async def test_bad_times_are_refused(client, database):
    checkout_id, _, sam = await accepted_pair(client, database)
    url = f"/meetings/{checkout_id}/times"
    past = await client.put(url, json={"times": iso(slot(-1))}, headers=sam)
    assert past.status_code == 422
    assert "passed" in past.json()["detail"]
    too_many = await client.put(url, json={"times": iso(*(slot(day) for day in range(2, 8)))}, headers=sam)
    assert too_many.status_code == 422
    no_zone = await client.put(url, json={"times": [slot(3).replace(tzinfo=None).isoformat()]}, headers=sam)
    assert no_zone.status_code == 422
    seconds = await client.put(url, json={"times": [slot(3).replace(second=30).isoformat()]}, headers=sam)
    assert seconds.status_code == 422
    not_a_time = await client.put(url, json={"times": ["soon"]}, headers=sam)
    assert not_a_time.status_code == 422


async def test_the_same_time_twice_counts_once(client, database):
    checkout_id, _, sam = await accepted_pair(client, database)
    response = await client.put(
        f"/meetings/{checkout_id}/times", json={"times": iso(slot(3), slot(3))}, headers=sam
    )
    assert len(response.json()["my_times"]) == 1


async def test_either_person_can_confirm_an_offered_time(client, database):
    checkout_id, maya, sam = await accepted_pair(client, database)
    await client.put(f"/meetings/{checkout_id}/times", json={"times": iso(slot(3), slot(4))}, headers=maya)

    confirmed = await client.put(
        f"/meetings/{checkout_id}/confirm", json={"start": slot(4).isoformat()}, headers=sam
    )
    assert confirmed.status_code == 200
    for headers in (maya, sam):
        meeting = (await client.get(f"/meetings/{checkout_id}", headers=headers)).json()
        assert datetime.fromisoformat(meeting["start"]) == slot(4)


async def test_only_an_offered_future_time_can_be_confirmed(client, database):
    checkout_id, maya, sam = await accepted_pair(client, database)
    await client.put(f"/meetings/{checkout_id}/times", json={"times": iso(slot(3))}, headers=maya)
    url = f"/meetings/{checkout_id}/confirm"
    assert (await client.put(url, json={"start": slot(5).isoformat()}, headers=sam)).status_code == 422

    # A time that has gone by can't be confirmed, even if it was offered once.
    past = slot(-2)
    await database.meetings.update_one(
        {"_id": checkout_id}, {"$set": {f"times.{await _id(database, 'Maya')}": [past]}}
    )
    assert (await client.put(url, json={"start": past.isoformat()}, headers=sam)).status_code == 422


async def _id(database, first_name: str) -> str:
    return (await database.users.find_one({"first_name": first_name}))["_id"]


async def test_video_link_and_place(client, database):
    checkout_id, maya, sam = await accepted_pair(client, database)
    url = f"/meetings/{checkout_id}/details"

    saved = await client.put(
        url,
        json={"video_link": "https://meet.example.com/abc", "place_note": " Coffee at Tinkham "},
        headers=maya,
    )
    assert saved.status_code == 200
    seen = (await client.get(f"/meetings/{checkout_id}", headers=sam)).json()
    assert seen["video_link"] == "https://meet.example.com/abc"
    assert seen["place_note"] == "Coffee at Tinkham"

    for bad in (
        "http://meet.example.com/abc",
        "javascript:alert(1)",
        "meet.example.com",
        "https://a b.com/x",
    ):
        assert (await client.put(url, json={"video_link": bad}, headers=sam)).status_code == 422

    cleared = (await client.put(url, json={"video_link": "", "place_note": ""}, headers=sam)).json()
    assert cleared["video_link"] is None
    assert cleared["place_note"] is None


async def test_calendar_invite(client, database):
    checkout_id, maya, sam = await accepted_pair(client, database)
    url = f"/meetings/{checkout_id}/invite.ics"
    assert (await client.get(url, headers=sam)).status_code == 404  # nothing confirmed yet

    await client.put(f"/meetings/{checkout_id}/times", json={"times": iso(slot(3))}, headers=maya)
    await client.put(f"/meetings/{checkout_id}/confirm", json={"start": slot(3).isoformat()}, headers=sam)
    await client.put(
        f"/meetings/{checkout_id}/details", json={"video_link": "https://meet.example.com/abc"}, headers=sam
    )

    response = await client.get(url, headers=sam)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    assert "attachment" in response.headers["content-disposition"]
    text = response.text
    assert text.startswith("BEGIN:VCALENDAR\r\n")
    assert text.endswith("END:VCALENDAR\r\n")
    assert f"DTSTART:{slot(3):%Y%m%dT%H%M%SZ}" in text
    assert f"DTEND:{slot(3) + timedelta(minutes=30):%Y%m%dT%H%M%SZ}" in text
    assert "Maya Lee" in text  # Sam's copy names the other person
    assert "https://meet.example.com/abc" in text
    assert "Sam Lee" in (await client.get(url, headers=maya)).text


def test_calendar_text_is_escaped_and_folded():
    start = slot(3)
    checkout = {"_id": "c1", "book_title": "Hiring, firing; and a very long title " + "x" * 90}
    meeting = {"start": start, "updated_at": start, "video_link": None, "place_note": "Line one\nLine two"}
    text = calendar_invite(checkout, meeting, "Maya Lee")
    assert "\\," in text and "\\;" in text and "\\n" in text
    assert all(len(line.encode()) <= 75 for line in text.split("\r\n"))
    # Unfolding gives back the whole title.
    assert "x" * 90 in text.replace("\r\n ", "")


async def test_reminders_go_to_both_people_once_a_meeting_is_close(client, database, monkeypatch):
    sent = []

    async def record(database, **details):
        sent.append(details)

    monkeypatch.setattr(meetings_router, "notify_meeting_reminder", record)
    checkout_id, _, sam = await accepted_pair(client, database)
    soon = datetime.now(UTC) + timedelta(hours=5)
    await client.put(
        f"/meetings/{checkout_id}/details", json={"video_link": "https://meet.example.com/abc"}, headers=sam
    )
    await database.meetings.update_one({"_id": checkout_id}, {"$set": {"start": soon}})

    await client.get(f"/meetings/{checkout_id}", headers=sam)
    assert sorted(item["other_name"] for item in sent) == ["Maya Lee", "Sam Lee"]
    assert {item["video_link"] for item in sent} == {"https://meet.example.com/abc"}
    assert all(item["book_title"] == "Maya's book" for item in sent)

    # Too far off, or already started: no reminder.
    sent.clear()
    await database.meetings.update_one(
        {"_id": checkout_id}, {"$set": {"start": datetime.now(UTC) + timedelta(days=3)}}
    )
    await client.get(f"/meetings/{checkout_id}", headers=sam)
    await database.meetings.update_one(
        {"_id": checkout_id}, {"$set": {"start": datetime.now(UTC) - timedelta(hours=1)}}
    )
    await client.get(f"/meetings/{checkout_id}", headers=sam)
    assert sent == []


async def test_a_reminder_email_names_the_meeting(client, database, capsys):
    checkout_id, _, _ = await accepted_pair(client, database)
    maya_id = await _id(database, "Maya")
    result = await notify_meeting_reminder(
        database,
        checkout_id=checkout_id,
        user_id=maya_id,
        other_name="Sam Lee",
        book_title="Maya's book",
        start=slot(1, 15, 30),
        video_link="https://meet.example.com/abc",
        place_note=None,
    )
    assert result == "logged"  # no SMTP in tests, so it is printed instead of sent
    printed = capsys.readouterr().out
    assert "Sam Lee" in printed
    assert "15:30 UTC" in printed
    assert "https://meet.example.com/abc" in printed


async def test_deleting_an_account_removes_its_meetings(client, database):
    checkout_id, maya, sam = await accepted_pair(client, database)
    await client.put(f"/meetings/{checkout_id}/times", json={"times": iso(slot(3))}, headers=maya)
    # A meeting between two other members is left alone.
    await database.meetings.insert_one({"_id": "other", "reader_id": "x", "author_id": "y", "times": {}})
    assert await database.meetings.count_documents({}) == 2

    response = await client.request("DELETE", "/auth/me", json={"email": "sam@example.com"}, headers=sam)
    assert response.status_code == 204
    assert [m["_id"] async for m in database.meetings.find()] == ["other"]
