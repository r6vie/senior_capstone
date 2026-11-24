"""Members editing their own book, taking it off the shelf, and what goes when an account is deleted."""

import json
from datetime import UTC, datetime

import pytest

from tests.fakes import text_message
from tests.test_growing_books import (
    CHAPTERS,
    OLD_ANSWER,
    change,
    member,
    propose,
    shelve_book,
    start_round,
    waiting_question,
)
from trove.books import service as books
from trove.checkouts import service as checkouts
from trove.interview import service as interview


@pytest.fixture
async def author(client, database):
    person = await member(client, "author@case.edu")
    person["book"] = await shelve_book(database, person["id"])
    return person


async def my_book(client, person) -> dict:
    return (await client.get("/books/me", headers=person["headers"])).json()


async def edit(client, person, **body):
    return await client.patch("/books/me", json=body, headers=person["headers"])


async def edit_chapter(client, person, chapter_id: str, **body):
    return await client.patch(f"/books/me/chapters/{chapter_id}", json=body, headers=person["headers"])


# Editing a book on the shelf.


async def test_an_edit_on_the_shelf_is_live_at_once_and_undo_takes_it_back(client, database, author):
    reader = await member(client, "reader@case.edu", "Rae", "Jones")
    before = await database.books.find_one({"author_id": author["id"]})

    response = await edit(client, author, title="  Thick Without Gums  ", blurb="My own words on the back.")
    assert response.status_code == 200, response.text
    book = response.json()
    assert book["title"] == "Thick Without Gums"
    assert book["blurb"] == "My own words on the back."
    assert book["can_undo"] is True
    seen = (await client.get(f"/books/{book['id']}", headers=reader["headers"])).json()
    assert seen["title"] == "Thick Without Gums"
    after = await database.books.find_one({"author_id": author["id"]})
    assert after["published_at"] == before["published_at"]

    undone = (await client.post("/interview/book/undo", headers=author["headers"])).json()
    assert undone["title"] == "The Book"
    assert undone["blurb"] == "The old blurb."
    assert undone["can_undo"] is False


async def test_a_chapter_edit_keeps_its_quotes_and_can_be_undone(client, database, author):
    response = await edit_chapter(client, author, "c1", summary="I ran the schedule nobody else would touch.")
    assert response.status_code == 200, response.text
    chapter = response.json()["chapters"][1]
    assert chapter["summary"] == "I ran the schedule nobody else would touch."
    assert chapter["title"] == "Chapter 1"
    assert chapter["quotes"] == [OLD_ANSWER]

    undone = (await client.post("/interview/book/undo", headers=author["headers"])).json()
    assert undone["chapters"][1]["summary"] == "Summary 1."


async def test_undoing_an_edit_doesnt_put_the_members_words_off_limits(client, database, author):
    await edit_chapter(client, author, "c0", title="My own title")
    await client.post("/interview/book/undo", headers=author["headers"])
    saved = await database.interviews.find_one({"user_id": author["id"]})
    assert not saved.get("declined_changes")


async def test_undo_takes_back_only_the_last_change(client, author):
    await edit(client, author, title="First try")
    await edit(client, author, title="Second try")
    undone = (await client.post("/interview/book/undo", headers=author["headers"])).json()
    assert undone["title"] == "First try"
    assert (await client.post("/interview/book/undo", headers=author["headers"])).status_code == 409


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": "x" * 81},
        {"blurb": "x" * 601},
        {"title": 3},
        {"title": "A title", "copies": 10},
    ],
)
async def test_bad_book_edits_are_refused(client, author, body):
    assert (await edit(client, author, **body)).status_code == 422
    assert (await my_book(client, author))["title"] == "The Book"


@pytest.mark.parametrize(
    "body",
    [{}, {"summary": ""}, {"summary": "x" * 301}, {"title": "x" * 101}],
)
async def test_bad_chapter_edits_are_refused(client, author, body):
    assert (await edit_chapter(client, author, "c0", **body)).status_code == 422


async def test_an_unknown_chapter_is_404(client, author):
    assert (await edit_chapter(client, author, "nope", title="New")).status_code == 404


@pytest.mark.parametrize(
    "text",
    [
        "Write to me at hana.sato@case.edu any time.",
        "See https://hanasato.dev for more.",
        "My site, hanasato.com, has the rest.",
        "Find me at www.example.org.",
        "Call me on (216) 555-0134 after six.",
        "Text 216.368.4000 and ask for me.",
        "Ring 555-0134.",
    ],
)
async def test_contact_details_cant_go_on_a_book(client, author, text):
    for response in (
        await edit(client, author, blurb=text),
        await edit_chapter(client, author, "c0", summary=text),
    ):
        assert response.status_code == 422
        assert response.json()["detail"] == books.CONTACT_REFUSED
    assert (await my_book(client, author))["blurb"] == "The old blurb."


async def test_ordinary_numbers_and_dots_are_fine(client, author):
    text = (
        "From 2019 to 2021 I cut waits from 25 minutes to under 10. It was 3.5 times faster, e.g. on Fridays."
    )
    assert (await edit(client, author, blurb=text)).status_code == 200


async def test_no_edits_while_proposed_changes_wait(client, author, fake_claude):
    await propose(client, author, fake_claude, change())
    for response in (
        await edit(client, author, title="Mid-proposal"),
        await edit_chapter(client, author, "c0", title="Mid-proposal"),
    ):
        assert response.status_code == 409
        assert "proposed changes waiting" in response.json()["detail"]


async def test_edits_are_fine_during_a_round_of_questions(client, author, fake_claude):
    await start_round(client, author, fake_claude)
    assert (await edit(client, author, title="Edited mid-round")).status_code == 200


# Editing a draft in review.


@pytest.fixture
async def drafter(client, database):
    person = await member(client, "draft@case.edu")
    await books.create_draft_book(
        database, author_id=person["id"], title="Draft", chapters=CHAPTERS, blurb="Draft blurb."
    )
    await database.interviews.insert_one(
        {
            "_id": "i-draft",
            "user_id": person["id"],
            "stage": "reviewing",
            "turns": [{"question": "Q?", "answer": OLD_ANSWER, "phase": "dig"}],
            "current": None,
            "draft": None,
        }
    )
    return person


async def test_a_draft_title_edit_stays_a_draft(client, drafter):
    edited = (await edit(client, drafter, title="My own title")).json()
    assert edited["title"] == "My own title"
    assert edited["status"] == "draft"
    assert edited["published_at"] is None


# Taking a book off the shelf.


async def test_taking_a_book_down_hides_it_and_putting_it_back_keeps_its_place(client, database, author):
    reader = await member(client, "reader@case.edu", "Rae", "Jones")
    other = await member(client, "other@case.edu", "Other", "Author")
    await shelve_book(database, other["id"])
    book_id = author["book"]["_id"]
    before = await database.books.find_one({"_id": book_id})

    down = await client.post("/books/me/take-down", headers=author["headers"])
    assert down.status_code == 200
    assert down.json()["status"] == "off_shelf"
    shelf = (await client.get("/books", headers=reader["headers"])).json()["books"]
    assert book_id not in [item["id"] for item in shelf]
    assert (await client.get(f"/books/{book_id}", headers=reader["headers"])).status_code == 404
    assert (await client.post("/books/me/take-down", headers=author["headers"])).status_code == 409

    back = await client.post("/books/me/put-back", headers=author["headers"])
    assert back.json()["status"] == "on_shelf"
    after = await database.books.find_one({"_id": book_id})
    assert after["published_at"] == before["published_at"]
    shelf = (await client.get("/books", headers=reader["headers"])).json()["books"]
    # Back in its old place: below the newer book, not on top.
    assert [item["id"] for item in shelf].index(book_id) == 1
    assert (await client.post("/books/me/put-back", headers=author["headers"])).status_code == 409


async def test_a_draft_cant_be_taken_down(client, drafter):
    assert (await client.post("/books/me/take-down", headers=drafter["headers"])).status_code == 409


async def test_no_new_checkouts_of_a_book_off_the_shelf(client, database, author):
    reader = await member(client, "reader@case.edu", "Rae", "Jones")
    await shelve_book(database, reader["id"])
    await client.post("/books/me/take-down", headers=author["headers"])
    with pytest.raises(checkouts.CheckoutRefused) as refused:
        await checkouts.check_out(
            database, reader_id=reader["id"], book_id=author["book"]["_id"], message="Can we talk?"
        )
    assert refused.value.detail == "This book isn't available right now."


@pytest.mark.parametrize("answer", ["accept", "decline"])
async def test_what_was_already_arranged_still_goes_ahead(client, database, author, answer):
    reader = await member(client, "reader@case.edu", "Rae", "Jones")
    await shelve_book(database, reader["id"])
    checkout = await checkouts.check_out(
        database, reader_id=reader["id"], book_id=author["book"]["_id"], message="Can we talk?"
    )
    await client.post("/books/me/take-down", headers=author["headers"])
    answered = await getattr(checkouts, answer)(database, checkout["_id"], author["id"])
    assert answered["status"] == ("accepted" if answer == "accept" else "declined")


async def test_the_author_works_on_a_book_off_the_shelf_as_before(client, database, author, fake_claude):
    await client.post("/books/me/take-down", headers=author["headers"])
    assert (await edit(client, author, title="Still mine")).status_code == 200
    assert (await client.post("/interview/book/undo", headers=author["headers"])).status_code == 200

    question = await waiting_question(client, database, author)
    fake_claude.responses.append(text_message(json.dumps({"changes": [change()], "blurb": "A blurb."})))
    response = await client.post(
        f"/interview/reading-questions/{question}/answer",
        json={"answer": "Last spring I ran the whole lab inventory by hand for six weeks straight."},
        headers=author["headers"],
    )
    assert response.status_code == 200
    state = (await client.get("/interview", headers=author["headers"])).json()
    ids = [item["id"] for item in state["changes"]]
    book = (
        await client.post("/interview/revision", json={"approved": ids}, headers=author["headers"])
    ).json()
    assert book["status"] == "off_shelf"
    assert book["chapters"][-1]["title"] == "New title"

    reopened = await start_round(client, author, fake_claude)
    assert reopened["stage"] == "adding"


# Deleting an account.


async def delete_account(client, person, email: str):
    return await client.request("DELETE", "/auth/me", json={"email": email}, headers=person["headers"])


async def test_deleting_an_account_takes_the_book_and_interview_with_it(client, database, author):
    reader = await member(client, "reader@case.edu", "Rae", "Jones")
    await database.resume_texts.insert_one(
        {"_id": f"interview-{author['id']}", "text": "A résumé.", "last_activity_at": datetime.now(UTC)}
    )
    await interview.ask_after_reading(database, author["id"], "checkout-1")
    # The author's own spark on someone else's book, and a reader's spark on the author's book.
    await shelve_book(database, reader["id"])
    reader_book = await database.books.find_one({"author_id": reader["id"]})
    await client.post(
        "/interview/sparks",
        json={"book_id": reader_book["_id"], "chapter_id": "c0"},
        headers=author["headers"],
    )
    unused = (
        await client.post(
            "/interview/sparks",
            json={"book_id": author["book"]["_id"], "chapter_id": "c0"},
            headers=reader["headers"],
        )
    ).json()
    used = (
        await client.post(
            "/interview/sparks",
            json={"book_id": author["book"]["_id"], "chapter_id": "c1"},
            headers=reader["headers"],
        )
    ).json()
    await database.sparks.update_one({"_id": used["id"]}, {"$set": {"used_at": datetime.now(UTC)}})

    assert (await delete_account(client, author, "author@case.edu")).status_code == 204

    assert await database.books.count_documents({"author_id": author["id"]}) == 0
    assert await database.interviews.count_documents({"user_id": author["id"]}) == 0
    assert await database.resume_texts.count_documents({}) == 0
    assert await database.reading_questions.count_documents({"author_id": author["id"]}) == 0
    assert await database.sparks.count_documents({"user_id": author["id"]}) == 0
    assert await database.sparks.find_one({"_id": unused["id"]}) is None
    # One that already fed the reader's interview was used up there; it's part of their history.
    assert await database.sparks.find_one({"_id": used["id"]}) is not None
    shelf = (await client.get("/books", headers=reader["headers"])).json()["books"]
    assert author["book"]["_id"] not in [item["id"] for item in shelf]
    assert (await client.get(f"/books/{author['book']['_id']}", headers=reader["headers"])).status_code == 404


async def test_the_cleanup_hooks_are_safe_to_run_twice(client, database, author):
    for _ in range(2):
        await books.delete_books_of(database, author["id"])
        await interview.delete_interview_of(database, author["id"])
    assert await database.books.count_documents({}) == 0
    assert await database.interviews.count_documents({}) == 0


async def test_a_spark_from_before_the_author_was_recorded_still_goes(client, database, author):
    reader = await member(client, "reader@case.edu", "Rae", "Jones")
    spark = (
        await client.post(
            "/interview/sparks",
            json={"book_id": author["book"]["_id"], "chapter_id": "c0"},
            headers=reader["headers"],
        )
    ).json()
    await database.sparks.update_one({"_id": spark["id"]}, {"$unset": {"book_author_id": ""}})
    # The interview's cleanup runs while the book still exists, so it can find the book's sparks.
    await interview.delete_interview_of(database, author["id"])
    assert await database.sparks.find_one({"_id": spark["id"]}) is None
