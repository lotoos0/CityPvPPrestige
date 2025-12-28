"""add building occupancy table

Revision ID: 0007_building_occupancy
Revises: 0006_buildings_unique_tile
Create Date: 2025-12-26 20:40:48.378240

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0007_building_occupancy"
down_revision: Union[str, None] = "0006_buildings_unique_tile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "building_occupancy",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "city_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cities.id"),
            nullable=False,
        ),
        sa.Column(
            "building_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("buildings.id"),
            nullable=False,
        ),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.UniqueConstraint("city_id", "x", "y", name="uq_building_occupancy_city_tile"),
    )
    op.create_index(
        "ix_building_occupancy_city_id",
        "building_occupancy",
        ["city_id"],
    )
    op.create_index(
        "ix_building_occupancy_building_id",
        "building_occupancy",
        ["building_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_building_occupancy_building_id", table_name="building_occupancy")
    op.drop_index("ix_building_occupancy_city_id", table_name="building_occupancy")
    op.drop_table("building_occupancy")
