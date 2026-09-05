"""Process liveness and database readiness routes."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from piecewise_linear.api.schemas import ErrorRead, HealthRead
from piecewise_linear.db.config import SessionDependency

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> HealthRead:
    """Report process liveness without querying the database."""
    return HealthRead(status="ok")


@router.get(
    "/ready",
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorRead}},
)
async def ready(session: SessionDependency) -> HealthRead:
    """Report readiness after an asynchronous database probe."""
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc
    return HealthRead(status="ok")
