import random
from datetime import date, datetime, time, timedelta
import os
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, aliased

from app import models, schemas
from app.db import get_db
from app.pvp_constants import (
    BASE_GAIN,
    BASE_LOSS,
    COOLDOWN_MINUTES,
    DAILY_ATTACK_LIMIT,
    EXPECTED_WIN_BASE,
    EXPECTED_WIN_DIVISOR,
    EXPECTED_WIN_MAX,
    EXPECTED_WIN_MIN,
    GLOBAL_ATTACK_COOLDOWN_SEC,
    PRESTIGE_GAIN_CAP,
    PRESTIGE_LOSS_CAP,
    SERVER_TZ,
)
from app.routes.auth import get_current_user

router = APIRouter(prefix="/pvp", tags=["pvp"])

ATTACK_BONUS = {1: 3, 2: 7, 3: 12}
WALL_BONUS = {1: 4, 2: 9, 3: 15}
TOWER_BONUS = {1: 2, 2: 5, 3: 9}



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


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def compute_expected_win(attacker_prestige: int, defender_prestige: int) -> float:
    delta = defender_prestige - attacker_prestige
    expected = EXPECTED_WIN_BASE + (delta / EXPECTED_WIN_DIVISOR)
    return clamp(expected, EXPECTED_WIN_MIN, EXPECTED_WIN_MAX)


def compute_prestige_delta(expected_win: float, result: str) -> int:
    if result == "win":
        return round(BASE_GAIN * (1 + (1 - expected_win)))
    return -round(BASE_LOSS * (1 + expected_win))


def get_or_create_daily_stats(
    db: Session, user_id: UUID, day: date, lock: bool, create: bool
) -> Optional[models.PvpDailyStats]:
    query = db.query(models.PvpDailyStats).filter(
        models.PvpDailyStats.user_id == user_id,
        models.PvpDailyStats.day == day,
    )
    if lock:
        query = query.with_for_update()
    stats = query.first()
    if stats:
        return stats

    if not create:
        return None

    stats = models.PvpDailyStats(user_id=user_id, day=day)
    db.add(stats)
    db.flush()
    return stats


def get_reset_at(now: datetime) -> datetime:
    next_day = now.date() + timedelta(days=1)
    return datetime.combine(next_day, time(0, 0, 0), tzinfo=SERVER_TZ)


@router.post("/attack", response_model=schemas.PvPAttackResponseOut)
def attack(
    payload: schemas.AttackRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if payload.defender_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot attack yourself")

    defender = db.query(models.User).filter(models.User.id == payload.defender_id).first()
    if not defender:
        raise HTTPException(status_code=404, detail="Defender not found")

    idempotency_key = request.headers.get("Idempotency-Key")
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency-Key")

    now = datetime.now(SERVER_TZ)
    today = now.date()

    attacker = (
        db.query(models.User)
        .filter(models.User.id == current_user.id)
        .with_for_update()
        .first()
    )
    if not attacker:
        raise HTTPException(status_code=404, detail="Attacker not found")

    is_test_env = os.getenv("APP_ENV") == "test"
    has_test_headers = any(
        key.lower().startswith("x-test-") for key in request.headers.keys()
    )
    if has_test_headers and not is_test_env:
        raise HTTPException(
            status_code=400, detail="Test headers are not allowed outside APP_ENV=test"
        )

    ignore_cooldowns = (
        is_test_env and request.headers.get("X-Test-Ignore-Cooldowns") == "true"
    )

    if (
        not ignore_cooldowns
        and attacker.last_pvp_at
        and (now - attacker.last_pvp_at) < timedelta(seconds=GLOBAL_ATTACK_COOLDOWN_SEC)
    ):
        raise HTTPException(status_code=429, detail="Global attack cooldown")

    idempotency = models.PvpIdempotency(
        attacker_id=attacker.id,
        idempotency_key=idempotency_key,
        status="pending",
    )
    try:
        db.add(idempotency)
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = (
            db.query(models.PvpIdempotency)
            .filter(
                models.PvpIdempotency.attacker_id == attacker.id,
                models.PvpIdempotency.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing and existing.response_json:
            return existing.response_json
        if existing and existing.status == "pending":
            raise HTTPException(status_code=409, detail="Request in progress")
        raise HTTPException(status_code=409, detail="Idempotency conflict")

    daily_stats = get_or_create_daily_stats(db, attacker.id, today, lock=True, create=True)
    if daily_stats.attacks_used >= DAILY_ATTACK_LIMIT:
        raise HTTPException(status_code=429, detail="Daily attack limit reached")

    cooldown = db.query(models.PvpAttackCooldown).filter(
        models.PvpAttackCooldown.attacker_id == attacker.id,
        models.PvpAttackCooldown.defender_id == defender.id,
    ).first()
    if (
        not ignore_cooldowns
        and cooldown
        and now - cooldown.last_attack_at < timedelta(minutes=COOLDOWN_MINUTES)
    ):
        raise HTTPException(status_code=429, detail="Target on cooldown")

    attacker_city = get_or_create_city(db, attacker)
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

    result = "win" if attack_effective >= defense_effective else "loss"

    expected_win = compute_expected_win(attacker.prestige, defender.prestige)
    raw_delta = compute_prestige_delta(expected_win, result)

    if is_test_env:
        forced_result = request.headers.get("X-Test-Force-Result")
        forced_delta = request.headers.get("X-Test-Force-Delta")
        if forced_result in {"win", "loss"}:
            result = forced_result
        if forced_delta is not None:
            try:
                raw_delta = int(forced_delta)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid X-Test-Force-Delta")
        elif forced_result in {"win", "loss"}:
            raw_delta = compute_prestige_delta(expected_win, result)

    remaining_gain = max(0, PRESTIGE_GAIN_CAP - daily_stats.prestige_gain)
    remaining_loss = max(0, PRESTIGE_LOSS_CAP - daily_stats.prestige_loss)

    if raw_delta > 0:
        attacker_delta = min(raw_delta, remaining_gain)
    elif raw_delta < 0:
        attacker_delta = -min(abs(raw_delta), remaining_loss)
    else:
        attacker_delta = 0

    defender_delta = 0

    attacker.prestige += attacker_delta
    attacker.last_pvp_at = now

    log = models.AttackLog(
        attacker_id=attacker.id,
        defender_id=defender.id,
        result=result,
        prestige_delta_attacker=attacker_delta,
        prestige_delta_defender=defender_delta,
        attacker_prestige_before=attacker.prestige - attacker_delta,
        defender_prestige_before=defender.prestige,
        expected_win=expected_win,
        attacker_attack_power=attack_power,
        defender_defense_power=defense_power,
    )
    db.add(log)
    db.flush()

    daily_stats.attacks_used += 1
    if attacker_delta > 0:
        daily_stats.prestige_gain += attacker_delta
    elif attacker_delta < 0:
        daily_stats.prestige_loss += abs(attacker_delta)

    daily_stats.updated_at = now

    if cooldown:
        cooldown.last_attack_at = now
    else:
        db.add(
            models.PvpAttackCooldown(
                attacker_id=attacker.id,
                defender_id=defender.id,
                last_attack_at=now,
            )
        )

    attacks_left = max(0, DAILY_ATTACK_LIMIT - daily_stats.attacks_used)
    gain_left = max(0, PRESTIGE_GAIN_CAP - daily_stats.prestige_gain)
    loss_left = max(0, PRESTIGE_LOSS_CAP - daily_stats.prestige_loss)

    message_codes = []
    if attacks_left <= 2:
        message_codes.append("APPROACHING_ATTACK_CAP")
    if gain_left <= 50:
        message_codes.append("APPROACHING_GAIN_CAP")
    if attacks_left == 0:
        message_codes.append("ATTACK_CAP_REACHED")
    if gain_left == 0:
        message_codes.append("GAIN_CAP_REACHED")
    if loss_left == 0:
        message_codes.append("LOSS_CAP_REACHED")

    response_payload = schemas.PvPAttackResponseOut(
        battle_id=log.id,
        attacker_id=attacker.id,
        defender_id=defender.id,
        result=result,
        expected_win=expected_win,
        prestige=schemas.PvPPrestigeOut(
            delta=attacker_delta,
            attacker_before=attacker.prestige - attacker_delta,
            attacker_after=attacker.prestige,
        ),
        limits=schemas.PvpLimitsOut(
            reset_at=get_reset_at(now),
            attacks_used=daily_stats.attacks_used,
            attacks_left=attacks_left,
            prestige_gain_today=daily_stats.prestige_gain,
            prestige_gain_left=gain_left,
            prestige_loss_today=daily_stats.prestige_loss,
            prestige_loss_left=loss_left,
        ),
        cooldowns=schemas.PvPCooldownsOut(
            global_available_at=now + timedelta(seconds=GLOBAL_ATTACK_COOLDOWN_SEC),
            same_target_available_at=now + timedelta(minutes=COOLDOWN_MINUTES),
        ),
        messages=message_codes,
    ).model_dump(mode="json")

    idempotency.status = "completed"
    idempotency.response_json = response_payload
    idempotency.updated_at = now

    db.commit()

    return response_payload


@router.get("/limits", response_model=schemas.PvPLimitsResponseOut)
def limits(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    now = datetime.now(SERVER_TZ)
    today = now.date()
    stats = get_or_create_daily_stats(db, current_user.id, today, lock=False, create=False)

    attacks_used = stats.attacks_used if stats else 0
    prestige_gain = stats.prestige_gain if stats else 0
    prestige_loss = stats.prestige_loss if stats else 0

    limits_out = schemas.PvpLimitsOut(
        attacks_used=attacks_used,
        attacks_left=max(0, DAILY_ATTACK_LIMIT - attacks_used),
        prestige_gain_today=prestige_gain,
        prestige_gain_left=max(0, PRESTIGE_GAIN_CAP - prestige_gain),
        prestige_loss_today=prestige_loss,
        prestige_loss_left=max(0, PRESTIGE_LOSS_CAP - prestige_loss),
        reset_at=get_reset_at(now),
    )

    return schemas.PvPLimitsResponseOut(limits=limits_out)


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
