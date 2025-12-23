from zoneinfo import ZoneInfo

SERVER_TZ = ZoneInfo("Europe/Warsaw")

# Type alias for unit losses
Losses = dict[str, int]  # {"raider": 2, "guardian": 1}


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))

COOLDOWN_MINUTES = 30
GLOBAL_ATTACK_COOLDOWN_SEC = 30
DAILY_ATTACK_LIMIT = 20
PRESTIGE_GAIN_CAP = 300
PRESTIGE_LOSS_CAP = 250

BASE_GAIN = 30
BASE_LOSS = 25
EXPECTED_WIN_BASE = 0.35
EXPECTED_WIN_DIVISOR = 2000
EXPECTED_WIN_MIN = 0.15
EXPECTED_WIN_MAX = 0.85

DECAY_THRESHOLD = 1200
DAILY_DECAY_RATE = 0.06
DAILY_DECAY_MAX = 60
INACTIVITY_GRACE = 2
INACTIVITY_MULT = 1.5

PVP_MIN_ARMY_UNITS = 10

# Unit loss rates (V2-B)
# Attacker losses when WIN
LOSS_RATE_ATT_WIN_MIN = 0.03
LOSS_RATE_ATT_WIN_MAX = 0.10
LOSS_RATE_ATT_WIN_DIFFICULTY_FACTOR = 0.07

# Attacker losses when LOSS
LOSS_RATE_ATT_LOSS_MIN = 0.08
LOSS_RATE_ATT_LOSS_MAX = 0.25
LOSS_RATE_ATT_LOSS_DIFFICULTY_FACTOR = 0.17

# Defender losses when attacker WIN (defender lost)
LOSS_RATE_DEF_LOSS_MIN = 0.06
LOSS_RATE_DEF_LOSS_MAX = 0.18
LOSS_RATE_DEF_LOSS_EASE_FACTOR = 0.12

# Defender losses when attacker LOSS (defender won)
LOSS_RATE_DEF_WIN_MIN = 0.02
LOSS_RATE_DEF_WIN_MAX = 0.08
LOSS_RATE_DEF_WIN_EASE_FACTOR = 0.06

# Defense factor from buildings
DEFENSE_FACTOR_BASE = 1.0
DEFENSE_FACTOR_PER_WALL_LEVEL = 0.05
DEFENSE_FACTOR_PER_SPIRE_LEVEL = 0.05
DEFENSE_FACTOR_MIN = 1.0
DEFENSE_FACTOR_MAX = 1.2

# Minimum losses (if army >= 10 and losses == 0)
MINIMUM_LOSS_THRESHOLD = 10
MINIMUM_LOSS_UNITS = 1

# Keep in sync with docs/BALANCE_CONSTANTS.md
