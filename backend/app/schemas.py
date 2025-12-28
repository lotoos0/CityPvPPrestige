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
    rotation: int = 0
    is_stored: bool = False
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
    rotation: int = 0


class MoveRequest(BaseModel):
    x: int
    y: int
    rotation: int = 0


class UpgradeRequest(BaseModel):
    x: int
    y: int


class BuildingLevelMeta(BaseModel):
    level: int
    effects: dict[str, int]
    cost_gold: int


class BuildingCatalogItem(BaseModel):
    type: str
    display_name: str
    size: dict[str, int]
    levels: list[BuildingLevelMeta]


class BuildingCatalogResponse(BaseModel):
    items: list[BuildingCatalogItem]


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
    global_remaining_sec: Optional[int] = None


class PvPLimitsResponseOut(BaseModel):
    limits: PvpLimitsOut
    nightly_decay: Optional[int] = None
    nightly_decay_applied_at: Optional[datetime] = None
    cooldowns: Optional[PvPCooldownsOut] = None


class UnitLossesOut(BaseModel):
    raider: int = Field(ge=0)
    guardian: int = Field(ge=0)


class PvPLossesOut(BaseModel):
    attacker: UnitLossesOut
    defender: UnitLossesOut


class PvPAttackResponseOut(BaseModel):
    battle_id: UUID
    attacker_id: UUID
    defender_id: UUID
    result: Literal["win", "loss"]
    expected_win: float = Field(ge=0.0, le=1.0)
    prestige: PvPPrestigeOut
    losses: PvPLossesOut
    limits: PvpLimitsOut
    cooldowns: PvPCooldownsOut
    messages: list[MessageCode]


class ArmyUnitOut(BaseModel):
    code: str
    qty: int = Field(ge=0)


class ArmyOut(BaseModel):
    units: list[ArmyUnitOut]


class BarracksTrainIn(BaseModel):
    unit_code: Literal["raider", "guardian"]
    qty: int = Field(ge=1, le=1000)


class BarracksTrainOut(BaseModel):
    job_id: UUID
    status: Literal["running"]
    unit_code: str
    qty: int
    started_at: datetime
    completes_at: datetime


class BarracksQueueOut(BaseModel):
    status: Optional[Literal["running", "done"]] = None
    job_id: Optional[UUID] = None
    unit_code: Optional[str] = None
    qty: Optional[int] = None
    started_at: Optional[datetime] = None
    completes_at: Optional[datetime] = None


class BarracksClaimOut(BaseModel):
    claimed: bool
    unit_code: Optional[str] = None
    qty: Optional[int] = None
    job_id: Optional[UUID] = None


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


class PvPLogItemOut(BaseModel):
    battle_id: UUID
    attacker_id: UUID
    attacker_email: EmailStr
    defender_id: UUID
    defender_email: EmailStr
    result: str
    prestige_delta: int
    expected_win: Optional[float] = None
    units_lost_attacker: UnitLossesOut
    units_lost_defender: UnitLossesOut
    created_at: datetime


class PvPLogResponseOut(BaseModel):
    items: list[PvPLogItemOut]
    next_cursor: Optional[str] = None


class SeasonOut(BaseModel):
    id: UUID
    number: int
    starts_at: datetime
    ends_at: datetime
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
