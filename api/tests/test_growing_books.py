"""Adding to a book (I3), sparks (I5) and the question after a reading (I6), through the routes,
with the real engine on FakeClaude so what reaches the prompts can be checked."""

import base64
import json
from datetime import UTC, datetime, timedelta

import pytest

from tests.fakes import send_answer, send_skip, text_message
from tests.test_interview import minimal_pdf
from trove.ai import scripted
from trove.ai.client import get_claude
from trove.ai.prompts import load_prompt
from trove.ai.scripted import ScriptedClaude
from trove.books import service as books
from trove.core.config import get_settings
from trove.interview import engine, service
from trove.main import app

OLD_ANSWER = "I rebuilt the dining hall schedule in a spreadsheet nobody else would touch."
NEW_ANSWER = "Last spring I ran the whole lab inventory by hand for six weeks straight."
# Two parts of it, because a quote grounds only one chapter.
PART_ONE = "Last spring I ran the whole lab"
PART_TWO = "inventory by hand for six weeks straight"
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
    await send_answer(client, author["headers"], NEW_ANSWER)
    fake_claude.responses.append(revision(*changes, blurb=blurb))
    response = await client.post("/interview/finish", headers=author["headers"])
    assert response.status_code == 200, response.text
    return (await client.get("/interview", headers=author["headers"])).json()


def prompt_text(request: dict) -> str:
    content = request["messages"][-1]["content"]
    text = content if isinstance(content, str) else "".join(block["text"] for block in content)
    return f"{request['system']}\n{text}"


def member_data(request: dict) -> str:
    content = request["messages"][-1]["content"]
    return content if isinstance(content, str) else "".join(block["text"] for block in content)


# I3: adding to your book.


async def test_a_round_keeps_the_old_turns_and_marks_where_it_starts(client, database, author, fake_claude):
    state = await start_round(client, author, fake_claude)
    assert state["stage"] == "adding"
    assert state["question"]["question_id"]
    assert state["question"] == {
        "question_id": state["question"]["question_id"],
        "text": "What did you do next?",
        "phase": "adding",
        "playback": None,
    }
    assert state["can_finish"] is False

    saved = await database.interviews.find_one({"user_id": author["id"]})
    assert saved["round_start"] == 1
    assert saved["turns"][0]["answer"] == OLD_ANSWER

    prompt = fake_claude.requests[-1]
    assert prompt["system"] == load_prompt("interview/adding")
    assert OLD_ANSWER in member_data(prompt)
    assert "Chapter 0" in member_data(prompt)


async def test_finishing_needs_one_real_answer(client, author, fake_claude):
    await start_round(client, author, fake_claude)
    assert (await client.post("/interview/finish", headers=author["headers"])).status_code == 409

    fake_claude.responses.append(next_question("Another?"))
    state = (await send_skip(client, author["headers"])).json()
    assert state["can_finish"] is False
    assert state["question"]["text"] == "Another?"

    fake_claude.responses.append(next_question("And another?"))
    state = (await send_answer(client, author["headers"], NEW_ANSWER)).json()
    assert state["can_finish"] is True


async def test_finishing_a_round_keeps_what_is_in_the_field(client, database, author, fake_claude):
    state = await start_round(client, author, fake_claude)
    fake_claude.responses.append(revision(change()))
    response = await client.post("/interview/finish", json={"answer": NEW_ANSWER}, headers=author["headers"])
    assert response.status_code == 200, response.text
    assert response.json()["stage"] == "revising"
    # One request wrote the first question and one the revision: no extra question in between.
    assert [r["system"] for r in fake_claude.requests] == [
        load_prompt("interview/adding"),
        load_prompt("interview/revise"),
    ]
    saved = await database.interviews.find_one({"user_id": author["id"]})
    assert saved["turns"][-1] == {
        "question": state["question"]["text"],
        "answer": NEW_ANSWER,
        "phase": "adding",
    }


async def test_the_shape_step_doesnt_exist_in_a_round(client, author, fake_claude):
    await start_round(client, author, fake_claude)
    assert (await client.post("/interview/shape", json={}, headers=author["headers"])).status_code == 409


async def test_the_librarian_can_end_the_round(client, author, fake_claude):
    await start_round(client, author, fake_claude)
    fake_claude.responses.append(round_over())
    state = (await send_answer(client, author["headers"], NEW_ANSWER)).json()
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
    state = (await send_answer(client, author["headers"], NEW_ANSWER)).json()
    assert state["ready_for_reveal"] is True
    assert len(fake_claude.requests) == calls


async def test_a_change_shows_what_is_there_now(client, author, fake_claude):
    state = await propose(
        client,
        author,
        fake_claude,
        change(quotes=[PART_ONE]),
        change("improve", "c1", quotes=[PART_TWO], title="Better"),
    )
    new, improved = state["changes"]
    assert new["kind"] == "new"
    assert new["chapter_id"] is None
    assert new["current"] is None
    assert new["note"] == "Adds the inventory."
    assert improved["chapter_id"] == "c1"
    assert improved["current"] == {"title": "Chapter 1", "summary": "Summary 1."}
    assert state["proposed_blurb"] == "The proposed blurb."


async def test_a_bad_chapter_id_or_a_second_improve_is_dropped(client, author, fake_claude):
    state = await propose(
        client,
        author,
        fake_claude,
        change("improve", "no-such-chapter", title="Lost"),
        change("improve", "c0", quotes=[PART_ONE], title="First"),
        change("improve", "c0", quotes=[PART_TWO], title="Second"),
    )
    assert [c["title"] for c in state["changes"]] == ["First"]


async def test_a_book_at_eight_chapters_can_only_improve(client, database, fake_claude):
    person = await member(client, "full@case.edu")
    full = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(8)]
    await shelve_book(database, person["id"], full)
    state = await propose(
        client,
        person,
        fake_claude,
        change(title="Ninth", quotes=[PART_ONE]),
        change("improve", "c0", quotes=[PART_TWO], title="Better"),
    )
    assert [c["title"] for c in state["changes"]] == ["Better"]
    assert "<room>0</room>" in member_data(fake_claude.requests[-1])


async def test_new_chapters_stop_at_eight(client, database, fake_claude):
    person = await member(client, "seven@case.edu")
    seven = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(7)]
    await shelve_book(database, person["id"], seven)
    state = await propose(
        client,
        person,
        fake_claude,
        change(title="Eighth", quotes=[PART_ONE]),
        change(title="Ninth", quotes=[PART_TWO]),
    )
    assert [c["title"] for c in state["changes"]] == ["Eighth"]


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
        await send_answer(client, person["headers"], answer)
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
    await send_answer(client, person["headers"], NEW_ANSWER)
    await client.post("/interview/finish", headers=person["headers"])
    later = scripted_ai.requests[first_after:]
    assert [r["system"] for r in later[-1:]] == [load_prompt("interview/revise")]
    assert not any("RESUMEMARKER" in member_data(request) for request in later)


async def test_a_resume_only_term_stays_out_of_book_steps_and_the_saved_interview(
    client, database, scripted_ai
):
    person = await member(client, "terms@case.edu")
    pdf = base64.b64encode(minimal_pdf("Operations at Brindle Foods 2019")).decode()
    await client.post("/interview", json={"resume_pdf": pdf}, headers=person["headers"])
    saved = await database.interviews.find_one({"user_id": person["id"]})
    assert "Brindle" not in str(saved)
    # The Librarian's question names the company, as a résumé can make it do.
    await database.interviews.update_one(
        {"user_id": person["id"]},
        {"$set": {"current.question": "What happened at Brindle Foods in 2019?"}},
    )
    for answer in scripted.THEO_ANSWERS:
        await send_answer(client, person["headers"], answer)
    await client.post("/interview/shape", json={}, headers=person["headers"])
    await client.post("/interview/finish", headers=person["headers"])

    draft_request = next(r for r in scripted_ai.requests if r["system"] == load_prompt("interview/draft"))
    data = member_data(draft_request)
    assert "Brindle" not in data
    assert "2019" not in data
    assert "What happened at that one" in data
    assert await database.resume_texts.count_documents({}) == 0


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
        state = (await send_answer(client, person["headers"], answer)).json()
    assert len(seen) == len(set(seen))
    assert state["ready_for_reveal"] is True

    state = (await client.post("/interview/finish", headers=person["headers"])).json()
    assert state["stage"] == "revising"
    assert state["revision_status"] == "writing"
    state = (await client.get("/interview", headers=person["headers"])).json()
    assert state["revision_status"] == "ready"
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
    await send_answer(client, person["headers"], "Nothing much.")
    await client.post("/interview/finish", headers=person["headers"])
    state = (await client.get("/interview", headers=person["headers"])).json()
    assert state["stage"] == "done"
    assert state["nothing_new"] is True


# Amendments: the blurb, off limits, removal, undo, collisions, background writing, improve, position.


async def test_reopen_only_from_done_and_a_book_with_no_interview_gets_one(client, database, fake_claude):
    person = await member(client, "new@case.edu")
    assert (await client.post("/interview/reopen", headers=person["headers"])).status_code == 404

    await books.create_draft_book(database, author_id=person["id"], title="Seeded", chapters=CHAPTERS)
    assert (await client.post("/interview/reopen", headers=person["headers"])).status_code == 404
    await books.put_on_shelf(database, person["id"])
    state = await start_round(client, person, fake_claude)
    assert state["stage"] == "adding"
    saved = await database.interviews.find_one({"user_id": person["id"]})
    assert saved["turns"] == []
    assert saved["round_start"] == 0

    again = await client.post("/interview/reopen", headers=person["headers"])
    assert again.json()["question"] == state["question"]
    assert len(fake_claude.requests) == 1


async def test_reopen_from_revising_is_409(client, author, fake_claude):
    await propose(client, author, fake_claude, change())
    assert (await client.post("/interview/reopen", headers=author["headers"])).status_code == 409


async def test_the_book_on_the_shelf_only_changes_on_approval(client, database, author, fake_claude):
    before = await database.books.find_one({"author_id": author["id"]})
    reader = await member(client, "reader@case.edu", "Reader", "One")

    async def public():
        return (await client.get(f"/books/{before['_id']}", headers=reader["headers"])).json()

    seen = await public()
    state = await propose(
        client,
        author,
        fake_claude,
        change(quotes=[PART_ONE]),
        change("improve", "c1", quotes=[PART_TWO], title="Better"),
    )
    assert state["stage"] == "revising"
    assert await database.books.find_one({"author_id": author["id"]}) == before
    assert await public() == seen

    ids = [item["id"] for item in state["changes"]]
    book = (
        await client.post(
            "/interview/revision", json={"approved": ids, "blurb": "use"}, headers=author["headers"]
        )
    ).json()
    assert [c["title"] for c in book["chapters"]] == ["Chapter 0", "Better", "Chapter 2", "New title"]
    assert book["chapters"][1]["id"] == "c1"
    assert book["blurb"] == "The proposed blurb."

    after = await database.books.find_one({"author_id": author["id"]})
    assert after["published_at"] == before["published_at"]
    assert after["status"] == books.ON_SHELF
    assert (await client.get("/interview", headers=author["headers"])).json()["stage"] == "done"
    assert [c["title"] for c in (await public())["chapters"]][-1] == "New title"


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
    # The old quote already grounds a chapter, so it can't ground this one too.
    assert state["changes"][0]["quotes"] == [NEW_ANSWER]


async def test_an_improve_needs_something_new_and_keeps_the_old_quotes(client, author, fake_claude):
    state = await propose(
        client,
        author,
        fake_claude,
        change("improve", "c0", quotes=[OLD_ANSWER], title="Just reworded"),
        change("improve", "c1", title="Gained something"),
    )
    assert [c["title"] for c in state["changes"]] == ["Gained something"]
    assert state["changes"][0]["quotes"] == [OLD_ANSWER, NEW_ANSWER]


async def test_a_new_chapter_goes_where_it_says(client, author, fake_claude):
    state = await propose(client, author, fake_claude, {**change(title="Second now"), "position": 2})
    assert state["changes"][0]["position"] == 2
    book = (
        await client.post(
            "/interview/revision", json={"approved": [state["changes"][0]["id"]]}, headers=author["headers"]
        )
    ).json()
    assert [c["title"] for c in book["chapters"]] == ["Chapter 0", "Second now", "Chapter 1", "Chapter 2"]


async def test_at_the_cap_the_librarian_is_told_to_only_improve(client, database, fake_claude):
    person = await member(client, "cap@case.edu")
    full = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(8)]
    await shelve_book(database, person["id"], full)
    await start_round(client, person, fake_claude)
    assert "Only improve" in member_data(fake_claude.requests[-1])


async def choose(client, headers, ids: list[str]) -> dict:
    response = await client.put("/interview/revision/choices", json={"approved": ids}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


async def ask_for_blurb(client, headers) -> dict:
    """Ask for the back cover of the saved choices. It's written after the response, so read it."""
    response = await client.post("/interview/revision/blurb", headers=headers)
    assert response.status_code == 200, response.text
    return (await client.get("/interview", headers=headers)).json()


async def test_a_partial_selection_shows_a_new_blurb_before_anything_applies(
    client, database, author, fake_claude
):
    state = await propose(
        client,
        author,
        fake_claude,
        change(title="Yes", quotes=[PART_ONE]),
        change(title="No", quotes=[PART_TWO]),
    )
    yes = state["changes"][0]["id"]
    headers = author["headers"]

    refused = await client.post(
        "/interview/revision", json={"approved": [yes], "blurb": "use"}, headers=headers
    )
    assert refused.status_code == 409

    await choose(client, headers, [yes])
    fake_claude.responses.append(text_message(json.dumps({"blurb": "A blurb for what's left."})))
    started = (await client.post("/interview/revision/blurb", headers=headers)).json()
    assert started["selection_blurb_status"] == "writing"
    assert started["selection_blurb"] is None
    state = (await client.get("/interview", headers=headers)).json()
    assert state["selection_blurb_status"] == "ready"
    assert state["selection_blurb"] == "A blurb for what's left."
    assert fake_claude.requests[-1]["system"] == load_prompt("interview/blurb")
    assert (await database.books.find_one({"author_id": author["id"]}))["blurb"] == "The old blurb."

    # A different selection can't use it.
    other = await client.post(
        "/interview/revision", json={"approved": [state["changes"][1]["id"]], "blurb": "use"}, headers=headers
    )
    assert other.status_code == 409

    calls = len(fake_claude.requests)
    book = (
        await client.post("/interview/revision", json={"approved": [yes], "blurb": "use"}, headers=headers)
    ).json()
    assert book["blurb"] == state["selection_blurb"]
    assert len(fake_claude.requests) == calls
    titles = [c["title"] for c in book["chapters"]]
    assert "Yes" in titles
    assert "No" not in titles


async def test_choices_are_saved_on_the_server(client, database, author, fake_claude):
    state = await propose(
        client,
        author,
        fake_claude,
        change(title="A", quotes=[PART_ONE]),
        change(title="B", quotes=[PART_TWO]),
    )
    headers = author["headers"]
    assert state["approved_changes"] is None
    assert state["selection_blurb_status"] is None
    first = state["changes"][0]["id"]
    await choose(client, headers, [first])
    assert (await client.get("/interview", headers=headers)).json()["approved_changes"] == [first]
    # Nothing is applied by saving a choice.
    assert (await database.books.find_one({"author_id": author["id"]}))["chapters"][-1][
        "title"
    ] == "Chapter 2"
    bad = await client.put("/interview/revision/choices", json={"approved": ["nope"]}, headers=headers)
    assert bad.status_code == 422


async def test_the_blurb_needs_choices_first(client, author, fake_claude):
    await propose(client, author, fake_claude, change())
    assert (await client.post("/interview/revision/blurb", headers=author["headers"])).status_code == 409


async def test_changing_a_choice_makes_the_blurb_stale(client, author, fake_claude):
    state = await propose(
        client,
        author,
        fake_claude,
        change(title="A", quotes=[PART_ONE]),
        change(title="B", quotes=[PART_TWO]),
    )
    one, two = [item["id"] for item in state["changes"]]
    headers = author["headers"]
    await choose(client, headers, [one])
    fake_claude.responses.append(text_message(json.dumps({"blurb": "For the first one."})))
    assert (await ask_for_blurb(client, headers))["selection_blurb"] == "For the first one."

    stale = await choose(client, headers, [two])
    assert stale["selection_blurb_status"] == "stale"
    assert stale["selection_blurb"] is None
    refused = await client.post(
        "/interview/revision", json={"approved": [two], "blurb": "use"}, headers=headers
    )
    assert refused.status_code == 409

    fake_claude.responses.append(text_message(json.dumps({"blurb": "For the second one."})))
    state = await ask_for_blurb(client, headers)
    assert state["selection_blurb_status"] == "ready"
    assert state["selection_blurb"] == "For the second one."
    book = (
        await client.post("/interview/revision", json={"approved": [two], "blurb": "use"}, headers=headers)
    ).json()
    assert book["blurb"] == "For the second one."


async def test_a_failed_blurb_can_be_tried_again_or_skipped(client, author, fake_claude):
    state = await propose(
        client,
        author,
        fake_claude,
        change(title="A", quotes=[PART_ONE]),
        change(title="B", quotes=[PART_TWO]),
    )
    one = state["changes"][0]["id"]
    headers = author["headers"]
    await choose(client, headers, [one])
    fake_claude.responses += [
        text_message(json.dumps({"blurb": ""})),
        text_message(json.dumps({"blurb": ""})),
    ]
    state = await ask_for_blurb(client, headers)
    assert state["selection_blurb_status"] == "failed"

    fake_claude.responses.append(text_message(json.dumps({"blurb": "Second try."})))
    state = await ask_for_blurb(client, headers)
    assert state["selection_blurb"] == "Second try."


async def test_approving_everything_uses_the_proposed_blurb_for_free(client, author, fake_claude):
    state = await propose(client, author, fake_claude, change())
    headers = author["headers"]
    await choose(client, headers, [state["changes"][0]["id"]])
    calls = len(fake_claude.requests)
    state = (await client.post("/interview/revision/blurb", headers=headers)).json()
    assert state["selection_blurb_status"] == "ready"
    assert state["selection_blurb"] == "The proposed blurb."
    assert len(fake_claude.requests) == calls


async def test_undoing_takes_a_change_back_for_good(client, database, author, fake_claude):
    state = await propose(
        client,
        author,
        fake_claude,
        change(title="Regretted", quotes=[PART_ONE]),
        change("improve", "c1", quotes=[PART_TWO], title="Worse"),
    )
    ids = [item["id"] for item in state["changes"]]
    await client.post("/interview/revision", json={"approved": ids}, headers=author["headers"])
    await client.post("/interview/book/undo", headers=author["headers"])
    saved = await database.interviews.find_one({"user_id": author["id"]})
    assert {item["title"] for item in saved["declined_changes"]} == {"Regretted", "Worse"}

    await start_round(client, author, fake_claude)
    assert "Regretted" in member_data(fake_claude.requests[-1]).split("<off_limits>")[1]


async def test_a_round_with_nothing_keeps_undo_available(client, author, fake_claude):
    state = await propose(client, author, fake_claude, change(quotes=[PART_ONE]))
    await client.post(
        "/interview/revision", json={"approved": [state["changes"][0]["id"]]}, headers=author["headers"]
    )
    state = await propose(client, author, fake_claude, change(quotes=["Not something anyone said here."]))
    assert state["nothing_new"] is True
    assert (await client.get("/books/me", headers=author["headers"])).json()["can_undo"] is True


async def test_declining_the_new_blurb_keeps_the_old_one(client, author, fake_claude):
    state = await propose(client, author, fake_claude, change())
    book = (
        await client.post(
            "/interview/revision",
            json={"approved": [state["changes"][0]["id"]], "blurb": "keep"},
            headers=author["headers"],
        )
    ).json()
    assert book["blurb"] == "The old blurb."
    assert book["chapters"][-1]["title"] == "New title"


async def test_removed_and_declined_chapters_are_off_limits(client, database, author, fake_claude):
    state = await propose(client, author, fake_claude, change(title="Declined one"))
    await client.post("/interview/revision", json={"approved": []}, headers=author["headers"])
    assert state["changes"]

    await database.interviews.update_one(
        {"user_id": author["id"]},
        {
            "$push": {
                "removed_chapters": {"id": "gone", "title": "Removed one", "summary": "Left that job badly."}
            }
        },
    )
    await propose(client, author, fake_claude, change())
    for request in fake_claude.requests[-2:]:
        data = member_data(request)
        assert "<off_limits>" in data
        assert "Removed one" in data
        assert "Declined one" in data
    assert "<off_limits>" in load_prompt("interview/adding")
    assert "<off_limits>" in load_prompt("interview/revise")


async def test_removing_a_draft_chapter_is_remembered(client, database, fake_claude, monkeypatch):
    person = await member(client, "draft@case.edu")
    many = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(4)]
    await books.create_draft_book(database, author_id=person["id"], title="Draft", chapters=many, blurb="B.")
    await database.interviews.insert_one(
        {
            "_id": "i",
            "user_id": person["id"],
            "stage": "reviewing",
            "turns": [{"question": "Q?", "answer": OLD_ANSWER, "phase": "dig"}],
            "current": None,
        }
    )
    fake_claude.responses.append(text_message(json.dumps({"blurb": "What's left."})))
    response = await client.delete("/interview/book/chapters/c1", headers=person["headers"])
    assert response.status_code == 200
    saved = await database.interviews.find_one({"user_id": person["id"]})
    assert saved["removed_chapters"][0]["title"] == "T1"


async def test_removing_from_a_shelved_book_goes_through_the_confirm_step(client, database, fake_claude):
    person = await member(client, "remove@case.edu")
    many = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(4)]
    await shelve_book(database, person["id"], many)
    before = await database.books.find_one({"author_id": person["id"]})

    state = (
        await client.post("/interview/removal", json={"chapter_id": "c1"}, headers=person["headers"])
    ).json()
    assert state["stage"] == "revising"
    assert state["revision_status"] == "ready"
    item = state["changes"][0]
    assert item["kind"] == "remove"
    assert item["current"]["title"] == "T1"
    assert state["proposed_blurb"] is None
    assert await database.books.find_one({"author_id": person["id"]}) == before

    await choose(client, person["headers"], [item["id"]])
    fake_claude.responses.append(text_message(json.dumps({"blurb": "Without that chapter."})))
    shown = await ask_for_blurb(client, person["headers"])
    assert shown["selection_blurb"] == "Without that chapter."
    book = (
        await client.post(
            "/interview/revision", json={"approved": [item["id"]], "blurb": "use"}, headers=person["headers"]
        )
    ).json()
    assert [c["id"] for c in book["chapters"]] == ["c0", "c2", "c3"]
    assert book["blurb"] == "Without that chapter."
    saved = await database.interviews.find_one({"user_id": person["id"]})
    assert saved["removed_chapters"][0]["title"] == "T1"
    assert saved["stage"] == "done"


async def test_no_removal_at_three_chapters_or_during_a_round(client, author, fake_claude):
    response = await client.post("/interview/removal", json={"chapter_id": "c0"}, headers=author["headers"])
    assert response.status_code == 409
    missing = await client.post("/interview/removal", json={"chapter_id": "nope"}, headers=author["headers"])
    assert missing.status_code == 404


async def test_declining_a_removal_changes_nothing(client, database, fake_claude):
    person = await member(client, "keep@case.edu")
    many = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(4)]
    await shelve_book(database, person["id"], many)
    before = await database.books.find_one({"author_id": person["id"]})
    await client.post("/interview/removal", json={"chapter_id": "c1"}, headers=person["headers"])
    await client.post("/interview/revision", json={"approved": []}, headers=person["headers"])
    assert await database.books.find_one({"author_id": person["id"]}) == before
    saved = await database.interviews.find_one({"user_id": person["id"]})
    assert not saved.get("removed_chapters")
    assert not saved.get("declined_changes")


async def test_an_applied_revision_can_be_undone_once(client, database, author, reader, fake_claude):
    before = await database.books.find_one({"author_id": author["id"]})
    assert (await client.post("/interview/book/undo", headers=author["headers"])).status_code == 409

    state = await propose(client, author, fake_claude, change("improve", "c1", title="Worse"))
    book = (
        await client.post(
            "/interview/revision",
            json={"approved": [state["changes"][0]["id"]], "blurb": "use"},
            headers=author["headers"],
        )
    ).json()
    assert book["can_undo"] is True
    assert book["blurb"] == "The proposed blurb."

    public = (await client.get(f"/books/{before['_id']}", headers=reader["headers"])).text
    assert "previous_version" not in public
    assert "Chapter 1" not in public
    assert "previous_version" not in books.PUBLIC_FIELDS

    undone = (await client.post("/interview/book/undo", headers=author["headers"])).json()
    assert undone["can_undo"] is False
    assert [c["title"] for c in undone["chapters"]] == ["Chapter 0", "Chapter 1", "Chapter 2"]
    assert undone["blurb"] == "The old blurb."
    after = await database.books.find_one({"author_id": author["id"]})
    assert after["chapters"] == before["chapters"]
    assert after["published_at"] == before["published_at"]
    assert (await client.post("/interview/book/undo", headers=author["headers"])).status_code == 409


async def test_undo_is_only_from_done(client, author, fake_claude):
    state = await propose(client, author, fake_claude, change())
    await client.post(
        "/interview/revision", json={"approved": [state["changes"][0]["id"]]}, headers=author["headers"]
    )
    await start_round(client, author, fake_claude)
    assert (await client.post("/interview/book/undo", headers=author["headers"])).status_code == 409


async def test_undo_lets_a_removed_chapter_come_back_for_good(client, database, fake_claude):
    person = await member(client, "undo@case.edu")
    many = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(4)]
    await shelve_book(database, person["id"], many)
    state = (
        await client.post("/interview/removal", json={"chapter_id": "c1"}, headers=person["headers"])
    ).json()
    await client.post(
        "/interview/revision", json={"approved": [state["changes"][0]["id"]]}, headers=person["headers"]
    )
    await client.post("/interview/book/undo", headers=person["headers"])
    saved = await database.interviews.find_one({"user_id": person["id"]})
    assert saved["removed_chapters"] == []


async def finish_to_failure(client, author, fake_claude) -> dict:
    await start_round(client, author, fake_claude)
    fake_claude.responses.append(round_over())
    await send_answer(client, author["headers"], NEW_ANSWER)
    fake_claude.responses.append(text_message("not json"))
    response = await client.post("/interview/finish", headers=author["headers"])
    assert response.status_code == 200
    return response.json()


async def test_finishing_writes_in_the_background_and_reports_it(client, author, fake_claude):
    await start_round(client, author, fake_claude)
    fake_claude.responses.append(round_over())
    await send_answer(client, author["headers"], NEW_ANSWER)
    fake_claude.responses.append(revision(change()))
    state = (await client.post("/interview/finish", headers=author["headers"])).json()
    assert state["stage"] == "revising"
    assert state["revision_status"] == "writing"
    assert state["changes"] is None
    state = (await client.get("/interview", headers=author["headers"])).json()
    assert state["revision_status"] == "ready"
    assert len(state["changes"]) == 1
    assert (await client.post("/interview/finish", headers=author["headers"])).status_code == 409


async def test_a_return_after_a_failed_write_retries_once_on_its_own(client, database, author, fake_claude):
    await finish_to_failure(client, author, fake_claude)
    saved = await database.interviews.find_one({"user_id": author["id"]})
    assert saved["write_status"] == "failed"
    assert saved["turns"][-1]["answer"] == NEW_ANSWER

    fake_claude.responses.append(text_message("still not json"))
    state = (await client.get("/interview", headers=author["headers"])).json()
    assert state["revision_status"] == "writing"

    calls = len(fake_claude.requests)
    state = (await client.get("/interview", headers=author["headers"])).json()
    assert state["revision_status"] == "failed"
    assert state["can_finish"] is True
    assert len(fake_claude.requests) == calls

    fake_claude.responses.append(revision(change()))
    await client.post("/interview/finish", headers=author["headers"])
    state = (await client.get("/interview", headers=author["headers"])).json()
    assert len(state["changes"]) == 1


async def test_a_write_that_died_with_the_server_counts_as_failed(client, database, author, fake_claude):
    await start_round(client, author, fake_claude)
    fake_claude.responses.append(round_over())
    await send_answer(client, author["headers"], NEW_ANSWER)
    await database.interviews.update_one(
        {"user_id": author["id"]},
        {
            "$set": {
                "stage": "revising",
                "proposal": None,
                "round_end": 2,
                "write_status": "writing",
                "write_retried": True,
                "updated_at": datetime.now(UTC) - service.WRITING_TIMEOUT - timedelta(seconds=1),
            }
        },
    )
    state = (await client.get("/interview", headers=author["headers"])).json()
    assert state["revision_status"] == "failed"


async def test_no_key_doesnt_break_reading_the_interview(client, database, author, monkeypatch):
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "")
    state = await client.get("/interview", headers=author["headers"])
    assert state.status_code == 200


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
    saved = await spark(client, reader, author)
    own = [
        {"id": f"r{n}", "title": f"Mine {n}", "summary": "Mine.", "quotes": [OLD_ANSWER]} for n in range(3)
    ]
    await shelve_book(database, reader["id"], own)
    await start_round(client, reader, fake_claude)

    prompt = member_data(fake_claude.requests[-1])
    assert f"<sparks>\n- [{saved.json()['id']}] Chapter 0\n</sparks>" in prompt
    assert "Summary 0" not in prompt
    assert "Hana" not in prompt
    assert "Sato" not in prompt
    assert author["book"]["_id"] not in prompt
    assert author["id"] not in prompt


async def test_sparks_reach_a_first_interview(client, author, reader, scripted_ai):
    await spark(client, reader, author)
    await client.post("/interview", json={}, headers=reader["headers"])
    prompt = member_data(scripted_ai.requests[0])
    assert "Chapter 0\n</sparks>" in prompt
    assert "Summary 0" not in prompt
    assert "The Book" not in prompt


async def test_a_spark_is_used_only_when_its_question_is_asked(client, database, author, reader, fake_claude):
    await shelve_book(database, reader["id"])
    used = (await spark(client, reader, author, "c0")).json()
    await spark(client, reader, author, "c1")

    await start_round(client, reader, fake_claude)
    assert len((await client.get("/interview/sparks", headers=reader["headers"])).json()) == 2

    fake_claude.responses.append(
        text_message(json.dumps({"question": "Yours?", "topic": "t", "done": False, "spark_id": used["id"]}))
    )
    await send_answer(client, reader["headers"], NEW_ANSWER)
    waiting = (await client.get("/interview/sparks", headers=reader["headers"])).json()
    assert [item["chapter_id"] for item in waiting] == ["c1"]

    # Finishing the round doesn't use up the one nobody asked about.
    fake_claude.responses.append(revision(change()))
    await client.post("/interview/finish", headers=reader["headers"])
    assert len((await client.get("/interview/sparks", headers=reader["headers"])).json()) == 1


async def test_a_spark_title_stays_out_of_a_first_book(client, database, author, reader, fake_claude):
    saved = (await spark(client, reader, author, "c0")).json()
    fake_claude.responses.append(
        text_message(
            json.dumps(
                {
                    "threads": [],
                    "phase": "sweep",
                    "question": "You saved Chapter 0. Yours?",
                    "playback": None,
                    "topic": "t",
                    "ready_for_reveal": False,
                    "spark_id": saved["id"],
                }
            )
        )
    )
    await client.post("/interview", json={}, headers=reader["headers"])
    await database.interviews.update_one(
        {"user_id": reader["id"]},
        {
            "$push": {
                "turns": {
                    "$each": [
                        {"question": "Q?", "answer": f"{OLD_ANSWER} {n}", "phase": "dig"} for n in range(10)
                    ]
                }
            }
        },
    )
    fake_claude.responses.append(
        text_message(
            json.dumps(
                {
                    "pool": [
                        {"title": "Chapter 0", "summary": "S.", "quotes": [f"{OLD_ANSWER} 9"]},
                        *(
                            {"title": f"Own {n}", "summary": "S.", "quotes": [f"{OLD_ANSWER} {n}"]}
                            for n in range(3)
                        ),
                    ],
                    "titles": [{"title": f"T{n}", "why": "W."} for n in range(3)],
                    "blurb": "A blurb of mine.",
                }
            )
        )
    )
    await client.post("/interview/finish", headers=reader["headers"])
    saved_interview = await database.interviews.find_one({"user_id": reader["id"]})
    assert [c["title"] for c in saved_interview["draft"]["pool"]] == ["Own 0", "Own 1", "Own 2"]
    assert "You saved Chapter 0" not in member_data(fake_claude.requests[-1])


async def test_a_used_spark_can_be_saved_again(client, database, author, reader):
    saved = (await spark(client, reader, author)).json()
    await database.sparks.update_one({"_id": saved["id"]}, {"$set": {"used_at": datetime.now(UTC)}})
    assert (await client.get("/interview/sparks", headers=reader["headers"])).json() == []
    await spark(client, reader, author)
    assert len((await client.get("/interview/sparks", headers=reader["headers"])).json()) == 1
    assert await database.sparks.count_documents({"user_id": reader["id"]}) == 1


async def test_at_most_three_sparks_a_round_newest_first(client, database, reader, fake_claude):
    other = await member(client, "big@case.edu", "Big", "Book")
    many = [{"id": f"m{n}", "title": f"Title {n}", "summary": "S.", "quotes": [OLD_ANSWER]} for n in range(5)]
    other["book"] = await shelve_book(database, other["id"], many)
    await shelve_book(database, reader["id"])
    ids = {}
    for n in range(5):
        ids[n] = (await spark(client, reader, other, f"m{n}")).json()["id"]
        await database.sparks.update_one(
            {"_id": ids[n]}, {"$set": {"created_at": datetime(2026, 1, 1 + n, tzinfo=UTC)}}
        )
    await start_round(client, reader, fake_claude)
    prompt = member_data(fake_claude.requests[-1])
    assert all(f"Title {n}" in prompt for n in (4, 3, 2))
    assert not any(f"Title {n}" in prompt for n in (1, 0))

    for n in (4, 3, 2):
        fake_claude.responses.append(
            text_message(json.dumps({"question": f"Q{n}?", "topic": "t", "done": False, "spark_id": ids[n]}))
        )
        await send_answer(client, reader["headers"], NEW_ANSWER)
    # Three have been asked about, so the rest wait for the next round.
    assert "<sparks>" not in member_data(fake_claude.requests[-1]) or "Title 1" not in member_data(
        fake_claude.requests[-1]
    )
    fake_claude.responses.append(round_over())
    await send_answer(client, reader["headers"], NEW_ANSWER)
    assert "<sparks>" not in member_data(fake_claude.requests[-1])
    assert len((await client.get("/interview/sparks", headers=reader["headers"])).json()) == 2


async def test_a_spark_title_is_redacted_and_cant_become_a_chapter(
    client, database, author, reader, fake_claude
):
    await shelve_book(database, reader["id"])
    used = (await spark(client, reader, author, "c0")).json()
    fake_claude.responses.append(
        text_message(
            json.dumps(
                {
                    "question": "You saved Chapter 0. Yours?",
                    "topic": "t",
                    "done": False,
                    "spark_id": used["id"],
                }
            )
        )
    )
    await client.post("/interview/reopen", headers=reader["headers"])
    fake_claude.responses.append(round_over())
    await send_answer(client, reader["headers"], NEW_ANSWER)
    fake_claude.responses.append(
        revision(
            change(title="chapter 0", quotes=[PART_ONE]),
            change(title="My own inventory story", quotes=[PART_TWO]),
        )
    )
    await client.post("/interview/finish", headers=reader["headers"])

    state = (await client.get("/interview", headers=reader["headers"])).json()
    assert [c["title"] for c in state["changes"]] == ["My own inventory story"]
    data = member_data(fake_claude.requests[-1])
    assert "You saved that topic. Yours?" in data
    assert "You saved Chapter 0" not in data


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
    assert set(questions[0]) == {"id", "question", "created_at", "reader_name"}
    assert "checkout-1" not in json.dumps(questions)


async def a_reading_with(database, author, reader, checkout_id="checkout-secret") -> None:
    await database.checkouts.insert_one(
        {
            "_id": checkout_id,
            "reader_id": reader["id"],
            "author_id": author["id"],
            "book_id": author["book"]["_id"],
            "status": "accepted",
            "created_at": datetime.now(UTC),
            "open": True,
        }
    )
    await service.ask_after_reading(database, author["id"], checkout_id)


async def test_the_author_sees_who_the_reading_was_with(client, database, author, reader):
    await a_reading_with(database, author, reader)
    questions = (await client.get("/interview/reading-questions", headers=author["headers"])).json()
    assert questions[0]["reader_name"] == "Rae Jones"


async def test_only_the_newest_shows_and_old_ones_go_away(client, database, author):
    await service.ask_after_reading(database, author["id"], "old")
    await service.ask_after_reading(database, author["id"], "recent")
    await service.ask_after_reading(database, author["id"], "newest")
    now = datetime.now(UTC)
    await database.reading_questions.update_one(
        {"checkout_id": "old"},
        {"$set": {"created_at": now - timedelta(days=service.READING_QUESTION_DAYS + 1)}},
    )
    await database.reading_questions.update_one(
        {"checkout_id": "recent"}, {"$set": {"created_at": now - timedelta(days=1)}}
    )
    questions = (await client.get("/interview/reading-questions", headers=author["headers"])).json()
    assert len(questions) == 1

    newest = await database.reading_questions.find_one({"checkout_id": "newest"})
    assert questions[0]["id"] == newest["_id"]
    assert (await database.reading_questions.find_one({"checkout_id": "old"}))["dismissed_at"] is not None
    assert (await database.reading_questions.find_one({"checkout_id": "recent"}))["dismissed_at"] is None


async def test_the_reader_never_enters_the_prompt(client, database, author, reader, fake_claude):
    await a_reading_with(database, author, reader)
    question = (await client.get("/interview/reading-questions", headers=author["headers"])).json()[0]["id"]
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
    assert "Never name or describe" in prompt


NAMED = "Sam from Deloitte asked how I would handle leaving since she is about to quit."
PLAIN = "They asked how I would handle leaving a steady job before anything else lined up."


async def answer_reading(client, database, author, fake_claude, text: str, *changes: dict) -> dict:
    question = await waiting_question(client, database, author)
    fake_claude.responses.append(revision(*changes))
    response = await client.post(
        f"/interview/reading-questions/{question}/answer", json={"answer": text}, headers=author["headers"]
    )
    assert response.status_code == 200, response.text
    return (await client.get("/interview", headers=author["headers"])).json()


async def test_a_reading_quote_naming_someone_is_dropped(client, database, author, fake_claude):
    state = await answer_reading(client, database, author, fake_claude, NAMED, change(quotes=[NAMED]))
    assert state["stage"] == "done"
    assert state["nothing_new"] is True


async def test_a_name_from_a_reading_answer_cant_reach_public_text(client, database, author, fake_claude):
    text = f"{NAMED} {PLAIN}"
    named_summary = {
        **change(quotes=[PLAIN], title="About leaving"),
        "summary": "What Sam asked me about leaving.",
    }
    plain = change(quotes=[PLAIN], title="Leaving before the next thing")
    state = await answer_reading(client, database, author, fake_claude, text, named_summary, plain)
    assert [c["title"] for c in state["changes"]] == ["Leaving before the next thing"]
    assert state["changes"][0]["quotes"] == [PLAIN]


async def test_the_members_own_name_in_a_reading_answer_is_fine(client, database, author, fake_claude):
    text = "They asked why everyone calls me Hana instead of my full name at work."
    state = await answer_reading(client, database, author, fake_claude, text, change(quotes=[text]))
    assert state["stage"] == "revising"
    assert len(state["changes"]) == 1


async def test_a_blurb_naming_someone_isnt_proposed(client, database, author, fake_claude):
    text = f"{NAMED} {PLAIN}"
    question = await waiting_question(client, database, author)
    fake_claude.responses.append(
        revision(change(quotes=[PLAIN]), blurb="I learned this from Sam, and now I know it.")
    )
    await client.post(
        f"/interview/reading-questions/{question}/answer", json={"answer": text}, headers=author["headers"]
    )
    state = (await client.get("/interview", headers=author["headers"])).json()
    assert state["stage"] == "revising"
    assert state["proposed_blurb"] is None


async def test_an_answer_goes_through_revise_and_approval(client, database, author, fake_claude):
    before = await database.books.find_one({"author_id": author["id"]})
    state = await answer_reading(client, database, author, fake_claude, NEW_ANSWER, change())
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


async def test_a_thin_answer_can_yield_no_changes(client, database, author, fake_claude):
    state = await answer_reading(client, database, author, fake_claude, "Not much.")
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
    assert response.status_code == 200
    saved = await database.interviews.find_one({"user_id": author["id"]})
    assert saved["write_status"] == "failed"
    assert saved["turns"][-1]["answer"] == NEW_ANSWER
    fake_claude.responses.append(revision(change()))
    state = (await client.get("/interview", headers=author["headers"])).json()
    assert state["revision_status"] == "writing"
    state = (await client.get("/interview", headers=author["headers"])).json()
    assert len(state["changes"]) == 1


async def test_while_changes_wait_an_answer_runs_after_the_decision(client, database, author, fake_claude):
    question = await waiting_question(client, database, author)
    waiting = await propose(client, author, fake_claude, change(title="First proposal"))
    state = (
        await client.post(
            f"/interview/reading-questions/{question}/answer",
            json={"answer": PLAIN},
            headers=author["headers"],
        )
    ).json()
    # Nothing lands on the undecided proposal.
    assert [c["title"] for c in state["changes"]] == ["First proposal"]
    assert (await client.get("/interview/reading-questions", headers=author["headers"])).json() == []

    fake_claude.responses.append(revision(change(quotes=[PLAIN], title="From the reading")))
    await client.post(
        "/interview/revision", json={"approved": [waiting["changes"][0]["id"]]}, headers=author["headers"]
    )
    state = (await client.get("/interview", headers=author["headers"])).json()
    assert state["stage"] == "revising"
    assert [c["title"] for c in state["changes"]] == ["From the reading"]
    data = member_data(fake_claude.requests[-1])
    new_round = data.split("<new_round>")[1].split("</new_round>")[0]
    assert PLAIN in new_round
    assert NEW_ANSWER not in new_round


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


async def test_someone_elses_question_is_404(client, database, author, reader):
    question = await waiting_question(client, database, author)
    await shelve_book(database, reader["id"])
    for path, body in (("answer", {"answer": "Mine now."}), ("dismiss", None)):
        response = await client.post(
            f"/interview/reading-questions/{question}/{path}", json=body, headers=reader["headers"]
        )
        assert response.status_code == 404
