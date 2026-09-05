"""Advanced Alchemy repository for points."""

from advanced_alchemy.repository import SQLAlchemyAsyncRepository

from piecewise_linear.db.models import Point


class PointRepository(SQLAlchemyAsyncRepository[Point]):
    """Persist and query point models."""

    model_type = Point
