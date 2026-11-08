from datetime import UTC, datetime, timedelta

from trove.books.samples import SAMPLES, remove_samples, seed_samples
from trove.books.service import get_book_of, get_public_book, list_shelf

SIGNUP = {
    "first_name": "Maya",
    "last_name": "Okafor",
    "email": "maya@example.com",
    "password": "a long test passphrase",
}
NOW = datetime.now(UTC).replace(microsecond=0)


async def sign_in(client) -> tuple[dict, str]:
    """Sign up and in; returns (the account, auth headers)."""
    account = (await client.post("/auth/signup", json=SIGNUP)).json()
    login = await client.post("/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]})
    return account, {"Authorization": f"Bearer {login.json()['access_token']}"}


def book(number: int, **fields) -> dict:
    return {
        "_id": f"book-{number}",
        "author_id": f"author-{number}",
        "author_name": "Jordan",
        "title": f"Book {number}",
        "cover_style": "cover-1",
        "blurb": None,
        "chapters": [{"id": "c1", "title": "One thing", "summary": "About it.", "quotes": ["My own words."]}],
        "copies": 3,
        "status": "on_shelf",
        "published_at": NOW - timedelta(hours=number),
        "created_at": NOW,
        "updated_at": NOW,
        **fields,
    }


async def test_books_require_sign_in(client):
    assert (await client.get("/books")).status_code == 401
    assert (await client.get("/books/me")).status_code == 401
    assert (await client.get("/books/book-1")).status_code == 401


async def test_open_a_book(client, database):
    await database.books.insert_one(book(1, blurb="A blurb."))
    _, headers = await sign_in(client)

    response = await client.get("/books/book-1", headers=headers)
    assert response.status_code == 200
    assert response.json() == {
        "id": "book-1",
        "title": "Book 1",
        "author_name": "Jordan",
        "cover_style": "cover-1",
        "blurb": "A blurb.",
        "chapters": [{"id": "c1", "title": "One thing", "summary": "About it."}],
    }


async def test_books_show_the_authors_full_name_from_signup(client, database):
    account, headers = await sign_in(client)
    await database.books.insert_one(book(1, author_id=account["id"], author_name="Maya"))

    opened = await client.get("/books/book-1", headers=headers)
    assert opened.json()["author_name"] == "Maya Okafor"
    shelf = (await client.get("/books", headers=headers)).json()
    assert shelf["books"][0]["author_name"] == "Maya Okafor"
    assert (await client.get("/books/me", headers=headers)).json()["author_name"] == "Maya Okafor"
    # The account's email never comes with the name.
    assert "maya@example.com" not in opened.text + str(shelf)


async def test_reader_view_never_has_employer_contacts_or_counts(client, database):
    # Even if private details end up on the document, they never reach a reader.
    await database.books.insert_one(
        book(1, employer="Acme Corp", job_title="CTO", email="jordan@example.com", phone="216-555-0100")
    )
    _, headers = await sign_in(client)

    for path in ("/books/book-1", "/books"):
        text = (await client.get(path, headers=headers)).text
        for private in (
            "Acme Corp",
            "CTO",
            "jordan@example.com",
            "216-555-0100",
            "author-1",
            "copies",
            "My own words.",
        ):
            assert private not in text


async def test_unknown_or_draft_book_is_404(client, database):
    await database.books.insert_one(book(1, status="draft"))
    _, headers = await sign_in(client)
    assert (await client.get("/books/book-1", headers=headers)).status_code == 404
    assert (await client.get("/books/nope", headers=headers)).status_code == 404


async def test_my_book(client, database):
    account, headers = await sign_in(client)
    response = await client.get("/books/me", headers=headers)
    assert response.status_code == 404

    await database.books.insert_one(book(1, author_id=account["id"], status="draft", published_at=None))
    mine = (await client.get("/books/me", headers=headers)).json()
    assert mine["status"] == "draft"
    assert mine["copies"] == 3
    assert mine["chapters"][0]["quotes"] == ["My own words."]


async def test_shelf_is_newest_first_and_pages(client, database):
    await database.books.insert_many([book(n) for n in range(1, 6)])
    await database.books.insert_one(book(0, status="draft"))
    _, headers = await sign_in(client)

    first = (await client.get("/books", params={"limit": 2}, headers=headers)).json()
    assert [b["id"] for b in first["books"]] == ["book-1", "book-2"]
    second = (await client.get("/books", params={"limit": 2, "after": first["next"]}, headers=headers)).json()
    assert [b["id"] for b in second["books"]] == ["book-3", "book-4"]
    last = (await client.get("/books", params={"limit": 2, "after": second["next"]}, headers=headers)).json()
    assert [b["id"] for b in last["books"]] == ["book-5"]
    assert last["next"] is None


async def test_shelf_rejects_a_bad_cursor(client):
    _, headers = await sign_in(client)
    response = await client.get("/books", params={"after": "not a cursor"}, headers=headers)
    assert response.status_code == 422


async def test_contract_functions(database):
    await database.books.insert_one(book(1))
    public = await get_public_book(database, "book-1")
    # Other features need the author and copies for their own logic, but never the grounding quotes.
    assert public["author_id"] == "author-1"
    assert public["copies"] == 3
    assert "quotes" not in public["chapters"][0]
    assert (await get_book_of(database, "author-1"))["_id"] == "book-1"
    assert await get_book_of(database, "someone-else") is None
    assert [b["_id"] for b in await list_shelf(database, limit=10)] == ["book-1"]


async def test_seed_is_repeatable_and_removes_only_samples(client, database):
    await database.books.insert_one(book(1))
    await seed_samples(database)
    await seed_samples(database)
    assert await database.books.count_documents({"is_sample": True}) == len(SAMPLES)

    _, headers = await sign_in(client)
    shelf = (await client.get("/books", params={"limit": 50}, headers=headers)).json()["books"]
    samples = [b for b in shelf if b["id"] != "book-1"]
    assert len(samples) == len(SAMPLES)
    opened = await client.get(f"/books/{samples[0]['id']}", headers=headers)
    assert opened.status_code == 200
    assert "is_sample" not in opened.text  # samples aren't labelled for readers (yet)

    assert await remove_samples(database) == len(SAMPLES)
    assert await database.books.count_documents({}) == 1


def test_samples_have_invented_full_names():
    for author_name, *_ in SAMPLES:
        first, last = author_name.split(" ")
        assert first.isalpha() and last.isalpha(), author_name
