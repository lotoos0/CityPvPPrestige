"""add building stored flag

Revision ID: 0010_building_storage_flag
Revises: 0009_building_rotation
Create Date: 2025-01-XX
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_building_storage_flag"
down_revision = "0009_building_rotation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "buildings",
        sa.Column("is_stored", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("buildings", "is_stored")
