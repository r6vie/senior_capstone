"""The free checks on saved runs, and the saved transcripts themselves."""

import os
from pathlib import Path

import pytest

from evals.interview.personas import PERSONAS
from evals.lints import (
    Finding,
    lint_answers,
    lint_book,
    lint_change,
    lint_playbacks,
    lint_question,
    lint_questions,
    lint_run,
)
from evals.saved import HOLDOUTS, fixtures, load_run, packet, parse_run, persona_of, turns_of
from evals.usage import member_client, product_client
from tests.fakes import FakeClaude
from trove.ai.prompts import PROMPTS_DIR
from trove.interview.engine import Turn


def rules(findings: list[Finding]) -> set[str]:
    return {f.rule for f in findings}


def turn(
    question="What broke first?", answer="The nozzle jammed on the first print I ever ran alone.", phase="dig"
):
    return Turn(question=question, answer=answer, phase=phase)


def chapter(**changes) -> dict:
    return {
        "title": "Why the nozzle jammed",
        "summary": "The nozzle jammed on the first print I ever ran alone.",
        "quotes": ["The nozzle jammed on the first print"],
    } | changes


def book(**changes) -> dict:
    return {
        "titles": [
            {"title": "The Nozzle Problem", "why": "You kept coming back to it."},
            {"title": "Alone at the Desk", "why": "You ran it by yourself."},
            {"title": "What Jams First", "why": "You learned by breaking things."},
        ],
        "pool": [],
        "chapters": [
            chapter(),
            chapter(title="Cleaning a bed properly"),
            chapter(title="Training every new worker"),
        ],
        "blurbs": {"finished": "I ran the printers alone. The nozzle jammed on my first print."},
    } | changes


def test_a_clean_book_and_question_have_no_errors():
    assert not [f for f in lint_book(book(), [turn()]) if f.level == "error"]
    assert lint_question("What broke first?") == []


@pytest.mark.parametrize(
    ("question", "rule"),
    [
        ("Tell me about yourself.", "tell me about yourself"),
        ("Why does that matter?", "importance of"),
        ("How do you balance the two?", "how do you balance"),
        ("What happened? And what did you do?", "two questions"),
        ("What did you do last Saturday?", "small talk"),
        ("That's okay. What else comes to mind?", "reassurance"),
        ("That's fascinating. What broke?", "praise"),
        ("Did you fix it?", "yes/no opener"),
    ],
)
def test_question_rules(question, rule):
    assert rule in rules(lint_question(question))


def test_a_shape_playback_may_ask_yes_or_no():
    assert lint_question("Is this you?", "shape") == []
    assert "yes/no opener" not in rules(lint_question("Is this you?", "shape"))


def test_repeated_question_shapes_are_flagged():
    turns = [
        turn("Think of the last time it broke. What did you almost do?"),
        turn("What did you almost do then?"),
    ]
    assert "repeated shape" in rules(lint_questions(turns))
    same = [turn(f"What was the hardest {thing}?") for thing in ("part", "day", "week")]
    assert "repeated opener" in rules(lint_questions(same))


def test_quotes_must_be_verbatim():
    changed = book(chapters=[chapter(quotes=["The nozzle jammed badly on every print"])] * 3)
    assert "quote not verbatim" in rules(lint_book(changed, [turn()]))


@pytest.mark.parametrize(
    ("changes", "rule"),
    [
        ({"summary": "I " + "jammed " * 60}, "summary length"),
        ({"summary": "This chapter covers how I fixed it."}, "meta phrasing"),
        ({"summary": "My journey through printers."}, "hype"),
        ({"title": "Printers"}, "title length"),
    ],
)
def test_chapter_rules(changes, rule):
    assert rule in rules(lint_book(book(chapters=[chapter(**changes)] * 3), [turn()]))


def test_blurb_rules():
    def lint(blurb):
        return rules(lint_book(book(blurbs={"finished": blurb}), [turn()]))

    assert "blurb length" in lint("I jammed it. " * 60)
    assert "blurb sentences" in lint("I jammed it.")
    assert "not first person" in lint("Printers jam. Nozzles too.")
    assert "meta phrasing" in lint("In this book I explain. I jammed it.")


def test_a_stock_offer_and_a_quote_that_repeats_the_summary_are_flagged():
    closing = (
        "I ran the printers alone. If you're trying to keep printers running, I can tell you what I check."
    )
    assert "stock offer" in rules(lint_book(book(blurbs={"finished": closing}), [turn()]))
    assert "quote repeats summary" in rules(lint_book(book(), [turn()]))
    added = chapter(summary="I fixed it alone after the sign went up.")
    assert "quote repeats summary" not in rules(lint_book(book(chapters=[added] * 3), [turn()]))


def test_three_titles_that_overlap_are_flagged():
    titles = [
        {"title": "Fixing Broken Printers", "why": "x"},
        {"title": "Broken Printers Everywhere", "why": "x"},
        {"title": "Alone at the Desk", "why": "x"},
    ]
    findings = lint_book(book(titles=titles), [turn()])
    assert any(f.rule == "titles overlap" and f.level == "error" for f in findings)


def test_resume_terms_and_names_in_the_book_are_flagged():
    leaked = book(chapters=[chapter(summary="At Initech, I fixed the nozzle that jammed in 2019.")] * 3)
    findings = lint_book(leaked, [turn()], resume="Engineer, Initech, 2019-2024.")
    assert {("error", "résumé term in book", "Initech"), ("error", "résumé term in book", "2019")} <= {
        (f.level, f.rule, f.detail) for f in findings
    }
    named = book(chapters=[chapter(summary="I learned it from my boss, Jane Doe, and Dr. Smith.")] * 3)
    assert {"Jane Doe", "Dr. Smith"} <= {
        f.detail for f in lint_book(named, [turn()]) if f.rule == "possible name"
    }
    author = book(chapters=[chapter(summary="Dana fixed the nozzle.")] * 3)
    assert "author's name" in rules(lint_book(author, [turn()], author="Dana"))


def test_a_number_the_member_never_said_is_flagged():
    stated = book(chapters=[chapter(summary="I fixed twelve jams and 40 nozzles.")] * 3)
    answers = [turn(answer="There were 12 jams that year and maybe a few nozzles.")]
    found = {f.detail for f in lint_book(stated, answers) if f.rule == "number not in answers"}
    assert found == {"40"}


def test_fixtures_are_real_invented_interviews():
    saved = fixtures()
    assert {"dana", "theo", "ruth", "marcus"} <= set(saved)
    names = {p["name"] for p in PERSONAS}
    for run in saved.values():
        assert run["persona"] in names
        assert len(run["turns"]) >= 8


def test_a_member_writing_their_reasoning_is_caught():
    leaked = [turn(answer='The profile says she goes quiet. Her reply: "It was the bed."')]
    assert "member out of character" in rules(lint_answers(leaked))
    assert not lint_answers([turn(answer="My brother got me that call, and the bed was dirty.")])


def test_fixtures_are_the_members_words_only():
    for run in fixtures().values():
        assert not lint_answers(turns_of(run)), run["slug"]


def test_fixtures_replay_with_grounded_quotes():
    for run in fixtures().values():
        findings = lint_run(run, resume=persona_of(run).get("resume"))
        assert "quote not verbatim" not in rules(findings), run["slug"]
        assert all(t.question for t in turns_of(run))
        # The packet is the editor's view, and hides what the persona was hoped to surface.
        assert "Should surface" not in packet(run)


def test_parsing_a_saved_run_keeps_skips_and_long_answers():
    markdown = """## Dana (quiet)

### Transcript

**Q1 [sweep]** What takes your week?

<sub>topic: x</sub>

**A:** The desk.

And then more.

---

**Q2 [dig]** Which one?

**A:** *(skips)*

---

**Q3 [shape]** Is this you?

> playback: You fix printers.

**A:** Yes.

---

**Q4 [shape]** Enough.

*(ready for reveal)*

### Titles

1. **One Two**: why one

### Pool

- **A title here**: A summary.
  > A quote goes here.

### Finished book: One Two

- **A title here**: A summary.
  > A quote goes here.
"""
    run = parse_run(markdown)
    assert [t["answer"] for t in run["turns"]] == ["The desk.\n\nAnd then more.", "", "Yes."]
    assert run["turns"][2]["playback"] == "You fix printers."
    assert run["book"]["title"] == "One Two"
    assert run["book"]["chapters"][0]["quotes"] == ["A quote goes here."]


@pytest.mark.skipif("EVAL_OUTPUT" not in os.environ, reason="point EVAL_OUTPUT at a saved run to lint it")
def test_a_saved_output_has_no_lint_errors():
    run = load_run(Path(os.environ["EVAL_OUTPUT"]))
    errors = [str(f) for f in lint_run(run, resume=persona_of(run).get("resume")) if f.level == "error"]
    assert not errors, "\n".join(errors)


# Distinctive words from every persona. An example lifted from one would make every run of that persona look
# better than a real member's interview, and the holdouts (saved.HOLDOUTS) must stay unseen altogether.
PERSONA_WORDS = [
    "batch",
    "tasted",
    "print bed",
    "printer",
    "nozzle",
    "alcohol",
    "dorm",
    "bed frame",
    "slats",
    "fry stand",
    "fryer",
    "creek",
    "skeptical",
    "tidier",
    "supply guy",
    "big deal",
    "out of order",
    "my mom",
    "nurse",
    "scared famil",
    "hospice",
    "dying",
    "robotics",
    "physics",
    "convoy",
    "padded",
    "incident",
    "on-call",
    "viola",
    "bakery",
    "paczki",
    "cost sheet",
    "metronome",
    "implant",
    "first batch",
    "county fair",
    "split in two",
    "dye",
    "yarn",
    "skein",
    "madder",
    "bridge inspect",
    "stitch night",
]


def test_prompts_dont_teach_the_test():
    for path in (PROMPTS_DIR / "interview").glob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        for word in PERSONA_WORDS:
            assert word not in text, f"{word!r} in {path.name}"


def test_a_change_note_only_says_what_was_added():
    change = {
        "summary": "I took the lease and kept the keys. I still have them.",
        "note": "A stronger, richer chapter.",
    }
    assert "praise in note" in rules(lint_change(change))
    assert "praise in note" not in rules(lint_change(change | {"note": "Adds the keys you kept."}))
    assert "improve reworded" in rules(lint_change(change, current_summary="I took it. I kept it."))
    assert not lint_change(
        change | {"note": "Adds the keys."}, current_summary="I took the lease and kept the keys."
    )


def test_holdouts_are_saved_fixtures():
    assert set(fixtures()) >= HOLDOUTS


def test_flags_from_the_quality_round():
    def rules_of(*questions, **fields):
        return rules(lint_questions([turn(q, **fields) for q in questions]))

    assert "two asks in one" in rules_of("What broke, and what did you do?", "What broke?")
    assert "first everywhere" in rules_of("What did you check first?", "What broke?")
    assert "long question" in rules(lint_question(" ".join(["word"] * 26) + "?"))
    opening = lint_questions(
        [Turn(question="What are you studying or working on?", answer="Math.", phase="sweep")]
    )
    assert "form-letter opening" in rules(opening)
    skip = [turn("Which math class beat you?", answer=""), turn("Which math class do you still argue about?")]
    assert "back to skipped subject" in rules(lint_questions(skip))
    pressed = [
        turn(answer="I don't want to make up a run."),
        turn("Which one specific run changed your mind?"),
    ]
    assert "pressed after no example" in rules(lint_questions(pressed))
    area = [
        Turn(question=f"Which repair {x}?", answer="A long enough answer here.", phase="sweep") for x in "abc"
    ]
    assert "sweep stuck in one area" in rules(lint_questions(area))


def test_book_flags_from_the_quality_round():
    played_down = [turn(answer="Mostly. I don't think the slats are that big a deal though.", phase="shape")]
    titles = [{"title": "Check the Slats First", "why": "x"}, *book()["titles"][1:]]
    assert "disowned at Shape" in rules(lint_book(book(titles=titles), played_down))
    steps = chapter(
        summary="I turn it off, then I pull the filament, then I heat it again, and my nozzle jammed."
    )
    assert "steps in summary" in rules(lint_book(book(chapters=[steps] * 3), [turn()]))
    long = {
        "persona": "x",
        "turns": [{"question": "Is this you?", "answer": "Yes.", "phase": "shape", "playback": "word " * 31}],
        "book": {},
    }
    assert "long playback" in rules(lint_playbacks(long))


def test_evals_run_the_product_on_opus_and_the_member_on_the_cheap_model():
    # A .env pointing the app at a cheap model must not change what an eval measures.
    claude = FakeClaude([])
    claude.model = "claude-haiku-5-5"
    assert product_client(claude).model == "claude-opus-5-5"
    assert member_client(claude).model == "claude-sonnet-5-5"
    assert claude.model == "claude-haiku-5-5"
