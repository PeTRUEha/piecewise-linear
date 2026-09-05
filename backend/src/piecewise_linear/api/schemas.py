"""Validated HTTP request and response schemas."""

from typing import Self

from pydantic import BaseModel, ConfigDict, FiniteFloat, PositiveInt, model_validator


class PointCreate(BaseModel):
    """Coordinates required to append a point."""

    x: FiniteFloat
    y: FiniteFloat


class PointUpdate(BaseModel):
    """One or both coordinates supplied for an update."""

    x: FiniteFloat | None = None
    y: FiniteFloat | None = None

    @model_validator(mode="after")
    def validate_coordinates(self) -> Self:
        """Reject empty updates and explicit null coordinate values."""
        if not self.model_fields_set or any(
            getattr(self, field_name) is None for field_name in self.model_fields_set
        ):
            msg = "At least one finite coordinate is required"
            raise ValueError(msg)
        return self


class PointOrder(BaseModel):
    """The complete ordered collection of current point identifiers."""

    ids: list[PositiveInt]


class PointRead(BaseModel):
    """A point returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: PositiveInt
    x: FiniteFloat
    y: FiniteFloat


class HealthRead(BaseModel):
    """Health endpoint response."""

    status: str


class ErrorRead(BaseModel):
    """Public error response."""

    detail: str
