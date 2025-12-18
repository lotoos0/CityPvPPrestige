import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
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
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Season(Base):
    __tablename__ = "seasons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number = Column(Integer, nullable=False)
    starts_at = Column(DateTime(timezone=True), nullable=False)
    ends_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, server_default=text("false"), nullable=False)
