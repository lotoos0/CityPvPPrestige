from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BuildingOut(BaseModel):
    id: UUID
    type: str
    level: int
    x: int
    y: int
    model_config = ConfigDict(from_attributes=True)


class CityOut(BaseModel):
    id: UUID
    grid_size: int
    gold: int
    pop: int
    power: int
    prestige: int
    buildings: list[BuildingOut]
    model_config = ConfigDict(from_attributes=True)


class BuildRequest(BaseModel):
    type: str
    x: int
    y: int


class StatsOut(BaseModel):
    attack_power: int
    defense_power: int


class AttackRequest(BaseModel):
    defender_id: UUID


class AttackResult(BaseModel):
    result: str
    attacker_power: int
    defender_power: int
    prestige_delta_attacker: int
    prestige_delta_defender: int
    attacks_left: Optional[int] = None
    prestige_gain_left: Optional[int] = None
    prestige_loss_left: Optional[int] = None
    reset_at: Optional[datetime] = None
    message_codes: Optional[list[str]] = None


class PvpLimitsOut(BaseModel):
    attacks_used: int
    attacks_left: int
    prestige_gain_today: int
    prestige_gain_left: int
    prestige_loss_today: int
    prestige_loss_left: int
    reset_at: datetime


MessageCode = Literal[
    "APPROACHING_ATTACK_CAP",
    "ATTACK_CAP_REACHED",
    "APPROACHING_GAIN_CAP",
    "GAIN_CAP_REACHED",
    "LOSS_CAP_REACHED",
    "TARGET_COOLDOWN",
    "GLOBAL_COOLDOWN",
]


class PvPPrestigeOut(BaseModel):
    delta: int
    attacker_before: int
    attacker_after: int


class PvPCooldownsOut(BaseModel):
    global_available_at: Optional[datetime] = None
    same_target_available_at: Optional[datetime] = None


class PvPLimitsResponseOut(BaseModel):
    limits: PvpLimitsOut
    nightly_decay: Optional[int] = None
    nightly_decay_applied_at: Optional[datetime] = None
    cooldowns: Optional[PvPCooldownsOut] = None


class PvPAttackResponseOut(BaseModel):
    battle_id: UUID
    attacker_id: UUID
    defender_id: UUID
    result: Literal["win", "loss"]
    expected_win: float = Field(ge=0.0, le=1.0)
    prestige: PvPPrestigeOut
    limits: PvpLimitsOut
    cooldowns: PvPCooldownsOut
    messages: list[MessageCode]


class RankEntry(BaseModel):
    rank: int
    user_id: UUID
    email: EmailStr
    prestige: int


class AttackLogEntry(BaseModel):
    id: UUID
    attacker_id: UUID
    attacker_email: EmailStr
    defender_id: UUID
    defender_email: EmailStr
    result: str
    prestige_delta_attacker: int
    prestige_delta_defender: int
    created_at: datetime


class SeasonOut(BaseModel):
    id: UUID
    number: int
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
