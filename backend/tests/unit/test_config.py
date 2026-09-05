"""Unit tests for dependency and database configuration helpers."""

from typing import cast
from unittest.mock import MagicMock, patch

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from piecewise_linear.api.dependencies import provide_point_service
from piecewise_linear.db.config import create_database_config, provide_session


def test_database_config_uses_manual_transactions() -> None:
    """Build an async configuration without implicit schema creation."""
    url = "postgresql+asyncpg://user:pass@localhost/database"

    config = create_database_config(url)

    assert config.connection_string == url
    assert config.create_all is False
    assert config.commit_mode == "manual"
    assert config.session_config.expire_on_commit is False


def test_dependency_helpers_use_request_session() -> None:
    """Resolve the request session and bind it to a point service."""
    session = MagicMock(spec=AsyncSession)
    request = MagicMock(spec=Request)
    request.app.state.advanced_alchemy.get_async_session.return_value = session

    resolved = provide_session(cast("Request", request))
    with patch("piecewise_linear.api.dependencies.PointService") as service_type:
        service = provide_point_service(cast("AsyncSession", session))

    assert resolved is session
    assert service is service_type.return_value
    service_type.assert_called_once_with(session)
