"""Placeholder for the interview engine, which Trove AI owns. Its version replaces this file wholesale.

Only the interface agreed for T7 is defined here, so the routes can be built and tested against it.
"""

from typing import Literal

from pydantic import BaseModel

from trove.ai.client import Claude

Phase = Literal["sweep", "dig", "shape"]


class Turn(BaseModel):
    question: str
    answer: str
    phase: Phase


class NextTurn(BaseModel):
    question: str
    phase: Phase
    playback: str | None
    ready_for_reveal: bool
    topic: str


class DraftChapter(BaseModel):
    id: str
    title: str
    summary: str
    quotes: list[str]


class TitleOption(BaseModel):
    title: str
    why: str


class Draft(BaseModel):
    pool: list[DraftChapter]
    titles: list[TitleOption]


async def next_turn(claude: Claude, *, turns: list[Turn], resume_text: str | None) -> NextTurn:
    raise NotImplementedError


async def draft_book(claude: Claude, *, turns: list[Turn]) -> Draft:
    raise NotImplementedError


async def finish_book(claude: Claude, *, turns: list[Turn], draft: Draft, title: str) -> list[DraftChapter]:
    raise NotImplementedError


async def rewrite_chapter(
    claude: Claude, *, turns: list[Turn], chapters: list[DraftChapter], chapter_id: str
) -> DraftChapter:
    raise NotImplementedError
