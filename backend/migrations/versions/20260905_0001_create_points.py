"""Create the points table.

Revision ID: 20260905_0001
Revises:
Create Date: 2026-09-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260905_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create storage for ordered finite points."""
    op.create_table(
        "points",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("x", sa.Float(precision=53), nullable=False),
        sa.Column("y", sa.Float(precision=53), nullable=False),
        sa.CheckConstraint("id > 0", name="id_positive"),
        sa.CheckConstraint(
            "x NOT IN ('NaN'::double precision, 'Infinity'::double precision, "
            "'-Infinity'::double precision)",
            name="x_finite",
        ),
        sa.CheckConstraint(
            "y NOT IN ('NaN'::double precision, 'Infinity'::double precision, "
            "'-Infinity'::double precision)",
            name="y_finite",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_points"),
    )


def downgrade() -> None:
    """Remove point storage."""
    op.drop_table("points")
