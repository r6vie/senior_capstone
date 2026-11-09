"""A stand-in for Claude for walking through the app: AI_MODE=scripted. No key, no cost.

It has the same `create` as the real client and picks a reply by which prompt is the system prompt.
The questions and chapters come from a real saved interview (the eval persona Theo). Paste the
answers in THEO_ANSWERS and the book reads true. Type anything else and the chapters keep Theo's
titles and summaries but quote what you typed, because quotes must be verbatim from your answers
or the engine drops them.
"""

import asyncio
import json
import re
from typing import NamedTuple
from urllib.parse import urlparse
from uuid import uuid4

from anthropic.types.beta import BetaMessage, BetaTextBlock, BetaUsage

from trove.ai.prompts import prompt_name

DEV_ENVIRONMENTS = {"development", "dev", "local", "test"}
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}
# Sweep this many questions, then Dig, then Shape once this many are answered.
SWEEP_QUESTIONS = 5
SHAPE_AFTER_ANSWERS = 12
# The book steps take longer than a question, as the real ones do.
BOOK_STEP_SLOWER = 2


def ensure_scripted_allowed(settings) -> None:
    """Raise unless this is plainly a developer's machine. Canned replies must never reach a member."""
    if settings.ai_mode != "scripted":
        return
    if settings.environment.lower() not in DEV_ENVIRONMENTS:
        raise RuntimeError(f"AI_MODE=scripted is for development, not ENVIRONMENT={settings.environment}.")
    for url in (settings.frontend_url, settings.api_url):
        if urlparse(url).hostname not in LOCAL_HOSTS:
            raise RuntimeError(f"AI_MODE=scripted only runs on local URLs, not {url}.")
    if not settings.mongodb_database.startswith("trove_dev"):
        raise RuntimeError(
            f"AI_MODE=scripted only runs on a trove_dev database, not {settings.mongodb_database}."
        )


class Asked(NamedTuple):
    question: str
    topic: str


QUESTIONS = [
    Asked(
        "What are you studying or working on these days, and what part of it takes up most of your week?",
        "what you're studying or working on right now",
    ),
    Asked(
        "What was the last printer you got working on your floor, and how did it end up on your desk?",
        "the printers you fix on your floor",
    ),
    Asked(
        "Before you got to campus, what's something you built or fixed that nobody had asked you to touch?",
        "the jammed printer on your floor",
    ),
    Asked(
        "When you first looked at the guy's bed frame down the hall, what was wrong with it, and what did "
        "you check before you picked up a tool?",
        "the wobbly bed frame down the hall",
    ),
    Asked(
        "Before campus, was there a job, team, or family situation where people kept handing you the "
        "problem nobody else wanted, and what was it?",
        "the bed frame and printer on your floor",
    ),
    Asked(
        "In the creek project for AP Environmental Science, what was the first measurement or step that "
        "didn't go the way you planned, and what did you change?",
        "the creek project",
    ),
    Asked(
        "What was the plan for the creek samples before the 7am Tuesday routine?",
        "the creek project's nitrate readings",
    ),
    Asked(
        "The jammed printer had paper behind the roller, but what did you check first before you opened it up?",
        "the jammed floor printer",
    ),
    Asked(
        "On a busy night at the fry stand, when the line backed up, what did you do to get it moving again?",
        "the fry stand line at the county fair",
    ),
    Asked(
        "When you split the fry stand line into an order taker and a fryer, who pushed back on it, and what "
        "did they say?",
        "the fry stand line you split in two",
    ),
    Asked(
        "Your mom came around after one night of you running it that way. If a kid at that window watched "
        "the line back up next summer, what would you have them check first?",
        "the fry stand line you split at sixteen",
    ),
    Asked(
        "What did the blank sample catch that the nitrate numbers alone couldn't show you?",
        "the 7am Tuesday sampling routine",
    ),
]
# The thin-answer angle: other ground, and something concrete to stand on.
THIN_ANGLES = [
    Asked(
        "Forget the big picture for a second. What's the last thing somebody asked you for help with, and "
        "what did you do first?",
        "the last time someone asked you for help",
    ),
    Asked(
        "When someone new does this for the first time, what do they usually get wrong?",
        "what people get wrong the first time",
    ),
    Asked(
        "Which repair on your floor has taken you the longest, and what did you try first that didn't work?",
        "the longest repair on your floor",
    ),
]
# More ground for a member who skips a lot, so a skipped question never comes back.
SPARE_QUESTIONS = [
    Asked(
        "How did people on your floor find out you'd fix things, before anyone asked you to?",
        "how people on your floor found you",
    ),
    Asked(
        "When someone on your floor brings you something broken, what do they usually get wrong before they ask you?",
        "what people bring you",
    ),
    Asked(
        "On the creek project, which part of the sampling ended up being yours to handle, and how did that get decided?",
        "your part in the creek project",
    ),
    Asked(
        "What made biology the one you kept coming back to, and was there a point where you almost went another way?",
        "choosing biology",
    ),
    Asked(
        "What was the first thing someone asked you for that you said no to or passed on to someone else?",
        "what you pass on",
    ),
]
LAST_RESORT = Asked(
    "What's one more thing you've worked out that most people haven't?", "what you've worked out"
)

# Paste these, in order, for a book that reads true.
THEO_ANSWERS = [
    "Honestly not a lot yet, I'm just a freshman. I'm probably going into biology, and most of my week is "
    "classes and figuring out the campus. I fix wobbly bed frames and printers on my floor sometimes, which "
    "takes more time than I'd expect.",
    "Honestly it was a pretty basic one. Someone on my floor had a printer that kept jamming and nobody "
    "wanted to deal with it, so they asked around. I opened it up and found a piece of paper stuck behind "
    "the roller, so it was pretty quick. It's not really a big deal.",
    "Honestly not much, I don't think I've really built anything. I guess in high school I did a creek "
    "project for AP Environmental Science, but that was just a class thing.",
    "Honestly it was mostly the bolts on one side. The frame would rock when he moved, so I checked whether "
    "the slats were sitting right first, then tightened the bolts by hand before grabbing anything. It was "
    "pretty simple, nothing special.",
    "Honestly my family has a fry stand at the county fair, and I worked there every summer. I guess I was "
    "the one who always got stuck with the line when it backed up, but that's just what happens when you're "
    "the kid working the fair.",
    "Honestly the first couple months of nitrate readings were pretty useless. We were sampling at different "
    "times of day, and some of the samples were taken right after rain, so the numbers jumped around and "
    "didn't mean much. We changed it so we always went to the same spot at 7am every Tuesday, kept a log of "
    "rain, and ran a blank sample each time.",
    "Honestly the first plan was pretty loose. We were just going out whenever we had a free period or "
    "whenever it seemed like a good day to get water, so the times kept changing. Nobody really thought "
    "about rain until the numbers looked weird.",
    "Honestly I just checked whether the paper tray was seated right and whether there was a jam light on. "
    "Then I opened the back panel and saw the paper. It was pretty quick.",
    "Honestly not a lot at first, I just tried to keep up with whoever was at the window. But when I was "
    "about 16 I noticed the fryer person was stopping every time they had to take an order and make change, "
    "so I changed it so one person walks down the line taking orders and money and writes the order on the "
    "paper boat. Then the fryer only has to cook. Waits went from around 25 minutes to under 10, which was a "
    "big deal for us, but it's not really a big thing.",
    "Honestly I don't think anyone really pushed back that much. My mom was the one running the fryer, and "
    "she was skeptical at first, so I just showed her by doing it for a night. After that she didn't really "
    "argue.",
    "Honestly I'd probably tell them to watch whoever's at the fryer for a few minutes first, to see how "
    "often they stop to take orders or make change. That's usually where the time goes. It's not really a "
    "complicated thing.",
    "Honestly I'm not sure I'd know the technical side well enough to explain it. I think it was supposed "
    "to show whether something was contaminating the samples in the lab or during collection, so we'd know "
    "if a high number was real or just from our process.",
]
THEO_PLAYBACK = (
    "You split the fry stand line at 16 so one person takes orders and money while the fryer only cooks, and "
    "waits went from about 25 minutes to under 10. You also check the bolts and the slats before touching a "
    "tool, and you learned the creek samples only meant something once they moved to a fixed 7am Tuesday with "
    "a rain log."
)
TITLES = [
    {
        "title": "Check the Slats First",
        "why": "You checked whether the slats sat right before grabbing a tool, and tightened the bolts by hand first.",
    },
    {
        "title": "The Fryer Only Cooks",
        "why": "Once order-taking moved down the line, you said waits went from around 25 minutes to under 10.",
    },
    {
        "title": "Stuck With the Line",
        "why": "You were the kid who always got stuck with the line when it backed up at the county fair.",
    },
]
POOL = [
    {
        "title": "Splitting a fry line between two jobs",
        "summary": "I was keeping up with the window until I saw the fryer person stopping to take orders and "
        "make change. I had one person walk the line taking orders and money, writing each on the paper boat, "
        "so the fryer only cooked. Waits went from around 25 minutes to under 10.",
        "quotes": [
            "I noticed the fryer person was stopping every time they had to take an order and make change",
            "Waits went from around 25 minutes to under 10",
        ],
    },
    {
        "title": "Checking the simple things before the tools",
        "summary": "When a bed frame rocked, I checked whether the slats were sitting right, then tightened the "
        "bolts by hand before grabbing a tool. A jammed printer got the same order: tray seated, jam light, "
        "then the back panel.",
        "quotes": [
            "I checked whether the slats were sitting right first, then tightened the bolts by hand before grabbing anything",
            "I just checked whether the paper tray was seated right and whether there was a jam light on",
        ],
    },
    {
        "title": "Why the creek numbers jumped after rain",
        "summary": "The first couple months of nitrate readings were pretty useless, since we sampled at "
        "different times of day and some samples came right after rain. We changed it so we always went to "
        "the same spot at 7am every Tuesday, kept a log of rain, and ran a blank sample each time.",
        "quotes": [
            "We were sampling at different times of day, and some of the samples were taken right after rain, "
            "so the numbers jumped around and didn't mean much",
            "We changed it so we always went to the same spot at 7am every Tuesday, kept a log of rain, and "
            "ran a blank sample each time",
        ],
    },
    {
        "title": "Stuck with the line at the county fair",
        "summary": "My family has a fry stand at the county fair, and I worked there every summer. I was usually "
        "the one who got stuck with the line when it backed up.",
        "quotes": [
            "my family has a fry stand at the county fair, and I worked there every summer",
            "I guess I was the one who always got stuck with the line when it backed up",
        ],
    },
    {
        "title": "Running it one night for my mom",
        "summary": "My mom was running the fryer and was skeptical of the change, so I showed her by doing it for "
        "one night. After that she didn't really argue.",
        "quotes": [
            "My mom was the one running the fryer, and she was skeptical at first, so I just showed her by doing it for a night",
        ],
    },
]
# A rewrite swaps a chapter for this telling; rewriting again swaps it back, so it always visibly changes.
RETOLD = {
    "Splitting a fry line between two jobs": {
        "title": "The fryer kept stopping to make change",
        "summary": "I'd been keeping up with the window until I noticed the fryer stopping to take orders and make "
        "change. So I had one person walk the line taking orders and money, writing each on the paper boat, and "
        "the fryer only had to cook. Waits went from around 25 minutes to under 10.",
    },
    "Checking the simple things before the tools": {
        "title": "Slats and bolts before any tool",
        "summary": "When a bed frame rocked, I checked whether the slats were sitting right, then tightened the "
        "bolts by hand before grabbing a tool. The jammed printer got the same order: tray seated, jam light, then "
        "the back panel, where the paper was.",
    },
    "Why the creek numbers jumped after rain": {
        "title": "Nitrate numbers that jumped after rain",
        "summary": "The first couple months of nitrate readings were pretty useless, since we sampled at different "
        "times of day and some samples came right after rain. We changed it to the same spot at 7am every Tuesday, "
        "kept a log of rain, and ran a blank sample each time.",
    },
    "Stuck with the line at the county fair": {
        "title": "Stuck with the line at the fair",
        "summary": "I worked my family's fry stand at the county fair every summer, and I was usually the one who "
        "got stuck with the line when it backed up.",
    },
    "Running it one night for my mom": {
        "title": "One night to convince the fryer",
        "summary": "The fryer was my mom's, and she was skeptical of the change. I showed her by doing it for one "
        "night, and after that she didn't really argue.",
    },
}
DRAFT_BLURB = (
    "I worked my family's fry stand at the county fair every summer, and I noticed the fryer kept stopping to take "
    "orders. One person walking the line taking orders and money cut waits from around 25 minutes to under 10. On "
    "my floor I fix bed frames and printers, checking the simple things before I reach for a tool. If you're trying "
    "to get a line moving, I can tell you what I'd watch for first."
)
FINISHED_BLURB = (
    "I fix wobbly bed frames and printers on my floor, and I check the simple things before reaching for a tool: "
    "whether the slats sit right, whether the tray is seated, whether the jam light is on. On my family's fry stand "
    "at the county fair, I found that the fryer was where the time went, and splitting order-taking from frying cut "
    "waits from around 25 minutes to under 10. If you're trying to get something moving again and don't know where "
    "to start, I can tell you where I'd look first."
)
REMOVED_BLURB = (
    "Early nitrate readings from a creek jumped around because we sampled at random times, some right after rain. "
    "We settled on 7am Tuesdays at one spot, a rain log, and a blank sample each time. At my family's county fair "
    "fry stand, I was usually stuck with the line until I had one person take orders and money, so the fryer only "
    "cooked, and waits fell from about 25 minutes to under 10. If you're trying to get a line moving, I can tell you "
    "what to watch first."
)

_TURN = re.compile(
    r"^Q\d+ \[(\w+)\]: (.*?)\nA\d+: (.*?)(?=\n+Q\d+ \[|\n*</interview>)", re.DOTALL | re.MULTILINE
)
SKIPPED = "(skipped)"


class ParsedTurn(NamedTuple):
    phase: str
    question: str
    answer: str


def _text_of(content: str | list[dict]) -> str:
    return content if isinstance(content, str) else "".join(block["text"] for block in content)


def _turns(text: str) -> list[ParsedTurn]:
    return [ParsedTurn(*match) for match in _TURN.findall(text)]


def _answers(turns: list[ParsedTurn]) -> list[str]:
    """What the member actually said: no skips, and not their "yes" to the Shape playback."""
    return [turn.answer.strip() for turn in turns if turn.answer != SKIPPED and turn.phase != "shape"]


def _first_sentence(answer: str) -> str:
    return re.split(r"(?<=[.!?])\s+", answer.strip())[0]


def _grounded_chapters(text: str) -> list[dict]:
    """Theo's chapters, with quotes that are verbatim from this member's answers whatever they typed."""
    answers = _answers(_turns(text))
    said = " ".join(answers).casefold()
    chapters = []
    for number, chapter in enumerate(POOL):
        quotes = [quote for quote in chapter["quotes"] if quote.casefold() in said]
        if not quotes and answers:
            quotes = [_first_sentence(answers[number % len(answers)])]
        chapters.append({**chapter, "quotes": quotes})
    return chapters


def _next_question(turns: list[ParsedTurn], thin: bool) -> Asked:
    asked = {turn.question for turn in turns}
    order = (
        [*THIN_ANGLES, *QUESTIONS, *SPARE_QUESTIONS] if thin else [*QUESTIONS, *SPARE_QUESTIONS, *THIN_ANGLES]
    )
    return next((option for option in order if option.question not in asked), LAST_RESORT)


def _plan(phase: str, question: str, topic: str, *, playback: str | None = None, ready: bool = False) -> dict:
    return {
        "threads": [{"thread": topic, "has_moment": False, "missing": "A specific moment."}],
        "phase": phase,
        "question": question,
        "playback": playback,
        "topic": topic,
        "ready_for_reveal": ready,
    }


def _interviewer(text: str) -> dict:
    turns = _turns(text)
    if turns and turns[-1].phase == "shape":
        return _plan("shape", "Thanks, I have enough to start your book.", "your book", ready=True)
    answers = _answers(turns)
    if len(answers) >= SHAPE_AFTER_ANSWERS:
        if "fry stand" in " ".join(answers).casefold():
            playback = THEO_PLAYBACK
        else:
            longest = sorted(answers, key=len, reverse=True)[:2]
            playback = "You told me: " + " ".join(_first_sentence(answer) for answer in longest)
        return _plan("shape", "Is this you?", "what you've told me so far", playback=playback)
    # Answers ran thin, or the member is skipping: the next question comes from other ground.
    thin = "Answers are running thin" in text
    question, topic = _next_question(turns, thin)
    return _plan("sweep" if len(turns) < SWEEP_QUESTIONS else "dig", question, topic)


def _draft(text: str) -> dict:
    return {"pool": _grounded_chapters(text), "titles": TITLES, "blurb": DRAFT_BLURB}


def _finish(text: str) -> dict:
    pool = json.loads(re.search(r"<pool>\n(.*?)\n</pool>", text, re.DOTALL).group(1))
    chapters = [{"pool_id": c["pool_id"], "title": c["title"], "summary": c["summary"]} for c in pool[:4]]
    return {"chapters": chapters, "blurb": FINISHED_BLURB}


def _book_chapters(text: str) -> list[dict]:
    return json.loads(re.search(r"<book_chapters>\n(.*?)\n</book_chapters>", text, re.DOTALL).group(1))


def _blurb(_text: str) -> dict:
    return {"blurb": REMOVED_BLURB}


def _rewrite(text: str) -> dict:
    chapter = next(c for c in _book_chapters(text) if c["rewrite_this"])
    if retold := RETOLD.get(chapter["title"]):
        return retold
    for original, telling in RETOLD.items():
        if telling["title"] == chapter["title"]:
            return next(
                {"title": c["title"], "summary": c["summary"]} for c in POOL if c["title"] == original
            )
    return {"title": f"{chapter['title']}, retold", "summary": chapter["summary"]}


REPLIES = {
    "interview/interviewer": _interviewer,
    "interview/draft": _draft,
    "interview/finish": _finish,
    "interview/blurb": _blurb,
    "interview/rewrite": _rewrite,
}


class ScriptedClaude:
    def __init__(self, delay_seconds: float = 0, model: str = "scripted"):
        self.model = model
        self.delay_seconds = delay_seconds

    async def create(self, **params) -> BetaMessage:
        name = prompt_name(params.get("system"))
        if name not in REPLIES:
            raise ValueError(f"The scripted AI has no reply for the prompt {name!r}.")
        slower = 1 if name == "interview/interviewer" else BOOK_STEP_SLOWER
        await asyncio.sleep(self.delay_seconds * slower)
        reply = REPLIES[name](_text_of(params["messages"][-1]["content"]))
        return BetaMessage(
            id=f"msg_scripted_{uuid4().hex}",
            type="message",
            role="assistant",
            model=self.model,
            content=[BetaTextBlock(type="text", text=json.dumps(reply))],
            stop_reason="end_turn",
            stop_sequence=None,
            usage=BetaUsage(input_tokens=0, output_tokens=0),
        )
