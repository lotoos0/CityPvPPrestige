from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.city_constants import (
    ALLOWED_MVP_BUILDING_TYPES,
    BASE_GOLD_CAP,
    BUILDING_DISPLAY_NAMES,
    BUILDING_EFFECTS,
    BUILDING_FOOTPRINTS,
    MAX_BUILDING_LEVEL,
    get_build_cost,
    get_effect_value,
    normalize_building_type,
)
from app.db import get_db
from app.routes.auth import get_current_user
from app.city_production import apply_city_production
from app.city_seed import seed_town_hall

router = APIRouter(prefix="/city", tags=["city"])


def get_or_create_city(db: Session, user: models.User) -> models.City:
    city = db.query(models.City).filter(models.City.user_id == user.id).first()
    if city:
        return city

    city = models.City(user_id=user.id)
    db.add(city)
    db.commit()
    db.refresh(city)
    seed_town_hall(db, city)
    return city


def aggregate_city_rates(buildings: list[models.Building]) -> tuple[int, int, int]:
    gold_rate = 0
    power_rate = 0
    storage_bonus = 0

    for building in buildings:
        gold_rate += get_effect_value(building.type, building.level, "gold_per_hour")
        power_rate += get_effect_value(building.type, building.level, "power_per_hour")
        storage_bonus += get_effect_value(building.type, building.level, "gold_cap")

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
    now = datetime.now(timezone.utc)
    apply_city_production(city, buildings, now)
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
    normalized_type = normalize_building_type(payload.type)
    if normalized_type not in ALLOWED_MVP_BUILDING_TYPES:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "BUILDING_TYPE_NOT_ALLOWED",
                    "message": "Invalid building type.",
                }
            },
        )

    city = get_or_create_city(db, current_user)

    buildings = (
        db.query(models.Building)
        .filter(models.Building.city_id == city.id)
        .all()
    )
    now = datetime.now(timezone.utc)
    apply_city_production(city, buildings, now)
    db.commit()

    if normalized_type == "town_hall":
        has_town_hall = any(b.type == "town_hall" for b in buildings)
        if has_town_hall:
            return JSONResponse(
                status_code=409,
                content={
                    "error": {
                        "code": "TOWN_HALL_ALREADY_EXISTS",
                        "message": "Town Hall already placed.",
                    }
                },
            )

    if (
        payload.x < 0
        or payload.y < 0
        or payload.x >= city.grid_size
        or payload.y >= city.grid_size
    ):
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "POSITION_OUT_OF_BOUNDS",
                    "message": "Position out of bounds.",
                }
            },
        )

    footprint = BUILDING_FOOTPRINTS.get(normalized_type, {"w": 1, "h": 1})
    occupied_tiles = []
    for dx in range(footprint["w"]):
        for dy in range(footprint["h"]):
            tile_x = payload.x + dx
            tile_y = payload.y + dy
            if (
                tile_x < 0
                or tile_y < 0
                or tile_x >= city.grid_size
                or tile_y >= city.grid_size
            ):
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "code": "TILE_OUT_OF_BOUNDS",
                            "message": "Footprint exceeds city bounds.",
                        }
                    },
                )
            occupied_tiles.append((tile_x, tile_y))

    build_cost = get_build_cost(normalized_type, 1)
    if build_cost is None:
        raise HTTPException(status_code=400, detail="Invalid building configuration")

    locked_city = (
        db.query(models.City)
        .filter(models.City.id == city.id)
        .with_for_update()
        .first()
    )
    if not locked_city:
        raise HTTPException(status_code=404, detail="City not found")

    if locked_city.gold < build_cost:
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "INSUFFICIENT_GOLD",
                    "message": "Not enough gold to build.",
                }
            },
        )

    locked_city.gold -= build_cost

    building = models.Building(
        city_id=city.id,
        type=normalized_type,
        level=1,
        x=payload.x,
        y=payload.y,
    )
    db.add(building)
    try:
        db.flush()
        occupancy_rows = [
            models.BuildingOccupancy(
                city_id=city.id,
                building_id=building.id,
                x=tile_x,
                y=tile_y,
            )
            for tile_x, tile_y in occupied_tiles
        ]
        db.add_all(occupancy_rows)
        db.commit()
    except IntegrityError:
        db.rollback()
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "TILE_OCCUPIED",
                    "message": "Tile already occupied.",
                }
            },
        )

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


@router.post("/upgrade", response_model=schemas.CityOut)
def upgrade(
    payload: schemas.UpgradeRequest,
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
    apply_city_production(city, buildings, now)
    db.commit()

    if (
        payload.x < 0
        or payload.y < 0
        or payload.x >= city.grid_size
        or payload.y >= city.grid_size
    ):
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "POSITION_OUT_OF_BOUNDS",
                    "message": "Position out of bounds.",
                }
            },
        )

    building = next(
        (b for b in buildings if b.x == payload.x and b.y == payload.y),
        None,
    )
    if not building:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "TILE_EMPTY",
                    "message": "No building found on this tile.",
                }
            },
        )

    if building.level >= MAX_BUILDING_LEVEL:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "MAX_LEVEL",
                    "message": "Building is already at max level.",
                }
            },
        )

    next_level = building.level + 1
    upgrade_cost = get_build_cost(building.type, next_level)
    if upgrade_cost is None:
        raise HTTPException(status_code=400, detail="Invalid building configuration")

    locked_city = (
        db.query(models.City)
        .filter(models.City.id == city.id)
        .with_for_update()
        .first()
    )
    if not locked_city:
        raise HTTPException(status_code=404, detail="City not found")

    if locked_city.gold < upgrade_cost:
        return JSONResponse(
            status_code=403,
            content={
                "error": {
                    "code": "INSUFFICIENT_GOLD",
                    "message": "Not enough gold to upgrade.",
                }
            },
        )

    locked_city.gold -= upgrade_cost
    building.level = next_level
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


@router.get("/buildings/catalog", response_model=schemas.BuildingCatalogResponse)
def get_buildings_catalog():
    items = []
    for building_type in sorted(ALLOWED_MVP_BUILDING_TYPES):
        display_name = BUILDING_DISPLAY_NAMES.get(building_type, building_type)
        footprint = BUILDING_FOOTPRINTS.get(building_type, {"w": 1, "h": 1})
        levels = []
        for level in range(1, MAX_BUILDING_LEVEL + 1):
            effects = BUILDING_EFFECTS.get(building_type, {}).get(level, {})
            cost = get_build_cost(building_type, level)
            if cost is None:
                continue
            levels.append(
                schemas.BuildingLevelMeta(
                    level=level,
                    effects=effects,
                    cost_gold=cost,
                )
            )
        items.append(
            schemas.BuildingCatalogItem(
                type=building_type,
                display_name=display_name,
                size=footprint,
                levels=levels,
            )
        )

    return schemas.BuildingCatalogResponse(items=items)
