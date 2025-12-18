# MVP Spec

## Core loop

1. Player logs in.
2. Player builds in a 12x12 city grid.
3. Resources generate over time; player collects.
4. Player attacks others asynchronously.
5. Prestige changes and ranking updates.
6. Repeat: build -> collect -> attack -> climb.

## Systems

- Grid: 12x12, one building per tile.
- Resources: gold, pop, power.
- Buildings: 7 types, 3 levels each.
- Production and bonuses are simple and readable.

## Async PvP

- Attack is a single request with immediate result.
- Cooldown per defender and daily attack limit.
- Result uses attack vs defense with +/- 10% randomness.

## Ranking

- Prestige-based ladder.
- Top 10 and near-me views.
- Prestige updates after each attack.

## Season

- 14-day season.
- New season resets prestige to 1000.
- Only prestige resets in MVP.
