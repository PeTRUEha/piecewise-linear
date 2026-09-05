"""HTTP routes for point management."""

from fastapi import APIRouter, status

from piecewise_linear.api.dependencies import PointServiceDependency
from piecewise_linear.api.schemas import ErrorRead, PointCreate, PointOrder, PointRead, PointUpdate

router = APIRouter(prefix="/points", tags=["points"])


@router.get("")
async def list_points(service: PointServiceDependency) -> list[PointRead]:
    """Return all saved points in identifier order."""
    return [PointRead.model_validate(point) for point in await service.list_points()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_point(payload: PointCreate, service: PointServiceDependency) -> PointRead:
    """Append a point to the ordered set."""
    point = await service.create_point(x=payload.x, y=payload.y)
    return PointRead.model_validate(point)


@router.put(
    "/order",
    responses={status.HTTP_409_CONFLICT: {"model": ErrorRead}},
)
async def reorder_points(payload: PointOrder, service: PointServiceDependency) -> list[PointRead]:
    """Persist a complete point order and return sequential identifiers."""
    points = await service.reorder_points(payload.ids)
    return [PointRead.model_validate(point) for point in points]


@router.patch(
    "/{point_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorRead}},
)
async def update_point(
    point_id: int,
    payload: PointUpdate,
    service: PointServiceDependency,
) -> PointRead:
    """Update one or both coordinates of an existing point."""
    point = await service.update_point(point_id, x=payload.x, y=payload.y)
    return PointRead.model_validate(point)


@router.delete(
    "/{point_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorRead}},
)
async def delete_point(point_id: int, service: PointServiceDependency) -> list[PointRead]:
    """Delete a point and return the remaining ordered set."""
    points = await service.delete_point(point_id)
    return [PointRead.model_validate(point) for point in points]
