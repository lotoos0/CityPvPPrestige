import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
    text,
)
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"), nullable=False)
    type = Column(String(50), nullable=False)
    level = Column(Integer, server_default=text("1"), nullable=False)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    placed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


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
