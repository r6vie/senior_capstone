"""Fixes from the code review of josef/full-build, one test or more each."""

import json

from fastapi import HTTPException

from tests.fakes import send_skip, text_message
from tests.test_growing_books import (
    NEW_ANSWER,
    PART_ONE,
    PART_TWO,
    PLAIN,
    change,
    member,
    propose,
    shelve_book,
    start_round,
    waiting_question,
)
from trove.ai import usage
from trove.ai.client import get_claude
from trove.ai.prompts import load_prompt
from trove.interview import engine, service
from trove.main import app


async def test_a_round_skipped_to_its_limit_closes_with_nothing_new(client, database, fake_claude):
    person = await member(client, "skipper@case.edu")
    await shelve_book(database, person["id"])
    await start_round(client, person, fake_claude)
    skipped = [
        {"question": f"Q{n}?", "answer": "", "phase": "adding"} for n in range(engine.MAX_ADDING_TURNS - 1)
    ]
    await database.interviews.update_one({"user_id": person["id"]}, {"$push": {"turns": {"$each": skipped}}})
    calls = len(fake_claude.requests)

    state = (await send_skip(client, person["headers"])).json()
    assert state["stage"] == "done"
    assert state["nothing_new"] is True
    assert len(fake_claude.requests) == calls
    # The member can start another round later.
    fake_claude.responses.append(
        text_message(json.dumps({"question": "Again?", "topic": "t", "done": False}))
    )
    assert (await client.post("/interview/reopen", headers=person["headers"])).json()["stage"] == "adding"


async def test_declining_everything_doesnt_offer_an_older_undo(client, database, fake_claude):
    person = await member(client, "decliner@case.edu")
    await shelve_book(database, person["id"])
    state = await propose(client, person, fake_claude, change(quotes=[PART_ONE]))
    applied = await client.post(
        "/interview/revision", json={"approved": [state["changes"][0]["id"]]}, headers=person["headers"]
    )
    assert applied.json()["can_undo"] is True

    await propose(client, person, fake_claude, change(title="Another", quotes=[PART_TWO]))
    declined = (
        await client.post("/interview/revision", json={"approved": []}, headers=person["headers"])
    ).json()
    assert declined["can_undo"] is False


def test_a_short_spark_title_only_redacts_whole_words():
    interview = {
        "_id": "i",
        "turns": [
            {"question": "You saved Time. Do you sometimes lose track of time?", "answer": "", "phase": "dig"}
        ],
        "asked_spark_titles": ["Time"],
    }
    question = service.book_turns(interview)[0].question
    assert question == "You saved that topic. Do you sometimes lose track of that topic?"


def no_ai():
    raise HTTPException(status_code=503, detail="AI isn't set up.")


async def test_decisions_and_saved_answers_need_no_ai(client, database, fake_claude):
    person = await member(client, "noai@case.edu")
    await shelve_book(database, person["id"])
    state = await propose(client, person, fake_claude, change())
    question = await waiting_question(client, database, person)
    app.dependency_overrides[get_claude] = no_ai
    try:
        # A reading answer while changes wait only saves the answer.
        saved = await client.post(
            f"/interview/reading-questions/{question}/answer",
            json={"answer": PLAIN},
            headers=person["headers"],
        )
        assert saved.status_code == 200
        # The decision is applied, and the reading answer's write waits for AI, marked failed.
        decided = await client.post(
            "/interview/revision", json={"approved": [state["changes"][0]["id"]]}, headers=person["headers"]
        )
        assert decided.status_code == 200
        later = await database.interviews.find_one({"user_id": person["id"]})
        assert later["stage"] == "revising"
        assert later["write_status"] == "failed"
    finally:
        app.dependency_overrides[get_claude] = lambda: fake_claude


async def test_a_reading_answer_that_needs_ai_says_so_and_saves_nothing(client, database, fake_claude):
    person = await member(client, "noai2@case.edu")
    await shelve_book(database, person["id"])
    question = await waiting_question(client, database, person)
    app.dependency_overrides[get_claude] = no_ai
    try:
        response = await client.post(
            f"/interview/reading-questions/{question}/answer",
            json={"answer": NEW_ANSWER},
            headers=person["headers"],
        )
    finally:
        app.dependency_overrides[get_claude] = lambda: fake_claude
    assert response.status_code == 503
    still = (await client.get("/interview/reading-questions", headers=person["headers"])).json()
    assert [item["id"] for item in still] == [question]
    saved = await database.interviews.find_one({"user_id": person["id"]})
    assert NEW_ANSWER not in [turn["answer"] for turn in saved["turns"]]


async def test_cancelling_a_removal_needs_no_ai(client, database, fake_claude):
    person = await member(client, "cancel-noai@case.edu")
    many = [{"id": f"c{n}", "title": f"T{n}", "summary": "S.", "quotes": ["q"]} for n in range(4)]
    await shelve_book(database, person["id"], many)
    await client.post("/interview/removal", json={"chapter_id": "c1"}, headers=person["headers"])
    app.dependency_overrides[get_claude] = no_ai
    try:
        response = await client.post("/interview/removal/cancel", headers=person["headers"])
    finally:
        app.dependency_overrides[get_claude] = lambda: fake_claude
    assert response.status_code == 200
    assert response.json()["stage"] == "done"


def test_the_ledger_total_skips_a_half_written_line_and_reads_only_whats_new(tmp_path):
    ledger = tmp_path / "usage.jsonl"
    ledger.write_text(json.dumps({"cost_usd": 1.0}) + "\n" + '{"cost_usd": 0.5', encoding="utf-8")
    assert usage.total_spent(ledger) == 1.0
    with ledger.open("a", encoding="utf-8") as file:
        file.write("}\n" + json.dumps({"cost_usd": 0.25}) + "\n")
    assert usage.total_spent(ledger) == 1.75
    # A line that's broken for good is skipped, not fatal.
    with ledger.open("a", encoding="utf-8") as file:
        file.write("not json\n")
    assert usage.total_spent(ledger) == 1.75
    ledger.write_text(json.dumps({"cost_usd": 0.1}) + "\n", encoding="utf-8")
    assert usage.total_spent(ledger) == 0.1


def test_the_retry_nudges_are_prompt_files():
    assert str(engine.MAX_PLAYBACK_WORDS) in load_prompt("interview/retry_playback")
    assert "too close to the original" in load_prompt("interview/retry_rewrite")
    with open(engine.__file__, encoding="utf-8") as file:
        source = file.read()
    assert "Write it again, shorter" not in source
    assert "Tell it differently" not in source
