from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/city", tags=["city"])

ALLOWED_BUILDINGS = {
    "gold_mine",
    "house",
    "power_plant",
    "barracks",
    "wall",
    "tower",
    "storage",
}

GOLD_PRODUCTION = {1: 20, 2: 45, 3: 80}
POWER_PRODUCTION = {1: 5, 2: 12, 3: 20}
STORAGE_GOLD_CAP = {1: 200, 2: 500, 3: 900}
BASE_GOLD_CAP = 200


def get_or_create_city(db: Session, user: models.User) -> models.City:
    city = db.query(models.City).filter(models.City.user_id == user.id).first()
    if city:
        return city

    city = models.City(user_id=user.id)
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


def aggregate_city_rates(buildings: list[models.Building]) -> tuple[int, int, int]:
    gold_rate = 0
    power_rate = 0
    storage_bonus = 0

    for building in buildings:
        if building.type == "gold_mine":
            gold_rate += GOLD_PRODUCTION.get(building.level, 0)
        elif building.type == "power_plant":
            power_rate += POWER_PRODUCTION.get(building.level, 0)
        elif building.type == "storage":
            storage_bonus += STORAGE_GOLD_CAP.get(building.level, 0)

    return gold_rate, power_rate, storage_bonus


@router.get("", response_model=schemas.CityOut)
def get_city(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    city = get_or_create_city(db, current_user)
    buildings = (
        db.query(models.Building)
        .filter(models.Building.city_id == city.id)
        .all()
    )

    return schemas.CityOut(
        id=city.id,
        grid_size=city.grid_size,
        gold=city.gold,
        pop=city.pop,
        power=city.power,
        prestige=current_user.prestige,
        buildings=buildings,
    )


@router.post("/collect", response_model=schemas.CityOut)
def collect_resources(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    city = get_or_create_city(db, current_user)
    buildings = (
        db.query(models.Building)
        .filter(models.Building.city_id == city.id)
        .all()
    )

    now = datetime.now(timezone.utc)
    if city.last_collected_at is None:
        city.last_collected_at = now
        db.commit()
        return schemas.CityOut(
            id=city.id,
            grid_size=city.grid_size,
            gold=city.gold,
            pop=city.pop,
            power=city.power,
            prestige=current_user.prestige,
            buildings=buildings,
        )

    delta_seconds = (now - city.last_collected_at).total_seconds()
    if delta_seconds <= 0:
        return schemas.CityOut(
            id=city.id,
            grid_size=city.grid_size,
            gold=city.gold,
            pop=city.pop,
            power=city.power,
            prestige=current_user.prestige,
            buildings=buildings,
        )

    hours = delta_seconds / 3600
    gold_rate, power_rate, storage_bonus = aggregate_city_rates(buildings)
    gold_gain = int(hours * gold_rate)
    power_gain = int(hours * power_rate)
    gold_cap = BASE_GOLD_CAP + storage_bonus

    city.gold = min(city.gold + gold_gain, gold_cap)
    city.power = city.power + power_gain
    city.last_collected_at = now
    db.commit()

    return schemas.CityOut(
        id=city.id,
        grid_size=city.grid_size,
        gold=city.gold,
        pop=city.pop,
        power=city.power,
        prestige=current_user.prestige,
        buildings=buildings,
    )


@router.post("/build", response_model=schemas.CityOut, status_code=status.HTTP_201_CREATED)
def build(
    payload: schemas.BuildRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if payload.type not in ALLOWED_BUILDINGS:
        raise HTTPException(status_code=400, detail="Invalid building type")

    city = get_or_create_city(db, current_user)

    if (
        payload.x < 0
        or payload.y < 0
        or payload.x >= city.grid_size
        or payload.y >= city.grid_size
    ):
        raise HTTPException(status_code=400, detail="Position out of bounds")

    existing = (
        db.query(models.Building)
        .filter(
            models.Building.city_id == city.id,
            models.Building.x == payload.x,
            models.Building.y == payload.y,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Tile already occupied")

    building = models.Building(
        city_id=city.id,
        type=payload.type,
        level=1,
        x=payload.x,
        y=payload.y,
    )
    db.add(building)
    db.commit()

    buildings = (
        db.query(models.Building)
        .filter(models.Building.city_id == city.id)
        .all()
    )

    return schemas.CityOut(
        id=city.id,
        grid_size=city.grid_size,
        gold=city.gold,
        pop=city.pop,
        power=city.power,
        prestige=current_user.prestige,
        buildings=buildings,
    )
