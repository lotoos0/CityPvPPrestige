from typing import Optional

MAX_BUILDING_LEVEL = 3
BASE_GOLD_CAP = 200

BUILDING_TYPE_ALIASES = {
    "scout_tower": "tower",
}

ALLOWED_MVP_BUILDING_TYPES = {
    "town_hall",
    "gold_mine",
    "house",
    "barracks",
    "wall",
    "tower",
    "storage",
}

PRIMARY_EFFECT_KEYS = {
    "gold_mine": "gold_per_hour",
    "house": "pop_cap",
    "barracks": "attack",
    "wall": "defense",
    "tower": "defense",
    "storage": "gold_cap",
}

BUILDING_EFFECTS = {
    "town_hall": {
        1: {},
        2: {},
        3: {},
    },
    "gold_mine": {
        1: {"gold_per_hour": 20},
        2: {"gold_per_hour": 45},
        3: {"gold_per_hour": 80},
    },
    "house": {
        1: {"pop_cap": 5},
        2: {"pop_cap": 12},
        3: {"pop_cap": 20},
    },
    "power_plant": {
        1: {"power_per_hour": 5},
        2: {"power_per_hour": 12},
        3: {"power_per_hour": 20},
    },
    "barracks": {
        1: {"attack": 3},
        2: {"attack": 7},
        3: {"attack": 12},
    },
    "wall": {
        1: {"defense": 4},
        2: {"defense": 9},
        3: {"defense": 15},
    },
    "tower": {
        1: {"defense": 2},
        2: {"defense": 5},
        3: {"defense": 9},
    },
    "storage": {
        1: {"gold_cap": 200},
        2: {"gold_cap": 500},
        3: {"gold_cap": 900},
    },
}

BUILDING_FOOTPRINTS = {
    "town_hall": {"w": 2, "h": 2},
    "barracks": {"w": 2, "h": 2},
    "gold_mine": {"w": 2, "h": 2},
    "house": {"w": 2, "h": 1},
    "wall": {"w": 3, "h": 1},
    "tower": {"w": 1, "h": 1},
    "storage": {"w": 2, "h": 2},
}

BUILDING_COST_MULTIPLIERS = {
    "gold_mine": 30,
    "house": 60,
    "barracks": 140,
    "wall": 110,
    "tower": 130,
    "storage": 0.6,
}

BUILDING_DISPLAY_NAMES = {
    "town_hall": "Town Hall",
    "gold_mine": "Gold Mine",
    "house": "House",
    "barracks": "Barracks",
    "wall": "Wall",
    "tower": "Scout Tower",
    "storage": "Storage",
}

TOWN_HALL_BUILD_COST = 0
TOWN_HALL_UPGRADE_COSTS = {
    2: 2500,
    3: 6500,
}


def normalize_building_type(building_type: Optional[str]) -> Optional[str]:
    if building_type is None:
        return None
    normalized = building_type.strip().lower()
    return BUILDING_TYPE_ALIASES.get(normalized, normalized)


def get_effect_value(building_type: str, level: int, key: str) -> int:
    canonical = normalize_building_type(building_type)
    if not canonical:
        return 0
    return BUILDING_EFFECTS.get(canonical, {}).get(level, {}).get(key, 0)


def get_primary_effect_value(building_type: str, level: int) -> int:
    canonical = normalize_building_type(building_type)
    if not canonical:
        return 0
    key = PRIMARY_EFFECT_KEYS.get(canonical)
    if not key:
        return 0
    return BUILDING_EFFECTS.get(canonical, {}).get(level, {}).get(key, 0)


def get_build_cost(building_type: str, level: int) -> Optional[int]:
    canonical = normalize_building_type(building_type)
    if not canonical:
        return None
    if canonical == "town_hall":
        if level == 1:
            return TOWN_HALL_BUILD_COST
        return TOWN_HALL_UPGRADE_COSTS.get(level)

    primary_effect = get_primary_effect_value(canonical, level)
    multiplier = BUILDING_COST_MULTIPLIERS.get(canonical)
    if multiplier is None:
        return None
    return int(round(primary_effect * multiplier))
