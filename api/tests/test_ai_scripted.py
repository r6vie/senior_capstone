import json
from types import SimpleNamespace

import pytest

from trove.ai import scripted
from trove.ai.client import get_claude, text_of
from trove.ai.prompts import load_prompt
from trove.ai.scripted import ScriptedClaude, ensure_scripted_allowed
from trove.core.config import get_settings
from trove.main import app

SIGNUP = {"email": "theo@case.edu", "password": "a-long-password", "first_name": "Theo", "last_name": "Park"}


@pytest.fixture
def scripted_ai():
    app.dependency_overrides[get_claude] = lambda: ScriptedClaude()
    yield
    app.dependency_overrides.pop(get_claude, None)


@pytest.fixture
async def headers(client):
    await client.post("/auth/signup", json=SIGNUP)
    login = await client.post("/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def walk_to_shape(client, headers, answers: list[str]) -> dict:
    state = (await client.post("/interview", json={}, headers=headers)).json()
    for answer in answers:
        response = await client.post("/interview/answers", json={"answer": answer}, headers=headers)
        assert response.status_code == 200, response.text
        state = response.json()
    return state


async def test_a_whole_interview_walks_through_on_the_scripted_ai(client, database, headers, scripted_ai):
    state = await walk_to_shape(client, headers, scripted.THEO_ANSWERS)
    assert state["question"]["phase"] == "shape"
    assert "fry stand" in state["question"]["playback"]

    state = (await client.post("/interview/shape", json={}, headers=headers)).json()
    assert state["ready_for_reveal"] is True

    state = (await client.post("/interview/finish", headers=headers)).json()
    assert state["stage"] == "choosing"
    assert state["titles"][0]["title"] == "Check the Slats First"

    book = (await client.post("/interview/title", json={"title": 0}, headers=headers)).json()
    assert 3 <= len(book["chapters"]) <= 5
    said = " ".join(scripted.THEO_ANSWERS).casefold()
    for chapter in book["chapters"]:
        assert chapter["quotes"]
        assert all(quote.casefold() in said for quote in chapter["quotes"])

    first = book["chapters"][0]
    rewritten = await client.post(f"/interview/book/chapters/{first['id']}/rewrite", headers=headers)
    assert rewritten.json()["chapters"][0]["title"] != first["title"]
    again = await client.post(f"/interview/book/chapters/{first['id']}/rewrite", headers=headers)
    assert again.json()["chapters"][0]["title"] == first["title"]

    removed = await client.delete(f"/interview/book/chapters/{first['id']}", headers=headers)
    assert all(chapter["id"] != first["id"] for chapter in removed.json()["chapters"])

    shelved = (await client.post("/interview/book/shelve", headers=headers)).json()
    assert shelved["status"] == "on_shelf"


async def test_anything_typed_still_makes_a_grounded_book(client, headers, scripted_ai):
    answers = [
        f"I spent year {n} fixing the thing nobody else wanted to touch. More detail." for n in range(12)
    ]
    state = await walk_to_shape(client, headers, answers)
    assert state["question"]["phase"] == "shape"
    assert "fixing the thing" in state["question"]["playback"]
    await client.post("/interview/shape", json={}, headers=headers)
    await client.post("/interview/finish", headers=headers)
    book = (await client.post("/interview/title", json={"title": 1}, headers=headers)).json()
    for chapter in book["chapters"]:
        assert chapter["quotes"]
        assert all("fixing the thing" in quote for quote in chapter["quotes"])


async def test_thin_answers_get_a_new_angle_and_questions_never_repeat(client, headers, scripted_ai):
    state = await walk_to_shape(client, headers, ["Not sure.", "Honestly, no idea."])
    assert state["question"]["text"] == scripted.THIN_ANGLES[0].question

    seen = []
    for _ in range(8):
        seen.append(state["question"]["text"])
        state = (await client.post("/interview/answers", json={"answer": "Dunno."}, headers=headers)).json()
    assert len(seen) == len(set(seen))


async def test_a_skipped_question_never_comes_back(client, headers, scripted_ai):
    state = (await client.post("/interview", json={}, headers=headers)).json()
    seen = [state["question"]["text"]]
    for _ in range(10):
        state = (await client.post("/interview/skip", headers=headers)).json()
        seen.append(state["question"]["text"])
    assert len(seen) == len(set(seen))


async def test_the_interview_has_sweep_then_dig(client, headers, scripted_ai):
    answers = scripted.THEO_ANSWERS[:7]
    state = (await client.post("/interview", json={}, headers=headers)).json()
    phases = [state["question"]["phase"]]
    for answer in answers:
        state = (await client.post("/interview/answers", json={"answer": answer}, headers=headers)).json()
        phases.append(state["question"]["phase"])
    assert phases[:5] == ["sweep"] * 5
    assert set(phases[5:]) == {"dig"}


async def test_an_unknown_prompt_is_an_error_not_a_guess():
    with pytest.raises(ValueError):
        await ScriptedClaude().create(system="Who knows.", messages=[{"role": "user", "content": "Hi"}])


async def test_it_picks_the_reply_by_system_prompt():
    response = await ScriptedClaude().create(
        system=load_prompt("interview/blurb"), messages=[{"role": "user", "content": "Write it."}]
    )
    assert json.loads(text_of(response))["blurb"] == scripted.REMOVED_BLURB


def allowed(**changes):
    settings = {
        "ai_mode": "scripted",
        "environment": "development",
        "frontend_url": "http://127.0.0.1:5273",
        "api_url": "http://localhost:8100",
        "mongodb_database": "trove_dev_qc",
    }
    return SimpleNamespace(**{**settings, **changes})


def test_a_local_dev_setup_may_use_it():
    ensure_scripted_allowed(allowed())


@pytest.mark.parametrize(
    "changes",
    [
        {"environment": "production"},
        {"frontend_url": "https://trove.example.com"},
        {"api_url": "https://api.trove.example.com"},
        {"mongodb_database": "trove"},
    ],
)
def test_it_refuses_to_run_outside_dev(changes):
    with pytest.raises(RuntimeError):
        ensure_scripted_allowed(allowed(**changes))


def test_real_mode_is_never_blocked():
    ensure_scripted_allowed(allowed(ai_mode="real", environment="production"))


def test_get_claude_returns_the_stand_in_with_no_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "ai_mode", "scripted")
    monkeypatch.setattr(get_settings(), "anthropic_api_key", "")
    monkeypatch.setattr(get_settings(), "environment", "development")
    monkeypatch.setattr(get_settings(), "frontend_url", "http://127.0.0.1:5173")
    monkeypatch.setattr(get_settings(), "api_url", "http://127.0.0.1:8000")
    monkeypatch.setattr(get_settings(), "mongodb_database", "trove_dev_qc")
    assert isinstance(get_claude(), ScriptedClaude)


def test_get_claude_refuses_outside_dev(monkeypatch):
    monkeypatch.setattr(get_settings(), "ai_mode", "scripted")
    monkeypatch.setattr(get_settings(), "environment", "production")
    with pytest.raises(RuntimeError):
        get_claude()
