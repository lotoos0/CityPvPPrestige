# MVP: PvP + Army v1 (tag: mvp-pvp-army-v1)

## Scope
This milestone delivers the first complete playable loop:
Train units -> build army -> PvP attack -> see limits/cooldowns -> review battle history.

## Backend (FastAPI)
- Army foundation (DB-first):
  - Unit types: raider, guardian
  - User units inventory
  - Barracks ownership (auto-created for existing users + on registration)
  - Training queue (single-slot): train -> queue -> claim

- PvP system:
  - POST /pvp/attack with caps/cooldowns and strict response contract
  - Hard idempotency via Idempotency-Key (no double prestige / no double stats)
  - Minimum army gate: requires >= 10 total units to attack
  - Nightly prestige soft-decay job (idempotent via system ticks)
  - Systemd service + timer for nightly decay

- API contracts + enforcement:
  - /pvp/attack contract enforced + contract tests
  - /pvp/limits contract enforced + contract tests
  - /pvp/log contract enforced + contract tests
  - Cursor pagination for /pvp/log (base64 JSON cursor: created_at + battle_id)

- Time correctness:
  - Security module uses timezone-aware UTC timestamps

## Frontend (Vanilla JS/HTML/CSS)
- PvP Status HUD (read-only):
  - Limits and global cooldown (cooldowns.global_remaining_sec)
  - Auto-refresh

- Army/Barracks panels:
  - /army: inventory view
  - /barracks/train, /barracks/queue, /barracks/claim
  - Auto-refresh

- PvP Attack History:
  - Reads /pvp/log items and prestige_delta
  - Cursor-based "Load more"
  - Minimal UX polish: loading state + "Loaded X entries"

## Known limitations (intentional)
- /pvp/log does not store expected_win yet (planned for v2).
- /pvp/limits exposes only global cooldown (same-target cooldown is target-dependent).
- No unit losses on PvP yet (planned for v2+).
- No building placement / city grid UI (post-MVP).

## How to run (high level)
- Apply migrations: alembic upgrade head
- Start backend + frontend
- Configure nightly decay timer using docs/ops/NIGHTLY_DECAY_SETUP.md

## Next
Pick one v2 axis:
A) Store expected_win in PvP logs (better diagnostics)
B) Add unit losses and rebalance training/economy (higher complexity)
