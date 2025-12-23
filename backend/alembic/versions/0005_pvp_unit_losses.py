"""add unit losses to attack logs

Revision ID: 0005_pvp_unit_losses
Revises: 0004_units_barracks
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0005_pvp_unit_losses"
down_revision: Union[str, None] = "0004_units_barracks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add unit loss tracking columns to attack_logs
    # Use nullable=True first to avoid issues with existing rows
    op.add_column(
        "attack_logs",
        sa.Column(
            "units_lost_attacker",
            postgresql.JSONB,
            nullable=True,
        ),
    )
    op.add_column(
        "attack_logs",
        sa.Column(
            "units_lost_defender",
            postgresql.JSONB,
            nullable=True,
        ),
    )

    # Set default for existing rows using jsonb_build_object to avoid colon issues
    conn = op.get_bind()
    conn.execute(sa.text("""
        UPDATE attack_logs
        SET units_lost_attacker = jsonb_build_object('raider', 0, 'guardian', 0)
        WHERE units_lost_attacker IS NULL
    """))
    conn.execute(sa.text("""
        UPDATE attack_logs
        SET units_lost_defender = jsonb_build_object('raider', 0, 'guardian', 0)
        WHERE units_lost_defender IS NULL
    """))

    # Now make NOT NULL and add server default using jsonb_build_object
    op.alter_column("attack_logs", "units_lost_attacker", nullable=False)
    op.alter_column("attack_logs", "units_lost_defender", nullable=False)
    op.alter_column(
        "attack_logs",
        "units_lost_attacker",
        server_default=sa.text("jsonb_build_object('raider', 0, 'guardian', 0)")
    )
    op.alter_column(
        "attack_logs",
        "units_lost_defender",
        server_default=sa.text("jsonb_build_object('raider', 0, 'guardian', 0)")
    )


def downgrade() -> None:
    op.drop_column("attack_logs", "units_lost_defender")
    op.drop_column("attack_logs", "units_lost_attacker")
