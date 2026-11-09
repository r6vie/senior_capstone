"""Adding to a book (I3), sparks (I5) and the question after a reading (I6), through the routes,
with the real engine on FakeClaude so what reaches the prompts can be checked."""

import base64
import json

import pytest

from tests.fakes import text_message
from tests.test_interview import minimal_pdf
from trove.ai import scripted
from trove.ai.client import get_claude
from trove.ai.prompts import load_prompt
from trove.ai.scripted import ScriptedClaude
from trove.books import service as books
from trove.interview import engine, service
from trove.main import app

OLD_ANSWER = "I rebuilt the dining hall schedule in a spreadsheet nobody else would touch."
NEW_ANSWER = "Last spring I ran the whole lab inventory by hand for six weeks straight."
CHAPTERS = [
    {"id": f"c{n}", "title": f"Chapter {n}", "summary": f"Summary {n}.", "quotes": [OLD_ANSWER]}
    for n in range(3)
]


async def member(client, email: str, first: str = "Hana", last: str = "Sato") -> dict:
    password = "a-long-password"
    await client.post(
        "/auth/signup", json={"email": email, "password": password, "first_name": first, "last_name": last}
    )
    login = await client.post("/auth/login", json={"email": email, "password": password})
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {login.json()['access_token']}"})
    return {"id": me.json()["id"], "headers": {"Authorization": f"Bearer {login.json()['access_token']}"}}


async def shelve_book(database, user_id: str, chapters: list[dict] | None = None) -> dict:
    """A member who has finished their interview, with a book on the shelf."""
    await books.create_draft_book(
        database, author_id=user_id, title="The Book", chapters=chapters or CHAPTERS, blurb="The old blurb."
    )
    book = await books.put_on_shelf(database, user_id)
    await database.interviews.insert_one(
        {
            "_id": f"interview-{user_id}",
            "user_id": user_id,
            "stage": "done",
            "turns": [{"question": "Old question?", "answer": OLD_ANSWER, "phase": "dig"}],
            "current": None,
            "topic": "the schedule",
            "ready_for_reveal": True,
            "draft": None,
        }
    )
    return book


@pytest.fixture
async def author(client, database):
    person = await member(client, "author@case.edu")
    person["book"] = await shelve_book(database, person["id"])
    return person


def next_question(question: str = "What did you do next?") -> object:
    return text_message(json.dumps({"question": question, "topic": "what's next", "done": False}))


def round_over() -> object:
    return text_message(json.dumps({"question": "", "topic": "what's next", "done": True}))


def change(kind="new", chapter_id=None, quotes=(NEW_ANSWER,), title="New title") -> dict:
    return {
        "kind": kind,
        "chapter_id": chapter_id,
        "title": title,
        "summary": "A new summary.",
        "quotes": list(quotes),
        "note": "Adds the inventory.",
    }


def revision(*changes: dict, blurb: str = "The proposed blurb.") -> object:
    return text_message(json.dumps({"changes": list(changes), "blurb": blurb}))


async def start_round(client, author, fake_claude) -> dict:
    fake_claude.responses.append(next_question())
    response = await client.post("/interview/reopen", headers=author["headers"])
    assert response.status_code == 200, response.text
    return response.json()


async def propose(client, author, fake_claude, *changes: dict, blurb: str = "The proposed blurb.") -> dict:
    await start_round(client, author, fake_claude)
    fake_claude.responses.append(round_over())
    await client.post("/interview/answers", json={"answer": NEW_ANSWER}, headers=author["headers"])
    fake_claude.responses.append(revision(*changes, blurb=blurb))
    response = await client.post("/interview/finish", headers=author["headers"])
    assert response.status_code == 200, response.text
    return response.json()


def prompt_text(request: dict) -> str:
    content = request["messages"][-1]["content"]
    text = content if isinstance(content, str) else "".join(block["text"] for block in content)
    return f"{request['system']}\n{text}"


def member_data(request: dict) -> str:
    content = request["messages"][-1]["content"]
    return content if isinstance(content, str) else "".join(block["text"] for block in content)


# I3: adding to your book.


async def test_reopen_needs_a_book_on_the_shelf(client, database, fake_claude):
    person = await member(client, "new@case.edu")
    assert (await client.post("/interview/reopen", headers=person["headers"])).status_code == 404

    await books.create_draft_book(database, author_id=person["id"], title="Draft", chapters=CHAPTERS)
    await database.interviews.insert_one(
        {"_id": "i", "user_id": person["id"], "stage": "reviewing", "turns": [], "current": None}
    )
    assert (await client.post("/interview/reopen", headers=person["headers"])).status_code == 409


async def test_a_round_keeps_the_old_turns_and_marks_where_it_starts(client, database, author, fake_claude):
    state = await start_round(client, author, fake_claude)
    assert state["stage"] == "adding"
    assert state["question"] == {"text": "What did you do next?", "phase": "adding", "playback": None}
    assert state["can_finish"] is False

    saved = await database.interviews.find_one({"user_id": author["id"]})
    assert saved["round_start"] == 1
    assert saved["turns"][0]["answer"] == OLD_ANSWER

    prompt = fake_claude.requests[-1]
    assert prompt["system"] == load_prompt("interview/adding")
    assert OLD_ANSWER in member_data(prompt)
    assert "Chapter 0" in member_data(prompt)


async def test_reopening_twice_returns_the_same_round(client, database, author, fake_claude):
    first = await start_round(client, author, fake_claude)
    second = await client.post("/interview/reopen", headers=author["headers"])
    assert second.json()["question"] == first["question"]
    assert len(fake_claude.requests) == 1


async def test_finishing_needs_one_real_answer(client, author, fake_claude):
    await start_round(client, author, fake_claude)
    assert (await client.post("/interview/finish", headers=author["headers"])).status_code == 409

    fake_claude.responses.append(next_question("Another?"))
    state = (await client.post("/interview/skip", headers=author["headers"])).json()
    assert state["can_finish"] is False
    assert state["question"]["text"] == "Another?"

    fake_claude.responses.append(next_question("And another?"))
    state = (
        await client.post("/interview/answers", json={"answer": NEW_ANSWER}, headers=author["headers"])
    ).json()
    assert state["can_finish"] is True


async def test_the_shape_step_doesnt_exist_in_a_round(client, author, fake_claude):
    await start_round(client, author, fake_claude)
    assert (await client.post("/interview/shape", json={}, headers=author["headers"])).status_code == 409


async def test_the_librarian_can_end_the_round(client, author, fake_claude):
    await start_round(client, author, fake_claude)
    fake_claude.responses.append(round_over())
    state = (
        await client.post("/interview/answers", json={"answer": NEW_ANSWER}, headers=author["headers"])
    ).json()
    assert state["question"] is None
    assert state["ready_for_reveal"] is True
    assert state["can_finish"] is True


async def test_the_librarian_cant_end_a_round_before_any_answer(client, author, fake_claude):
    fake_claude.responses.append(round_over())
    response = await client.post("/interview/reopen", headers=author["headers"])
    assert response.status_code == 502
    fake_claude.responses.append(next_question())
    state = (await client.post("/interview/question", headers=author["headers"])).json()
    assert state["question"]["text"] == "What did you do next?"


async def test_a_round_ends_on_its_own_at_the_limit_without_spending(client, database, author, fake_claude):
    await start_round(client, author, fake_claude)
    answers = [{"question": "Q?", "answer": "An answer here.", "phase": "adding"}] * (
        engine.MAX_ADDING_ANSWERS - 1
    )
    await database.interviews.update_one({"user_id": author["id"]}, {"$push": {"turns": {"$each": answers}}})
    calls = len(fake_claude.requests)
    state = (
        await client.post("/interview/answers", json={"answer": NEW_ANSWER}, headers=author["headers"])
    ).json()
    assert state["ready_for_reveal"] is True
    assert len(fake_claude.requests) == calls


async def test_the_book_on_the_shelf_only_changes_on_approval(client, database, author, fake_claude):
    before = await database.books.find_one({"author_id": author["id"]})
    reader = await member(client, "reader@case.edu", "Reader", "One")

    async def public():
        return (await client.get(f"/books/{before['_id']}", headers=reader["headers"])).json()

    seen = await public()
    state = await propose(client, author, fake_claude, change(), change("improve", "c1", title="Better"))
    assert state["stage"] == "revising"
    assert await database.books.find_one({"author_id": author["id"]}) == before
    assert await public() == seen

    ids = [item["id"] for item in state["changes"]]
    book = (
        await client.post("/interview/revision", json={"approved": ids}, headers=author["headers"])
    ).json()
    assert [c["title"] for c in book["chapters"]] == ["Chapter 0", "Better", "Chapter 2", "New title"]
    assert book["chapters"][1]["id"] == "c1"
    assert book["blurb"] == "The proposed blurb."

    after = await database.books.find_one({"author_id": author["id"]})
    assert after["published_at"] == before["published_at"]
    assert after["status"] == books.ON_SHELF
    assert (await client.get("/interview", headers=author["headers"])).json()["stage"] == "done"
    assert [c["title"] for c in (await public())["chapters"]][-1] == "New title"


async def test_a_change_shows_what_is_there_now(client, author, fake_claude):
    state = await propose(client, author, fake_claude, change(), change("improve", "c1", title="Better"))
    new, improved = state["changes"]
    assert new["kind"] == "new"
    assert new["chapter_id"] is None
    assert new["current"] is None
    assert new["note"] == "Adds the inventory."
    assert improved["chapter_id"] == "c1"
    assert improved["current"] == {"title": "Chapter 1", "summary": "Summary 1."}
    assert state["proposed_blurb"] == "The proposed blurb."


async def test_quotes_must_be_verbatim_and_from_the_new_round(client, database, author, fake_claude):
    state = await propose(
        client,
        author,
        fake_claude,
        change(title="Invented", quotes=["I ran a nuclear reactor for six weeks."]),
        change(title="Old material only", quotes=[OLD_ANSWER]),
        change(title="Kept", quotes=[NEW_ANSWER, OLD_ANSWER, "Words nobody said at all here."]),
    )
    assert [c["title"] for c in state["changes"]] == ["Kept"]
    assert state["changes"][0]["quotes"] == [NEW_ANSWER, OLD_ANSWER]


async def test_a_bad_chapter_id_or_a_second_improve_is_dropped(client, author, fake_claude):
    state = await propose(
        client,
        author,
        fake_claude,
        change("improve", "no-such-chapter", title="Lost"),
        change("improve", "c0", title="First"),
        change("improve", "c0", title="Second"),
    )
    assert [c["title"] for c in state["changes"]] == ["First"]


async def test_a_book_at_eight_chapters_can_only_improve(client, database, fake_claude):
    person = await member(client, "full@case.edu")
    full = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(8)]
    await shelve_book(database, person["id"], full)
    state = await propose(
        client, person, fake_claude, change(title="Ninth"), change("improve", "c0", title="Better")
    )
    assert [c["title"] for c in state["changes"]] == ["Better"]
    assert "<room>0</room>" in member_data(fake_claude.requests[-1])


async def test_new_chapters_stop_at_eight(client, database, fake_claude):
    person = await member(client, "seven@case.edu")
    seven = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(7)]
    await shelve_book(database, person["id"], seven)
    state = await propose(client, person, fake_claude, change(title="Eighth"), change(title="Ninth"))
    assert [c["title"] for c in state["changes"]] == ["Eighth"]


async def test_declined_changes_are_dropped_and_the_blurb_is_rewritten(client, database, author, fake_claude):
    state = await propose(client, author, fake_claude, change(title="Yes"), change(title="No"))
    fake_claude.responses.append(text_message(json.dumps({"blurb": "A blurb for what's left."})))
    book = (
        await client.post(
            "/interview/revision", json={"approved": [state["changes"][0]["id"]]}, headers=author["headers"]
        )
    ).json()
    titles = [c["title"] for c in book["chapters"]]
    assert "Yes" in titles
    assert "No" not in titles
    assert book["blurb"] == "A blurb for what's left."
    assert fake_claude.requests[-1]["system"] == load_prompt("interview/blurb")


async def test_declining_everything_leaves_the_book_alone(client, database, author, fake_claude):
    before = await database.books.find_one({"author_id": author["id"]})
    await propose(client, author, fake_claude, change())
    calls = len(fake_claude.requests)
    response = await client.post("/interview/revision", json={"approved": []}, headers=author["headers"])
    assert response.status_code == 200
    assert await database.books.find_one({"author_id": author["id"]}) == before
    assert len(fake_claude.requests) == calls
    assert (await client.get("/interview", headers=author["headers"])).json()["stage"] == "done"


async def test_an_unknown_change_is_422_and_changes_nothing(client, database, author, fake_claude):
    before = await database.books.find_one({"author_id": author["id"]})
    await propose(client, author, fake_claude, change())
    response = await client.post(
        "/interview/revision", json={"approved": ["nope"]}, headers=author["headers"]
    )
    assert response.status_code == 422
    assert await database.books.find_one({"author_id": author["id"]}) == before


async def test_revision_is_409_without_a_proposal(client, author):
    response = await client.post("/interview/revision", json={"approved": []}, headers=author["headers"])
    assert response.status_code == 409


async def test_a_round_with_nothing_usable_says_so_and_returns_to_done(client, database, author, fake_claude):
    before = await database.books.find_one({"author_id": author["id"]})
    state = await propose(client, author, fake_claude, change(quotes=["Not something anyone said here."]))
    assert state["stage"] == "done"
    assert state["nothing_new"] is True
    assert state["changes"] is None
    assert await database.books.find_one({"author_id": author["id"]}) == before

    fake_claude.responses.append(next_question())
    again = (await client.post("/interview/reopen", headers=author["headers"])).json()
    assert again["nothing_new"] is False


async def test_a_failed_revise_loses_nothing_and_can_be_tried_again(client, database, author, fake_claude):
    await start_round(client, author, fake_claude)
    fake_claude.responses.append(round_over())
    await client.post("/interview/answers", json={"answer": NEW_ANSWER}, headers=author["headers"])
    fake_claude.responses.append(text_message("not json"))
    assert (await client.post("/interview/finish", headers=author["headers"])).status_code == 502

    state = (await client.get("/interview", headers=author["headers"])).json()
    assert state["stage"] == "revising"
    assert state["changes"] is None
    assert state["can_finish"] is True

    fake_claude.responses.append(revision(change()))
    state = (await client.post("/interview/finish", headers=author["headers"])).json()
    assert len(state["changes"]) == 1
    assert (await client.post("/interview/finish", headers=author["headers"])).status_code == 409


class Recording(ScriptedClaude):
    def __init__(self):
        super().__init__()
        self.requests: list[dict] = []

    async def create(self, **params):
        self.requests.append(params)
        return await super().create(**params)


@pytest.fixture
def scripted_ai():
    claude = Recording()
    app.dependency_overrides[get_claude] = lambda: claude
    yield claude
    app.dependency_overrides.pop(get_claude, None)


async def first_interview(client, person, resume_pdf: str | None = None):
    body = {"resume_pdf": resume_pdf} if resume_pdf else {}
    await client.post("/interview", json=body, headers=person["headers"])
    for answer in scripted.THEO_ANSWERS:
        await client.post("/interview/answers", json={"answer": answer}, headers=person["headers"])
    await client.post("/interview/shape", json={}, headers=person["headers"])
    await client.post("/interview/finish", headers=person["headers"])
    await client.post("/interview/title", json={"title": 0}, headers=person["headers"])
    await client.post("/interview/book/shelve", headers=person["headers"])


async def test_the_resume_never_comes_back(client, scripted_ai):
    person = await member(client, "resume@case.edu")
    pdf = base64.b64encode(minimal_pdf("RESUMEMARKER Acme Corp")).decode()
    await first_interview(client, person, pdf)
    assert "RESUMEMARKER" in member_data(
        scripted_ai.requests[0] | {"messages": scripted_ai.requests[0]["messages"]}
    )

    first_after = len(scripted_ai.requests)
    await client.post("/interview/reopen", headers=person["headers"])
    await client.post("/interview/answers", json={"answer": NEW_ANSWER}, headers=person["headers"])
    await client.post("/interview/finish", headers=person["headers"])
    later = scripted_ai.requests[first_after:]
    assert [r["system"] for r in later[-1:]] == [load_prompt("interview/revise")]
    assert not any("RESUMEMARKER" in member_data(request) for request in later)


async def test_a_whole_round_walks_on_the_scripted_ai(client, database, scripted_ai):
    person = await member(client, "walk@case.edu")
    await first_interview(client, person)
    state = (await client.post("/interview/reopen", headers=person["headers"])).json()
    assert state["stage"] == "adding"
    seen = []
    answers = [NEW_ANSWER, "We taught the next group the same routine in two afternoons."]
    for answer in [
        *answers,
        "I rewrote the checklist after that for everyone.",
        "Then I stopped doing it myself.",
    ]:
        seen.append(state["question"]["text"])
        state = (
            await client.post("/interview/answers", json={"answer": answer}, headers=person["headers"])
        ).json()
    assert len(seen) == len(set(seen))
    assert state["ready_for_reveal"] is True

    state = (await client.post("/interview/finish", headers=person["headers"])).json()
    assert state["stage"] == "revising"
    assert {item["kind"] for item in state["changes"]} == {"new", "improve"}

    before = len((await books.get_book_of(database, person["id"]))["chapters"])
    ids = [item["id"] for item in state["changes"]]
    book = (
        await client.post("/interview/revision", json={"approved": ids}, headers=person["headers"])
    ).json()
    assert len(book["chapters"]) == before + 1


async def test_a_thin_round_on_the_scripted_ai_earns_nothing(client, scripted_ai):
    person = await member(client, "thin@case.edu")
    await first_interview(client, person)
    await client.post("/interview/reopen", headers=person["headers"])
    await client.post("/interview/answers", json={"answer": "Nothing much."}, headers=person["headers"])
    state = (await client.post("/interview/finish", headers=person["headers"])).json()
    assert state["stage"] == "done"
    assert state["nothing_new"] is True


# I5: sparks.


@pytest.fixture
async def reader(client):
    return await member(client, "reader@case.edu", "Rae", "Jones")


async def spark(client, reader, author, chapter_id: str = "c0"):
    return await client.post(
        "/interview/sparks",
        json={"book_id": author["book"]["_id"], "chapter_id": chapter_id},
        headers=reader["headers"],
    )


async def test_save_list_and_remove_a_spark(client, author, reader):
    saved = await spark(client, reader, author)
    assert saved.status_code == 200
    assert saved.json()["chapter_title"] == "Chapter 0"

    again = await spark(client, reader, author)
    assert again.json()["id"] == saved.json()["id"]
    sparks = (await client.get("/interview/sparks", headers=reader["headers"])).json()
    assert [item["id"] for item in sparks] == [saved.json()["id"]]

    removed = await client.delete(f"/interview/sparks/{saved.json()['id']}", headers=reader["headers"])
    assert removed.status_code == 204
    assert (await client.get("/interview/sparks", headers=reader["headers"])).json() == []


async def test_no_spark_on_your_own_book_or_a_missing_chapter(client, author, reader):
    assert (await spark(client, author, author)).status_code == 409
    assert (await spark(client, reader, author, "no-such-chapter")).status_code == 404
    response = await client.post(
        "/interview/sparks", json={"book_id": "no-such-book", "chapter_id": "c0"}, headers=reader["headers"]
    )
    assert response.status_code == 404


async def test_at_most_twelve_unused_sparks(client, database, reader):
    other = await member(client, "big@case.edu", "Big", "Book")
    many = [
        {"id": f"m{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]}
        for n in range(service.MAX_UNUSED_SPARKS + 1)
    ]
    other["book"] = await shelve_book(database, other["id"], many)
    for n in range(service.MAX_UNUSED_SPARKS):
        assert (await spark(client, reader, other, f"m{n}")).status_code == 200
    assert (await spark(client, reader, other, f"m{service.MAX_UNUSED_SPARKS}")).status_code == 409
    # Saving one again is still fine at the limit.
    assert (await spark(client, reader, other, "m0")).status_code == 200


async def test_only_the_title_reaches_the_interviewer(client, database, author, reader, fake_claude):
    await spark(client, reader, author)
    await shelve_book(database, reader["id"])
    await start_round(client, reader, fake_claude)

    prompt = member_data(fake_claude.requests[-1])
    assert "<sparks>\n- Chapter 0\n</sparks>" in prompt
    # The reader's own book is also called "The Book", so check what only the other book has.
    assert "Hana" not in prompt
    assert "Sato" not in prompt
    assert author["book"]["_id"] not in prompt
    assert author["id"] not in prompt


async def test_sparks_reach_a_first_interview_and_are_used_when_it_ends(
    client, database, author, reader, scripted_ai
):
    await spark(client, reader, author)
    await client.post("/interview", json={}, headers=reader["headers"])
    assert "<sparks>\n- Chapter 0\n</sparks>" in member_data(scripted_ai.requests[0])
    assert "Summary 0" not in member_data(scripted_ai.requests[0])
    assert "The Book" not in member_data(scripted_ai.requests[0])

    for answer in scripted.THEO_ANSWERS:
        await client.post("/interview/answers", json={"answer": answer}, headers=reader["headers"])
    await client.post("/interview/shape", json={}, headers=reader["headers"])
    assert len((await client.get("/interview/sparks", headers=reader["headers"])).json()) == 1
    await client.post("/interview/finish", headers=reader["headers"])
    assert (await client.get("/interview/sparks", headers=reader["headers"])).json() == []
    saved = await database.sparks.find_one({"user_id": reader["id"]})
    assert saved["used_at"] is not None


async def test_a_spark_is_used_when_the_round_finishes_and_can_be_saved_again(
    client, database, author, reader, fake_claude
):
    await shelve_book(database, reader["id"])
    await spark(client, reader, author)
    await propose(client, reader, fake_claude, change())
    assert (await client.get("/interview/sparks", headers=reader["headers"])).json() == []

    await spark(client, reader, author)
    assert len((await client.get("/interview/sparks", headers=reader["headers"])).json()) == 1
    assert await database.sparks.count_documents({"user_id": reader["id"]}) == 1


async def test_sparks_never_reach_the_other_author(client, database, author, reader):
    async def what_the_author_can_see():
        return [
            (await client.get(path, headers=author["headers"])).json()
            for path in (
                f"/books/{author['book']['_id']}",
                "/books/me",
                "/interview",
                "/interview/sparks",
                "/auth/me",
            )
        ]

    before = await what_the_author_can_see()
    notifications = await database.notifications.count_documents({})
    saved = await spark(client, reader, author)
    assert await what_the_author_can_see() == before
    assert await database.notifications.count_documents({}) == notifications
    assert "spark" not in json.dumps(before).lower()

    # Nor can they touch it, even with its id.
    gone = await client.delete(f"/interview/sparks/{saved.json()['id']}", headers=author["headers"])
    assert gone.status_code == 404


# I6: the question after a reading.


async def test_ask_after_reading_is_idempotent(client, database, author):
    await service.ask_after_reading(database, author["id"], "checkout-1")
    await service.ask_after_reading(database, author["id"], "checkout-1")
    questions = (await client.get("/interview/reading-questions", headers=author["headers"])).json()
    assert len(questions) == 1
    assert questions[0]["question"] == "What did they ask you about that surprised you?"
    assert set(questions[0]) == {"id", "question", "created_at"}


async def waiting_question(client, database, author) -> str:
    await service.ask_after_reading(database, author["id"], "checkout-secret")
    return (await client.get("/interview/reading-questions", headers=author["headers"])).json()[0]["id"]


async def test_dismissing_is_quiet_and_final(client, database, author):
    question = await waiting_question(client, database, author)
    response = await client.post(
        f"/interview/reading-questions/{question}/dismiss", headers=author["headers"]
    )
    assert response.status_code == 204
    assert (await client.get("/interview/reading-questions", headers=author["headers"])).json() == []
    # Confirming the same meeting again doesn't bring it back.
    await service.ask_after_reading(database, author["id"], "checkout-secret")
    assert (await client.get("/interview/reading-questions", headers=author["headers"])).json() == []
    again = await client.post(f"/interview/reading-questions/{question}/dismiss", headers=author["headers"])
    assert again.status_code == 404


async def test_an_answer_goes_through_revise_and_approval(client, database, author, fake_claude):
    before = await database.books.find_one({"author_id": author["id"]})
    question = await waiting_question(client, database, author)
    fake_claude.responses.append(revision(change()))
    state = (
        await client.post(
            f"/interview/reading-questions/{question}/answer",
            json={"answer": NEW_ANSWER},
            headers=author["headers"],
        )
    ).json()
    assert state["stage"] == "revising"
    assert len(state["changes"]) == 1
    assert await database.books.find_one({"author_id": author["id"]}) == before

    saved = await database.interviews.find_one({"user_id": author["id"]})
    assert saved["turns"][-1] == {
        "question": service.READING_QUESTION,
        "answer": NEW_ANSWER,
        "phase": "reading",
    }
    assert (await client.get("/interview/reading-questions", headers=author["headers"])).json() == []

    book = (
        await client.post(
            "/interview/revision", json={"approved": [state["changes"][0]["id"]]}, headers=author["headers"]
        )
    ).json()
    assert book["chapters"][-1]["title"] == "New title"


async def test_the_reader_never_enters_the_prompt(client, database, author, reader, fake_claude):
    question = await waiting_question(client, database, author)
    fake_claude.responses.append(revision(change()))
    await client.post(
        f"/interview/reading-questions/{question}/answer",
        json={"answer": NEW_ANSWER},
        headers=author["headers"],
    )
    prompt = prompt_text(fake_claude.requests[-1])
    assert "checkout-secret" not in prompt
    assert reader["id"] not in prompt
    assert "Rae" not in prompt
    assert "Jones" not in prompt
    assert "Never name or describe anyone else" in prompt


async def test_a_thin_answer_can_yield_no_changes(client, database, author, fake_claude):
    question = await waiting_question(client, database, author)
    fake_claude.responses.append(revision())
    state = (
        await client.post(
            f"/interview/reading-questions/{question}/answer",
            json={"answer": "Not much."},
            headers=author["headers"],
        )
    ).json()
    assert state["stage"] == "done"
    assert state["nothing_new"] is True


async def test_a_failed_revise_keeps_the_answer(client, database, author, fake_claude):
    question = await waiting_question(client, database, author)
    fake_claude.responses.append(text_message("not json"))
    response = await client.post(
        f"/interview/reading-questions/{question}/answer",
        json={"answer": NEW_ANSWER},
        headers=author["headers"],
    )
    assert response.status_code == 502
    fake_claude.responses.append(revision(change()))
    state = (await client.post("/interview/finish", headers=author["headers"])).json()
    assert len(state["changes"]) == 1


async def test_during_a_round_an_answer_joins_it(client, database, author, fake_claude):
    question = await waiting_question(client, database, author)
    waiting = await start_round(client, author, fake_claude)
    state = (
        await client.post(
            f"/interview/reading-questions/{question}/answer",
            json={"answer": NEW_ANSWER},
            headers=author["headers"],
        )
    ).json()
    assert state["stage"] == "adding"
    assert state["question"] == waiting["question"]
    assert state["can_finish"] is True


async def test_while_changes_wait_an_answer_is_409_and_stays_open(client, database, author, fake_claude):
    question = await waiting_question(client, database, author)
    await propose(client, author, fake_claude, change())
    response = await client.post(
        f"/interview/reading-questions/{question}/answer",
        json={"answer": NEW_ANSWER},
        headers=author["headers"],
    )
    assert response.status_code == 409
    assert len((await client.get("/interview/reading-questions", headers=author["headers"])).json()) == 1


async def test_someone_elses_question_is_404(client, database, author, reader):
    question = await waiting_question(client, database, author)
    await shelve_book(database, reader["id"])
    for path, body in (("answer", {"answer": "Mine now."}), ("dismiss", None)):
        response = await client.post(
            f"/interview/reading-questions/{question}/{path}", json=body, headers=reader["headers"]
        )
        assert response.status_code == 404
