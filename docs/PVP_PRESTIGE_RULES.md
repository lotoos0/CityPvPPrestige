# PvP Prestige Rules (Project Standard)

**Single source of truth:** All PvP prestige constants, caps, and cooldowns
are defined in docs/BALANCE_CONSTANTS.md.

1) Definicje

P_a - prestiż atakującego
P_d - prestiż obrońcy
ΔP = P_d - P_a (różnica prestiżu; dodatnia = atak wyżej w rankingu)

---

2) Oczekiwane prawdopodobieństwo (ELO-light)

Używamy lekkiego ELO, ale nie pełnego (bez krzywych logistycznych w MVP):

expected_win = clamp(0.35 + (ΔP / 2000), 0.15, 0.85)

Atak wyżej w rankingu -> expected_win rośnie wolniej
Atak niżej -> expected_win spada, ale nigdy do zera
clamp chroni przed ekstremami

---

3) Bazowe wartości (stałe projektu)

BASE_GAIN = 30
BASE_LOSS = 25

Zysk jest nieco większy niż strata -> gra zachęca do agresji
Porażki bolą, ale nie kasują sesji

---

4) Finalna zmiana prestiżu

Jeśli atakujący wygra:

prestige_delta_attacker =
  round(BASE_GAIN * (1 + (1 - expected_win)))

Jeśli atakujący przegra:

prestige_delta_attacker =
  -round(BASE_LOSS * (1 + expected_win))

Obrońca:

MVP: 0 (najprościej, najmniej frustracji)

(Opcjonalnie później: +-30% wartości atakującego)

Only the formulas live here. All numeric values must be changed in
docs/BALANCE_CONSTANTS.md only.

---

5) Dlaczego to działa (krótko)

Wygrana z kimś wyżej = duży skok
Farmienie słabszych = mały zysk
Porażka z wyższym = mniejsza kara
Porażka z niższym = boli (i ma boleć)

To tworzy:

ryzyko-nagrodę,
ruch w rankingu,
realną decyzję "czy atakować teraz".

---

6) Ograniczenia anty-abuse (przypięte do prestiżu)

- Max prestige gain per day: 300
- Max prestige loss per day: 250

Chroni:

casuali,
topkę przed snowballem 24/7,
serwer przed nolifami.

---

7) Widoczność w UI (ważne!)

Po każdej walce UI musi pokazać:

+X / -Y prestige

krótką etykietę:

"High-risk victory"

"Farming win"

"Punished for attacking lower rank"

---

Seasonal Rank Decay (Soft Decay to Baseline)

Definitions

P – current prestige

BASE – seasonal base prestige (e.g., 1000; same as season reset)

THRESHOLD – decay starts only above this value (buffer over BASE)

Daily decay (runs at 00:00 server time)

excess = max(0, P - THRESHOLD)

if inactive_days >= INACTIVITY_GRACE:
    rate = DAILY_DECAY_RATE * INACTIVITY_MULT
else:
    rate = DAILY_DECAY_RATE

decay = round(min(DAILY_DECAY_MAX, excess * rate))

P_next = P - decay

Notes

No decay is applied at or below THRESHOLD (mid-ladder is protected).

Decay never pushes a player below THRESHOLD.

PvP prestige changes apply normally; decay is an independent daily tick.

UI

Banner after reset (first login after 00:00, decay > 0):
"Nightly decay applied: -{X} prestige
Excess above the seasonal threshold is trimmed daily.
Inactivity accelerates decay."

Tooltip on rank:
"Prestige above the seasonal threshold is subject to nightly soft-decay.
Decay is minimal for active players and increases with inactivity."

History/log entry:
"System: Nightly soft-decay -{X} prestige"

---

## UI Messaging - PvP Limits & Caps (MVP)

Purpose: clearly communicate PvP limits and prestige caps to prevent
confusion and perceived unfairness. Messages are informational, not punitive.

---

### 1) Approaching Daily Attack Limit

**Trigger:**
- When remaining daily attacks <= 2

**UI Message (non-blocking):**
"Approaching daily PvP limit: {remaining}/{ATTACKS_PER_DAY_LIMIT} attacks left."

**Tooltip / Info:**
"Daily PvP limits reset at 00:00 server time."

---

### 2) Daily Attack Limit Reached

**Trigger:**
- Player attempts to start a PvP battle after reaching ATTACKS_PER_DAY_LIMIT

**UI Message (blocking):**
"Daily PvP limit reached. Resets at 00:00 server time."

**CTA:**
"Check ranking" / "Upgrade city"

---

### 3) Approaching Prestige Gain Cap

**Trigger:**
- Remaining prestige gain for the day <= 50

**UI Message (non-blocking):**
"Approaching daily prestige gain cap."

**Tooltip / Info:**
"Further wins today will grant reduced or no prestige.
Limits reset at 00:00 server time."

---

### 4) Prestige Gain Cap Reached

**Trigger:**
- prestige_gain_today >= PRESTIGE_GAIN_PER_DAY_CAP

**UI Message (non-blocking):**
"Daily prestige gain cap reached."

**Tooltip / Info:**
"You can still fight battles, but additional prestige
will be available after the daily reset."

---

### 5) Prestige Loss Cap Reached

**Trigger:**
- prestige_loss_today >= PRESTIGE_LOSS_PER_DAY_CAP

**UI Message (informational):**
"Daily prestige loss cap reached. Further losses are protected."

**Tooltip / Info:**
"Loss protection resets at 00:00 server time."

---

### 6) Nightly Soft-Decay Notification (Reference)

**Trigger:**
- First login after nightly reset AND decay_amount > 0

**UI Banner:**
"Nightly decay applied: -{decay_amount} prestige."

**Tooltip / Info:**
"Soft-decay trims excess prestige above the seasonal threshold.
Inactivity accelerates decay."

---

## UX Rules
- Never stack multiple blocking messages at once.
- Prefer tooltips for explanations; banners for state changes.
- All limits and caps must reference the daily reset time explicitly.
