"""The one-service setup used for hosting: the API under /api, the built website everywhere else."""

import pytest
from httpx import ASGITransport, AsyncClient

from trove.serve import build_site


@pytest.fixture
def dist(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<html>the app</html>")
    (tmp_path / "assets" / "app-3f9c.js").write_text("console.log('app')")
    return tmp_path


async def get(site, path: str):
    async with AsyncClient(transport=ASGITransport(app=site), base_url="http://test") as http:
        return await http.get(path)


async def test_the_api_answers_under_api(dist):
    response = await get(build_site(dist), "/api/auth/me")
    assert response.status_code == 401  # the API's own answer, not the website's page
    assert response.headers["cache-control"] == "no-store"


async def test_the_home_page_and_app_routes_get_the_app(dist):
    site = build_site(dist)
    for path in ("/", "/checkouts", "/checkouts/abc/meeting", "/sign-up"):
        response = await get(site, path)
        assert response.status_code == 200, path
        assert "the app" in response.text
        # The page is always asked for again, so a new release reaches people.
        assert response.headers["cache-control"] == "no-cache"


async def test_built_files_are_kept_for_a_year(dist):
    response = await get(build_site(dist), "/assets/app-3f9c.js")
    assert response.status_code == 200
    assert "immutable" in response.headers["cache-control"]


async def test_a_missing_file_is_a_404_not_the_app(dist):
    response = await get(build_site(dist), "/assets/gone-1a2b.js")
    assert response.status_code == 404


async def test_files_outside_the_website_cannot_be_read(dist, tmp_path_factory):
    secret = tmp_path_factory.mktemp("elsewhere") / "secret.txt"
    secret.write_text("private")
    for path in ("/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"):
        response = await get(build_site(dist), path)
        assert "private" not in response.text


async def test_without_a_built_website_only_the_api_runs(tmp_path):
    site = build_site(tmp_path / "missing")
    assert (await get(site, "/api/auth/me")).status_code == 401
    assert (await get(site, "/")).status_code == 404


async def test_the_api_docs_are_not_on_the_site_root(dist):
    # The root has no /docs of its own; under /api the API keeps its own.
    response = await get(build_site(dist), "/openapi.json")
    assert "openapi" not in response.text[:50]
