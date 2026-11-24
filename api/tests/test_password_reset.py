"""Forgot your password: a 6-digit code by email, then a new password."""

from datetime import UTC, datetime, timedelta

import pytest

from trove.auth import verification

MEMBER = {
    "first_name": "Rui",
    "last_name": "Okafor",
    "email": "rui@example.com",
    "password": "the original passphrase",
}
NEW_PASSWORD = "a brand new passphrase"


@pytest.fixture
def sent_codes(monkeypatch):
    """Capture the codes that would be emailed."""
    codes = []

    async def record(database, user_id, code, email):
        codes.append((email, code))

    monkeypatch.setattr("trove.auth.router.notify_password_reset_code", record)
    return codes


@pytest.fixture
async def member(client):
    await client.post("/auth/signup", json=MEMBER)
    login = await client.post("/auth/login", json={"email": MEMBER["email"], "password": MEMBER["password"]})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def forgot(client, email=MEMBER["email"]):
    return await client.post("/auth/password/forgot", json={"email": email})


async def reset(client, code, password=NEW_PASSWORD, email=MEMBER["email"]):
    return await client.post(
        "/auth/password/reset", json={"email": email, "code": code, "new_password": password}
    )


async def login(client, password):
    return await client.post("/auth/login", json={"email": MEMBER["email"], "password": password})


def wrong(code: str) -> str:
    return f"{(int(code) + 1) % 10**6:06d}"


async def test_a_member_resets_their_password_and_signs_in_with_it(client, database, member, sent_codes):
    assert (await forgot(client, "Rui@Example.com")).status_code == 204
    [(email, code)] = sent_codes
    assert email == "rui@example.com"
    assert code not in str((await database.users.find_one({"email": email}))["password_reset"])

    assert (await reset(client, code)).status_code == 204
    assert (await login(client, MEMBER["password"])).status_code == 401
    assert (await login(client, NEW_PASSWORD)).status_code == 200
    # The old session is signed out, and the code can't be used twice.
    assert (await client.get("/auth/me", headers=member)).status_code == 401
    assert (await reset(client, code, "yet another passphrase")).status_code == 400


async def test_an_unknown_email_gets_the_same_answer_and_no_email(client, sent_codes):
    response = await forgot(client, "nobody@example.com")
    assert response.status_code == 204
    assert sent_codes == []
    assert (await reset(client, "123456", email="nobody@example.com")).status_code == 400


async def test_a_wrong_code_changes_nothing(client, member, sent_codes):
    await forgot(client)
    [(_, code)] = sent_codes
    response = await reset(client, wrong(code))
    assert response.status_code == 400
    assert "new one" in response.json()["detail"]
    assert (await login(client, MEMBER["password"])).status_code == 200
    # The right code still works after one miss.
    assert (await reset(client, code)).status_code == 204


async def test_an_expired_code_is_refused(client, database, member, sent_codes):
    await forgot(client)
    [(_, code)] = sent_codes
    await database.users.update_one(
        {"email": MEMBER["email"]},
        {"$set": {"password_reset.expires_at": datetime.now(UTC) - timedelta(seconds=1)}},
    )
    assert (await reset(client, code)).status_code == 400
    assert (await login(client, MEMBER["password"])).status_code == 200


async def test_five_wrong_tries_end_the_code(client, member, sent_codes):
    await forgot(client)
    [(_, code)] = sent_codes
    for _ in range(verification.MAX_ATTEMPTS):
        assert (await reset(client, wrong(code))).status_code == 400
    assert (await reset(client, code)).status_code == 400
    assert (await login(client, MEMBER["password"])).status_code == 200


async def test_one_code_a_minute(client, database, member, sent_codes):
    await forgot(client)
    await forgot(client)
    assert len(sent_codes) == 1
    await database.users.update_one(
        {"email": MEMBER["email"]},
        {"$set": {"password_reset.sent_at": datetime.now(UTC) - timedelta(seconds=61)}},
    )
    await forgot(client)
    assert len(sent_codes) == 2
    # Only the newest code works.
    assert (await reset(client, sent_codes[0][1])).status_code == 400
    assert (await reset(client, sent_codes[1][1])).status_code == 204


async def test_the_new_password_follows_the_sign_up_rules(client, member, sent_codes):
    await forgot(client)
    [(_, code)] = sent_codes
    assert (await reset(client, code, "too short")).status_code == 422
    assert (await reset(client, code, " " * 12)).status_code == 422
    assert (await reset(client, code)).status_code == 204


async def test_a_reset_leaves_a_pending_sign_up_code_alone(client, database, member, sent_codes):
    record = {"code_hash": "x", "expires_at": datetime.now(UTC), "sent_at": datetime.now(UTC), "attempts": 0}
    await database.users.update_one({"email": MEMBER["email"]}, {"$set": {"verification": record}})
    await forgot(client)
    assert (await database.users.find_one({"email": MEMBER["email"]}))["verification"]["code_hash"] == "x"


async def test_forgot_is_rate_limited(client, sent_codes):
    for _ in range(5):
        assert (await forgot(client, "nobody@example.com")).status_code == 204
    assert (await forgot(client, "nobody@example.com")).status_code == 429


async def test_the_email_goes_out_even_with_notifications_off(client, database, member, capsys):
    from trove.notifications.service import notify_password_reset_code

    await database.users.update_one({"email": MEMBER["email"]}, {"$set": {"email_notifications": False}})
    user = await database.users.find_one({"email": MEMBER["email"]})
    assert await notify_password_reset_code(database, user["_id"], "654321", MEMBER["email"]) == "logged"
    printed = capsys.readouterr().out
    assert "654321" in printed and "/reset-password?email=rui%40example.com" in printed
