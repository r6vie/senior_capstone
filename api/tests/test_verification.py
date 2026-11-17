"""CWRU verification (docs/trove.md §9.2): a case.edu code for students, an invite for alumni."""

from datetime import UTC, datetime, timedelta

import pytest

from trove.auth import verification
from trove.core.config import get_settings

STUDENT = {
    "first_name": "Sam",
    "last_name": "Lee",
    "email": "sam@case.edu",
    "password": "a long test passphrase",
}
ALUM = {**STUDENT, "first_name": "Ada", "email": "ada@gmail.com"}


@pytest.fixture(autouse=True)
def verification_on(monkeypatch):
    monkeypatch.setattr(get_settings(), "verification_required", True)


@pytest.fixture
def sent_codes(monkeypatch):
    """Capture the codes that would be emailed instead of printing them."""
    codes = []

    async def record(database, user_id, code, email):
        codes.append((email, code))

    monkeypatch.setattr("trove.auth.router.notify_verification_code", record)
    monkeypatch.setattr("trove.auth.verify_router.notify_verification_code", record)
    return codes


async def make_member(client, database, email="host@case.edu") -> dict:
    """A verified member with a session, made directly so tests of invites don't depend on codes."""
    await client.post("/auth/signup", json={**STUDENT, "email": email})
    await database.users.update_one({"email": email}, {"$set": {"verified": True}})
    login = await client.post("/auth/login", json={"email": email, "password": STUDENT["password"]})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def invite_token(client, headers) -> str:
    made = await client.post("/auth/invites", headers=headers)
    return made.json()["link"].split("invite=")[1]


async def test_a_student_signs_up_verifies_and_signs_in(client, sent_codes):
    response = await client.post("/auth/signup", json=STUDENT)
    assert response.status_code == 201
    assert response.json()["verified"] is False
    assert sent_codes[0][0] == "sam@case.edu"
    login = {"email": STUDENT["email"], "password": STUDENT["password"]}

    # Right password, but not verified yet.
    assert (await client.post("/auth/login", json=login)).status_code == 403

    verified = await client.post("/auth/verify", json={"email": "Sam@case.edu", "code": sent_codes[0][1]})
    assert verified.status_code == 200
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {verified.json()['access_token']}"})
    assert me.json()["verified"] is True
    assert (await client.post("/auth/login", json=login)).status_code == 200


async def test_the_code_is_stored_as_a_hash(client, database, sent_codes):
    await client.post("/auth/signup", json=STUDENT)
    stored = (await database.users.find_one({"email": "sam@case.edu"}))["verification"]
    assert sent_codes[0][1] not in str(stored)


async def test_only_exactly_case_edu_counts(client, sent_codes):
    for email in ("sam@alumni.case.edu", "sam@case.edu.evil.com", "sam@notcase.edu", "sam@gmail.com"):
        response = await client.post("/auth/signup", json={**STUDENT, "email": email})
        assert response.status_code == 422, email
        assert "case.edu" in response.json()["detail"]
    assert sent_codes == []


async def test_a_wrong_code_is_refused_and_five_tries_kill_the_code(client, sent_codes):
    await client.post("/auth/signup", json=STUDENT)
    right = sent_codes[0][1]
    wrong = "000000" if right != "000000" else "111111"
    for _ in range(5):
        response = await client.post("/auth/verify", json={"email": STUDENT["email"], "code": wrong})
        assert response.status_code == 400
    # Even the right code no longer works until a new one is sent.
    assert (
        await client.post("/auth/verify", json={"email": STUDENT["email"], "code": right})
    ).status_code == 400


async def test_an_expired_code_is_refused(client, database, sent_codes):
    await client.post("/auth/signup", json=STUDENT)
    await database.users.update_one(
        {"email": "sam@case.edu"},
        {"$set": {"verification.expires_at": datetime.now(UTC) - timedelta(seconds=1)}},
    )
    response = await client.post("/auth/verify", json={"email": STUDENT["email"], "code": sent_codes[0][1]})
    assert response.status_code == 400


async def test_a_code_must_be_six_digits(client):
    response = await client.post("/auth/verify", json={"email": STUDENT["email"], "code": "12ab56"})
    assert response.status_code == 422


async def test_resend_sends_a_new_code_but_not_twice_in_a_minute(client, database, sent_codes):
    await client.post("/auth/signup", json=STUDENT)
    body = {"email": STUDENT["email"]}
    assert (await client.post("/auth/verify/resend", json=body)).status_code == 204
    assert len(sent_codes) == 1  # too soon after the first one

    too_long_ago = datetime.now(UTC) - timedelta(seconds=verification.RESEND_SECONDS + 1)
    await database.users.update_one(
        {"email": "sam@case.edu"}, {"$set": {"verification.sent_at": too_long_ago}}
    )
    assert (await client.post("/auth/verify/resend", json=body)).status_code == 204
    assert len(sent_codes) == 2
    assert (await client.post("/auth/verify", json={**body, "code": sent_codes[1][1]})).status_code == 200


async def test_resend_does_not_reveal_which_emails_have_accounts(client, sent_codes):
    response = await client.post("/auth/verify/resend", json={"email": "nobody@case.edu"})
    assert response.status_code == 204
    assert sent_codes == []


async def test_signing_up_again_before_verifying_replaces_the_unverified_account(
    client, database, sent_codes
):
    first_password = "the first long passphrase"
    await client.post("/auth/signup", json={**STUDENT, "password": first_password})
    await client.post("/auth/signup", json={**STUDENT, "first_name": "Samuel"})
    assert await database.users.count_documents({"email": "sam@case.edu"}) == 1
    verified = await client.post("/auth/verify", json={"email": STUDENT["email"], "code": sent_codes[-1][1]})
    assert verified.status_code == 200
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {verified.json()['access_token']}"})
    assert me.json()["first_name"] == "Samuel"
    # The first password no longer works.
    login = await client.post("/auth/login", json={"email": STUDENT["email"], "password": first_password})
    assert login.status_code == 401


async def test_a_verified_account_cannot_be_taken_over(client, database, sent_codes):
    headers = await make_member(client, database, "sam@case.edu")
    response = await client.post("/auth/signup", json={**STUDENT, "password": "someone elses passphrase"})
    assert response.status_code == 409
    assert (await client.get("/auth/me", headers=headers)).status_code == 200


async def test_old_accounts_without_the_flag_count_as_verified(client, database):
    await client.post("/auth/signup", json=STUDENT)
    await database.users.update_one(
        {"email": "sam@case.edu"}, {"$unset": {"verified": "", "verification": ""}}
    )
    login = await client.post(
        "/auth/login", json={"email": STUDENT["email"], "password": STUDENT["password"]}
    )
    assert login.status_code == 200


async def test_an_alum_joins_with_an_invite_and_it_works_once(client, database, sent_codes):
    host = await make_member(client, database)
    token = await invite_token(client, host)
    codes_before = len(sent_codes)

    joined = await client.post("/auth/signup", json={**ALUM, "invite": token})
    assert joined.status_code == 201
    assert joined.json()["verified"] is True
    assert len(sent_codes) == codes_before  # no code for an invited alum
    login = await client.post("/auth/login", json={"email": ALUM["email"], "password": ALUM["password"]})
    assert login.status_code == 200
    host_id = (await database.users.find_one({"email": "host@case.edu"}))["_id"]
    assert (await database.users.find_one({"email": "ada@gmail.com"}))["invited_by"] == host_id

    second = await client.post("/auth/signup", json={**ALUM, "email": "bo@gmail.com", "invite": token})
    assert second.status_code == 422
    assert (await client.get("/auth/invites", headers=host)).json() == []


async def test_the_token_is_only_stored_as_a_hash(client, database):
    host = await make_member(client, database)
    token = await invite_token(client, host)
    assert token not in str(await database.invites.find_one({}))


async def test_a_failed_sign_up_gives_the_invite_back(client, database):
    host = await make_member(client, database)
    token = await invite_token(client, host)
    await make_member(client, database, "ada@case.edu")  # the email is already taken
    taken = await client.post("/auth/signup", json={**ALUM, "email": "ada@case.edu", "invite": token})
    assert taken.status_code == 409
    fresh = await client.post("/auth/signup", json={**ALUM, "email": "bo@gmail.com", "invite": token})
    assert fresh.status_code == 201


async def test_an_expired_or_made_up_invite_is_refused(client, database):
    host = await make_member(client, database)
    token = await invite_token(client, host)
    await database.invites.update_many({}, {"$set": {"expires_at": datetime.now(UTC) - timedelta(seconds=1)}})
    assert (await client.post("/auth/signup", json={**ALUM, "invite": token})).status_code == 422
    assert (await client.post("/auth/signup", json={**ALUM, "invite": "made-up"})).status_code == 422
    assert (await client.post("/auth/invites/check", json={"invite": token})).status_code == 404


async def test_the_sign_up_page_can_ask_who_invited_you(client, database):
    host = await make_member(client, database)
    token = await invite_token(client, host)
    checked = await client.post("/auth/invites/check", json={"invite": token})
    assert checked.json() == {"inviter_name": "Sam Lee"}
    # Looking doesn't use it up.
    assert (await client.post("/auth/signup", json={**ALUM, "invite": token})).status_code == 201


async def test_five_open_invites_at_most_and_cancelling_makes_room(client, database):
    host = await make_member(client, database)
    made = [await client.post("/auth/invites", headers=host) for _ in range(5)]
    assert all(response.status_code == 201 for response in made)
    assert (await client.post("/auth/invites", headers=host)).status_code == 409
    listed = (await client.get("/auth/invites", headers=host)).json()
    assert len(listed) == 5
    assert "link" not in listed[0]
    assert (await client.delete(f"/auth/invites/{listed[0]['id']}", headers=host)).status_code == 204
    assert (await client.post("/auth/invites", headers=host)).status_code == 201


async def test_you_cannot_cancel_someone_elses_invite(client, database):
    host = await make_member(client, database)
    other = await make_member(client, database, "other@case.edu")
    invite_id = (await client.post("/auth/invites", headers=host)).json()["id"]
    assert (await client.delete(f"/auth/invites/{invite_id}", headers=other)).status_code == 404


async def test_invites_need_a_signed_in_member(client):
    assert (await client.post("/auth/invites")).status_code == 401
    assert (await client.get("/auth/invites")).status_code == 401


async def test_deleting_an_account_removes_its_invites_but_not_the_people_it_invited(client, database):
    host = await make_member(client, database)
    token = await invite_token(client, host)
    await client.post("/auth/invites", headers=host)
    await client.post("/auth/signup", json={**ALUM, "invite": token})
    deleted = await client.request("DELETE", "/auth/me", json={"email": "host@case.edu"}, headers=host)
    assert deleted.status_code == 204
    assert await database.invites.count_documents({}) == 0
    assert await database.users.count_documents({"email": "ada@gmail.com"}) == 1


async def test_with_verification_off_anyone_can_sign_up(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "verification_required", False)
    response = await client.post("/auth/signup", json=ALUM)
    assert response.status_code == 201
    assert response.json()["verified"] is True


async def test_the_code_email_prints_when_email_is_not_configured(client, capsys):
    await client.post("/auth/signup", json=STUDENT)
    await client.post("/auth/verify/resend", json={"email": STUDENT["email"]})
    assert "Your Trove code:" in capsys.readouterr().out
