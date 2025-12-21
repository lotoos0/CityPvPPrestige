# Data Model

## Entities

### User

- id (uuid, pk)
- email (unique)
- password_hash
- created_at

### City

- id (uuid, pk)
- user_id (fk -> user.id)
- grid_size (int, default 12)
- gold (int)
- pop (int)
- power (int)
- prestige (int, default 1000)
- last_collected_at (timestamp)

### Building

- id (uuid, pk)
- city_id (fk -> city.id)
- type (enum)
- level (int, 1-3)
- x (int)
- y (int)
- placed_at (timestamp)

### AttackLog

- id (uuid, pk)
- attacker_id (fk -> user.id)
- defender_id (fk -> user.id)
- result (win/loss)
- prestige_delta_attacker (int)
- prestige_delta_defender (int)
- created_at (timestamp)

### Season

- id (uuid, pk)
- number (int)
- starts_at (timestamp)
- ends_at (timestamp)
- is_active (bool)

## Building Types and Effects (lvl1-lvl3)

Simple, readable numbers for MVP. Values are per hour for production.

| Building | L1 | L2 | L3 |
| --- | --- | --- | --- |
| Gold Mine | +20 gold/h | +45 gold/h | +80 gold/h |
| House | +5 pop cap | +12 pop cap | +20 pop cap |
| Power Plant | +5 power/h | +12 power/h | +20 power/h |
| Barracks | +3 attack | +7 attack | +12 attack |
| Wall | +4 defense | +9 defense | +15 defense |
| Tower | +2 defense | +5 defense | +9 defense |
| Storage | +200 gold cap | +500 gold cap | +900 gold cap |

Notes:
- Attack power = sum(Barracks bonuses).
- Defense power = attack power + Wall/Tower bonuses.
- Gold cap = base cap (e.g., 200) + sum(Storage bonuses).
