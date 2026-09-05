"""Unit tests for public validation schemas."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from piecewise_linear.api.schemas import PointCreate, PointOrder, PointRead, PointUpdate


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), "bad", None])
def test_point_create_rejects_invalid_coordinates(value: object) -> None:
    """Reject non-finite and non-numeric coordinate values."""
    with pytest.raises(ValidationError):
        PointCreate.model_validate({"x": value, "y": 1})


@pytest.mark.parametrize("payload", [{}, {"x": None}, {"y": None}, {"x": 1, "y": None}])
def test_point_update_requires_supplied_finite_coordinates(payload: dict[str, object]) -> None:
    """Reject empty updates and explicit nulls."""
    with pytest.raises(ValidationError, match="At least one finite coordinate is required"):
        PointUpdate.model_validate(payload)


def test_point_update_accepts_each_coordinate_independently() -> None:
    """Keep omitted coordinates distinct from supplied values."""
    expected_x = -2.5
    update = PointUpdate.model_validate({"x": expected_x})

    assert update.x == expected_x
    assert update.y is None
    assert update.model_fields_set == {"x"}


@pytest.mark.parametrize("ids", [[0], [-1], [1, 0]])
def test_point_order_requires_positive_identifiers(ids: list[int]) -> None:
    """Reject identifiers outside the persisted domain."""
    with pytest.raises(ValidationError):
        PointOrder(ids=ids)


def test_point_read_supports_model_attributes() -> None:
    """Create response data from an object with model attributes."""
    response = PointRead.model_validate(SimpleNamespace(id=2, x=1.25, y=-4.0))

    assert response.model_dump() == {"id": 2, "x": 1.25, "y": -4.0}
