"""Unit tests for route adapters and application handlers."""

from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from piecewise_linear.api.health import live, ready
from piecewise_linear.api.points import (
    create_point,
    delete_point,
    list_points,
    reorder_points,
    update_point,
)
from piecewise_linear.api.schemas import PointCreate, PointOrder, PointUpdate
from piecewise_linear.core.settings import Settings
from piecewise_linear.db.errors import PointNotFoundError, PointOrderConflictError
from piecewise_linear.db.models import Point
from piecewise_linear.db.service import PointService
from piecewise_linear.main import create_app, handle_point_not_found, handle_point_order_conflict


def make_service() -> MagicMock:
    """Create an asynchronous service double for route tests."""
    service = MagicMock(spec=PointService)
    service.list_points = AsyncMock()
    service.create_point = AsyncMock()
    service.update_point = AsyncMock()
    service.delete_point = AsyncMock()
    service.reorder_points = AsyncMock()
    return service


async def test_point_routes_map_payloads_and_models() -> None:
    """Convert route payloads to service calls and response schemas."""
    service = make_service()
    service.list_points.return_value = [Point(id=1, x=1, y=2)]
    service.create_point.return_value = Point(id=2, x=3, y=4)
    service.update_point.return_value = Point(id=1, x=5, y=2)
    service.delete_point.return_value = [Point(id=1, x=5, y=2)]
    service.reorder_points.return_value = [Point(id=1, x=3, y=4), Point(id=2, x=5, y=2)]
    typed_service = cast("PointService", service)

    listed = await list_points(typed_service)
    created = await create_point(PointCreate(x=3, y=4), typed_service)
    updated = await update_point(1, PointUpdate(x=5), typed_service)
    deleted = await delete_point(2, typed_service)
    reordered = await reorder_points(PointOrder(ids=[2, 1]), typed_service)

    assert [point.model_dump() for point in listed] == [{"id": 1, "x": 1.0, "y": 2.0}]
    assert created.model_dump() == {"id": 2, "x": 3.0, "y": 4.0}
    expected_x = 5
    assert updated.x == expected_x
    assert [point.id for point in deleted] == [1]
    assert [point.x for point in reordered] == [3, 5]
    service.update_point.assert_awaited_once_with(1, x=5.0, y=None)
    service.reorder_points.assert_awaited_once_with([2, 1])


async def test_health_routes_report_database_state() -> None:
    """Keep liveness independent and readiness dependent on the session."""
    session = MagicMock(spec=AsyncSession)
    session.execute = AsyncMock()

    assert (await live()).status == "ok"
    assert (await ready(cast("AsyncSession", session))).status == "ok"
    session.execute.side_effect = SQLAlchemyError("offline")
    with pytest.raises(HTTPException) as caught:
        await ready(cast("AsyncSession", session))
    assert caught.value.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert caught.value.detail == "Database is unavailable"


async def test_domain_handlers_return_public_errors() -> None:
    """Translate domain errors to stable status and response bodies."""
    not_found = await handle_point_not_found(MagicMock(), PointNotFoundError(9))
    conflict = await handle_point_order_conflict(MagicMock(), PointOrderConflictError())

    assert not_found.status_code == status.HTTP_404_NOT_FOUND
    assert not_found.body == b'{"detail":"Point not found"}'
    assert conflict.status_code == status.HTTP_409_CONFLICT
    assert conflict.body == b'{"detail":"Point set has changed"}'


def test_application_factory_registers_public_contract() -> None:
    """Create an application with the configured title and routes."""
    settings = Settings(
        app_name="Unit Test API",
        DATABASE_URL="postgresql+asyncpg://test:test@localhost/test",
    )

    app = create_app(settings)
    paths = set(app.openapi()["paths"])

    assert app.title == "Unit Test API"
    assert app.state.settings is settings
    assert {"/api/v1/points", "/api/v1/health/live", "/api/v1/health/ready"} <= paths
