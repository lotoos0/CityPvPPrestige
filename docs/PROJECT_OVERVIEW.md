# Project Overview — _Prestige Wars_ (working title)

## 1. What this project is

This project is a **browser-based strategic city-builder PvP game**, developed as a **side project**, with a strong focus on:

- player competition,
- prestige and ranking as the main progression metric,
- asynchronous 1v1 PvP battles,
- seasonal resets.

The game is **not a clone of Forge of Empires**, but it is **inspired by its competitive elements** (rankings, prestige, PvP), implemented with a **much smaller and controlled MVP scope**.

The goal of this project is **not** to build a full-scale MMO, but to deliver a **playable, testable MVP** that can be iterated on and expanded over time.

---

## 2. Core design philosophy

### 2.1. Player goal

The player’s goal is **not** to build a beautiful city.
The city is a **tool** used to:

- increase combat power,
- win PvP battles,
- gain prestige,
- climb the global ranking.

**Prestige and ranking are the core of the game.**

---

### 2.2. Why players return

Players log back in because:

- they may have lost ranking positions,
- they may have been attacked by other players,
- they can retaliate against players ranked above them,
- the season is ending and competition intensifies.

The game is built around **tension, competition, and visible consequences**, not passive waiting.

---

## 3. Core Gameplay Loop

1. Player logs into the game
2. Collects city resource production
3. Checks ranking and current position
4. Identifies potential PvP targets
5. Attacks another player (asynchronous 1v1 PvP)
6. Receives battle result and prestige change
7. Upgrades the city to prepare for future battles
8. Logs out while the ranking remains at risk

Every system in the MVP **must support this loop**.

---

## 4. MVP Scope (Scope Lock)

### 4.1. Included in MVP

- browser-based game (desktop-first),
- single city per player on a grid,
- time-based resource production,
- 3 resources + prestige,
- 7 building types (3 levels each),
- asynchronous 1v1 PvP,
- global prestige ranking,
- seasonal system (14 days),
- **prestige-only reset** between seasons.

---

### 4.2. Explicitly excluded from MVP

- guilds,
- Guild Battlegrounds / territory wars,
- time-limited events,
- ages / technology trees,
- player trading,
- real-time PvP,
- monetization,
- mobile application,
- advanced graphics or animations.

These features are **deliberately postponed** to later development phases.

---

## 5. City system (MVP)

- Each player owns **one city**.
- The city is built on a **12×12 grid**.
- Each building occupies **one tile**.
- No decorative buildings — only functional ones.
- The city **persists between seasons**.

### Buildings available in MVP:

1. **Town Hall** – starting building
2. **House** – increases population
3. **Mint** – produces gold
4. **Barracks** – increases attack power
5. **Wall** – increases defense
6. **Storage** – increases resource capacity
7. **Scout Tower** – defensive / anti-attack bonus

Each building has **a maximum of 3 levels**.

---

## 6. Resources and Prestige

### Resources:

- **Gold** – currency used for construction and upgrades
- **Population** – limits city expansion
- **Power** – determines combat strength

### Prestige:

- the primary progression metric,
- the only ranking factor,
- gained and lost **exclusively through PvP combat**.

---

## 7. PvP system — asynchronous 1v1

- Players attack a **snapshot** of another player’s city.
- Battle resolution is fully server-side.
- Combat compares:
  - attacker’s attack power,
  - defender’s defense power,
  - a small randomness factor (±10%).

### Anti-abuse limits:

- 30-minute cooldown for attacking the same player,
- daily attack limit of 20 battles.

---

## 8. Prestige and ranking system

Prestige model (MVP, ELO-light):

- win vs higher-ranked opponent → **large prestige gain**
- win vs lower-ranked opponent → **small prestige gain**
- loss → **prestige loss**, regardless of opponent

Ranking system:

- global leaderboard,
- Top 10 always visible,
- “neighbor view” showing ±3 positions around the player.

---

## 9. Seasons

- Each season lasts **14 days**.
- At the end of a season:
  - all players’ prestige resets to a base value,
  - cities and buildings remain unchanged.

- Seasons prevent permanent ranking stagnation and keep competition fresh.

---

## 10. Project objectives

The objectives of this project are to:

- deliver a **fully playable MVP**,
- validate the prestige-based competitive loop,
- build a solid foundation for future features such as:
  - guilds,
  - territory control maps,
  - Guild Battleground–style systems.

This project prioritizes **clarity, scope control, and iteration** over feature quantity.
