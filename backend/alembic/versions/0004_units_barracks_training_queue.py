"""army unit types and training queue

Revision ID: 0004_units_barracks_training_queue
Revises: 0003_pvp_idempotency
Create Date: 2025-01-01 00:00:00.000000

"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision: str = "0004_units_barracks_training_queue"
down_revision: Union[str, None] = "0003_pvp_idempotency"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "unit_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("attack", sa.Integer(), nullable=False),
        sa.Column("defense", sa.Integer(), nullable=False),
        sa.Column("train_time_sec", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_unit_types_code", "unit_types", ["code"])

    op.create_table(
        "user_units",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "unit_type_id",
            sa.Integer(),
            sa.ForeignKey("unit_types.id", ondelete="RESTRICT"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("qty", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "user_buildings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("building_type", sa.String(length=32), nullable=False),
        sa.Column("level", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "building_type", name="uq_user_buildings_user_type"),
    )
    op.create_index("ix_user_buildings_user_id", "user_buildings", ["user_id"])

    op.create_table(
        "training_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "unit_type_id",
            sa.Integer(),
            sa.ForeignKey("unit_types.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completes_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
    )
    op.create_index("ix_training_jobs_user_id", "training_jobs", ["user_id"])
    op.create_index("ix_training_jobs_status", "training_jobs", ["status"])

    conn = op.get_bind()
    now = datetime.now(timezone.utc)

    conn.execute(
        text(
            """
            INSERT INTO unit_types (code, name, attack, defense, train_time_sec, created_at)
            VALUES (:code, :name, :attack, :defense, :train_time_sec, :created_at)
            """
        ),
        [
            {
                "code": "raider",
                "name": "Raider",
                "attack": 12,
                "defense": 6,
                "train_time_sec": 60,
                "created_at": now,
            },
            {
                "code": "guardian",
                "name": "Guardian",
                "attack": 6,
                "defense": 12,
                "train_time_sec": 60,
                "created_at": now,
            },
        ],
    )

    user_rows = conn.execute(text("SELECT id FROM users")).fetchall()
    for (user_id,) in user_rows:
        exists = conn.execute(
            text(
                """
                SELECT 1 FROM user_buildings
                WHERE user_id = :user_id AND building_type = 'barracks'
                """
            ),
            {"user_id": user_id},
        ).fetchone()
        if exists:
            continue

        conn.execute(
            text(
                """
                INSERT INTO user_buildings (id, user_id, building_type, level, created_at)
                VALUES (:id, :user_id, 'barracks', 1, :created_at)
                """
            ),
            {"id": str(uuid.uuid4()), "user_id": user_id, "created_at": now},
        )


def downgrade() -> None:
    op.drop_index("ix_training_jobs_status", table_name="training_jobs")
    op.drop_index("ix_training_jobs_user_id", table_name="training_jobs")
    op.drop_table("training_jobs")

    op.drop_index("ix_user_buildings_user_id", table_name="user_buildings")
    op.drop_table("user_buildings")

    op.drop_table("user_units")

    op.drop_index("ix_unit_types_code", table_name="unit_types")
    op.drop_table("unit_types")
