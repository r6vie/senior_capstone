"""The Librarian's live notes and notebook (L1): code checks, silence, caps and the notes route."""

import asyncio
import json
from datetime import UTC, datetime

import pytest

from tests.fakes import FakeClaude, send_answer, send_skip, text_message
from tests.test_interview import SIGNUP, FakeEngine
from trove.ai.scripted import ScriptedClaude
from trove.interview import engine, librarian, service, silence
from trove.interview.engine import Turn
from trove.interview.librarian import Context, Entry, Mark, _NewEntry, _NewMark

# Unit checks, no database.


@pytest.mark.parametrize(
    ("text", "silent"),
    [
        ("My dad died last spring, and I took the semester off.", True),
        ("I sat with the family while he was dying.", True),
        ("We got divorced the year I started the job.", True),
        ("I came out to my parents that summer.", True),
        ("I miss my mom\u2019s lasagna, so I learned to make it.", False),
        ("We played death metal in the basement.", False),
        ("I'm dying to try the new lathe.", False),
        ("The terminal crashed and I diagnosed the bug in a day.", False),
        ("It came out fine in the end.", False),
    ],
)
def test_silence_is_about_the_subject_not_a_passing_word(text, silent):
    assert silence.is_silent(text) is silent


def test_the_librarian_only_reads_once_a_sentence_has_ended():
    assert librarian.nothing_to_read("I fixed the", "I fixed the printer twice over and over")
    assert not librarian.nothing_to_read("I fixed the printer", "I fixed the printer.")
    assert not librarian.nothing_to_read("One. Two", "One. Two. Three")
    assert librarian.nothing_to_read("same text.", "same text.")


@pytest.mark.parametrize(
    ("line", "problem"),
    [
        ("this one is great!", "exclamation"),
        ("we should talk.", '"we"'),
        ("slay.", "slang"),
        ("good next question.", "interview itself"),
        ("very spanish of you.", "heritage"),
        ("a salary would help.", "salary"),
        ("email me at jo (at) mail (dot) com", "contact details"),
        ("Says who?", "lowercase"),
        ("a very long note that goes on past the limit.", "characters"),
        ("a verb would help.", "copies an example"),
    ],
)
def test_every_line_is_checked(line, problem):
    problems = librarian.line_problems(line, limit=librarian.NOTE_CHARS, member_text="I fixed the press.")
    assert any(problem in p for p in problems), problems


def test_a_line_passes_when_it_keeps_the_rules():
    assert librarian.line_problems("says who?", limit=32, member_text="Everyone loved it.") == []
    # A capital is fine when the member wrote the word that way.
    assert librarian.line_problems("ask the PI.", limit=32, member_text="My PI said no.") == []
    # A sensitive word the member raised themselves can come back.
    assert librarian.line_problems("salary, then.", limit=32, member_text="I took a salary cut.") == []


TURNS = {
    1: "I rebuilt the intake form for the free clinic.",
    2: "The intake form had nine pages nobody read.",
}


def entry(kind, text, anchors, sources):
    return _NewEntry(kind=kind, text=text, anchors=anchors, source_turns=sources)


def problems(item):
    return librarian.entry_problems(item, turns=TURNS, current=2, member_text=" ".join(TURNS.values()))


def test_notebook_entries_are_grounded_in_the_members_words():
    assert problems(entry("chapter", "ch. ? nine pages nobody read", ["nine pages"], [2])) == []
    assert problems(entry("chapter", "ch. ? the big mystery", ["nine pages"], [2]))
    assert problems(entry("saving", "ask: who wrote the pages?", ["nine pages"], [2])) == []
    assert problems(entry("connection", "the intake form again.", ["intake form"], [1, 2])) == []
    # A connection names words from both answers.
    assert problems(entry("connection", "nine pages again.", ["nine pages"], [1, 2]))
    assert problems(entry("connection", "intake form again.", ["intake form"], [2]))
    assert problems(entry("clip", "nine pages nobody read", ["nine pages nobody read"], [2])) == []
    assert problems(entry("clip", "nine pages that nobody ever read", ["nine pages"], [2]))
    # Every entry is about the answer being written, and its anchors are the member's exact words.
    assert problems(entry("note", "a clinic story.", ["free clinic"], [1]))
    assert problems(entry("note", "a form story.", ["eleven pages"], [2]))


def test_marks_are_anchored_to_the_answer_and_circles_need_a_real_callback():
    answer = "The van broke down, and the van came back."
    member = answer

    def check(**fields):
        mark = _NewMark(**{"move": "underline", "occurrence": 1, "note": "says who?"} | fields)
        return librarian.mark_problems(
            mark, answer=answer, earlier=["The van.", "That van again."], member_text=member
        )

    assert check(anchor="the van", occurrence=2) == []
    assert check(anchor="the van", occurrence=3)
    assert check(anchor="the truck")
    assert check(anchor="van", move="strike", note=None)
    assert check(anchor="van", move="circle", note="\u00d73. the van again.") == []
    one_earlier = _NewMark(move="circle", anchor="van", occurrence=1, note="\u00d72.")
    assert librarian.mark_problems(one_earlier, answer=answer, earlier=["The van."], member_text=member)


def context(answer: str, **fields) -> Context:
    return Context(
        **{
            "question": "What did you change about the intake?",
            "question_number": 2,
            "setting": "the interview",
            "earlier": [Turn(question="What do people come to you for?", answer=TURNS[1], phase="sweep")],
            "silent_turns": [],
            "answer": answer,
            "pasted": False,
            "marks": [],
            "entries": [],
            "notebook": [],
        }
        | fields
    )


def notes_reply(**fields) -> str:
    base = {
        "silent": False,
        "keep_marks": [],
        "marks": [],
        "keep_entries": [],
        "revise": [],
        "erase": [],
        "entries": [],
    }
    return json.dumps(base | fields)


async def test_one_retry_with_the_broken_rules_then_bad_items_are_dropped():
    answer = TURNS[2]
    bad = {"move": "underline", "anchor": "eleven pages", "occurrence": 1, "note": "says who?"}
    good = {"move": "underline", "anchor": "nine pages", "occurrence": 1, "note": "a number would help."}
    claude = FakeClaude(
        [text_message(notes_reply(marks=[bad, good])), text_message(notes_reply(marks=[bad, good]))]
    )
    notes = await librarian.look(librarian.on_notes_model(claude), context(answer))
    assert [m.anchor for m in notes.marks] == ["nine pages"]
    first, retry = claude.requests
    assert first["model"] == librarian.NOTES_MODEL
    assert first["thinking"] == {"type": "adaptive"}
    assert first["output_config"]["effort"] == "low"
    # The system prompt and the per-question prefix are both cached.
    assert first["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert first["messages"][0]["content"][0]["cache_control"] == {"type": "ephemeral"}
    assert "eleven pages" in retry["messages"][-1]["content"]
    assert retry["messages"][1]["role"] == "assistant"


async def test_caps_on_marks_and_notebook_additions():
    answer = "The intake form had nine pages, nine fields, and nobody read the nine pages at all."
    marks = [
        {"move": "underline", "anchor": "nobody read", "occurrence": 1, "note": "says who?"},
        {"move": "note", "anchor": "nine fields", "occurrence": 1, "note": "a number, at last."},
        {"move": "underline", "anchor": "intake form", "occurrence": 1, "note": "says who?"},
        {"move": "underline", "anchor": "nine pages", "occurrence": 2, "note": "a number would help."},
        {"move": "underline", "anchor": "at all", "occurrence": 1, "note": "buried the lead."},
    ]
    entries = [
        {"kind": "chapter", "text": f"ch. ? the {w} problem", "anchors": [w], "source_turns": [2]}
        for w in ("nine pages", "nine fields", "intake form")
    ]
    claude = FakeClaude([text_message(notes_reply(marks=marks, entries=entries))])
    notes = await librarian.look(claude, context(answer))
    assert len(notes.marks) == librarian.MAX_MARKS_PER_ANSWER
    assert len(notes.added_entries) == librarian.MAX_ENTRY_ADDS_PER_CALL


async def test_the_back_cover_line_is_one_whole_sentence_once_per_interview():
    answer = "I sat in on the clinic. The intake form had nine pages nobody read. I cut it to one."
    sentence = "The intake form had nine pages nobody read."
    cover = {"move": "back_cover", "anchor": sentence, "occurrence": 1, "note": "a line."}
    claude = FakeClaude([text_message(notes_reply(marks=[cover]))])
    notes = await librarian.look(claude, context(answer))
    assert [(m.move, m.anchor, m.note) for m in notes.marks] == [("back_cover", sentence, None)]
    assert [e.text for e in notes.added_entries] == [librarian.BACK_COVER_NOTE]
    # Half a sentence isn't a back-cover line, and the second one in an interview isn't allowed.
    half = {**cover, "anchor": "The intake form had nine pages"}
    claude = FakeClaude([text_message(notes_reply(marks=[half])), text_message(notes_reply(marks=[half]))])
    assert (await librarian.look(claude, context(answer))).marks == []
    claude = FakeClaude([text_message(notes_reply(marks=[cover]))])
    assert (await librarian.look(claude, context(answer, back_cover_used=True))).marks == []
    # It goes when the sentence changes.
    assert librarian.marks_that_hold(notes.marks, "The intake form had eight pages nobody read.") == []


async def test_the_running_bit_counts_the_answers_and_comes_once():
    earlier = [
        Turn(question="Q1?", answer="Fixing the club van, mostly.", phase="sweep"),
        Turn(question="Q2?", answer="The van's battery dies in the cold.", phase="sweep"),
    ]
    circle = {"move": "circle", "anchor": "van", "occurrence": 1, "note": "\u00d73. the van has a pension."}
    claude = FakeClaude([text_message(notes_reply(marks=[circle]))])
    notes = await librarian.look(
        claude, context("I built a heater box for the van.", earlier=earlier, question_number=3)
    )
    assert [(m.count, m.note) for m in notes.marks] == [(3, "the van has a pension.")]
    claude = FakeClaude([text_message(notes_reply(marks=[circle]))])
    used = context(
        "I built a heater box for the van.", earlier=earlier, question_number=3, running_bit_used=True
    )
    assert (await librarian.look(claude, used)).marks == []


async def test_a_sharpened_phrase_gets_credit_on_its_own_mark():
    old = Mark(id="m_old", move="underline", anchor="a lot more efficient", occurrence=1, note="says who?")
    answer = "I cut the wait from forty minutes to nine."
    credit = {"id": "m_old", "anchor": "forty minutes to nine", "occurrence": 1, "note": "there it is."}
    claude = FakeClaude([text_message(notes_reply(credit=[credit]))])
    notes = await librarian.look(claude, context(answer, lost_marks=[old]))
    assert [(m.id, m.anchor, m.note, m.struck_note) for m in notes.revised_marks] == [
        ("m_old", "forty minutes to nine", "there it is.", "says who?")
    ]


async def test_the_concession_comes_once_and_only_for_deleted_marked_words():
    old = Mark(id="m_old", move="underline", anchor="synergy", occurrence=1, note="résumé voice.")
    claude = FakeClaude([text_message(notes_reply(concede=True))])
    notes = await librarian.look(claude, context(TURNS[2], lost_marks=[old]))
    assert [e.text for e in notes.added_entries] == [librarian.CONCESSION_NOTE] and notes.conceded
    claude = FakeClaude([text_message(notes_reply(concede=True))])
    assert not (await librarian.look(claude, context(TURNS[2], lost_marks=[old], conceded=True))).conceded
    claude = FakeClaude([text_message(notes_reply(concede=True))])
    assert not (await librarian.look(claude, context(TURNS[2]))).conceded


async def test_bets_are_capped_and_settled_by_a_later_answer():
    bet = {"kind": "bet", "text": "betting the form wins.", "anchors": ["intake form"], "source_turns": [2]}
    open_bets = [
        Entry(id=f"n_b{n}", kind="bet", text=f"bet {n}.", anchors=["clinic"], source_turns=[1])
        for n in range(2)
    ]
    claude = FakeClaude([text_message(notes_reply(entries=[bet]))])
    assert (await librarian.look(claude, context(TURNS[2], notebook=open_bets))).added_entries == []
    settle = {"id": "n_b0", "outcome": "called", "anchor": "nine pages"}
    claude = FakeClaude([text_message(notes_reply(settle=[settle]))])
    notes = await librarian.look(claude, context(TURNS[2], notebook=open_bets))
    ((called, by),) = notes.settled
    assert (called.id, called.status, called.outcome_note, by) == (
        "n_b0",
        "called",
        "called it.",
        "nine pages",
    )


async def test_one_clip_per_answer():
    clips = [
        {
            "kind": "clip",
            "text": "nine pages nobody read",
            "anchors": ["nine pages nobody read"],
            "source_turns": [2],
        },
        {"kind": "clip", "text": "The intake form", "anchors": ["The intake form"], "source_turns": [2]},
    ]
    claude = FakeClaude([text_message(notes_reply(entries=clips))])
    notes = await librarian.look(claude, context(TURNS[2]))
    assert [e.kind for e in notes.added_entries] == ["clip"]


async def test_the_model_can_declare_an_answer_silent():
    mine = Entry(id="n_1", kind="note", text="a form story.", anchors=["intake form"], source_turns=[2])
    claude = FakeClaude([text_message(notes_reply(silent=True))])
    notes = await librarian.look(claude, context(TURNS[2], entries=[mine]))
    assert notes.silent and notes.marks == [] and notes.erased_entries == ["n_1"]


async def test_earlier_silent_answers_are_masked_in_the_prompt():
    claude = FakeClaude([text_message(notes_reply())])
    await librarian.look(claude, context(TURNS[2], silent_turns=[1]))
    sent = claude.requests[0]["messages"][0]["content"][0]["text"]
    assert TURNS[1] not in sent and silence.MASKED in sent


def test_ids_are_stable_hashes():
    assert librarian.mark_id("underline", "Nine pages", 1) == librarian.mark_id("underline", "nine pages", 1)
    assert librarian.entry_id("chapter", 2, "ch. ? x") != librarian.entry_id("chapter", 3, "ch. ? x")


def test_marks_and_entries_are_rubbed_out_when_their_words_go():
    mark = Mark(id="m", move="underline", anchor="nine pages", occurrence=1, note="says who?")
    clip = Entry(id="c", kind="clip", text="nine pages", anchors=["nine pages"], source_turns=[2])
    note = Entry(id="n", kind="note", text="paper trail.", anchors=["intake form"], source_turns=[2])
    text = "The intake form had a few pages."
    assert librarian.marks_that_hold([mark], text) == []
    assert librarian.entries_that_hold([clip, note], text) == [note]


def test_the_notebook_is_trimmed_in_order_when_it_comes_back_for_adding():
    notebook = [
        {"id": "a", "kind": "saving", "status": "ticked"},
        {"id": "b", "kind": "note"},
        {"id": "c", "kind": "saving", "status": "open"},
        {"id": "lost-bet", "kind": "bet", "status": "lost"},
        {"id": "open-bet", "kind": "bet", "status": "open"},
        *({"id": f"k{n}", "kind": "chapter"} for n in range(librarian.NOTEBOOK_KEEP + 3)),
    ]
    kept = librarian.trim_for_adding(notebook)
    ids = [entry["id"] for entry in kept]
    assert "a" not in ids and "b" not in ids and "lost-bet" not in ids
    assert len(kept) == librarian.NOTEBOOK_KEEP
    assert librarian.trim_for_adding([{"id": "o", "kind": "bet", "status": "open"}])[0]["id"] == "o"
    # The newest are kept, still in the order they were written.
    assert ids[-1] == f"k{librarian.NOTEBOOK_KEEP + 2}" and ids == sorted(ids, key=ids.index)


def test_the_sign_off_is_checked_like_a_note():
    assert librarian.sign_off_problems("it took some red ink.", "") == []
    assert librarian.sign_off_problems("WOW, what a book!!", "")
    assert librarian.sign_off_problems("this was a pleasure to read, truly.", "")


async def test_the_scripted_stand_in_writes_grounded_notes_for_free():
    notes = await librarian.look(ScriptedClaude(), context("The intake form had nine pages nobody read."))
    assert notes.added_marks and notes.added_entries
    assert all(
        librarian.occurrences("The intake form had nine pages nobody read.", m.anchor)
        for m in notes.added_marks
    )


# The notes route, on the test database.


@pytest.fixture
async def headers(client):
    await client.post("/auth/signup", json=SIGNUP)
    login = await client.post("/auth/login", json={"email": SIGNUP["email"], "password": SIGNUP["password"]})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def librarian_engine(monkeypatch, fake_claude):
    fake = FakeEngine()
    for name in ("next_turn", "draft_book", "finish_book", "write_blurb"):
        monkeypatch.setattr(engine, name, getattr(fake, name))
    return fake


async def start(client, headers) -> dict:
    state = (await client.post("/interview", json={}, headers=headers)).json()
    return state


async def post_notes(client, headers, state, text, previous="", shown=None):
    return await client.post(
        "/interview/notes",
        json={
            "question_id": state["question"]["question_id"],
            "text": text,
            "previous_text": previous,
            "shown": shown or [],
        },
        headers=headers,
    )


GOOD = {"move": "underline", "anchor": "nine pages", "occurrence": 1, "note": "a number would help."}
CHAPTER = {
    "kind": "saving",
    "text": "ask: who wrote the nine pages?",
    "anchors": ["nine pages"],
    "source_turns": [1],
}


async def test_notes_are_kept_with_the_turn_and_the_notebook_on_the_interview(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    fake_claude.notes.append(text_message(notes_reply(marks=[GOOD], entries=[CHAPTER])))
    reply = (await post_notes(client, headers, state, "The intake form had nine pages nobody read.")).json()
    assert reply["silent"] is False
    assert [m["anchor"] for m in reply["marks"]["add"]] == ["nine pages"]
    assert [e["kind"] for e in reply["notebook"]["add"]] == ["saving"]
    assert fake_claude.requests[-1]["model"] == librarian.NOTES_MODEL

    # One more word costs nothing: no model call (FakeClaude has no reply left), everything kept.
    shown = [reply["marks"]["add"][0]["id"], reply["notebook"]["add"][0]["id"]]
    again = await post_notes(
        client, headers, state, "The intake form had nine pages nobody read ever", shown=shown
    )
    assert again.status_code == 200, again.text
    assert again.json()["marks"]["keep"] == [shown[0]] and again.json()["notebook"]["keep"] == [shown[1]]
    assert again.json()["marks"]["erase"] == [] and again.json()["notebook"]["erase"] == []

    saved = await send_answer(client, headers, "The intake form had nine pages nobody read.")
    interview = await database.interviews.find_one({})
    assert interview["turns"][0]["marks"][0]["anchor"] == "nine pages"
    assert interview["notebook"][0]["text"] == "ask: who wrote the nine pages?"
    view = saved.json()["librarian"]
    assert view["turns"][0]["marks"][0]["note"] == "a number would help."
    assert view["notebook"][0]["kind"] == "saving"


async def test_a_silent_answer_is_never_sent_and_rubs_out_what_it_had(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    fake_claude.notes.append(text_message(notes_reply(marks=[GOOD], entries=[CHAPTER])))
    reply = (await post_notes(client, headers, state, "The intake form had nine pages nobody read.")).json()
    shown = [reply["marks"]["add"][0]["id"], reply["notebook"]["add"][0]["id"]]
    text = "The intake form had nine pages nobody read. Then my dad died that winter."
    quiet = (await post_notes(client, headers, state, text, shown=shown)).json()
    calls = len(fake_claude.requests)
    assert quiet["silent"] is True
    assert quiet["marks"] == {"keep": [], "add": [], "revise": [], "erase": [shown[0]]}
    assert quiet["notebook"]["erase"] == [shown[1]]

    await send_answer(client, headers, text)
    interview = await database.interviews.find_one({})
    assert interview["turns"][0]["silent"] is True and "marks" not in interview["turns"][0]
    assert interview.get("notebook") == []

    # On the next answer the silent one is masked, never sent.
    state = (await client.get("/interview", headers=headers)).json()
    fake_claude.notes.append(text_message(notes_reply()))
    await post_notes(client, headers, state, "I rebuilt the intake form for the free clinic.")
    sent = json.dumps(fake_claude.requests[calls:])
    assert "my dad died" not in sent and silence.MASKED in sent


async def test_notes_stop_calling_the_model_past_the_caps(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    await database.interviews.update_one(
        {}, {"$set": {"current.librarian": {"marks": [], "calls": 8, "silent": False, "last_text": ""}}}
    )
    reply = await post_notes(client, headers, state, "The intake form had nine pages nobody read.")
    assert reply.status_code == 200 and fake_claude.requests == []

    await database.interviews.update_one(
        {}, {"$set": {"current.librarian.calls": 0, "notes_rate": {"since": datetime.now(UTC), "count": 200}}}
    )
    reply = await post_notes(client, headers, state, "The intake form had nine pages nobody ever read.")
    assert reply.status_code == 200 and fake_claude.requests == []


async def test_notes_for_a_question_that_isnt_waiting_are_409(client, headers, librarian_engine):
    await start(client, headers)
    reply = await client.post(
        "/interview/notes", json={"question_id": "old", "text": "x y z"}, headers=headers
    )
    assert reply.status_code == 409


async def test_a_failed_notes_call_adds_nothing_and_is_not_an_error(
    client, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    fake_claude.notes.append(text_message("not json"))
    reply = await post_notes(client, headers, state, "The intake form had nine pages nobody read.")
    assert reply.status_code == 200
    assert reply.json()["marks"]["add"] == [] and reply.json()["notebook"]["add"] == []


async def test_a_skip_rubs_out_that_answers_entries(client, database, headers, fake_claude, librarian_engine):
    state = await start(client, headers)
    fake_claude.notes.append(text_message(notes_reply(entries=[CHAPTER])))
    await post_notes(client, headers, state, "The intake form had nine pages nobody read.")
    await send_skip(client, headers)
    assert (await database.interviews.find_one({}))["notebook"] == []


async def test_the_next_question_can_build_on_the_notebook(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    fake_claude.notes.append(text_message(notes_reply(entries=[CHAPTER])))
    reply = (await post_notes(client, headers, state, "The intake form had nine pages nobody read.")).json()
    saving_id = reply["notebook"]["add"][0]["id"]
    librarian_engine.builds_on_next = saving_id
    await send_answer(client, headers, "The intake form had nine pages nobody read.")
    assert librarian_engine.calls[-1][1]["notebook"] == [
        {"id": saving_id, "kind": "saving", "text": "ask: who wrote the nine pages?"}
    ]
    interview = await database.interviews.find_one({})
    assert interview["current"]["builds_on"] == saving_id
    assert interview["notebook"][0]["status"] == "ticked"
    asked = (await client.get("/interview", headers=headers)).json()
    assert asked["question"]["builds_on"] == saving_id
    assert asked["librarian"]["notebook"][0]["status"] == "ticked"

    # An id the question writer wasn't shown is ignored.
    librarian_engine.builds_on_next = "n_made_up"
    await send_answer(client, headers, "Another answer about the clinic.")
    assert (await database.interviews.find_one({}))["current"]["builds_on"] is None


async def test_clips_go_to_the_draft_and_the_sign_off_is_checked(
    client, database, headers, fake_claude, librarian_engine
):
    from tests.fakes import choose_and_wait, finish_and_wait

    state = await start(client, headers)
    clip = {
        "kind": "clip",
        "text": "nine pages nobody read",
        "anchors": ["nine pages nobody read"],
        "source_turns": [1],
    }
    fake_claude.notes.append(text_message(notes_reply(entries=[clip])))
    await post_notes(client, headers, state, "The intake form had nine pages nobody read.")
    await send_answer(client, headers, "The intake form had nine pages nobody read.")
    for n in range(9):
        await send_answer(client, headers, f"Answer {n}.")
    await finish_and_wait(client, headers)
    drafted = next(call for name, call in librarian_engine.calls if name == "draft_book")
    assert drafted["clips"] == ["nine pages nobody read"]

    # The sign-off is a Haiku call, checked like a note with one retry: a line failing twice is left out.
    fake_claude.responses += [
        text_message('{"sign_off": "Great job!!"}'),
        text_message('{"sign_off": "WOW."}'),
    ]
    await choose_and_wait(client, headers, 0)
    assert fake_claude.requests[-1]["model"] == librarian.NOTES_MODEL
    assert "fallbacks" not in fake_claude.requests[-1]
    assert (await client.get("/interview", headers=headers)).json()["sign_off"] is None
    # The notebook is hidden after the reveal, but never deleted.
    assert (await client.get("/interview", headers=headers)).json()["librarian"] is None
    interview = await database.interviews.find_one({})
    assert interview["notebook"]
    claude = FakeClaude(
        [text_message('{"sign_off": "Bad!"}'), text_message('{"sign_off": "worth the margin."}')]
    )
    finished = engine.FinishedBook(chapters=[], blurb="I fixed it.")
    assert await service.sign_off_for(claude, interview, "Title", finished) == "worth the margin."


async def test_a_bet_settled_by_words_that_are_then_deleted_goes_back_to_open(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    bet = {"kind": "bet", "text": "betting the form wins.", "anchors": ["intake form"], "source_turns": [1]}
    fake_claude.notes.append(text_message(notes_reply(entries=[bet])))
    reply = (await post_notes(client, headers, state, "The intake form had nine pages nobody read.")).json()
    bet_id = reply["notebook"]["add"][0]["id"]
    await send_answer(client, headers, "The intake form had nine pages nobody read.")
    state = (await client.get("/interview", headers=headers)).json()
    settle = {"id": bet_id, "outcome": "called", "anchor": "one page"}
    fake_claude.notes.append(text_message(notes_reply(settle=[settle])))
    settled = (await post_notes(client, headers, state, "In the end the form was one page.")).json()
    assert [(e["id"], e["status"]) for e in settled["notebook"]["revise"]] == [(bet_id, "called")]
    await send_answer(client, headers, "In the end the form was shorter.")
    bets = [e for e in (await database.interviews.find_one({}))["notebook"] if e["id"] == bet_id]
    assert bets[0]["status"] == "open" and bets[0]["outcome_note"] is None


async def test_the_eval_cases_run_end_to_end_on_the_scripted_stand_in():
    # Free: proves the tuning loop runs before any paid run, and that the server's own silence list
    # already catches every silent case without the model.
    from evals.librarian import _typed
    from evals.librarian.cases import CASES

    for case in CASES:
        typed = await _typed(ScriptedClaude(), case)
        assert typed["silent"] is (case["expect"] == "silent"), case["name"]


async def test_a_chapter_entry_always_reads_ch_question_mark():
    chapter = {
        "kind": "chapter",
        "text": "ch. 1 nine pages nobody read",
        "anchors": ["nine pages"],
        "source_turns": [2],
    }
    claude = FakeClaude([text_message(notes_reply(entries=[chapter]))])
    notes = await librarian.look(claude, context(TURNS[2]))
    assert [e.text for e in notes.added_entries] == ["ch. ? nine pages nobody read"]


def test_a_prompt_example_with_one_word_swapped_is_still_a_copy():
    assert librarian.copies_an_example("the kettle is in every scene.")
    assert librarian.copies_an_example("the van is in every scene.")
    assert not librarian.copies_an_example("the van keeps getting upgrades.")
    assert "copies an example" in " ".join(
        librarian.line_problems("the toaster is in every scene.", limit=32, member_text="")
    )


# The final look on the answer as sent (the notebook catching up after Send).


EMPTY_DELTA = {"keep": [], "add": [], "revise": [], "erase": []}


async def final_notes(client, headers, question_id: str) -> dict:
    response = await client.get(
        "/interview/notes/final", params={"question_id": question_id}, headers=headers
    )
    assert response.status_code == 200, response.text
    return response.json()


async def test_a_pasted_answer_gets_its_notes_after_send(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    question_id = state["question"]["question_id"]
    # Pasted in one go: no look while typing ever saw it.
    fake_claude.notes.append(text_message(notes_reply(marks=[GOOD], entries=[CHAPTER])))
    sent = (await send_answer(client, headers, "The intake form had nine pages nobody read.")).json()
    assert any(r["model"] == librarian.NOTES_MODEL for r in fake_claude.requests)
    # The answer's own response already carries them, for a client that never asks.
    assert sent["librarian"]["turns"][0]["marks"][0]["anchor"] == "nine pages"
    assert [e["kind"] for e in sent["librarian"]["notebook"]] == ["saving"]

    final = await final_notes(client, headers, question_id)
    assert final["status"] == "done" and final["silent"] is False
    assert [m["anchor"] for m in final["marks"]["add"]] == ["nine pages"]
    assert [e["text"] for e in final["notebook"]["add"]] == ["ask: who wrote the nine pages?"]
    interview = await database.interviews.find_one({})
    assert interview["notebook"][0]["turn"] == 1
    assert interview["notes_rate"]["count"] == 1


async def test_no_final_look_when_the_words_were_already_read(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    text = "The intake form had nine pages nobody read."
    fake_claude.notes.append(text_message(notes_reply(marks=[GOOD])))
    await post_notes(client, headers, state, text)
    calls = len(fake_claude.requests)
    await send_answer(client, headers, text)
    assert not any(r["model"] == librarian.NOTES_MODEL for r in fake_claude.requests[calls:])
    assert (await final_notes(client, headers, state["question"]["question_id"]))["status"] == "none"


async def test_a_failed_final_look_never_fails_the_answer(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    # No notes reply queued: the look fails, and the next question comes all the same.
    response = await send_answer(client, headers, "The intake form had nine pages nobody read.")
    assert response.status_code == 200, response.text
    assert response.json()["question"]["text"] == "Question 2?"
    assert (await final_notes(client, headers, state["question"]["question_id"]))["status"] == "none"
    assert (await database.interviews.find_one({}))["notebook"] == []


async def test_a_final_look_that_goes_silent_rubs_the_answer_out(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    fake_claude.notes.append(text_message(notes_reply(silent=True)))
    await send_answer(client, headers, "The intake form had nine pages nobody read.")
    final = await final_notes(client, headers, state["question"]["question_id"])
    assert final["status"] == "done" and final["silent"] is True
    turn = (await database.interviews.find_one({}))["turns"][0]
    assert turn["silent"] is True and "marks" not in turn


async def test_final_notes_are_none_for_a_skip_or_an_unknown_question(
    client, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    calls = len(fake_claude.requests)
    await send_skip(client, headers)
    assert len(fake_claude.requests) == calls
    assert (await final_notes(client, headers, state["question"]["question_id"]))["status"] == "none"
    assert (await final_notes(client, headers, "not-a-question"))["status"] == "none"


async def test_final_notes_wait_for_a_look_still_running(
    client, database, headers, fake_claude, librarian_engine
):
    state = await start(client, headers)
    question_id = state["question"]["question_id"]
    await database.interviews.update_one(
        {},
        {"$set": {"final_look": {"question_id": question_id, "status": "running", "at": datetime.now(UTC)}}},
    )

    async def finish_later():
        await asyncio.sleep(0.4)
        done = {"silent": False, "marks": EMPTY_DELTA, "notebook": EMPTY_DELTA}
        await database.interviews.update_one(
            {}, {"$set": {"final_look.status": "done", "final_look.response": done}}
        )

    later = asyncio.create_task(finish_later())
    assert (await final_notes(client, headers, question_id))["status"] == "done"
    await later
