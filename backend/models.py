"""Pydantic defines what a valid profile looks like."""

from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator


# Names and labels must be actual strings and cannot be empty or just spaces.
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


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
            }]
        },
    )

    name: NonEmptyText
    affiliation: NonEmptyText
    location: NonEmptyText
    expertise: list[NonEmptyText]
    interests: list[NonEmptyText]


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

    @field_validator("name", "affiliation", "location", "expertise", "interests")
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
