import pytest

SIGNUP = {
    "first_name": "Maya",
    "last_name": "Okafor",
    "email": "Maya@Example.com",
    "password": "a long test passphrase",
}


async def sign_in(client) -> str:
    await client.post("/auth/signup", json=SIGNUP)
    response = await client.post(
        "/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


async def test_signup_login_me_logout(client):
    response = await client.post("/auth/signup", json=SIGNUP)
    assert response.status_code == 201
    assert response.json()["email"] == "maya@example.com"  # emails are case-insensitive
    assert "password" not in response.text

    token = await sign_in(client)
    headers = {"Authorization": f"Bearer {token}"}
    me = await client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["first_name"] == "Maya"
    assert me.json()["last_name"] == "Okafor"
    assert me.json()["full_name"] == "Maya Okafor"

    assert (await client.post("/auth/logout", headers=headers)).status_code == 204
    assert (await client.get("/auth/me", headers=headers)).status_code == 401


async def test_duplicate_email_is_rejected(client):
    await client.post("/auth/signup", json=SIGNUP)
    response = await client.post("/auth/signup", json={**SIGNUP, "email": "maya@example.com"})
    assert response.status_code == 409


async def test_wrong_password_is_rejected(client):
    await client.post("/auth/signup", json=SIGNUP)
    response = await client.post("/auth/login", json={"email": SIGNUP["email"], "password": "wrong password"})
    assert response.status_code == 401


async def test_validation_errors_never_echo_the_password(client):
    response = await client.post("/auth/signup", json={**SIGNUP, "password": "pw-7Xq"})
    assert response.status_code == 422
    assert "pw-7Xq" not in response.text


async def test_signup_needs_a_last_name(client):
    missing = {key: value for key, value in SIGNUP.items() if key != "last_name"}
    assert (await client.post("/auth/signup", json=missing)).status_code == 422
    assert (await client.post("/auth/signup", json={**SIGNUP, "last_name": "   "})).status_code == 422
    assert (await client.post("/auth/signup", json={**SIGNUP, "last_name": "x" * 61})).status_code == 422
    response = await client.post("/auth/signup", json={**SIGNUP, "last_name": "  Okafor "})
    assert response.json()["last_name"] == "Okafor"


async def test_members_can_set_and_change_their_name(client, database):
    token = await sign_in(client)
    headers = {"Authorization": f"Bearer {token}"}
    # Accounts made before last names were collected show the first name alone.
    await database.users.update_one({}, {"$unset": {"last_name": ""}})
    me = (await client.get("/auth/me", headers=headers)).json()
    assert me["last_name"] is None
    assert me["full_name"] == "Maya"

    response = await client.patch("/auth/me", json={"last_name": "Adeyemi"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Maya Adeyemi"
    response = await client.patch("/auth/me", json={"first_name": "May"}, headers=headers)
    assert response.json()["full_name"] == "May Adeyemi"
    assert (await client.get("/auth/me", headers=headers)).json()["full_name"] == "May Adeyemi"


async def test_name_changes_are_validated(client):
    token = await sign_in(client)
    headers = {"Authorization": f"Bearer {token}"}
    assert (await client.patch("/auth/me", json={}, headers=headers)).status_code == 422
    assert (await client.patch("/auth/me", json={"last_name": ""}, headers=headers)).status_code == 422
    assert (
        await client.patch("/auth/me", json={"email": "new@example.com"}, headers=headers)
    ).status_code == 422
    assert (await client.patch("/auth/me", json={"last_name": "Okafor"})).status_code == 401


# ---- Account basics (plan item A1) ----


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def test_contact_details_start_as_the_sign_in_email_only(client):
    headers = auth(await sign_in(client))
    response = await client.get("/auth/me/contact", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"email": "maya@example.com", "linkedin_url": None, "phone": None}


async def test_members_choose_and_clear_their_contact_details(client):
    headers = auth(await sign_in(client))
    details = {"linkedin_url": " https://www.linkedin.com/in/maya-okafor/ ", "phone": "+1 (216) 555-0142"}
    response = await client.put("/auth/me/contact", json=details, headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "email": "maya@example.com",
        "linkedin_url": "https://www.linkedin.com/in/maya-okafor/",
        "phone": "+1 (216) 555-0142",
    }
    assert (await client.get("/auth/me/contact", headers=headers)).json() == response.json()

    # Sending one detail, or blank fields, stops sharing the others.
    response = await client.put(
        "/auth/me/contact", json={"phone": "216-555-0142", "linkedin_url": "  "}, headers=headers
    )
    assert response.json()["linkedin_url"] is None
    assert response.json()["phone"] == "216-555-0142"
    response = await client.put("/auth/me/contact", json={}, headers=headers)
    assert response.json() == {"email": "maya@example.com", "linkedin_url": None, "phone": None}


async def test_contact_details_are_checked(client):
    headers = auth(await sign_in(client))
    for bad in (
        {"linkedin_url": "http://www.linkedin.com/in/maya"},
        {"linkedin_url": "https://evil.example/in/maya"},
        {"linkedin_url": "https://www.linkedin.com.evil.example/in/maya"},
        {"linkedin_url": "https://www.linkedin.com/in/maya/../admin"},
        {"linkedin_url": "javascript:alert(1)"},
        {"phone": "call me"},
        {"phone": "12345"},
        {"phone": "1" * 16},
        {"phone": 5551234567},
        {"email": "other@example.com"},
    ):
        response = await client.put("/auth/me/contact", json=bad, headers=headers)
        assert response.status_code == 422, bad
    unchanged = await client.get("/auth/me/contact", headers=headers)
    assert unchanged.json() == {"email": "maya@example.com", "linkedin_url": None, "phone": None}


async def test_account_routes_need_sign_in(client):
    assert (await client.get("/auth/me/contact")).status_code == 401
    assert (await client.put("/auth/me/contact", json={})).status_code == 401
    assert (
        await client.put("/auth/me/notifications", json={"email_notifications": False})
    ).status_code == 401
    assert (await client.request("DELETE", "/auth/me", json={"email": "a@example.com"})).status_code == 401


async def test_contact_details_stay_off_the_account_response(client):
    headers = auth(await sign_in(client))
    await client.put("/auth/me/contact", json={"phone": "216-555-0142"}, headers=headers)
    me = await client.get("/auth/me", headers=headers)
    assert "216" not in me.text
    assert "phone" not in me.json()


async def test_contract_functions_for_other_features(client, database):
    from trove.auth.service import contact_details_of, first_name_of

    headers = auth(await sign_in(client))
    user_id = (await client.get("/auth/me", headers=headers)).json()["id"]
    await client.put("/auth/me/contact", json={"phone": "216-555-0142"}, headers=headers)

    assert await first_name_of(database, user_id) == "Maya"
    details = await contact_details_of(database, user_id)
    assert details is not None
    assert (details.email, details.linkedin_url, details.phone) == ("maya@example.com", None, "216-555-0142")

    assert await first_name_of(database, "nobody") is None
    assert await contact_details_of(database, "nobody") is None
    await database.users.update_one({"_id": user_id}, {"$set": {"is_active": False}})
    assert await first_name_of(database, user_id) is None
    assert await contact_details_of(database, user_id) is None


async def test_members_turn_email_notifications_off_and_on(client, database):
    from trove.auth.service import email_recipient

    headers = auth(await sign_in(client))
    me = await client.get("/auth/me", headers=headers)
    assert me.json()["email_notifications"] is True
    user_id = me.json()["id"]

    response = await client.put(
        "/auth/me/notifications", json={"email_notifications": False}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["email_notifications"] is False
    assert (await client.get("/auth/me", headers=headers)).json()["email_notifications"] is False
    recipient = await email_recipient(database, user_id)
    assert recipient is not None
    assert recipient["email_notifications"] is False

    response = await client.put("/auth/me/notifications", json={"email_notifications": True}, headers=headers)
    assert response.json()["email_notifications"] is True
    bad = await client.put("/auth/me/notifications", json={"email_notifications": "no"}, headers=headers)
    assert bad.status_code == 422


async def test_deleting_an_account_needs_the_email_and_removes_everything(client, database):
    headers = auth(await sign_in(client))
    other = await client.post("/auth/signup", json={**SIGNUP, "email": "other@example.com"})
    assert other.status_code == 201

    wrong = await client.request("DELETE", "/auth/me", json={"email": "other@example.com"}, headers=headers)
    assert wrong.status_code == 422
    assert (await client.get("/auth/me", headers=headers)).status_code == 200

    response = await client.request("DELETE", "/auth/me", json={"email": "MAYA@example.com"}, headers=headers)
    assert response.status_code == 204
    assert (await client.get("/auth/me", headers=headers)).status_code == 401
    login = await client.post("/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]})
    assert login.status_code == 401
    assert await database.users.count_documents({"email": "maya@example.com"}) == 0
    assert await database.sessions.count_documents({}) == 0
    assert await database.users.count_documents({"email": "other@example.com"}) == 1  # only this account


async def test_other_features_clean_up_when_an_account_is_deleted(client, monkeypatch):
    from trove.auth import service

    calls: list[str] = []

    async def remove_book(db, user_id):
        calls.append(user_id)

    monkeypatch.setattr(service, "deletion_hooks", [])
    service.on_account_deleted(remove_book)
    headers = auth(await sign_in(client))
    user_id = (await client.get("/auth/me", headers=headers)).json()["id"]
    response = await client.request("DELETE", "/auth/me", json={"email": SIGNUP["email"]}, headers=headers)
    assert response.status_code == 204
    assert calls == [user_id]


async def test_a_failing_cleanup_keeps_the_account(client, monkeypatch):
    from trove.auth import service

    async def fails(db, user_id):
        raise RuntimeError("boom")

    monkeypatch.setattr(service, "deletion_hooks", [fails])
    headers = auth(await sign_in(client))
    with pytest.raises(RuntimeError):
        await client.request("DELETE", "/auth/me", json={"email": SIGNUP["email"]}, headers=headers)
    monkeypatch.setattr(service, "deletion_hooks", [])
    assert (await client.get("/auth/me", headers=headers)).status_code == 200
