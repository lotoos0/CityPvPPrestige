# GET /pvp/log - Response Contract (MVP)

This document defines the strict response contract for the PvP log endpoint.

Version: v1 (MVP)

---

## Endpoint
GET /pvp/log?limit=20&cursor=<optional>

---

## 200 OK - Success Response

```json
{
  "items": [
    {
      "battle_id": "uuid",
      "attacker_id": "uuid",
      "attacker_email": "user@example.com",
      "defender_id": "uuid",
      "defender_email": "user@example.com",
      "result": "win|loss",
      "prestige_delta": 12,
      "created_at": "2025-12-21T18:42:00+01:00"
    }
  ],
  "next_cursor": "opaque|string|null"
}
```

Field semantics

prestige_delta - final applied delta for the current user.

next_cursor - opaque pagination cursor (null if no more).

---

## Contract Rules

Backend must not remove or rename fields in v1 without bumping contract version.

Frontend must ignore unknown extra fields.

All timestamps are server time with timezone offset.
