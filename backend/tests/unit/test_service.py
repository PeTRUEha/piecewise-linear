"""Unit tests for transactional point service behavior."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from piecewise_linear.db.errors import PointNotFoundError, PointOrderConflictError
from piecewise_linear.db.models import Point
from piecewise_linear.db.repository import PointRepository
from piecewise_linear.db.service import PointService


def make_service() -> tuple[PointService, MagicMock, MagicMock]:
    """Create a service with isolated asynchronous collaborators."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    session.flush = AsyncMock()
    session.delete = AsyncMock()
    repository = MagicMock(spec=PointRepository)
    repository.get_many = AsyncMock()
    repository.add = AsyncMock()
    repository.add_many = AsyncMock()
    repository.get_one_or_none = AsyncMock()
    service = object.__new__(PointService)
    service.session = cast("AsyncSession", session)
    service.repository = cast("PointRepository", repository)
    return service, session, repository


async def test_list_points_orders_by_identifier() -> None:
    """Ask the repository for points in ascending identifier order."""
    service, _session, repository = make_service()
    points = [Point(id=1, x=2, y=3)]
    repository.get_many.return_value = points

    result = await service.list_points()

    assert result == points
    order_by = repository.get_many.await_args.kwargs["order_by"]
    assert str(order_by) == "points.id ASC"


async def test_create_point_uses_next_identifier() -> None:
    """Append a point after the current maximum identifier."""
    service, session, repository = make_service()
    created = Point(id=4, x=1.5, y=-2)
    session.scalar.return_value = 4
    repository.add.return_value = created

    result = await service.create_point(x=1.5, y=-2)

    assert result is created
    repository.add.assert_awaited_once()
    added = repository.add.await_args.args[0]
    assert (added.id, added.x, added.y) == (4, 1.5, -2)
    session.execute.assert_awaited_once()


async def test_update_point_changes_only_supplied_coordinate() -> None:
    """Preserve an omitted coordinate while updating another."""
    service, session, repository = make_service()
    point = Point(id=1, x=2, y=3)
    repository.get_one_or_none.return_value = point

    result = await service.update_point(1, x=None, y=8)

    assert result is point
    assert (point.x, point.y) == (2, 8)
    repository.get_one_or_none.assert_awaited_once_with(id=1, with_for_update=True)
    session.flush.assert_awaited_once()


async def test_update_point_rejects_missing_point() -> None:
    """Raise a domain error when an update target is absent."""
    service, session, repository = make_service()
    repository.get_one_or_none.return_value = None

    with pytest.raises(PointNotFoundError):
        await service.update_point(9, x=1, y=None)

    session.flush.assert_not_awaited()


async def test_delete_point_returns_remaining_order() -> None:
    """Delete the locked target and load the remaining points."""
    service, session, repository = make_service()
    deleted = Point(id=2, x=2, y=2)
    remaining = [Point(id=1, x=1, y=1)]
    repository.get_one_or_none.return_value = deleted
    repository.get_many.return_value = remaining

    result = await service.delete_point(2)

    assert result == remaining
    session.delete.assert_awaited_once_with(deleted)
    session.flush.assert_awaited_once()


async def test_delete_point_rejects_missing_point() -> None:
    """Raise a domain error when a delete target is absent."""
    service, session, repository = make_service()
    repository.get_one_or_none.return_value = None

    with pytest.raises(PointNotFoundError):
        await service.delete_point(7)

    session.delete.assert_not_awaited()


async def test_reorder_points_rebuilds_sequential_identifiers() -> None:
    """Rebuild coordinates in requested order with compact identifiers."""
    service, session, repository = make_service()
    repository.get_many.return_value = [
        Point(id=1, x=10, y=11),
        Point(id=2, x=20, y=21),
        Point(id=3, x=30, y=31),
    ]

    result = await service.reorder_points([3, 1, 2])

    assert [(point.id, point.x, point.y) for point in result] == [
        (1, 30, 31),
        (2, 10, 11),
        (3, 20, 21),
    ]
    repository.add_many.assert_awaited_once_with(result)
    expected_execute_count = 2
    assert session.execute.await_count == expected_execute_count


@pytest.mark.parametrize("point_ids", [[1], [1, 1], [1, 3]])
async def test_reorder_points_rejects_incomplete_permutation(point_ids: list[int]) -> None:
    """Reject a stale, duplicate, or incomplete identifier set."""
    service, _session, repository = make_service()
    repository.get_many.return_value = [Point(id=1, x=1, y=1), Point(id=2, x=2, y=2)]

    with pytest.raises(PointOrderConflictError):
        await service.reorder_points(point_ids)

    repository.add_many.assert_not_awaited()


async def test_reorder_empty_collection_skips_insert() -> None:
    """Keep an empty collection empty without a bulk insert."""
    service, _session, repository = make_service()
    repository.get_many.return_value = []

    result = await service.reorder_points([])

    assert result == []
    repository.add_many.assert_not_awaited()
