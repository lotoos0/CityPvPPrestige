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
