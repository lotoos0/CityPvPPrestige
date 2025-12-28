"""pvp limits and decay tables

Revision ID: 0002_pvp_limits_and_decay
Revises: 0001_initial
Create Date: 2025-12-21 10:39:14.600555

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_pvp_limits_and_decay"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("prestige", sa.Integer(), server_default=sa.text("1000"), nullable=False),
    )
    op.add_column("users", sa.Column("last_pvp_at", sa.DateTime(timezone=True)))
    op.execute(
        "UPDATE users SET prestige = cities.prestige FROM cities WHERE cities.user_id = users.id"
    )

    op.add_column("attack_logs", sa.Column("attacker_prestige_before", sa.Integer()))
    op.add_column("attack_logs", sa.Column("defender_prestige_before", sa.Integer()))
    op.add_column("attack_logs", sa.Column("expected_win", sa.Float()))
    op.add_column("attack_logs", sa.Column("attacker_attack_power", sa.Integer()))
    op.add_column("attack_logs", sa.Column("defender_defense_power", sa.Integer()))
    op.add_column(
        "attack_logs",
        sa.Column("season_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("seasons.id")),
    )

    op.create_table(
        "pvp_daily_stats",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("day", sa.Date(), primary_key=True),
        sa.Column("attacks_used", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("prestige_gain", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("prestige_loss", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "day", name="uq_pvp_daily_stats"),
    )
    op.create_index("ix_pvp_daily_stats_day", "pvp_daily_stats", ["day"])

    op.create_table(
        "pvp_attack_cooldowns",
        sa.Column("attacker_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("defender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), primary_key=True),
        sa.Column("last_attack_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("attacker_id", "defender_id", name="uq_pvp_attack_cooldowns"),
    )

    op.create_table(
        "prestige_decay_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column(
            "ts", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False
        ),
        sa.Column("prestige_before", sa.Integer(), nullable=False),
        sa.Column("prestige_after", sa.Integer(), nullable=False),
        sa.Column("decay_amount", sa.Integer(), nullable=False),
        sa.Column("inactive_days", sa.Integer(), nullable=False),
        sa.Column("rate_used", sa.Float(), nullable=False),
    )

    op.create_table(
        "system_ticks",
        sa.Column("tick_name", sa.String(length=50), primary_key=True),
        sa.Column("tick_day", sa.Date(), primary_key=True),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("tick_name", "tick_day", name="uq_system_ticks"),
    )


def downgrade() -> None:
    op.drop_table("system_ticks")
    op.drop_table("prestige_decay_log")
    op.drop_table("pvp_attack_cooldowns")
    op.drop_index("ix_pvp_daily_stats_day", table_name="pvp_daily_stats")
    op.drop_table("pvp_daily_stats")

    op.drop_column("attack_logs", "season_id")
    op.drop_column("attack_logs", "defender_defense_power")
    op.drop_column("attack_logs", "attacker_attack_power")
    op.drop_column("attack_logs", "expected_win")
    op.drop_column("attack_logs", "defender_prestige_before")
    op.drop_column("attack_logs", "attacker_prestige_before")

    op.drop_column("users", "last_pvp_at")
    op.drop_column("users", "prestige")
