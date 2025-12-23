"""
PvP unit loss calculation helpers
"""
import math
from typing import Dict, Tuple

from app.pvp_constants import (
    Losses,
    clamp,
    DEFENSE_FACTOR_PER_WALL_LEVEL,
    DEFENSE_FACTOR_PER_SPIRE_LEVEL,
    DEFENSE_FACTOR_MAX,
    LOSS_RATE_ATT_WIN_MIN,
    LOSS_RATE_ATT_WIN_MAX,
    LOSS_RATE_ATT_LOSS_MIN,
    LOSS_RATE_ATT_LOSS_MAX,
    LOSS_RATE_DEF_LOSS_MIN,
    LOSS_RATE_DEF_LOSS_MAX,
    LOSS_RATE_DEF_WIN_MIN,
    LOSS_RATE_DEF_WIN_MAX,
    MINIMUM_LOSS_THRESHOLD,
    MINIMUM_LOSS_UNITS,
)

_UNIT_KEYS = ("raider", "guardian")


def _get_level(buildings_by_type: Dict[str, int], building_type: str) -> int:
    """Get building level, defaulting to 1 if not present, clamping to 1-3."""
    lvl = buildings_by_type.get(building_type, 1)
    if lvl < 1:
        return 1
    if lvl > 3:
        return 3
    return lvl


def get_defense_factor(buildings_by_type: Dict[str, int]) -> float:
    """
    Calculate defense factor from Wall and Spire buildings.

    Args:
        buildings_by_type: Dict mapping building type to level (max if multiple)

    Returns:
        Defense factor between 1.0 and DEFENSE_FACTOR_MAX (1.2)
    """
    wall_lvl = _get_level(buildings_by_type, "wall")
    spire_lvl = _get_level(buildings_by_type, "tower")

    factor = 1.0
    factor += DEFENSE_FACTOR_PER_WALL_LEVEL * (wall_lvl - 1)
    factor += DEFENSE_FACTOR_PER_SPIRE_LEVEL * (spire_lvl - 1)

    return clamp(factor, 1.0, DEFENSE_FACTOR_MAX)


def calc_loss_rates(expected_win: float, result: str, defense_factor: float) -> Tuple[float, float]:
    """
    Calculate loss rates for attacker and defender.

    Args:
        expected_win: Attacker's expected win probability [0,1]
        result: Battle result from attacker's perspective ("win" or "loss")
        defense_factor: Defender's defense factor from buildings

    Returns:
        Tuple of (attacker_loss_rate, defender_loss_rate)
    """
    p = clamp(expected_win, 0.0, 1.0)
    difficulty = 1.0 - p

    df = clamp(defense_factor, 1.0, DEFENSE_FACTOR_MAX)

    result_norm = result.lower().strip()
    if result_norm not in ("win", "loss"):
        raise ValueError(f"Invalid result: {result}")

    if result_norm == "win":
        # attacker losses: 3%..10%
        att = 0.03 + 0.07 * difficulty
        att = clamp(att, LOSS_RATE_ATT_WIN_MIN, LOSS_RATE_ATT_WIN_MAX)

        # defender losses when attacker wins: 6%..18%
        # uses (1 - difficulty) == p
        deff = 0.06 + 0.12 * (1.0 - difficulty)
        deff = clamp(deff, LOSS_RATE_DEF_LOSS_MIN, LOSS_RATE_DEF_LOSS_MAX)
    else:
        # attacker losses on loss: 8%..25%
        att = 0.08 + 0.17 * difficulty
        att = clamp(att, LOSS_RATE_ATT_LOSS_MIN, LOSS_RATE_ATT_LOSS_MAX)

        # defender losses when attacker loses: 2%..8%
        deff = 0.02 + 0.06 * (1.0 - difficulty)
        deff = clamp(deff, LOSS_RATE_DEF_WIN_MIN, LOSS_RATE_DEF_WIN_MAX)

    # defense modifier
    att = clamp(att * df, 0.0, max(LOSS_RATE_ATT_WIN_MAX, LOSS_RATE_ATT_LOSS_MAX))
    deff = clamp(deff / df, 0.0, max(LOSS_RATE_DEF_LOSS_MAX, LOSS_RATE_DEF_WIN_MAX))

    return att, deff


def apply_losses(counts: Dict[str, int], loss_rate: float) -> Losses:
    """
    Apply loss rate to unit counts, returning actual losses.

    Args:
        counts: Dict of unit type to count {"raider": 50, "guardian": 30}
        loss_rate: Loss rate as decimal (0.10 = 10%)

    Returns:
        Losses dict with full shape {"raider": x, "guardian": y}
    """
    # normalize input
    normalized = {k: max(0, int(counts.get(k, 0))) for k in _UNIT_KEYS}
    total = sum(normalized.values())

    rate = clamp(loss_rate, 0.0, 1.0)

    losses: Losses = {k: int(math.floor(normalized[k] * rate)) for k in _UNIT_KEYS}

    # clamp per type
    for k in _UNIT_KEYS:
        if losses[k] > normalized[k]:
            losses[k] = normalized[k]

    lost_total = sum(losses.values())

    # enforce minimum 1 loss if the attacker/defender had >=10 units and rounding produced 0
    if total >= MINIMUM_LOSS_THRESHOLD and lost_total == 0:
        dominant = max(_UNIT_KEYS, key=lambda k: normalized[k])
        if normalized[dominant] > 0:
            losses[dominant] = MINIMUM_LOSS_UNITS

    # final safety clamp again
    for k in _UNIT_KEYS:
        if losses[k] > normalized[k]:
            losses[k] = normalized[k]

    return losses
