"""Asynchronous database configuration and request dependency."""

from typing import Annotated

from advanced_alchemy.config import AsyncSessionConfig
from advanced_alchemy.extensions.fastapi import SQLAlchemyAsyncConfig
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


def create_database_config(database_url: str) -> SQLAlchemyAsyncConfig:
    """Build the asynchronous database configuration for an application."""
    return SQLAlchemyAsyncConfig(
        connection_string=database_url,
        session_config=AsyncSessionConfig(expire_on_commit=False),
        create_all=False,
        commit_mode="manual",
    )


def provide_session(request: Request) -> AsyncSession:
    """Return the request-scoped asynchronous database session."""
    return request.app.state.advanced_alchemy.get_async_session(request)


SessionDependency = Annotated[AsyncSession, Depends(provide_session)]
