import json
from types import SimpleNamespace

import pytest

from tests.fakes import text_message
from trove.ai import usage
from trove.ai.client import Claude, ClaudeRefused
from trove.ai.prompts import load_prompt
from trove.core.config import get_settings
from trove.interview import service


class StubMessages:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    async def create(self, **_params):
        self.calls += 1
        return self.response


def client_returning(response, model="claude-opus-5-5") -> tuple[Claude, StubMessages]:
    """The real client class, with the network part replaced."""
    claude = Claude("not-a-real-key", model)
    messages = StubMessages(response)
    claude.client = SimpleNamespace(beta=SimpleNamespace(messages=messages))
    return claude, messages


def priced(usage_fields: dict, stop_reason="end_turn"):
    response = text_message("{}", stop_reason)
    response.usage = response.usage.model_copy(update=usage_fields)
    return response


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    path = tmp_path / "team" / "usage.jsonl"
    monkeypatch.setattr(get_settings(), "ai_usage_log", str(path))
    monkeypatch.setattr(get_settings(), "ai_budget_usd", 1.0)
    return path


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        # 1M of each: input, output, cache read, cache write.
        ("claude-opus-5-5", 4 + 20 + 0.20 + 5),
        ("claude-sonnet-5-5", 2 + 10 + 0.20 + 2.5),
        ("no-such-model", 10 + 50 + 1 + 12.5),
    ],
)
def test_prices(model, expected):
    tokens = SimpleNamespace(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_read_input_tokens=1_000_000,
        cache_creation_input_tokens=1_000_000,
    )
    assert usage.cost_of(model, tokens) == pytest.approx(expected)


def test_haiku_costs_more_past_100k_tokens():
    short = SimpleNamespace(
        input_tokens=100_000, output_tokens=0, cache_read_input_tokens=0, cache_creation_input_tokens=0
    )
    long = SimpleNamespace(
        input_tokens=100_001, output_tokens=0, cache_read_input_tokens=0, cache_creation_input_tokens=0
    )
    assert usage.cost_of("claude-haiku-5-5", short) == pytest.approx(0.01)
    assert usage.cost_of("claude-haiku-5-5", long) == pytest.approx(0.0500005)


async def test_each_real_call_adds_one_line_to_the_ledger(ledger):
    response = priced(
        {
            "input_tokens": 1000,
            "output_tokens": 500,
            "cache_read_input_tokens": 2000,
            "cache_creation_input_tokens": 100,
        }
    )
    claude, _ = client_returning(response)
    await claude.create(system=load_prompt("interview/draft"), max_tokens=10, messages=[])
    await claude.create(system="Not a prompt file.", max_tokens=10, messages=[])

    lines = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert len(lines) == 2
    first = lines[0]
    assert first["model"] == "claude-opus-5-5"
    assert first["prompt"] == "interview/draft"
    assert first["input_tokens"] == 1000
    assert first["output_tokens"] == 500
    assert first["cache_read_tokens"] == 2000
    assert first["cache_write_tokens"] == 100
    assert first["cost_usd"] == pytest.approx((1000 * 4 + 500 * 20 + 2000 * 0.2 + 100 * 5) / 1e6)
    assert first["time"]
    assert lines[1]["prompt"] is None


async def test_a_refusal_is_still_recorded(ledger):
    claude, _ = client_returning(priced({"input_tokens": 1000}, stop_reason="refusal"))
    with pytest.raises(ClaudeRefused):
        await claude.create(system="x", max_tokens=10, messages=[])
    assert len(ledger.read_text().splitlines()) == 1


async def test_calls_stop_before_spending_once_the_budget_is_reached(ledger):
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps({"cost_usd": 0.6}) + "\n" + json.dumps({"cost_usd": 0.4}) + "\n")
    claude, messages = client_returning(priced({"input_tokens": 1}))
    with pytest.raises(usage.BudgetExceeded):
        await claude.create(system="x", max_tokens=10, messages=[])
    assert messages.calls == 0


async def test_under_the_budget_calls_go_through(ledger):
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps({"cost_usd": 0.99}) + "\n")
    claude, messages = client_returning(priced({"input_tokens": 1}))
    await claude.create(system="x", max_tokens=10, messages=[])
    assert messages.calls == 1


async def test_without_a_ledger_nothing_is_written_or_limited(tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "ai_budget_usd", 0.0)
    claude, messages = client_returning(priced({"input_tokens": 1}))
    await claude.create(system="x", max_tokens=10, messages=[])
    assert messages.calls == 1
    assert list(tmp_path.iterdir()) == []


async def test_the_interview_turns_an_exhausted_budget_into_its_usual_502():
    async def over_budget():
        raise usage.BudgetExceeded("Spent it.")

    with pytest.raises(Exception) as caught:
        await service.ask_engine(over_budget())
    assert caught.value.status_code == 502


def test_report_shows_the_total_and_a_breakdown():
    entries = [
        {"model": "claude-opus-5-5", "prompt": "interview/draft", "cost_usd": 1.5},
        {"model": "claude-opus-5-5", "prompt": "interview/interviewer", "cost_usd": 0.25},
        {"model": "claude-haiku-5-5", "prompt": None, "cost_usd": 0.25},
    ]
    text = usage.report(entries, 15.0)
    assert "Total: $2.0000 of $15.00" in text
    assert "Calls: 3" in text
    assert "claude-opus-5-5" in text
    assert "interview/draft" in text
    assert "(unknown)" in text
