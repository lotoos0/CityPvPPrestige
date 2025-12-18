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


def get_or_create_city(db: Session, user: models.User) -> models.City:
    city = db.query(models.City).filter(models.City.user_id == user.id).first()
    if city:
        return city

    city = models.City(user_id=user.id)
    db.add(city)
    db.commit()
    db.refresh(city)
    return city


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
        prestige=city.prestige,
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

    if payload.x < 0 or payload.y < 0 or payload.x >= city.grid_size or payload.y >= city.grid_size:
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
        prestige=city.prestige,
        buildings=buildings,
    )
