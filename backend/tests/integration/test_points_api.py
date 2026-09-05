"""Integration scenarios for point persistence and transactions."""

import asyncio
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from piecewise_linear.db.repository import PointRepository

pytestmark = pytest.mark.integration


async def create(client: AsyncClient, x: float, y: float) -> dict[str, object]:
    """Create a point and return its decoded response."""
    response = await client.post("/api/v1/points", json={"x": x, "y": y})
    assert response.status_code == 201
    return response.json()


async def test_crud_validation_and_delete(client: AsyncClient) -> None:
    """Persist valid CRUD changes and reject invalid coordinates."""
    assert (await client.get("/api/v1/points")).json() == []
    first = await create(client, -1.5, 2)
    second = await create(client, 3, 4)
    assert first == {"id": 1, "x": -1.5, "y": 2.0}
    assert second == {"id": 2, "x": 3.0, "y": 4.0}

    updated = await client.patch("/api/v1/points/1", json={"y": 7.5})
    invalid = await client.post("/api/v1/points", json={"x": "NaN", "y": 1})
    missing = await client.patch("/api/v1/points/99", json={"x": 1})
    deleted = await client.delete("/api/v1/points/1")

    assert updated.status_code == 200
    assert updated.json() == {"id": 1, "x": -1.5, "y": 7.5}
    assert invalid.status_code == 422
    assert missing.status_code == 404
    assert deleted.status_code == 200
    assert deleted.json() == [{"id": 2, "x": 3.0, "y": 4.0}]


async def test_reorder_renumbers_and_rejects_stale_set(client: AsyncClient) -> None:
    """Renumber a full permutation and leave a stale request unchanged."""
    await create(client, 10, 11)
    await create(client, 20, 21)
    await create(client, 30, 31)

    reordered = await client.put("/api/v1/points/order", json={"ids": [3, 1, 2]})
    assert reordered.status_code == 200
    assert reordered.json() == [
        {"id": 1, "x": 30.0, "y": 31.0},
        {"id": 2, "x": 10.0, "y": 11.0},
        {"id": 3, "x": 20.0, "y": 21.0},
    ]

    await create(client, 40, 41)
    stale = await client.put("/api/v1/points/order", json={"ids": [3, 2, 1]})
    current = await client.get("/api/v1/points")
    assert stale.status_code == 409
    assert current.json() == [
        {"id": 1, "x": 30.0, "y": 31.0},
        {"id": 2, "x": 10.0, "y": 11.0},
        {"id": 3, "x": 20.0, "y": 21.0},
        {"id": 4, "x": 40.0, "y": 41.0},
    ]


async def test_concurrent_creates_receive_unique_identifiers(client: AsyncClient) -> None:
    """Serialize concurrent appends through the table lock."""
    responses = await asyncio.gather(
        client.post("/api/v1/points", json={"x": 1, "y": 1}),
        client.post("/api/v1/points", json={"x": 2, "y": 2}),
    )

    assert [response.status_code for response in responses] == [201, 201]
    points = (await client.get("/api/v1/points")).json()
    assert [point["id"] for point in points] == [1, 2]
    assert {(point["x"], point["y"]) for point in points} == {(1.0, 1.0), (2.0, 2.0)}


async def test_reorder_rolls_back_after_replacement_failure(client: AsyncClient) -> None:
    """Restore deleted rows when replacement insertion fails."""
    await create(client, 1, 2)
    await create(client, 3, 4)
    original = (await client.get("/api/v1/points")).json()

    with patch.object(PointRepository, "add_many", side_effect=RuntimeError("injected")):
        failed = await client.put("/api/v1/points/order", json={"ids": [2, 1]})

    current = await client.get("/api/v1/points")
    assert failed.status_code == 500
    assert current.json() == original
