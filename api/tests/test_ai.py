import pytest

from tests.fakes import FakeClaude, text_message
from trove.ai.client import Claude, ClaudeRefused, text_of
from trove.ai.prompts import load_prompt


def test_fallbacks_are_added_only_for_models_that_support_them():
    assert Claude("key", "claude-opus-5-5").request({"max_tokens": 10})["fallbacks"] == "default"
    assert "fallbacks" not in Claude("key", "claude-haiku-5-5").request({"max_tokens": 10})


async def test_refusals_raise_instead_of_returning():
    claude = FakeClaude([text_message("", stop_reason="refusal")])
    with pytest.raises(ClaudeRefused):
        await claude.create(max_tokens=10, messages=[])


async def test_text_of_joins_text_blocks():
    claude = FakeClaude([text_message("Hello")])
    assert text_of(await claude.create(max_tokens=10, messages=[])) == "Hello"
    assert claude.requests[0]["model"] == "claude-opus-5-5"


def test_prompt_names_cannot_escape_the_prompts_folder():
    with pytest.raises(ValueError):
        load_prompt("../client")
