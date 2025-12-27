"""enforce single town hall per city

Revision ID: 0008_town_hall_singleton
Revises: 0007_building_occupancy
Create Date: 2024-12-24 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0008_town_hall_singleton"
down_revision: Union[str, None] = "0007_building_occupancy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                city_id,
                ROW_NUMBER() OVER (PARTITION BY city_id ORDER BY placed_at, id) AS rn
            FROM buildings
            WHERE type = 'town_hall'
        )
        DELETE FROM building_occupancy bo
        USING ranked r
        WHERE bo.building_id = r.id AND r.rn > 1
        """
    )
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                city_id,
                ROW_NUMBER() OVER (PARTITION BY city_id ORDER BY placed_at, id) AS rn
            FROM buildings
            WHERE type = 'town_hall'
        )
        DELETE FROM buildings b
        USING ranked r
        WHERE b.id = r.id AND r.rn > 1
        """
    )
    op.create_index(
        "uq_buildings_city_town_hall",
        "buildings",
        ["city_id"],
        unique=True,
        postgresql_where=sa.text("type = 'town_hall'"),
    )


def downgrade() -> None:
    op.drop_index("uq_buildings_city_town_hall", table_name="buildings")
