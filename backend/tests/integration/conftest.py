"""PostgreSQL and HTTP fixtures for integration tests."""

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from piecewise_linear.core.settings import Settings
from piecewise_linear.main import create_app


def require_database_url() -> str:
    """Return the explicitly configured integration database URL."""
    database_url = os.getenv("TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("TEST_DATABASE_URL is required for integration tests")
    return database_url


@pytest_asyncio.fixture(autouse=True)
async def clean_database() -> AsyncIterator[None]:
    """Truncate points before and after each integration scenario."""
    engine = create_async_engine(require_database_url())
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE points"))
    yield
    async with engine.begin() as connection:
        await connection.execute(text("TRUNCATE TABLE points"))
    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Expose the FastAPI application through an in-process HTTP client."""
    settings = Settings(DATABASE_URL=require_database_url())
    app = create_app(settings)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
