"""Transactional service operations for ordered points."""

from collections.abc import Sequence
from typing import cast

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from piecewise_linear.db.errors import PointNotFoundError, PointOrderConflictError
from piecewise_linear.db.models import Point
from piecewise_linear.db.repository import PointRepository

_LOCK_POINTS = text("LOCK TABLE points IN EXCLUSIVE MODE")


class PointService:
    """Coordinate point persistence within explicit transactions."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the service to a request-scoped session."""
        self.session = session
        self.repository = PointRepository(session=session)

    async def list_points(self) -> list[Point]:
        """Return all points in identifier order."""
        return await self.repository.get_many(order_by=Point.id.asc())

    async def create_point(self, *, x: float, y: float) -> Point:
        """Append a point using the next available identifier."""
        async with self.session.begin():
            await self.session.execute(_LOCK_POINTS)
            next_id = cast(
                "int",
                await self.session.scalar(select(func.coalesce(func.max(Point.id), 0) + 1)),
            )
            return await self.repository.add(Point(id=next_id, x=x, y=y))

    async def update_point(self, point_id: int, *, x: float | None, y: float | None) -> Point:
        """Update the supplied coordinates of one existing point."""
        async with self.session.begin():
            await self.session.execute(_LOCK_POINTS)
            point = await self.repository.get_one_or_none(id=point_id, with_for_update=True)
            if point is None:
                raise PointNotFoundError(point_id)
            if x is not None:
                point.x = x
            if y is not None:
                point.y = y
            await self.session.flush()
            return point

    async def delete_point(self, point_id: int) -> list[Point]:
        """Delete one point and return the remaining ordered set."""
        async with self.session.begin():
            await self.session.execute(_LOCK_POINTS)
            point = await self.repository.get_one_or_none(id=point_id, with_for_update=True)
            if point is None:
                raise PointNotFoundError(point_id)
            await self.session.delete(point)
            await self.session.flush()
            return await self.list_points()

    async def reorder_points(self, point_ids: Sequence[int]) -> list[Point]:
        """Replace the complete set with sequential identifiers in requested order."""
        async with self.session.begin():
            await self.session.execute(_LOCK_POINTS)
            stored_points = await self.list_points()
            stored_by_id = {point.id: point for point in stored_points}
            if len(point_ids) != len(stored_points) or set(point_ids) != set(stored_by_id):
                raise PointOrderConflictError

            reordered = [stored_by_id[point_id] for point_id in point_ids]
            await self.session.execute(delete(Point))
            replacement = [
                Point(id=index, x=point.x, y=point.y)
                for index, point in enumerate(reordered, start=1)
            ]
            if replacement:
                await self.repository.add_many(replacement)
            return replacement
