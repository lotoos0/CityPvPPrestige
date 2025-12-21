"""pvp idempotency

Revision ID: 0003_pvp_idempotency
Revises: 0002_pvp_limits_and_decay
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_pvp_idempotency"
down_revision: Union[str, None] = "0002_pvp_limits_and_decay"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pvp_idempotency",
        sa.Column("attacker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("idempotency_key", sa.String(length=64), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("pvp_idempotency")
