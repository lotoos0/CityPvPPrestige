"""add building rotation

Revision ID: 0009_building_rotation
Revises: 0008_town_hall_singleton
Create Date: 2025-01-XX
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_building_rotation"
down_revision = "0008_town_hall_singleton"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "buildings",
        sa.Column("rotation", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("buildings", "rotation")
