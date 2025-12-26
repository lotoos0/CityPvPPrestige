# Changelog

## Unreleased

## city-loop-v1.1

### Added
- Gold collect feedback (+X animation)
- Disabled upgrade button with clear reasons
- Grid badges for building type and level

### City Building
- Added **grid-based building system** with tile selection and action panel (frontend)
- Enabled **building placement and upgrades** in city view using catalog-based costs
- Implemented **build and upgrade endpoints** with resource cost validation and production tick
- Exposed **buildings catalog** for frontend build menu
- Enforced **unique tile occupancy** - only one building per grid position
- Added **lazy production tick** on city endpoint to update resources before display
- Gold production now **clamped to city storage capacity**
- Collect now **refreshes production state** and reports actual gains

### Army & Combat
- Added **unit types and barracks ownership** with training queue system
- Implemented **barracks training API** - queue units, claim when ready
- Added **army management UI** - train units, view queue, claim trained troops
- Enforced **minimum army requirement** to initiate PvP attacks
- Integrated **event bus** to refresh army view after attacks

### PvP System
- Implemented **attack/defense stat calculations** based on buildings and units
- Added **PvP attack endpoint** with prestige rewards and resource raiding
- Built **attack history system** with cursor-based pagination
- Tracked and displayed **unit losses** for both attacker and defender
- Added **expected win probability** display in attack history
- Implemented **PvP caps and cooldowns** (per-player and global)
- Added **read-only PvP limits HUD** showing current restrictions
- Enforced strict **API response contracts** with validation tests

### Ranking & Prestige
- Created **prestige-based ranking** endpoints and UI
- Implemented **seasonal prestige resets** to restart competition
- Added **nightly soft-decay** for prestige above seasonal threshold
  - Excess prestige trimmed daily to prevent rank stagnation
  - Inactivity accelerates decay rate
- Deployed **systemd service/timer** for automated nightly decay job

### Frontend Architecture
- Refactored **SPA into router + views pattern** for better organization
- Improved **view switching stability** - preserved state like cooldowns
- Enhanced **PvP history UX** with loading states and pagination
- Introduced **FOE-like layout** with resource topbar, sidebar navigation, and game-style toasts
- Refined **FOE-like chrome** with heavier panels, bevels, and material styling
- Added **tile level badges** and upgrade indicators for city grid readability
- Added **gold delta animation** on collect to reinforce resource gains
- Added **disabled upgrade state** with tooltip reason for insufficient gold or max level
- Switched **city grid to isometric layout** (placeholder tiles, no sprites)
- Added **debug label toggle** to reduce visual noise in isometric grid

### Infrastructure & Quality
- Pinned backend to **Python 3.12** for reproducible installs
- Added **contract tests** for API endpoints (city, PvP, army)
- Fixed **timezone-aware UTC timestamps** in security module
- Added **validation tests** for build/upgrade cost enforcement
- Documented **asset sources** and added building graphics
