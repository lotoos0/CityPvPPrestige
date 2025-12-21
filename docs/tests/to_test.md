# Test plan after PvP/caps/decay changes

Scope: backend changes around PvP limits, prestige, cooldowns, and nightly decay.

---

## 1) Migrations / data

- Run `alembic upgrade head` and verify:
  - `users.prestige` is populated from `cities.prestige`.
  - New tables exist: `pvp_daily_stats`, `pvp_attack_cooldowns`,
    `prestige_decay_log`, `system_ticks`.
  - New columns in `attack_logs` exist and accept inserts.

---

## 2) PvP attack flow

- Attack a valid defender and verify:
  - `pvp_attack_cooldowns` gets a row for (attacker, defender).
  - `pvp_daily_stats` is created for today and `attacks_used` increments.
  - `attack_logs` row includes `expected_win`, `attacker_prestige_before`,
    `defender_prestige_before`, power fields.
  - `users.prestige` updates by returned delta.

---

## 3) Daily caps (attacks, gain, loss)

- Attacks cap:
  - Perform 20 attacks in one day.
  - 21st attack returns 429 with "Daily attack limit reached".

- Prestige gain cap (clamp):
  - Force wins until daily gain is close to 300.
  - Next win clamps delta so `prestige_gain` == 300.
  - Further wins give 0 delta.

- Prestige loss cap (clamp):
  - Force losses until daily loss is close to 250.
  - Next loss clamps delta so `prestige_loss` == 250.
  - Further losses give 0 delta.

---

## 4) Cooldowns

- Same target cooldown:
  - Attack the same defender twice within 30 minutes.
  - Second attempt returns 429 with "Target on cooldown".

- Global cooldown:
  - Attack twice within 30 seconds (any target).
  - Second attempt returns 429 with "Global attack cooldown".

---

## 5) /pvp/limits endpoint

- Fresh day with no attacks:
  - `attacks_used=0`, `attacks_left=20`,
    `prestige_gain_today=0`, `prestige_loss_today=0`,
    `reset_at` is next midnight server time.

- After some attacks:
  - Values reflect `pvp_daily_stats`.

---

## 6) Nightly soft-decay job

- Run `python -m app.jobs.nightly_decay` twice on the same day:
  - First run applies decay and writes `system_ticks` row.
  - Second run does nothing (idempotent).

- Verify decay logic:
  - No decay at or below threshold (1200).
  - Above threshold: decay = min(60, round(excess * 0.06)).
  - Inactive >= 2 days applies 1.5x rate.
  - `prestige_decay_log` entries are written.

---

## 7) Ranking / city prestige consistency

- `GET /rank/top` and `/rank/near` use `users.prestige`.
- `GET /city` returns prestige from `users.prestige`.

---

## 8) Idempotency (duplicate requests)

- Send the same `Idempotency-Key` twice:
  - Second response returns the first response payload.
  - No additional `attacks_used` increment.
  - No additional prestige change or attack log entry.

- Send two concurrent requests with the same key:
  - One succeeds, the other returns 409 "Request in progress" or the cached response.

---

## 9) /pvp/log response and result normalization

- GET `/pvp/log` returns object with `items` and `next_cursor`.
- Each `items` entry has: `battle_id`, `attacker_id`, `attacker_email`,
  `defender_id`, `defender_email`, `result`, `prestige_delta`, `created_at`.
- `prestige_delta` and `result` are computed from the current user perspective.
- `next_cursor` is `null` on last page; for more entries returns a valid cursor.
- GET `/pvp/log?limit=1` returns a single entry.
- GET `/pvp/log?cursor=<invalid>` returns 400.
- Attack result stored in `attack_logs.result` is `win` or `loss` (no `lose`).

---

## 10) Frontend - Attack History

- Attack History shows latest entries from `/pvp/log` without console errors.
- Correct opponent email and `win`/`loss` status are displayed.
- Prestige delta sign matches backend values.

---

## PvP deterministic tests (APP_ENV=test)

Some PvP integration tests rely on test-only request headers enabled only when:
`APP_ENV=test`.

Supported headers (test env only):
- `X-Test-Force-Result: win|loss` - forces battle outcome
- `X-Test-Force-Delta: <int>` - forces raw prestige delta (before caps/clamp)
- `X-Test-Ignore-Cooldowns: true` - bypasses cooldown checks for test determinism

Security note:
These headers must never be enabled outside `APP_ENV=test`.
