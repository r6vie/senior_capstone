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
