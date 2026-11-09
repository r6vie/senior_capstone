import base64
from datetime import UTC, datetime

import anthropic
import pytest

from tests.fakes import send_answer, send_skip
from trove.interview import engine, service
from trove.interview.engine import Draft, DraftChapter, FinishedBook, NextTurn, TitleOption

SIGNUP = {
    "first_name": "Hana",
    "last_name": "Sato",
    "email": "hana@example.com",
    "password": "a long test passphrase",
}


def minimal_pdf(text: str) -> bytes:
    """A one-page PDF containing `text`, built by hand so tests need no PDF writer."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R"
        b" /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    pdf, offsets = b"%PDF-1.4\n", []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref = len(pdf)
    pdf += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    pdf += b"".join(b"%010d 00000 n \n" % offset for offset in offsets)
    pdf += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objects) + 1, xref)
    return pdf


POOL = [
    DraftChapter(id=f"c{n}", title=f"Chapter {n}", summary=f"About {n}.", quotes=[f"Quote {n}."])
    for n in range(1, 6)
]
TITLES = [TitleOption(title=f"Title {n}", why=f"Because {n}.") for n in range(3)]


class FakeEngine:
    """Stands in for the interview engine: asks numbered questions, then a Shape step on request."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []
        self.shape_next = False
        self.ready_next = False
        self.fail_next = False
        self.fail_blurb = False

    async def next_turn(self, claude, *, turns, resume_text, sparks=None, more_material=False):
        self.calls.append(("next_turn", {"turns": turns, "resume_text": resume_text}))
        if self.fail_next:
            self.fail_next = False
            raise anthropic.APIConnectionError(request=None)
        if self.shape_next:
            self.shape_next = False
            return NextTurn(
                question="Is this you?",
                phase="shape",
                playback="You walked away twice.",
                ready_for_reveal=False,
                topic="the second offer you turned down",
            )
        return NextTurn(
            question=f"Question {len(turns) + 1}?",
            phase="sweep" if len(turns) < 5 else "dig",
            playback=None,
            ready_for_reveal=self.ready_next,
            topic=f"topic {len(turns)}",
        )

    async def draft_book(self, claude, *, turns, **_):
        self.calls.append(("draft_book", {"turns": turns}))
        return Draft(pool=POOL, titles=TITLES, blurb="I know the pool.")

    async def finish_book(self, claude, *, turns, draft, title, **_):
        self.calls.append(("finish_book", {"title": title}))
        return FinishedBook(chapters=POOL[:4], blurb=f"I know {title}.")

    async def write_blurb(self, claude, *, turns, chapters, **_):
        self.calls.append(("write_blurb", {"chapters": [c.id for c in chapters]}))
        if self.fail_blurb:
            self.fail_blurb = False
            raise ValueError("unusable")
        return "I know " + ", ".join(c.id for c in chapters) + "."

    async def rewrite_chapter(self, claude, *, turns, chapters, chapter_id, **_):
        self.calls.append(("rewrite_chapter", {"chapter_id": chapter_id}))
        return DraftChapter(id=chapter_id, title="Rewritten", summary="Better.", quotes=["Quote 1."])


@pytest.fixture
def fake_engine(monkeypatch, fake_claude):
    fake = FakeEngine()
    for name in ("next_turn", "draft_book", "finish_book", "write_blurb", "rewrite_chapter"):
        monkeypatch.setattr(engine, name, getattr(fake, name))
    return fake


@pytest.fixture
async def headers(client):
    await client.post("/auth/signup", json=SIGNUP)
    login = await client.post("/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def answer_questions(client, headers, count: int) -> dict:
    state = {}
    for n in range(count):
        response = await send_answer(client, headers, f"Answer {n}.")
        assert response.status_code == 200, response.text
        state = response.json()
    return state


async def test_routes_require_sign_in(client):
    assert (await client.post("/interview", json={})).status_code == 401
    assert (await client.get("/interview")).status_code == 401
    assert (await client.post("/interview/answers", json={"answer": "Hi"})).status_code == 401
    assert (await client.post("/interview/book/shelve")).status_code == 401


async def test_full_flow_from_first_question_to_the_shelf(client, database, headers, fake_engine):
    assert (await client.get("/interview", headers=headers)).status_code == 404

    started = await client.post("/interview", json={}, headers=headers)
    assert started.status_code == 201
    state = started.json()
    assert state["stage"] == "interviewing"
    assert state["question"]["question_id"]
    assert state["question"] == {
        "question_id": state["question"]["question_id"],
        "text": "Question 1?",
        "phase": "sweep",
        "playback": None,
    }
    assert state["can_finish"] is False
    assert state["has_answers"] is False

    state = await answer_questions(client, headers, 9)
    assert state["has_answers"] is True
    assert state["question"]["text"] == "Question 10?"
    assert state["can_finish"] is False
    # Too early to say "I've said enough".
    assert (await client.post("/interview/finish", headers=headers)).status_code == 409

    fake_engine.shape_next = True
    state = await answer_questions(client, headers, 1)
    assert state["can_finish"] is True
    assert state["question"]["question_id"]
    assert state["question"] == {
        "question_id": state["question"]["question_id"],
        "text": "Is this you?",
        "phase": "shape",
        "playback": "You walked away twice.",
    }
    # The Shape step takes a confirmation or correction, not an ordinary answer.
    assert (await send_answer(client, headers, "x")).status_code == 409

    state = (await client.post("/interview/shape", json={}, headers=headers)).json()
    assert state["question"]["text"] == "Question 12?"
    interview = await database.interviews.find_one({})
    assert interview["turns"][10] == {
        "question": "Is this you?",
        "answer": "Yes, that's me.",
        "phase": "shape",
    }

    # Resuming shows the waiting question and what they were talking about.
    resumed = (await client.get("/interview", headers=headers)).json()
    assert resumed["question"]["text"] == "Question 12?"
    assert resumed["topic"] == "topic 11"

    state = (await client.post("/interview/finish", headers=headers)).json()
    assert state["stage"] == "choosing"
    assert state["question"] is None
    assert state["titles"] == [{"title": f"Title {n}", "why": f"Because {n}."} for n in range(3)]
    assert state["blurb"] == "I know the pool."

    book = await client.post("/interview/title", json={"title": 1}, headers=headers)
    assert book.status_code == 200
    book = book.json()
    assert book["title"] == "Title 1"
    assert book["author_name"] == "Hana Sato"
    assert book["status"] == "draft"
    assert [c["id"] for c in book["chapters"]] == ["c1", "c2", "c3", "c4"]
    assert book["blurb"] == "I know Title 1."
    reviewing = (await client.get("/interview", headers=headers)).json()
    assert (reviewing["stage"], reviewing["blurb"]) == ("reviewing", "I know Title 1.")
    assert ("finish_book", {"title": "Title 1"}) in fake_engine.calls
    # A draft isn't on the shelf yet.
    assert (await client.get(f"/books/{book['id']}", headers=headers)).status_code == 404

    book = (await client.delete("/interview/book/chapters/c2", headers=headers)).json()
    assert [c["id"] for c in book["chapters"]] == ["c1", "c3", "c4"]
    # The back cover is rewritten for what's left.
    assert book["blurb"] == "I know c1, c3, c4."
    assert (await client.get("/interview", headers=headers)).json()["blurb"] == "I know c1, c3, c4."
    # Three chapters is the minimum.
    assert (await client.delete("/interview/book/chapters/c1", headers=headers)).status_code == 409
    assert (await client.delete("/interview/book/chapters/nope", headers=headers)).status_code == 404

    book = (await client.post("/interview/book/chapters/c3/rewrite", headers=headers)).json()
    assert book["chapters"][1] == {
        "id": "c3",
        "title": "Rewritten",
        "summary": "Better.",
        "quotes": ["Quote 1."],
        "has_previous": True,
    }
    # A rewrite keeps the chapter's topic, so the blurb stays.
    assert book["blurb"] == "I know c1, c3, c4."

    shelved = await client.post("/interview/book/shelve", headers=headers)
    assert shelved.status_code == 200
    assert shelved.json()["status"] == "on_shelf"
    shelved_book = await client.get(f"/books/{book['id']}", headers=headers)
    assert shelved_book.status_code == 200
    assert shelved_book.json()["blurb"] == "I know c1, c3, c4."
    shelf = (await client.get("/books", headers=headers)).json()["books"]
    assert next(b for b in shelf if b["id"] == book["id"])["blurb"] == "I know c1, c3, c4."
    assert (await client.get("/interview", headers=headers)).json()["stage"] == "done"
    assert (await client.post("/interview/book/shelve", headers=headers)).status_code == 409


async def test_a_member_with_a_book_cannot_start_again(client, database, headers, fake_engine):
    assert (await client.post("/interview", json={}, headers=headers)).status_code == 201
    assert (await client.post("/interview", json={}, headers=headers)).status_code == 409

    await database.interviews.delete_many({})
    user = await database.users.find_one({})
    await database.books.insert_one({"_id": "b", "author_id": user["_id"], "chapters": [], "status": "draft"})
    response = await client.post("/interview", json={}, headers=headers)
    assert response.status_code == 409
    assert response.json()["detail"] == "You already have a book."


async def test_steps_out_of_order_are_409(client, headers, fake_engine):
    assert (await send_answer(client, headers, "Hi")).status_code == 404
    await client.post("/interview", json={}, headers=headers)
    assert (await client.post("/interview/title", json={"title": 0}, headers=headers)).status_code == 409
    assert (await client.post("/interview/book/shelve", headers=headers)).status_code == 409
    assert (await client.post("/interview/shape", json={}, headers=headers)).status_code == 409


async def test_the_librarian_can_end_the_interview(client, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    fake_engine.ready_next = True
    state = await answer_questions(client, headers, 1)
    assert state["ready_for_reveal"] is True
    assert state["can_finish"] is True
    assert state["question"] is None
    assert (await client.post("/interview/finish", headers=headers)).json()["stage"] == "choosing"


async def test_answers_are_saved_even_when_the_next_question_fails(client, database, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    fake_engine.fail_next = True
    response = await send_answer(client, headers, "Something I'd hate to retype.")
    assert response.status_code == 502

    interview = await database.interviews.find_one({})
    assert interview["turns"][0]["answer"] == "Something I'd hate to retype."
    assert (await client.get("/interview", headers=headers)).json()["question"] is None

    state = (await client.post("/interview/question", headers=headers)).json()
    assert state["question"]["text"] == "Question 2?"


async def test_resume_text_is_used_then_deleted_and_the_file_is_never_kept(
    client, database, headers, fake_engine
):
    pdf = base64.b64encode(minimal_pdf("Ran the assay lab for three years")).decode()
    assert (await client.post("/interview", json={"resume_pdf": pdf}, headers=headers)).status_code == 201
    assert "assay lab" in fake_engine.calls[0][1]["resume_text"]
    interview = await database.interviews.find_one({})
    assert pdf not in str(interview)
    assert "assay lab" not in str(interview)
    saved = await database.resume_texts.find_one({"_id": interview["_id"]})
    assert "assay lab" in saved["text"]

    await answer_questions(client, headers, 10)
    await client.post("/interview/finish", headers=headers)
    assert await database.resume_texts.count_documents({}) == 0


async def test_unreadable_resume_is_422(client, headers, fake_engine):
    not_pdf = base64.b64encode(b"just text").decode()
    assert (await client.post("/interview", json={"resume_pdf": not_pdf}, headers=headers)).status_code == 422
    assert (await client.post("/interview", json={"resume_pdf": "%%%"}, headers=headers)).status_code == 422
    broken = base64.b64encode(b"%PDF-1.4 broken").decode()
    assert (await client.post("/interview", json={"resume_pdf": broken}, headers=headers)).status_code == 422


async def test_a_removal_whose_blurb_fails_removes_nothing(client, database, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    await answer_questions(client, headers, 10)
    await client.post("/interview/finish", headers=headers)
    await client.post("/interview/title", json={"title": 0}, headers=headers)

    fake_engine.fail_blurb = True
    assert (await client.delete("/interview/book/chapters/c2", headers=headers)).status_code == 502
    book = await database.books.find_one({})
    assert [c["id"] for c in book["chapters"]] == ["c1", "c2", "c3", "c4"]
    assert book["blurb"] == "I know Title 0."


async def test_skip_saves_an_empty_answer_and_moves_on(client, database, headers, fake_engine):
    first = (await client.post("/interview", json={}, headers=headers)).json()
    state = (await send_skip(client, headers)).json()
    assert state["question"]["text"] != first["question"]["text"]

    saved = await database.interviews.find_one({})
    assert saved["turns"] == [
        {"question": first["question"]["text"], "answer": "", "phase": first["question"]["phase"]}
    ]


async def test_skips_unlock_nothing(client, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    for _ in range(service.EXIT_AFTER_ANSWERS + 1):
        state = (await send_skip(client, headers)).json()
    assert state["has_answers"] is False
    assert state["can_finish"] is False
    assert (await client.post("/interview/finish", headers=headers)).status_code == 409


async def test_skips_are_never_in_the_response(client, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    state = (await send_skip(client, headers)).json()
    assert not [key for key in state if "skip" in key]


async def test_skip_is_409_without_a_question_and_on_the_shape_step(client, database, headers, fake_engine):
    assert (await send_skip(client, headers)).status_code == 404
    await client.post("/interview", json={}, headers=headers)
    await database.interviews.update_one(
        {}, {"$set": {"current": {"question": "Is this you?", "phase": "shape", "playback": "You."}}}
    )
    assert (await send_skip(client, headers)).status_code == 409
    await database.interviews.update_one({}, {"$set": {"current": None}})
    assert (await send_skip(client, headers)).status_code == 409


async def test_finish_saves_what_is_in_the_field_first(client, database, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    state = await answer_questions(client, headers, service.EXIT_AFTER_ANSWERS - 1)
    waiting = state["question"]
    assert state["can_finish"] is False

    response = await client.post(
        "/interview/finish", json={"answer": "The last thing I said."}, headers=headers
    )
    assert response.status_code == 200, response.text
    assert response.json()["stage"] == "choosing"
    saved = await database.interviews.find_one({})
    assert saved["turns"][-1] == {
        "question": waiting["text"],
        "answer": "The last thing I said.",
        "phase": waiting["phase"],
    }


async def test_finish_too_early_keeps_the_question_and_saves_nothing(client, database, headers, fake_engine):
    first = (await client.post("/interview", json={}, headers=headers)).json()
    response = await client.post("/interview/finish", json={"answer": "Too soon."}, headers=headers)
    assert response.status_code == 409
    saved = await database.interviews.find_one({})
    assert saved["turns"] == []
    assert saved["current"]["question"] == first["question"]["text"]


async def test_finish_with_no_body_still_works(client, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    await answer_questions(client, headers, service.EXIT_AFTER_ANSWERS)
    assert (await client.post("/interview/finish", headers=headers)).status_code == 200


async def test_abandoned_resume_text_expires_30_days_after_the_last_activity(
    client, database, headers, fake_engine
):
    indexes = await database.resume_texts.index_information()
    assert indexes["resume_texts_expire"]["expireAfterSeconds"] == 30 * 24 * 60 * 60
    assert indexes["resume_texts_expire"]["key"] == [("last_activity_at", 1)]

    pdf = base64.b64encode(minimal_pdf("Ran the assay lab for three years")).decode()
    await client.post("/interview", json={"resume_pdf": pdf}, headers=headers)
    long_ago = datetime(2020, 1, 1, tzinfo=UTC)
    await database.resume_texts.update_one({}, {"$set": {"last_activity_at": long_ago}})
    await answer_questions(client, headers, 1)
    saved = await database.resume_texts.find_one({})
    assert saved["last_activity_at"].year > 2020


async def test_the_start_request_says_what_happens_to_the_resume(client):
    schema = (await client.get("/openapi.json")).json()
    description = schema["components"]["schemas"]["StartRequest"]["properties"]["resume_pdf"]["description"]
    assert "30 days" in description
    assert "Never stored" not in description


async def to_review(client, headers, fake_engine) -> dict:
    await client.post("/interview", json={}, headers=headers)
    await answer_questions(client, headers, service.EXIT_AFTER_ANSWERS)
    await client.post("/interview/finish", headers=headers)
    return (await client.post("/interview/title", json={"title": 0}, headers=headers)).json()


async def test_the_other_titles_stay_available_in_review(client, headers, fake_engine):
    await to_review(client, headers, fake_engine)
    state = (await client.get("/interview", headers=headers)).json()
    assert state["stage"] == "reviewing"
    assert [t["title"] for t in state["titles"]] == [t.title for t in TITLES]


async def test_change_to_another_title_finishes_the_book_again(client, headers, fake_engine):
    book = await to_review(client, headers, fake_engine)
    response = await client.post("/interview/book/title", json={"title": 1}, headers=headers)
    assert response.status_code == 200
    changed = response.json()
    assert changed["title"] == TITLES[1].title
    assert changed["id"] == book["id"]
    assert changed["blurb"] == f"I know {TITLES[1].title}."


async def test_the_same_title_costs_nothing(client, headers, fake_engine):
    await to_review(client, headers, fake_engine)
    calls = len(fake_engine.calls)
    response = await client.post("/interview/book/title", json={"title": 0}, headers=headers)
    assert response.status_code == 200
    assert len(fake_engine.calls) == calls


async def test_a_removed_chapter_stays_out_when_the_title_changes(client, headers, monkeypatch, fake_engine):
    book = await to_review(client, headers, fake_engine)
    gone = book["chapters"][0]["id"]
    assert (await client.delete(f"/interview/book/chapters/{gone}", headers=headers)).status_code == 200

    seen = {}

    async def finish_book(claude, *, turns, draft, title, **_):
        seen["pool"] = [chapter.id for chapter in draft.pool]
        return FinishedBook(chapters=draft.pool[:3], blurb="Fresh.")

    monkeypatch.setattr(engine, "finish_book", finish_book)
    await client.post("/interview/book/title", json={"title": 2}, headers=headers)
    assert gone not in seen["pool"]


async def test_title_and_blurb_routes_only_in_review(client, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    assert (await client.post("/interview/book/blurb", headers=headers)).status_code == 409
    assert (await client.post("/interview/book/title", json={"title": 1}, headers=headers)).status_code == 409


async def test_rewrite_the_back_cover(client, database, headers, fake_engine):
    book = await to_review(client, headers, fake_engine)
    response = await client.post("/interview/book/blurb", headers=headers)
    assert response.status_code == 200
    assert response.json()["blurb"] == "I know " + ", ".join(c["id"] for c in book["chapters"]) + "."

    fake_engine.fail_blurb = True
    failed = await client.post("/interview/book/blurb", headers=headers)
    assert failed.status_code == 502
    assert (await client.get("/books/me", headers=headers)).json()["blurb"] == response.json()["blurb"]


async def test_a_rewrite_can_be_taken_back_until_the_shelf(client, database, headers, fake_engine):
    book = await to_review(client, headers, fake_engine)
    first = book["chapters"][0]
    assert first["has_previous"] is False

    restored_none = await client.post(f"/interview/book/chapters/{first['id']}/restore", headers=headers)
    assert restored_none.status_code == 409

    rewritten = (await client.post(f"/interview/book/chapters/{first['id']}/rewrite", headers=headers)).json()
    assert rewritten["chapters"][0]["title"] == "Rewritten"
    assert rewritten["chapters"][0]["has_previous"] is True

    back = (await client.post(f"/interview/book/chapters/{first['id']}/restore", headers=headers)).json()
    assert back["chapters"][0]["title"] == first["title"]
    assert back["chapters"][0]["summary"] == first["summary"]
    assert back["chapters"][0]["has_previous"] is False

    await client.post(f"/interview/book/chapters/{first['id']}/rewrite", headers=headers)
    await client.post("/interview/book/shelve", headers=headers)
    saved = await database.books.find_one({})
    assert all("previous" not in chapter for chapter in saved["chapters"])


async def test_a_rewrite_that_changes_nothing_says_so(client, headers, monkeypatch, fake_engine):
    book = await to_review(client, headers, fake_engine)
    first = book["chapters"][0]

    async def same(claude, *, turns, chapters, chapter_id, **_):
        return next(c for c in chapters if c.id == chapter_id)

    monkeypatch.setattr(engine, "rewrite_chapter", same)
    response = (await client.post(f"/interview/book/chapters/{first['id']}/rewrite", headers=headers)).json()
    assert response["rewrite_unchanged"] is True
    assert response["chapters"][0]["title"] == first["title"]
    assert response["chapters"][0]["has_previous"] is False


async def too_little(claude, *, turns, **_):
    raise engine.NotEnoughMaterial("Too few.")


async def test_said_enough_with_too_little_stays_on_the_question(client, headers, monkeypatch, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    state = await answer_questions(client, headers, service.EXIT_AFTER_ANSWERS)
    monkeypatch.setattr(engine, "draft_book", too_little)

    response = await client.post("/interview/finish", headers=headers)
    assert response.status_code == 200
    after = response.json()
    assert after["stage"] == "interviewing"
    assert after["question"] == state["question"]
    assert after["needs_more"] is True
    assert after["at_limit"] is False
    assert after["can_finish"] is False
    # No retry that can't succeed.
    assert (await client.post("/interview/finish", headers=headers)).status_code == 409

    for _ in range(service.MORE_ANSWERS_BEFORE_REDRAFT):
        after = (await send_answer(client, headers, "More.")).json()
    assert after["needs_more"] is False
    assert after["can_finish"] is True


async def test_a_librarian_finish_with_too_little_asks_on_new_ground(
    client, database, headers, monkeypatch, fake_engine
):
    await client.post("/interview", json={}, headers=headers)
    await answer_questions(client, headers, service.EXIT_AFTER_ANSWERS)
    await database.interviews.update_one({}, {"$set": {"current": None, "ready_for_reveal": True}})
    monkeypatch.setattr(engine, "draft_book", too_little)

    calls = len(fake_engine.calls)
    state = (await client.post("/interview/finish", headers=headers)).json()
    assert state["stage"] == "interviewing"
    assert state["question"] is not None
    assert state["ready_for_reveal"] is False
    assert state["needs_more"] is True
    assert fake_engine.calls[calls][0] == "next_turn"


async def test_too_little_at_the_turn_limit_lets_the_member_decide(
    client, database, headers, monkeypatch, fake_engine
):
    await client.post("/interview", json={}, headers=headers)
    many = [{"question": "Q?", "answer": "Short answer.", "phase": "dig"}] * engine.MAX_TURNS
    await database.interviews.update_one(
        {}, {"$set": {"turns": many, "current": None, "ready_for_reveal": True}}
    )
    monkeypatch.setattr(engine, "draft_book", too_little)
    calls = len(fake_engine.calls)
    state = (await client.post("/interview/finish", headers=headers)).json()
    assert state["at_limit"] is True
    assert state["question"] is None
    assert state["can_finish"] is False
    assert len(fake_engine.calls) == calls

    # "Keep answering".
    state = (await client.post("/interview/question", headers=headers)).json()
    assert state["question"] is not None
    assert state["at_limit"] is False
    assert (await database.interviews.find_one({}))["turns"] == many


async def test_a_resent_answer_doesnt_land_on_the_next_question(client, database, headers, fake_engine):
    first = (await client.post("/interview", json={}, headers=headers)).json()["question"]
    body = {"answer": "My real answer.", "question_id": first["question_id"]}
    next_up = (await client.post("/interview/answers", json=body, headers=headers)).json()["question"]
    assert next_up["question_id"] != first["question_id"]

    # The response above was lost, so the client sends it again.
    again = await client.post("/interview/answers", json=body, headers=headers)
    assert again.status_code == 409
    assert again.json()["interview"]["question"]["question_id"] == next_up["question_id"]
    assert again.json()["detail"]
    saved = await database.interviews.find_one({})
    assert [turn["answer"] for turn in saved["turns"]] == ["My real answer."]
    assert saved["current"]["question_id"] == next_up["question_id"]


async def test_a_stale_skip_saves_nothing(client, database, headers, fake_engine):
    first = (await client.post("/interview", json={}, headers=headers)).json()["question"]
    await send_answer(client, headers, "An answer.")
    stale = await client.post("/interview/skip", json={"question_id": first["question_id"]}, headers=headers)
    assert stale.status_code == 409
    saved = await database.interviews.find_one({})
    assert len(saved["turns"]) == 1


async def test_answers_and_skips_must_name_the_question(client, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    assert (
        await client.post("/interview/answers", json={"answer": "Hi."}, headers=headers)
    ).status_code == 422
    assert (await client.post("/interview/skip", json={}, headers=headers)).status_code == 422


async def test_a_stale_finish_with_an_answer_saves_nothing(client, database, headers, fake_engine):
    await client.post("/interview", json={}, headers=headers)
    await answer_questions(client, headers, service.EXIT_AFTER_ANSWERS)
    before = len((await database.interviews.find_one({}))["turns"])
    stale = await client.post(
        "/interview/finish", json={"answer": "Too late.", "question_id": "old"}, headers=headers
    )
    assert stale.status_code == 409
    assert stale.json()["interview"]["stage"] == "interviewing"
    assert len((await database.interviews.find_one({}))["turns"]) == before
