from datetime import datetime
from typing import Iterable, Tuple

from app import models
from app.city_constants import BASE_GOLD_CAP, get_effect_value


def apply_city_production(
    city: models.City,
    buildings: Iterable[models.Building],
    now: datetime,
) -> Tuple[int, float]:
    last_collected_at = city.last_collected_at
    if last_collected_at is None:
        city.last_collected_at = now
        return 0, 0.0

    delta_seconds = (now - last_collected_at).total_seconds()
    if delta_seconds <= 0:
        city.last_collected_at = now
        return 0, 0.0

    hours = delta_seconds / 3600
    gold_rate = 0
    storage_bonus = 0

    for building in buildings:
        gold_rate += get_effect_value(building.type, building.level, "gold_per_hour")
        storage_bonus += get_effect_value(building.type, building.level, "gold_cap")

    produced = int(gold_rate * hours)
    gold_cap = BASE_GOLD_CAP + storage_bonus

    if produced > 0:
        city.gold = min(city.gold + produced, gold_cap)

    city.last_collected_at = now
    return produced, hours
