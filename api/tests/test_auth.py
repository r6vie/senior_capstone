SIGNUP = {"first_name": "Maya", "email": "Maya@Example.com", "password": "a long test passphrase"}


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
