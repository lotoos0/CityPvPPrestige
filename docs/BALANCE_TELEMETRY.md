# Balance Telemetry (MVP)

Goal: collect minimal data to tune balance constants without guessing.
No external analytics required.

---

## 1) Daily KPIs (server time)

### Activity
- DAU: daily active users (logged in at least once)
- PvP Active Users: users with >= 1 PvP battle
- Avg Battles per PvP User
- % Users hitting ATTACKS_PER_DAY_LIMIT

### Prestige Flow
- Avg Prestige Gain per PvP User per day
- Avg Prestige Loss per PvP User per day
- % Users hitting PRESTIGE_GAIN_PER_DAY_CAP
- % Users hitting PRESTIGE_LOSS_PER_DAY_CAP

### Soft-Decay Impact
- % Users above DECAY_THRESHOLD
- Avg Nightly Decay (only users with decay > 0)
- Total Nightly Decay (sum) vs Total Daily Prestige Gain (sum)
- % Users affected by inactivity multiplier
- Avg Inactive Days among affected users

### Ladder Health
- Top10 Prestige Range: (P10 - P1)
- Top100 Prestige Range: (P100 - P1)
- Median Prestige (P50)
- Rank Mobility: avg absolute rank change per day (for users with >= 1 battle)
- Time-to-Recover: avg days to return to previous peak after loss (optional)

---

## 2) Event Log (minimal schema)

Record these events:

### PvP Battle Result
- ts
- attacker_id
- defender_id
- attacker_prestige_before
- defender_prestige_before
- result (win/loss)
- prestige_delta_attacker
- expected_win
- attacker_attack_power
- defender_defense_power

### Nightly Soft-Decay Tick
- ts
- user_id
- prestige_before
- prestige_after
- decay_amount
- inactive_days
- rate_used

### Daily Cap Hit (optional but useful)
- ts
- user_id
- cap_type (attacks / gain / loss)
- value_at_hit

---

## 3) Weekly Summary (human-readable)

Once per week, generate a short report:

- Are players hitting daily limits too often?
- Is soft-decay removing too much prestige (sum decay vs sum gain)?
- Is Top10 range expanding (stagnation) or collapsing (too volatile)?
- Are inactive players punished too hard?

---

## 4) Tuning Triggers (rules of thumb)

Adjust constants only when data confirms:

- If >20% of PvP users hit attack cap daily:
  -> increase ATTACKS_PER_DAY_LIMIT by +5 OR reduce GLOBAL_ATTACK_COOLDOWN

- If sum nightly decay > 35% of sum daily gains:
  -> reduce DAILY_DECAY_RATE or increase DECAY_THRESHOLD

- If Top10 range grows every week (P1 runs away):
  -> increase DAILY_DECAY_RATE slightly OR lower DAILY_DECAY_MAX cap? (careful)

- If rank mobility is near zero (players don’t move):
  -> increase BASE_GAIN/BASE_LOSS slightly OR lower DECAY_THRESHOLD

- If players churn after big loss days:
  -> lower PRESTIGE_LOSS_PER_DAY_CAP OR lower BASE_LOSS

---

## 5) Implementation Notes (MVP friendly)

- Store events in DB (append-only table).
- Export daily aggregates as JSON/CSV.
- No need for dashboards in MVP.

---

Minimal set (if you want even simpler):

- % users above threshold
- sum daily gains
- sum nightly decay
- % hitting attack cap

---

Next step:
Add this file and commit: docs(balance): add MVP telemetry metrics and tuning triggers
