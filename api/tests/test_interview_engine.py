import json

import pytest

from tests.fakes import FakeClaude, text_message
from trove.ai.client import ClaudeRefused
from trove.interview import engine
from trove.interview.engine import Draft, DraftChapter, TitleOption, Turn

ANSWERS = [
    "Honestly the texture was the whole problem. Every recipe online used guar gum and it felt slimy.",
    "I ferment the soy milk for eighteen hours, then strain it overnight, and that's what makes it thick.",
    "The first store said yes because I walked in with cold samples at four on a Friday.",
    "I do the business stuff on Sunday mornings and the lab gets everything else.",
]


def turns(count: int = 4, phase: str = "dig") -> list[Turn]:
    return [
        Turn(question=f"Question {n}?", answer=ANSWERS[n % len(ANSWERS)], phase=phase) for n in range(count)
    ]


def sent(claude: FakeClaude) -> str:
    content = claude.requests[-1]["messages"][0]["content"]
    return content if isinstance(content, str) else "".join(block["text"] for block in content)


def reply(data: dict):
    return text_message(json.dumps(data))


def plan(**overrides) -> dict:
    return {
        "threads": [{"thread": "texture without gums", "missing": "the exact steps"}],
        "phase": "dig",
        "question": "What did the first batch that worked look like?",
        "playback": None,
        "topic": "the batch that finally worked",
        "ready_for_reveal": False,
    } | overrides


def chapter(quote: str, title: str = "Thick without gums") -> dict:
    return {"title": title, "summary": "How to get texture from fermentation alone.", "quotes": [quote]}


TITLES = [{"title": f"Title {n}", "why": "You kept coming back to it."} for n in range(3)]


async def test_next_turn_sends_the_transcript_with_structured_output_and_adaptive_thinking():
    claude = FakeClaude([reply(plan())])
    result = await engine.next_turn(claude, turns=turns(3), resume_text="Chemical engineering, BS 2018")

    assert result.question == "What did the first batch that worked look like?"
    assert result.topic == "the batch that finally worked"
    request = claude.requests[0]
    assert request["model"] == "claude-opus-5-5"
    assert request["thinking"] == {"type": "adaptive"}
    assert request["output_config"]["format"]["type"] == "json_schema"
    assert "Librarian" in request["system"]
    blocks = request["messages"][0]["content"]
    assert blocks[0]["text"] == "<resume>\nChemical engineering, BS 2018\n</resume>\n"
    assert f"A1: {ANSWERS[0]}" in blocks[2]["text"]
    # The breakpoint sits on the newest turn, not on the status line that changes every request.
    assert [i for i, b in enumerate(blocks) if "cache_control" in b] == [len(blocks) - 2]


async def test_the_first_question_is_always_sweep_and_has_no_resume_block_without_a_resume():
    claude = FakeClaude([reply(plan(phase="dig"))])
    result = await engine.next_turn(claude, turns=[], resume_text=None)
    assert result.phase == "sweep"
    assert "<resume>" not in sent(claude)


async def test_the_reveal_is_never_offered_too_early():
    claude = FakeClaude([reply(plan(phase="shape", ready_for_reveal=True))])
    result = await engine.next_turn(claude, turns=turns(engine.MIN_ANSWERS - 1), resume_text=None)
    assert result.ready_for_reveal is False


async def test_skipped_answers_dont_count_toward_the_reveal():
    skipped = [Turn(question="Q?", answer="  ", phase="sweep") for _ in range(engine.MIN_ANSWERS)]
    claude = FakeClaude([reply(plan(ready_for_reveal=True))])
    result = await engine.next_turn(claude, turns=skipped, resume_text=None)
    assert result.ready_for_reveal is False
    assert "(skipped)" in sent(claude)


async def test_the_reveal_is_forced_at_the_question_limit():
    claude = FakeClaude([reply(plan(phase="shape", ready_for_reveal=False))])
    result = await engine.next_turn(claude, turns=turns(engine.MAX_QUESTIONS), resume_text=None)
    assert result.ready_for_reveal is True
    assert "limit" in sent(claude)


async def test_playback_is_kept_only_in_shape():
    claude = FakeClaude(
        [reply(plan(phase="dig", playback="stray")), reply(plan(phase="shape", playback="You make lassi."))]
    )
    assert (await engine.next_turn(claude, turns=turns(), resume_text=None)).playback is None
    assert (await engine.next_turn(claude, turns=turns(), resume_text=None)).playback == "You make lassi."


async def test_refusals_propagate():
    claude = FakeClaude([text_message("", stop_reason="refusal")])
    with pytest.raises(ClaudeRefused):
        await engine.next_turn(claude, turns=turns(), resume_text=None)


async def test_draft_keeps_only_verbatim_quotes_and_assigns_ids():
    pool = [
        chapter("it felt slimy", "Why gums feel wrong"),
        # Curly apostrophe and extra spacing still match the member's words.
        chapter("strain it overnight,  and that\u2019s what makes it thick", "Eighteen hours"),
        chapter("walked in with cold samples", "The Friday sample"),
        chapter("I invented this sentence", "Made up"),
    ]
    claude = FakeClaude([reply({"pool": pool, "titles": TITLES})])
    draft = await engine.draft_book(claude, turns=turns())

    assert [c.title for c in draft.pool] == ["Why gums feel wrong", "Eighteen hours", "The Friday sample"]
    assert len({c.id for c in draft.pool}) == 3
    assert len(draft.titles) == 3


async def test_draft_retries_once_when_too_little_is_grounded_then_gives_up():
    ungrounded = reply({"pool": [chapter("not something they said")], "titles": TITLES})
    claude = FakeClaude([ungrounded, ungrounded])
    with pytest.raises(ValueError):
        await engine.draft_book(claude, turns=turns())
    assert len(claude.requests) == 2


def a_draft() -> Draft:
    return Draft(
        pool=[
            DraftChapter(id=f"c{n}", title=f"Pool {n}", summary="S.", quotes=[ANSWERS[n]]) for n in range(4)
        ],
        titles=[TitleOption(**t) for t in TITLES],
    )


async def test_finish_uses_pool_ids_and_quotes_and_ignores_unknown_or_repeated_ids():
    picked = [
        {"pool_id": "c2", "title": "First", "summary": "Angled."},
        {"pool_id": "nope", "title": "Ghost", "summary": "?"},
        {"pool_id": "c0", "title": "Second", "summary": "Angled."},
        {"pool_id": "c2", "title": "Again", "summary": "?"},
        {"pool_id": "c1", "title": "Third", "summary": "Angled."},
    ]
    claude = FakeClaude([reply({"chapters": picked})])
    chapters = await engine.finish_book(claude, turns=turns(), draft=a_draft(), title="Title 1")

    assert [(c.id, c.title) for c in chapters] == [("c2", "First"), ("c0", "Second"), ("c1", "Third")]
    assert chapters[0].quotes == [ANSWERS[2]]
    assert "<chosen_title>Title 1</chosen_title>" in claude.requests[0]["messages"][0]["content"]


async def test_finish_tops_up_a_short_pick_from_the_pool():
    claude = FakeClaude([reply({"chapters": [{"pool_id": "c3", "title": "Only", "summary": "S."}]})])
    chapters = await engine.finish_book(claude, turns=turns(), draft=a_draft(), title="Title 0")
    assert [c.id for c in chapters] == ["c3", "c0", "c1"]


async def test_rewrite_keeps_the_id_and_grounds_the_quotes():
    book = a_draft().pool[:3]
    claude = FakeClaude([reply(chapter("Sunday mornings", "Sundays for the business"))])
    rewritten = await engine.rewrite_chapter(claude, turns=turns(), chapters=book, chapter_id="c1")

    assert rewritten.id == "c1"
    assert rewritten.title == "Sundays for the business"
    assert rewritten.quotes == ["Sunday mornings"]
    sent = claude.requests[0]["messages"][0]["content"]
    assert '"rewrite_this": true' in sent


async def test_rewrite_rejects_an_unknown_chapter_without_calling_claude():
    claude = FakeClaude()
    with pytest.raises(ValueError):
        await engine.rewrite_chapter(claude, turns=turns(), chapters=a_draft().pool, chapter_id="missing")
    assert claude.requests == []


def test_prompts_state_the_grounding_rule():
    from trove.ai.prompts import load_prompt

    for name in ("draft", "finish", "rewrite"):
        assert "Grounding" in load_prompt(f"interview/{name}")
