# POST /pvp/attack - Response Contract (MVP)

This document defines a strict response contract for the PvP attack endpoint.
Frontend must rely only on fields defined here.

Version: v1 (MVP)

---

## Endpoint
POST /pvp/attack

Request body:
```json
{ "defender_id": "uuid" }
```

Required headers:

Idempotency-Key: <uuid>

Optional headers (test env only):

X-Test-* (blocked outside APP_ENV=test)

---

## 200 OK - Success Response

```json
{
  "battle_id": "string",
  "attacker_id": "uuid",
  "defender_id": "uuid",

  "result": "win|loss",
  "expected_win": 0.42,

  "prestige": {
    "delta": 12,
    "attacker_before": 1300,
    "attacker_after": 1312
  },

  "limits": {
    "reset_at": "2025-12-20T00:00:00+01:00",
    "attacks_used": 7,
    "attacks_left": 13,

    "prestige_gain_today": 180,
    "prestige_gain_left": 120,

    "prestige_loss_today": 60,
    "prestige_loss_left": 190
  },

  "cooldowns": {
    "global_available_at": "2025-12-20T21:33:12+01:00",
    "same_target_available_at": "2025-12-20T22:02:00+01:00"
  },

  "messages": [
    "APPROACHING_ATTACK_CAP",
    "APPROACHING_GAIN_CAP"
  ]
}
```

Field semantics

battle_id - unique ID of the PvP battle log entry.

expected_win - value used in prestige calculation (for transparency/UI tooltips).

prestige.delta - final applied delta AFTER clamps/caps.

limits.* - snapshot AFTER the battle is processed.

cooldowns.* - timestamps when the next action becomes available.

If a cooldown is not applicable, return null.

messages[] - lightweight codes to drive UI banners/toasts.

---

## Message Codes (MVP)

Frontend must treat these as informational.

APPROACHING_ATTACK_CAP

ATTACK_CAP_REACHED (usually returned via error response)

APPROACHING_GAIN_CAP

GAIN_CAP_REACHED

LOSS_CAP_REACHED

TARGET_COOLDOWN

GLOBAL_COOLDOWN

Nightly decay uses separate UI messages and is returned via: GET /pvp/limits
(optional field) or user profile banner (implementation-specific).

---

## Error Responses (MVP)

### 400 / 422 - Validation

Returned when input is invalid (e.g. missing defender_id, missing Idempotency-Key).

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "..."
  }
}
```

### 409 - Idempotency Pending / Conflict

Returned when an idempotency record exists but response is not ready (pending),
or when the same key is reused with a different payload.

```json
{
  "error": {
    "code": "IDEMPOTENCY_CONFLICT",
    "message": "Request with this Idempotency-Key is pending or conflicts."
  }
}
```

### 429 - Cooldown or Cap Blocks

```json
{
  "error": {
    "code": "ATTACK_CAP_REACHED|TARGET_COOLDOWN|GLOBAL_COOLDOWN",
    "message": "...",
    "reset_at": "2025-12-20T00:00:00+01:00"
  }
}
```

---

## Contract Rules

Backend must not remove or rename fields in v1 without bumping contract version.

Frontend must ignore unknown extra fields.

All timestamps are server time with timezone offset.

limits.reset_at must always be present.

---

## Follow-up

1) Ensure /pvp/attack returns these fields OR adjust this contract to reality.
2) Add a response schema for this contract in backend/app/schemas.py.
3) Add a small contract test (at least limits.reset_at and prestige.delta).
