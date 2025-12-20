# Balance constants (single source)

Keep all tuneable numbers here. Change these before touching formulas.

---

## Building cost multipliers (K_type)

- gold_mine: 30
- house: 60
- barracks: 140
- wall: 110
- scout_tower: 130
- storage: 0.6

Town Hall is defined explicitly (see PVP and metadata docs).

---

## PvP prestige constants

- BASE_GAIN: 30
- BASE_LOSS: 25
- expected_win_clamp_min: 0.15
- expected_win_clamp_max: 0.85
- expected_win_base: 0.35
- expected_win_divisor: 2000

---

## Prestige daily caps

- max_gain_per_day: 300
- max_loss_per_day: 250

---

## Seasonal Soft-Decay (Anti-Stagnation)

- SEASON_BASE_PRESTIGE (BASE): 1000
- DECAY_THRESHOLD (THRESHOLD): 1200
- DAILY_DECAY_RATE: 0.06
- DAILY_DECAY_MAX: 60
- INACTIVITY_GRACE: 2
- INACTIVITY_MULT: 1.5

---

## PvP Daily Caps (MVP)

- ATTACKS_PER_DAY_LIMIT: 20
- PRESTIGE_GAIN_PER_DAY_CAP: 300
- PRESTIGE_LOSS_PER_DAY_CAP: 250

---

## PvP Cooldowns (MVP)

- ATTACK_SAME_TARGET_COOLDOWN_MIN: 30
- GLOBAL_ATTACK_COOLDOWN_SEC: 30

---

## Daily Reset

- DAILY_RESET_TIME: 00:00 (server time)

---

## MVP Validation Note

Caps, cooldowns, and soft-decay were validated against
casual / regular / grinder scenarios and are locked for MVP.
Adjust only after telemetry review.
