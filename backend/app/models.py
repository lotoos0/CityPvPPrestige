import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Index,
    JSON,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    prestige = Column(Integer, server_default=text("1000"), nullable=False)
    last_pvp_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class City(Base):
    __tablename__ = "cities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    grid_size = Column(Integer, server_default=text("12"), nullable=False)
    gold = Column(Integer, server_default=text("0"), nullable=False)
    pop = Column(Integer, server_default=text("0"), nullable=False)
    power = Column(Integer, server_default=text("0"), nullable=False)
    prestige = Column(Integer, server_default=text("1000"), nullable=False)
    last_collected_at = Column(DateTime(timezone=True), nullable=True)


class Building(Base):
    __tablename__ = "buildings"
    __table_args__ = (
        UniqueConstraint("city_id", "x", "y", name="uq_buildings_city_tile"),
        Index(
            "uq_buildings_city_town_hall",
            "city_id",
            unique=True,
            postgresql_where=text("type = 'town_hall'"),
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"), nullable=False)
    type = Column(String(50), nullable=False)
    level = Column(Integer, server_default=text("1"), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    rotation = Column(Integer, server_default=text("0"), nullable=False)
    is_stored = Column(Boolean, server_default=text("false"), nullable=False)
    placed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class BuildingOccupancy(Base):
    __tablename__ = "building_occupancy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"), nullable=False)
    building_id = Column(UUID(as_uuid=True), ForeignKey("buildings.id"), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("city_id", "x", "y", name="uq_building_occupancy_city_tile"),
        Index("ix_building_occupancy_city_id", "city_id"),
        Index("ix_building_occupancy_building_id", "building_id"),
    )


class AttackLog(Base):
    __tablename__ = "attack_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attacker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    defender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    result = Column(String(10), nullable=False)
    prestige_delta_attacker = Column(Integer, nullable=False)
    prestige_delta_defender = Column(Integer, nullable=False)
    attacker_prestige_before = Column(Integer, nullable=True)
    defender_prestige_before = Column(Integer, nullable=True)
    expected_win = Column(Float, nullable=True)
    attacker_attack_power = Column(Integer, nullable=True)
    defender_defense_power = Column(Integer, nullable=True)
    units_lost_attacker = Column(JSON, nullable=False, server_default=text("jsonb_build_object('raider', 0, 'guardian', 0)"))
    units_lost_defender = Column(JSON, nullable=False, server_default=text("jsonb_build_object('raider', 0, 'guardian', 0)"))
    season_id = Column(UUID(as_uuid=True), ForeignKey("seasons.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Season(Base):
    __tablename__ = "seasons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(Integer, nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, server_default=text("false"), nullable=False)


class PvpDailyStats(Base):
    __tablename__ = "pvp_daily_stats"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    day = Column(Date, primary_key=True)
    attacks_used = Column(Integer, server_default=text("0"), nullable=False)
    prestige_gain = Column(Integer, server_default=text("0"), nullable=False)
    prestige_loss = Column(Integer, server_default=text("0"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("user_id", "day", name="uq_pvp_daily_stats"),)


class PvpAttackCooldown(Base):
    __tablename__ = "pvp_attack_cooldowns"

    attacker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    defender_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    last_attack_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "attacker_id", "defender_id", name="uq_pvp_attack_cooldowns"
        ),
    )


class PrestigeDecayLog(Base):
    __tablename__ = "prestige_decay_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    day = Column(Date, nullable=False)
    ts = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    prestige_before = Column(Integer, nullable=False)
    prestige_after = Column(Integer, nullable=False)
    decay_amount = Column(Integer, nullable=False)
    inactive_days = Column(Integer, nullable=False)
    rate_used = Column(Float, nullable=False)


class SystemTick(Base):
    __tablename__ = "system_ticks"

    tick_name = Column(String(50), primary_key=True)
    tick_day = Column(Date, primary_key=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint("tick_name", "tick_day", name="uq_system_ticks"),)


class PvpIdempotency(Base):
    __tablename__ = "pvp_idempotency"

    attacker_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    idempotency_key = Column(String(64), primary_key=True)
    status = Column(String(20), nullable=False)
    response_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class UnitType(Base):
    __tablename__ = "unit_types"

    id = Column(Integer, primary_key=True)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(64), nullable=False)
    attack = Column(Integer, nullable=False)
    defense = Column(Integer, nullable=False)
    train_time_sec = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (Index("ix_unit_types_code", "code"),)


class UserUnit(Base):
    __tablename__ = "user_units"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    unit_type_id = Column(Integer, ForeignKey("unit_types.id", ondelete="RESTRICT"), primary_key=True)
    qty = Column(Integer, server_default=text("0"), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    unit_type = relationship("UnitType")


class UserBuilding(Base):
    __tablename__ = "user_buildings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    building_type = Column(String(32), nullable=False)
    level = Column(Integer, server_default=text("1"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "building_type", name="uq_user_buildings_user_type"),
        Index("ix_user_buildings_user_id", "user_id"),
    )


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    unit_type_id = Column(Integer, ForeignKey("unit_types.id", ondelete="RESTRICT"), nullable=False)
    qty = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    completes_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(16), nullable=False)

    unit_type = relationship("UnitType")

    __table_args__ = (
        Index("ix_training_jobs_user_id", "user_id"),
        Index("ix_training_jobs_status", "status"),
    )
