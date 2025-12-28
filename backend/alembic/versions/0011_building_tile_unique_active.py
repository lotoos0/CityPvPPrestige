"""make city tile unique only for active buildings

Revision ID: 0011_building_tile_unique_active
Revises: 0010_building_storage_flag
Create Date: 2025-12-28 22:30:40.129228
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_building_tile_unique_active"
down_revision = "0010_building_storage_flag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_buildings_city_tile", "buildings", type_="unique")
    op.create_index(
        "uq_buildings_city_tile_active",
        "buildings",
        ["city_id", "x", "y"],
        unique=True,
        postgresql_where=sa.text("is_stored = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_buildings_city_tile_active", table_name="buildings")
    op.create_unique_constraint(
        "uq_buildings_city_tile",
        "buildings",
        ["city_id", "x", "y"],
    )
