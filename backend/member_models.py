"""Shapes for onboarding data: the basics form, open-ended facts, and interview state."""

import re
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator,
)

from models import NonEmptyText

Role = Literal["student", "alum", "faculty", "staff", "other"]
# What the member wants from the network; drives which interview areas matter most.
Seeking = Literal["get_help", "give_help", "both"]
FactKind = Literal[
    "need", "offer", "experience", "background", "goal", "preference", "availability", "other",
]
Visibility = Literal["public", "matches_only", "private"]
FactSource = Literal["basics_form", "interview", "member_edit", "resume"]

ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
FactText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=400)]

LINK_KEY = re.compile(r"^[a-z][a-z0-9-]{0,30}:[a-z0-9][a-z0-9-]{0,80}$")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-")


def normalize_link_key(value: str) -> str:
    """Turn 'High School: St. Ignatius' into 'high-school:st-ignatius'."""
    kind, separator, rest = value.partition(":")
    key = f"{slug(kind)}:{slug(rest)}"
    if not separator or not LINK_KEY.match(key):
        raise ValueError("Link keys look like 'sport:swimming' or 'high-school:saint-ignatius-cleveland-oh'.")
    return key


def clean_link_keys(values: list[str]) -> list[str]:
    # Normalize, then drop repeats while keeping the order the AI gave.
    return list(dict.fromkeys(normalize_link_key(value) for value in values))


class BasicsForm(BaseModel):
    """The 30-second form before the AI interview: just what hard filters need."""

    model_config = ConfigDict(strict=True, extra="forbid", json_schema_extra={"examples": [{
        "role": "student", "school": "Case School of Engineering", "grad_year": 2027,
        "majors": ["Biomedical Engineering"], "seeking": "both", "location": "Cleveland, Ohio",
    }]})

    role: Role
    school: ShortText
    grad_year: int | None = Field(default=None, ge=1940, le=2040)
    majors: list[ShortText] = Field(default_factory=list, max_length=4)
    seeking: Seeking
    location: ShortText

    @model_validator(mode="after")
    def students_and_alumni_need_a_year(self) -> Self:
        if self.role in ("student", "alum") and self.grad_year is None:
            raise ValueError("Students and alumni need a graduation year.")
        return self


class FactDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: ShortText
    value: ShortText


class FactDraft(BaseModel):
    """A fact as the AI proposes it, before the server adds ownership and timestamps."""

    model_config = ConfigDict(extra="forbid")

    kind: FactKind
    topic: ShortText
    text: FactText
    detail: list[FactDetail] = Field(default_factory=list, max_length=8)
    links: list[str] = Field(default_factory=list, max_length=8)
    strength: int | None = Field(default=None, ge=1, le=3)
    visibility: Visibility
    confidence: float = Field(ge=0, le=1)

    @field_validator("links")
    @classmethod
    def normalize_links(cls, values: list[str]) -> list[str]:
        return clean_link_keys(values)


class FactRevision(BaseModel):
    """Changes the AI makes to a fact it saved earlier; null means unchanged."""

    model_config = ConfigDict(extra="forbid")

    fact_id: NonEmptyText
    topic: ShortText | None = None
    text: FactText | None = None
    detail: list[FactDetail] | None = Field(default=None, max_length=8)
    links: list[str] | None = Field(default=None, max_length=8)
    strength: int | None = Field(default=None, ge=1, le=3)
    visibility: Visibility | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)

    @field_validator("links")
    @classmethod
    def normalize_links(cls, values: list[str] | None) -> list[str] | None:
        return None if values is None else clean_link_keys(values)


class FactEdit(BaseModel):
    """What a member can change from the 'What we've learned' panel."""

    model_config = ConfigDict(strict=True, extra="forbid", json_schema_extra={"examples": [
        {"visibility": "private"}, {"text": "Wants help preparing a seed-round pitch", "confirmed": True},
    ]})

    text: FactText | None = None
    visibility: Visibility | None = None
    confirmed: Literal[True] | None = None

    @model_validator(mode="after")
    def require_changes(self) -> Self:
        if not {name for name in self.model_fields_set if getattr(self, name) is not None}:
            raise ValueError("Provide text, visibility, or confirmed: true.")
        return self


class FactOut(BaseModel):
    id: str
    kind: FactKind
    topic: str
    text: str
    detail: list[FactDetail]
    links: list[str]
    strength: int | None
    visibility: Visibility
    confirmed: bool
    confidence: float
    source: FactSource
    created_at: datetime
    updated_at: datetime


class SharedFact(BaseModel):
    """A fact as another member may see it: no confidence, source, or confirmation state."""

    id: str
    kind: FactKind
    topic: str
    text: str
    links: list[str]


AreaStatus = Literal["missing", "started", "good"]
Area = Literal["needs", "offers", "style", "background", "goals"]
AREA_ORDER: tuple[Area, ...] = ("needs", "offers", "style", "background", "goals")


class AreaCoverage(BaseModel):
    area: Area
    label: str
    status: AreaStatus
    important: bool  # False when this member's goals make the area optional


class Coverage(BaseModel):
    percent: int
    areas: list[AreaCoverage]


class NextQuestion(BaseModel):
    """The AI's next question, as it writes it (validated before the member sees it)."""

    area: Area
    prompt: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=300)]
    choices: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]] = Field(
        default_factory=list,
    )
    multiple: bool = False
    placeholder: Annotated[str, StringConstraints(strip_whitespace=True, max_length=120)] = ""
    done: bool = False

    @field_validator("choices")
    @classmethod
    def at_most_six_distinct(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))[:6]


class Question(BaseModel):
    id: str
    area: Area
    prompt: str
    choices: list[str]
    multiple: bool
    placeholder: str


class InterviewState(BaseModel):
    session_id: str
    status: Literal["active", "finished"]
    question: Question | None
    done: bool  # the AI judges the profile ready; the member may keep going
    answered: int
    added: list[str]  # ids of facts saved or changed by the last answer
    notice: str | None = None


class InterviewTurn(BaseModel):
    """Everything the interview screen needs after each answer."""

    interview: InterviewState
    facts: list[FactOut]
    coverage: Coverage


class MemberAnswer(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", json_schema_extra={"examples": [{
        "question_id": "q-3f2a", "choices": ["Pitch deck"], "text": "Demo day is in December.",
    }, {"question_id": "q-3f2a", "skipped": True}]})

    question_id: NonEmptyText
    choices: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]] = Field(
        default_factory=list, max_length=6,
    )
    text: Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)] = ""
    skipped: bool = False

    @model_validator(mode="after")
    def answer_or_skip(self) -> Self:
        if not self.skipped and not self.choices and not self.text:
            raise ValueError("Pick an answer, type one, or skip the question.")
        return self


class OnboardingStatus(BaseModel):
    basics_done: bool
    basics: BasicsForm | None
    open_interview_id: str | None
    coverage: Coverage
