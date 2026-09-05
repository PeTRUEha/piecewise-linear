"""HTTP dependency providers."""

from typing import Annotated

from fastapi import Depends

from piecewise_linear.db.config import SessionDependency
from piecewise_linear.db.service import PointService


def provide_point_service(session: SessionDependency) -> PointService:
    """Create a transactional point service for the current request."""
    return PointService(session)


PointServiceDependency = Annotated[PointService, Depends(provide_point_service)]
