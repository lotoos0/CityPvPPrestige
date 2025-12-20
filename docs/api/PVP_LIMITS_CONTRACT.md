# GET /pvp/limits - Response Contract (MVP)

This document defines the strict response contract for the PvP limits endpoint.

Version: v1 (MVP)

---

## Endpoint
GET /pvp/limits

---

## 200 OK - Success Response

```json
{
  "limits": {
    "reset_at": "2025-12-20T00:00:00+01:00",

    "attacks_used": 7,
    "attacks_left": 13,

    "prestige_gain_today": 180,
    "prestige_gain_left": 120,

    "prestige_loss_today": 60,
    "prestige_loss_left": 190
  },

  "nightly_decay": 36,
  "nightly_decay_applied_at": "2025-12-19T00:00:00+01:00",

  "cooldowns": {
    "global_available_at": "2025-12-20T21:33:12+01:00",
    "same_target_available_at": "2025-12-20T22:02:00+01:00"
  }
}
```

Field semantics

limits - required wrapper; fields match POST /pvp/attack.limits.

limits.reset_at - required; server timestamp for the next daily reset.

nightly_decay - optional; last applied decay amount for the current user (null if none).

nightly_decay_applied_at - optional; server timestamp when nightly decay was applied.

cooldowns - optional; current cooldown snapshots (null if not provided).

---

## Contract Rules

Backend must not remove or rename fields in v1 without bumping contract version.

Frontend must ignore unknown extra fields.

All timestamps are server time with timezone offset.

limits.reset_at must always be present.
