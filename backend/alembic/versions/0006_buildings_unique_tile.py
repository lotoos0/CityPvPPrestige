"""add unique constraint for building tile occupancy

Revision ID: 0006_buildings_unique_tile
Revises: 0005_pvp_unit_losses
Create Date: 2024-12-23 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_buildings_unique_tile"
down_revision: Union[str, None] = "0005_pvp_unit_losses"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_buildings_city_tile",
        "buildings",
        ["city_id", "x", "y"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_buildings_city_tile", "buildings", type_="unique")
