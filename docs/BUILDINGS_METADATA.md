# Upgrade Cost Rule (Gold)

All building build and upgrade costs are derived from the building’s
primary effect value E(level) defined in DATA_MODEL.md.

Cost formulas:

- Build cost (Level 1):
  build_cost_gold = round(E1 * K_type)

- Upgrade cost (Level 1 -> Level 2):
  upgrade_cost_gold = round(E2 * K_type)

- Upgrade cost (Level 2 -> Level 3):
  upgrade_cost_gold = round(E3 * K_type)

Where:
- E(level) is the main effect of the building at that level
  (e.g. gold_per_hour, attack_power_bonus, defense_power_bonus, etc.)
- K_type is a fixed multiplier per building type (balance constant)

This rule ensures:
- consistent scaling across all buildings
- easy global rebalance by adjusting K_type only
- no manual tuning per upgrade level

**Single source of truth:** All balance multipliers and numeric constants
are defined in docs/BALANCE_CONSTANTS.md.

Costs in this file must be derived from the cost rule + K_type constants.
Do not hand-tune individual costs outside the formula.

Note:
Building stats influence PvP outcomes indirectly via combat power.
Prestige changes are handled exclusively by PvP rules
defined in PVP_PRESTIGE_RULES.md.

### Town Hall Exception

Town Hall Level 1 is free (starting building).

Town Hall upgrade costs are handled separately and do NOT follow
the standard E(level) x K_type formula.

Town Hall costs are defined explicitly to act as major progression gates,
not as economic or military scaling.

---

# Building metadata (schema + example)

Goal: decouple balance and visuals from code.

---

## Required fields (per building)

- id
- name
- footprint (width, height)
- anchor (x, y) in pixels
- render_layer (ground / shadow / base / top / ui)
- collision_box (x, y, w, h)
- levels (per level: production/bonus + costs)

---

## Example (JSON)

```json
{
  "id": "credit_forge",
  "name": "Credit Forge",
  "footprint": [1, 1],
  "anchor": [64, 96],
  "render_layer": "base",
  "collision_box": [24, 48, 80, 48],
  "levels": {
    "1": {
      "gold_per_hour": 20,
      "build_cost_gold": 600
    },
    "2": {
      "gold_per_hour": 45,
      "upgrade_cost_gold": 1350
    },
    "3": {
      "gold_per_hour": 80,
      "upgrade_cost_gold": 2400
    }
  }
}
```

Notes:
- footprint is [width, height] in tiles.
- anchor uses tile-relative pixels (based on 128x64).

---

## MVP set (JSON)

Placeholders:
- upgrade_costs are initial placeholders for balance pass.
- render_layer is "base" for now; split to base/top later if needed.

```json
[
  {
    "id": "central_command_core",
    "name": "Central Command Core",
    "footprint": [1, 1],
    "anchor": [64, 64],
    "render_layer": "base",
    "collision_box": [24, 32, 80, 32],
    "levels": {
      "1": { "build_cost_gold": 0 },
      "2": { "upgrade_cost_gold": 2500 },
      "3": { "upgrade_cost_gold": 6500 }
    }
  },
  {
    "id": "habitat_block",
    "name": "Habitat Block",
    "footprint": [1, 1],
    "anchor": [64, 64],
    "render_layer": "base",
    "collision_box": [24, 32, 80, 32],
    "levels": {
      "1": { "pop_cap": 5, "build_cost_gold": 300 },
      "2": { "pop_cap": 12, "upgrade_cost_gold": 720 },
      "3": { "pop_cap": 20, "upgrade_cost_gold": 1200 }
    }
  },
  {
    "id": "credit_forge",
    "name": "Credit Forge",
    "footprint": [1, 1],
    "anchor": [64, 64],
    "render_layer": "base",
    "collision_box": [24, 32, 80, 32],
    "levels": {
      "1": { "gold_per_hour": 20, "build_cost_gold": 600 },
      "2": { "gold_per_hour": 45, "upgrade_cost_gold": 1350 },
      "3": { "gold_per_hour": 80, "upgrade_cost_gold": 2400 }
    }
  },
  {
    "id": "security_complex",
    "name": "Security Complex",
    "footprint": [1, 1],
    "anchor": [64, 64],
    "render_layer": "base",
    "collision_box": [24, 32, 80, 32],
    "levels": {
      "1": { "attack": 3, "build_cost_gold": 420 },
      "2": { "attack": 7, "upgrade_cost_gold": 980 },
      "3": { "attack": 12, "upgrade_cost_gold": 1680 }
    }
  },
  {
    "id": "perimeter_shield_wall",
    "name": "Perimeter Shield Wall",
    "footprint": [1, 1],
    "anchor": [64, 64],
    "render_layer": "base",
    "collision_box": [24, 32, 80, 32],
    "levels": {
      "1": { "defense": 4, "build_cost_gold": 440 },
      "2": { "defense": 9, "upgrade_cost_gold": 990 },
      "3": { "defense": 15, "upgrade_cost_gold": 1650 }
    }
  },
  {
    "id": "vault_depot",
    "name": "Vault Depot",
    "footprint": [1, 1],
    "anchor": [64, 64],
    "render_layer": "base",
    "collision_box": [24, 32, 80, 32],
    "levels": {
      "1": { "gold_cap": 200, "build_cost_gold": 120 },
      "2": { "gold_cap": 500, "upgrade_cost_gold": 300 },
      "3": { "gold_cap": 900, "upgrade_cost_gold": 540 }
    }
  },
  {
    "id": "surveillance_spire",
    "name": "Surveillance Spire",
    "footprint": [1, 1],
    "anchor": [64, 64],
    "render_layer": "base",
    "collision_box": [24, 32, 80, 32],
    "levels": {
      "1": { "defense": 2, "build_cost_gold": 260 },
      "2": { "defense": 5, "upgrade_cost_gold": 650 },
      "3": { "defense": 9, "upgrade_cost_gold": 1170 }
    }
  }
]
```
