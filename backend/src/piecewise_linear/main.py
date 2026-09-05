"""FastAPI application factory for the piecewise-linear service."""

from advanced_alchemy.extensions.fastapi import AdvancedAlchemy
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from piecewise_linear.api.router import api_router
from piecewise_linear.core.settings import Settings, get_settings
from piecewise_linear.db.config import create_database_config
from piecewise_linear.db.errors import PointNotFoundError, PointOrderConflictError


async def handle_point_not_found(_request: Request, _exc: Exception) -> JSONResponse:
    """Translate a missing point into the public response contract."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Point not found"},
    )


async def handle_point_order_conflict(_request: Request, _exc: Exception) -> JSONResponse:
    """Translate a stale point set into the public response contract."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Point set has changed"},
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure a FastAPI application instance."""
    resolved_settings = settings or get_settings()
    app = FastAPI(title=resolved_settings.app_name)
    app.state.settings = resolved_settings
    app.include_router(api_router)
    app.add_exception_handler(PointNotFoundError, handle_point_not_found)
    app.add_exception_handler(PointOrderConflictError, handle_point_order_conflict)

    alchemy = AdvancedAlchemy(
        config=create_database_config(str(resolved_settings.database_url)),
    )
    alchemy.init_app(app)
    return app


app = create_app()
