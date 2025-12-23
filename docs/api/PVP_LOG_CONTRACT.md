# GET /pvp/log - Response Contract (MVP)

This document defines the strict response contract for the PvP log endpoint.

Version: v1 (MVP)

---

## Endpoint
GET /pvp/log?limit=20&cursor=<optional>

Query params:
- limit: integer (1..50)
- cursor: opaque base64 JSON (optional)

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
      "expected_win": 0.63,
      "units_lost_attacker": {
        "raider": 2,
        "guardian": 0
      },
      "units_lost_defender": {
        "raider": 3,
        "guardian": 1
      },
      "created_at": "2025-12-21T18:42:00+01:00"
    }
  ],
  "next_cursor": "opaque|string|null"
}
```

Example cursor (base64 JSON):
`eyJjcmVhdGVkX2F0IjoiMjAyNS0xMi0yMVQxODo0MjowMCswMTowMCIsImJhdHRsZV9pZCI6IjU4MjZjNzYyLWEyMTAtNDM1YS05NzY4LTkxM2Q1Njg5YmQwMCJ9`

Field semantics

prestige_delta - final applied delta for the current user.

expected_win - win probability snapshot for the attacker at the moment of battle (null for legacy logs).

units_lost_attacker / units_lost_defender - unit losses for attacker and defender.
Both fields are ALWAYS present. Both keys (raider, guardian) are ALWAYS present (>= 0).
For legacy logs (before V2-B), both fields return {"raider": 0, "guardian": 0}.

next_cursor - opaque pagination cursor (null if no more).

---

## Contract Rules

Backend must not remove or rename fields in v1 without bumping contract version.

Frontend must ignore unknown extra fields.

All timestamps are server time with timezone offset.
