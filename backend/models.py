"""Pydantic defines what a valid profile looks like."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator


# Names and labels must be actual strings and cannot be empty or just spaces.
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
OptionalText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)]
MemberRole = Literal["student", "alumni"]
Availability = Literal["available", "limited", "unavailable"]
MeetingPreference = Literal["remote", "in_person", "either"]


class Profile(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra="forbid",
        json_schema_extra={
            "examples": [{
                "name": "Alex Morgan (fictional)",
                "affiliation": "CWRU alumni",
                "location": "Cleveland, Ohio",
                "expertise": ["Software engineering", "Startup mentoring"],
                "interests": ["Healthcare technology", "Entrepreneurship"],
                "role": "alumni",
                "industry": "Software",
                "background": "Engineering leader and startup mentor.",
                "help_offered": ["Technical strategy", "Startup mentoring"],
                "help_needed": [],
                "availability": "available",
                "meeting_preference": "either",
                "graduation_year": 2012,
            }]
        },
    )

    name: NonEmptyText
    affiliation: NonEmptyText
    location: NonEmptyText
    expertise: list[NonEmptyText]
    interests: list[NonEmptyText]
    # Defaults keep profiles created before matching was introduced readable.
    role: MemberRole = "alumni"
    industry: OptionalText = ""
    background: OptionalText = ""
    help_offered: list[NonEmptyText] = Field(default_factory=list)
    help_needed: list[NonEmptyText] = Field(default_factory=list)
    availability: Availability = "available"
    meeting_preference: MeetingPreference = "either"
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)


class SavedProfile(Profile):
    """A saved profile includes the ID used to retrieve, edit, or delete it."""

    id: NonEmptyText
    model_config = ConfigDict(json_schema_extra={"examples": [{
        "id": "sample-alex",
        "name": "Alex Morgan (fictional)",
        "affiliation": "CWRU alumni",
        "location": "Cleveland, Ohio",
        "expertise": ["Software engineering", "Startup mentoring"],
        "interests": ["Healthcare technology", "Entrepreneurship"],
        "role": "alumni",
        "industry": "Software",
        "background": "Engineering leader and startup mentor.",
        "help_offered": ["Technical strategy", "Startup mentoring"],
        "help_needed": [],
        "availability": "available",
        "meeting_preference": "either",
        "graduation_year": 2012,
    }]})


class ProfileUpdate(BaseModel):
    """Only supplied fields change; empty lists clear tags, but null is invalid."""

    model_config = ConfigDict(
        strict=True, extra="forbid",
        json_schema_extra={"examples": [{"location": "Boston, Massachusetts"}]},
    )

    name: NonEmptyText | None = None
    affiliation: NonEmptyText | None = None
    location: NonEmptyText | None = None
    expertise: list[NonEmptyText] | None = None
    interests: list[NonEmptyText] | None = None
    role: MemberRole | None = None
    industry: OptionalText | None = None
    background: OptionalText | None = None
    help_offered: list[NonEmptyText] | None = None
    help_needed: list[NonEmptyText] | None = None
    availability: Availability | None = None
    meeting_preference: MeetingPreference | None = None
    graduation_year: int | None = Field(default=None, ge=1900, le=2100)

    @field_validator(
        "name", "affiliation", "location", "expertise", "interests", "role",
        "industry", "background", "help_offered", "help_needed", "availability",
        "meeting_preference",
    )
    @classmethod
    def reject_null(cls, value):
        # Validators run for supplied fields; omitted fields are left unchanged.
        if value is None:
            raise ValueError("Omit a field to leave it unchanged; null is not allowed.")
        return value

    @model_validator(mode="after")
    def require_changes(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        return self
