import random
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, aliased

from app import models, schemas
from app.db import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/pvp", tags=["pvp"])

ATTACK_BONUS = {1: 3, 2: 7, 3: 12}
WALL_BONUS = {1: 4, 2: 9, 3: 15}
TOWER_BONUS = {1: 2, 2: 5, 3: 9}

COOLDOWN_MINUTES = 30
DAILY_ATTACK_LIMIT = 20


def get_or_create_city(db: Session, user: models.User) -> models.City:
    city = db.query(models.City).filter(models.City.user_id == user.id).first()
    if city:
        return city

    city = models.City(user_id=user.id)
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


def compute_stats(buildings: list[models.Building]) -> tuple[int, int]:
    attack = 0
    defense_bonus = 0

    for building in buildings:
        if building.type == "barracks":
            attack += ATTACK_BONUS.get(building.level, 0)
        elif building.type == "wall":
            defense_bonus += WALL_BONUS.get(building.level, 0)
        elif building.type == "tower":
            defense_bonus += TOWER_BONUS.get(building.level, 0)

    defense = attack + defense_bonus
    return attack, defense


def compute_prestige_delta(my_prestige: int, opponent_prestige: int, result: str) -> int:
    opponent_higher = opponent_prestige > my_prestige
    if result == "win":
        return 30 if opponent_higher else 10
    return -10 if opponent_higher else -25


def get_attackers_today(db: Session, attacker_id: UUID, now: datetime) -> int:
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.query(models.AttackLog)
        .filter(
            models.AttackLog.attacker_id == attacker_id,
            models.AttackLog.created_at >= day_start,
        )
        .count()
    )


def get_last_attack(db: Session, attacker_id: UUID, defender_id: UUID):
    return (
        db.query(models.AttackLog)
        .filter(
            models.AttackLog.attacker_id == attacker_id,
            models.AttackLog.defender_id == defender_id,
        )
        .order_by(models.AttackLog.created_at.desc())
        .first()
    )


@router.post("/attack", response_model=schemas.AttackResult)
def attack(
    payload: schemas.AttackRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if payload.defender_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot attack yourself")

    defender = db.query(models.User).filter(models.User.id == payload.defender_id).first()
    if not defender:
        raise HTTPException(status_code=404, detail="Defender not found")

    now = datetime.now(timezone.utc)
    if get_attackers_today(db, current_user.id, now) >= DAILY_ATTACK_LIMIT:
        raise HTTPException(status_code=429, detail="Daily attack limit reached")

    last_attack = get_last_attack(db, current_user.id, defender.id)
    if last_attack and last_attack.created_at:
        cooldown = timedelta(minutes=COOLDOWN_MINUTES)
        if now - last_attack.created_at < cooldown:
            raise HTTPException(status_code=429, detail="Target on cooldown")

    attacker_city = get_or_create_city(db, current_user)
    defender_city = get_or_create_city(db, defender)

    attacker_buildings = (
        db.query(models.Building)
        .filter(models.Building.city_id == attacker_city.id)
        .all()
    )
    defender_buildings = (
        db.query(models.Building)
        .filter(models.Building.city_id == defender_city.id)
        .all()
    )

    attack_power, _ = compute_stats(attacker_buildings)
    _, defense_power = compute_stats(defender_buildings)

    attack_effective = attack_power * random.uniform(0.9, 1.1)
    defense_effective = defense_power * random.uniform(0.9, 1.1)

    result = "win" if attack_effective >= defense_effective else "lose"

    attacker_delta = compute_prestige_delta(
        attacker_city.prestige, defender_city.prestige, result
    )
    defender_result = "lose" if result == "win" else "win"
    defender_delta = compute_prestige_delta(
        defender_city.prestige, attacker_city.prestige, defender_result
    )

    attacker_city.prestige += attacker_delta
    defender_city.prestige += defender_delta

    log = models.AttackLog(
        attacker_id=current_user.id,
        defender_id=defender.id,
        result=result,
        prestige_delta_attacker=attacker_delta,
        prestige_delta_defender=defender_delta,
    )
    db.add(log)
    db.commit()

    return schemas.AttackResult(
        result=result,
        attacker_power=attack_power,
        defender_power=defense_power,
        prestige_delta_attacker=attacker_delta,
        prestige_delta_defender=defender_delta,
    )


@router.get("/log", response_model=list[schemas.AttackLogEntry])
def log(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    attacker_alias = aliased(models.User)
    defender_alias = aliased(models.User)
    logs = (
        db.query(models.AttackLog, attacker_alias, defender_alias)
        .join(attacker_alias, models.AttackLog.attacker_id == attacker_alias.id)
        .join(defender_alias, models.AttackLog.defender_id == defender_alias.id)
        .filter(
            (models.AttackLog.attacker_id == current_user.id)
            | (models.AttackLog.defender_id == current_user.id)
        )
        .order_by(models.AttackLog.created_at.desc())
        .limit(20)
        .all()
    )

    results = []
    for log_entry, attacker, defender in logs:
        results.append(
            schemas.AttackLogEntry(
                id=log_entry.id,
                attacker_id=attacker.id,
                attacker_email=attacker.email,
                defender_id=defender.id,
                defender_email=defender.email,
                result=log_entry.result,
                prestige_delta_attacker=log_entry.prestige_delta_attacker,
                prestige_delta_defender=log_entry.prestige_delta_defender,
                created_at=log_entry.created_at,
            )
        )
    return results
