async def test_health_reports_database_state(client_without_database):
    response = await client_without_database.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "database": False}
    assert response.headers["cache-control"] == "no-store"


async def test_database_routes_return_503_without_a_database(client_without_database):
    response = await client_without_database.post(
        "/auth/login", json={"email": "a@example.com", "password": "x"}
    )
    assert response.status_code == 503
