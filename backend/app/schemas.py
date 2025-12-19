from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


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
