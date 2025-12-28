from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models
from app.city_constants import BUILDING_FOOTPRINTS


def get_default_town_hall_origin(grid_size: int) -> tuple[int, int]:
    footprint = BUILDING_FOOTPRINTS.get("town_hall", {"w": 1, "h": 1})
    origin_x = max(0, (grid_size // 2) - (footprint["w"] // 2))
    origin_y = max(0, (grid_size // 2) - (footprint["h"] // 2))
    return origin_x, origin_y


def seed_town_hall(db: Session, city: models.City) -> None:
    existing = (
        db.query(models.Building)
        .filter(
            models.Building.city_id == city.id,
            models.Building.type == "town_hall",
        )
        .first()
    )
    if existing:
        return

    origin_x, origin_y = get_default_town_hall_origin(city.grid_size)
    building = models.Building(
        city_id=city.id,
        type="town_hall",
        level=1,
        x=origin_x,
        y=origin_y,
        rotation=0,
    )
    db.add(building)
    try:
        db.flush()
        footprint = BUILDING_FOOTPRINTS.get("town_hall", {"w": 1, "h": 1})
        occupancy_rows = [
            models.BuildingOccupancy(
                city_id=city.id,
                building_id=building.id,
                x=origin_x + dx,
                y=origin_y + dy,
            )
            for dx in range(footprint["w"])
            for dy in range(footprint["h"])
        ]
        db.add_all(occupancy_rows)
        db.commit()
    except IntegrityError:
        db.rollback()
