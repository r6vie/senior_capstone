"""Pydantic building blocks shared by every feature's request and response models."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RequestBody(BaseModel):
    """Base class for request bodies: reject unknown fields and wrong types instead of guessing."""

    model_config = ConfigDict(strict=True, extra="forbid")
