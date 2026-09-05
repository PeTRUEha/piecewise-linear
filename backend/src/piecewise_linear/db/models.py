"""Database models for persisted points."""

from advanced_alchemy.base import AdvancedDeclarativeBase, CommonTableAttributes
from sqlalchemy import BigInteger, CheckConstraint, Float
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import Mapped, mapped_column


class Base(CommonTableAttributes, AdvancedDeclarativeBase, AsyncAttrs):
    """Declarative base for service models."""

    __abstract__ = True


class Point(Base):
    """A persisted point whose identifier defines its order."""

    __tablename__ = "points"
    __table_args__ = (
        CheckConstraint("id > 0", name="id_positive"),
        CheckConstraint(
            "x NOT IN ('NaN'::double precision, 'Infinity'::double precision, "
            "'-Infinity'::double precision)",
            name="x_finite",
        ),
        CheckConstraint(
            "y NOT IN ('NaN'::double precision, 'Infinity'::double precision, "
            "'-Infinity'::double precision)",
            name="y_finite",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    x: Mapped[float] = mapped_column(Float(precision=53), nullable=False)
    y: Mapped[float] = mapped_column(Float(precision=53), nullable=False)
