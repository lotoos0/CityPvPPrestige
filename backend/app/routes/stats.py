from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.city_seed import seed_town_hall
from app.db import get_db
from app.routes.auth import get_current_user

router = APIRouter(prefix="/stats", tags=["stats"])

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
    seed_town_hall(db, city)
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


@router.get("", response_model=schemas.StatsOut)
def get_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    city = get_or_create_city(db, current_user)
    buildings = (
        db.query(models.Building)
        .filter(models.Building.city_id == city.id)
        .all()
    )

    attack, defense = compute_stats(buildings)
    return schemas.StatsOut(attack_power=attack, defense_power=defense)
