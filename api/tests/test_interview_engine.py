import json

import pytest

from tests.fakes import FakeClaude, text_message
from trove.ai.client import ClaudeRefused
from trove.ai.prompts import load_prompt
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
        "threads": [{"thread": "texture without gums", "has_moment": True, "missing": "the exact steps"}],
        "phase": "dig",
        "question": "What did the first batch that worked look like?",
        "playback": None,
        "topic": "the batch that finally worked",
        "ready_for_reveal": False,
    } | overrides


def chapter(quote: str, title: str = "Thick without gums") -> dict:
    return {"title": title, "summary": "How to get texture from fermentation alone.", "quotes": [quote]}


TITLES = [{"title": f"Title {n}", "why": "You kept coming back to it."} for n in range(3)]
BLURB = "I make lassi thick with nothing but time. I learned it the slow way, one split batch at a time."


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
        chapter("used guar gum and it felt slimy", "Why gums feel wrong"),
        # Curly apostrophe and extra spacing still match the member's words.
        chapter("strain it overnight,  and that\u2019s what makes it thick", "Eighteen hours"),
        chapter("walked in with cold samples", "The Friday sample"),
        chapter("I invented this sentence", "Made up"),
    ]
    claude = FakeClaude([reply({"pool": pool, "titles": TITLES, "blurb": BLURB})])
    draft = await engine.draft_book(claude, turns=turns())

    assert [c.title for c in draft.pool] == ["Why gums feel wrong", "Eighteen hours", "The Friday sample"]
    assert len({c.id for c in draft.pool}) == 3
    assert len(draft.titles) == 3
    assert draft.blurb == BLURB


async def test_draft_retries_once_when_too_little_is_grounded_then_gives_up():
    ungrounded = reply({"pool": [chapter("not something they said")], "titles": TITLES, "blurb": BLURB})
    claude = FakeClaude([ungrounded, ungrounded])
    with pytest.raises(ValueError):
        await engine.draft_book(claude, turns=turns())
    assert len(claude.requests) == 2


async def test_draft_retries_when_the_blurb_is_too_long():
    pool = [chapter(ANSWERS[n][:40]) for n in range(3)]
    too_long = reply({"pool": pool, "titles": TITLES, "blurb": "I " + "know " * 200})
    claude = FakeClaude([too_long, reply({"pool": pool, "titles": TITLES, "blurb": f"  {BLURB} "})])
    draft = await engine.draft_book(claude, turns=turns())
    assert draft.blurb == BLURB
    assert len(claude.requests) == 2


def a_draft() -> Draft:
    return Draft(
        pool=[
            DraftChapter(id=f"c{n}", title=f"Pool {n}", summary="S.", quotes=[ANSWERS[n]]) for n in range(4)
        ],
        titles=[TitleOption(**t) for t in TITLES],
        blurb="I know the pool.",
    )


async def test_finish_uses_pool_ids_and_quotes_and_ignores_unknown_or_repeated_ids():
    picked = [
        {"pool_id": "c2", "title": "First", "summary": "Angled."},
        {"pool_id": "nope", "title": "Ghost", "summary": "?"},
        {"pool_id": "c0", "title": "Second", "summary": "Angled."},
        {"pool_id": "c2", "title": "Again", "summary": "?"},
        {"pool_id": "c1", "title": "Third", "summary": "Angled."},
    ]
    claude = FakeClaude([reply({"chapters": picked, "blurb": BLURB})])
    finished = await engine.finish_book(claude, turns=turns(), draft=a_draft(), title="Title 1")
    chapters = finished.chapters

    assert [(c.id, c.title) for c in chapters] == [("c2", "First"), ("c0", "Second"), ("c1", "Third")]
    assert chapters[0].quotes == [ANSWERS[2]]
    assert "<chosen_title>Title 1</chosen_title>" in claude.requests[0]["messages"][0]["content"]
    assert finished.blurb == BLURB


async def test_finish_tops_up_a_short_pick_from_the_pool():
    picked = [{"pool_id": "c3", "title": "Only", "summary": "S."}]
    claude = FakeClaude([reply({"chapters": picked, "blurb": ""})])
    finished = await engine.finish_book(claude, turns=turns(), draft=a_draft(), title="Title 0")
    assert [c.id for c in finished.chapters] == ["c3", "c0", "c1"]
    # An unusable blurb falls back to the draft's.
    assert finished.blurb == "I know the pool."


async def test_write_blurb_sees_only_the_chapters_left_and_retries_once():
    book = a_draft().pool[:3]
    claude = FakeClaude([reply({"blurb": "x" * 601}), reply({"blurb": BLURB})])
    assert await engine.write_blurb(claude, turns=turns(), chapters=book) == BLURB
    assert "Pool 2" in sent(claude) and "Pool 3" not in sent(claude)
    assert claude.requests[0]["system"] == load_prompt("interview/blurb")

    claude = FakeClaude([reply({"blurb": " "}), reply({"blurb": "I " + "know " * 200 + "a lot."})])
    with pytest.raises(ValueError):
        await engine.write_blurb(claude, turns=turns(), chapters=book)


async def test_rewrite_keeps_the_id_topic_and_quotes_and_changes_only_title_and_summary():
    book = a_draft().pool[:3]
    claude = FakeClaude([reply({"title": "Sundays for the business", "summary": "Retold."})])
    rewritten = await engine.rewrite_chapter(claude, turns=turns(), chapters=book, chapter_id="c1")

    assert rewritten.id == "c1"
    assert (rewritten.title, rewritten.summary) == ("Sundays for the business", "Retold.")
    assert rewritten.quotes == book[1].quotes
    sent = claude.requests[0]["messages"][0]["content"]
    assert '"rewrite_this": true' in sent


async def test_rewrite_rejects_an_unknown_chapter_without_calling_claude():
    claude = FakeClaude()
    with pytest.raises(ValueError):
        await engine.rewrite_chapter(claude, turns=turns(), chapters=a_draft().pool, chapter_id="missing")
    assert claude.requests == []


def test_prompts_state_the_grounding_rule():
    for name in ("draft", "finish", "rewrite", "blurb"):
        assert "Grounding" in load_prompt(f"interview/{name}")


def test_a_long_blurb_is_cut_back_to_whole_sentences():
    sentence = "I learned this one the slow way. "
    assert engine._usable_blurb(sentence * 30) == (sentence * 18).strip()
    assert len((sentence * 18).strip()) <= engine.MAX_BLURB
    assert engine._usable_blurb("I " + "know " * 200 + ". Short.") is None


# When answers run thin (docs/trove.md §4, §9.9).


def answered(*answers: str, phase: str = "dig") -> list[Turn]:
    return [Turn(question=f"Question {n}?", answer=a, phase=phase) for n, a in enumerate(answers)]


async def test_thin_answers_ask_for_a_sharper_angle_but_a_long_unsure_story_does_not():
    claude = FakeClaude([reply(plan())])
    await engine.next_turn(
        claude, turns=answered(ANSWERS[0], "Not really.", "Math, I guess."), resume_text=None
    )
    assert "Answers are running thin" in sent(claude)

    story = "I don't know, I guess it started when the printers broke and nobody would touch them, so I watched videos."
    claude = FakeClaude([reply(plan())])
    await engine.next_turn(claude, turns=answered(story, ANSWERS[1], "Fine."), resume_text=None)
    assert "Answers are running thin" not in sent(claude)


async def test_a_skip_moves_to_other_ground_and_isnt_counted_or_thin():
    skip = Turn(question="What do people get wrong?", answer="", phase="dig")
    claude = FakeClaude([reply(plan())])
    await engine.next_turn(claude, turns=[*turns(4), skip], resume_text=None)
    assert "A5: (skipped)" in sent(claude)
    assert "Move to other ground: don't rephrase it" in sent(claude)
    assert "Questions asked so far: 4." in sent(claude)
    # Skips say "not this", not "I'm unsure", so they never make answers look thin.
    claude = FakeClaude([reply(plan())])
    await engine.next_turn(
        claude,
        turns=[*turns(2), skip, skip, Turn(question="Q?", answer=ANSWERS[2], phase="dig")],
        resume_text=None,
    )
    assert "running thin" not in sent(claude)

    claude = FakeClaude([reply(plan())])
    history = [*turns(engine.MAX_QUESTIONS - 1), *[skip] * 5]
    assert (await engine.next_turn(claude, turns=history, resume_text=None)).ready_for_reveal is False

    claude = FakeClaude([reply(plan())])
    history = [*turns(10), *[skip] * (engine.MAX_TURNS - 10)]
    assert (await engine.next_turn(claude, turns=history, resume_text=None)).ready_for_reveal is True


async def test_the_status_keeps_the_sweep_wide_until_enough_areas_are_covered():
    claude = FakeClaude([reply(plan())])
    await engine.next_turn(claude, turns=turns(2, phase="sweep"), resume_text=None)
    assert "Stay in Sweep" in sent(claude)

    claude = FakeClaude([reply(plan())])
    await engine.next_turn(claude, turns=turns(engine.MIN_SWEEP, phase="sweep"), resume_text=None)
    assert "Stay in Sweep" not in sent(claude)


def test_the_interviewer_bans_small_talk_and_reassurance():
    prompt = load_prompt("interview/interviewer")
    assert "When answers run thin" in prompt
    assert "no reassurance" in prompt and "No small talk" in prompt


async def test_two_grounded_chapters_at_the_cap_is_not_enough_material():
    answers = turns(engine.MAX_QUESTIONS)
    quote = answers[0].answer
    thin = [chapter(quote), chapter(quote, "Another")]
    claude = FakeClaude(
        [
            reply({"pool": thin, "titles": TITLES, "blurb": BLURB}),
            reply({"pool": thin, "titles": TITLES, "blurb": BLURB}),
        ]
    )
    with pytest.raises(engine.NotEnoughMaterial):
        await engine.draft_book(claude, turns=answers)


async def test_more_material_goes_past_the_limits_with_a_status_note():
    claude = FakeClaude([reply(plan(ready_for_reveal=True, phase="shape", playback="You."))])
    result = await engine.next_turn(
        claude, turns=turns(engine.MAX_QUESTIONS), resume_text=None, more_material=True
    )
    assert result.ready_for_reveal is False
    assert result.phase == "dig"
    assert result.playback is None
    assert "can't yet make three distinct chapters" in sent(claude)
    assert "That is the limit" not in sent(claude)


def test_a_quote_needs_five_words():
    said = [engine.Turn(question="Q?", answer="I made it. I made it work on the third try.", phase="dig")]
    assert engine.grounded_quotes(["I made it."], said) == []
    assert engine.grounded_quotes(["I made it work on"], said) == ["I made it work on"]


async def test_rewrite_too_close_tries_once_more_then_keeps_the_original():
    book = [
        DraftChapter(
            id="c0", title="Old", summary="I split the line so the fryer only had to cook.", quotes=["q"]
        ),
    ]
    close = {"title": "New", "summary": "I split the line so the fryer only had to cook!"}
    claude = FakeClaude([reply(close), reply(close)])
    result = await engine.rewrite_chapter(claude, turns=turns(1), chapters=book, chapter_id="c0")
    assert result == book[0]
    assert len(claude.requests) == 2
    assert "too close to the original" in sent(claude)


async def test_rewrite_second_try_can_succeed():
    book = [
        DraftChapter(id="c0", title="Old", summary="I split the line so the fryer only cooked.", quotes=["q"])
    ]
    claude = FakeClaude(
        [
            reply({"title": "New", "summary": "I split the line so the fryer only cooked."}),
            reply(
                {"title": "New", "summary": "The window stopped backing up once orders moved down the line."}
            ),
        ]
    )
    result = await engine.rewrite_chapter(claude, turns=turns(1), chapters=book, chapter_id="c0")
    assert result.title == "New"
    assert result.quotes == ["q"]


async def test_book_output_with_a_resume_only_term_retries_then_drops_it():
    said = [engine.Turn(question="Q?", answer=a, phase="dig") for a in ANSWERS]
    leak = {"title": "My time at Gopala", "summary": "It was at Gopala.", "quotes": [ANSWERS[0]]}
    clean = [chapter(answer, f"Clean {n}") for n, answer in enumerate(ANSWERS[:3])]
    claude = FakeClaude(
        [
            reply({"pool": [leak, *clean], "titles": TITLES, "blurb": BLURB}),
            reply({"pool": [leak, *clean], "titles": TITLES, "blurb": BLURB}),
        ]
    )
    draft = await engine.draft_book(claude, turns=said, leaks=lambda text: "Gopala" in text)
    assert len(claude.requests) == 2
    assert [c.title for c in draft.pool] == ["Clean 0", "Clean 1", "Clean 2"]


async def test_a_blurb_with_a_resume_only_term_is_never_returned():
    claude = FakeClaude([reply({"blurb": "At Gopala, I did it."}), reply({"blurb": "I did it, twice."})])
    blurb = await engine.write_blurb(claude, turns=turns(1), chapters=[], leaks=lambda text: "Gopala" in text)
    assert blurb == "I did it, twice."
