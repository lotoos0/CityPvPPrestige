Założenie: przeglądarka + backend.

---

# Sprint MVP: 14 dni (krok po kroku)

## Dzień 1 — Repo + plan + scope lock

- [x] Utwórz repo (np. `CityPvPPrestige`)
- [x] Zrób foldery: `/frontend`, `/backend`, `/docs`
- [x] `docs/MVP_SPEC.md`:
  - [x] core loop
  - [x] systemy (grid, 3 zasoby, 7 budynków)
  - [x] PvP asynchro
  - [x] ranking
  - [x] sezon (14 dni, reset prestiżu)

- [x] `docs/DECISIONS.md` (żeby nie wracać do tematów):
  - [x] „Brak gildii/GBG w MVP”
  - [x] „Reset tylko prestiżu”
  - [x] limity ataków
        **Done:** masz repo + 2 dokumenty, commit `day01`.

## Dzień 2 — Model danych (papier → schema)

- [x] Rozpisz encje (w `docs/DATA_MODEL.md`):
  - [x] User
  - [x] City (grid)
  - [x] Building (type, level, x, y)
  - [x] Resources (gold, pop, power)
  - [x] AttackLog (attacker, defender, result, prestige_delta, timestamp)
  - [x] Season (start/end)

- [x] Ustal 7 budynków + ich efekty lvl1–lvl3 (proste liczby)
      **Done:** tabela z parametrami budynków i zasobów.

## Dzień 3 — Backend: szkielet + DB + migracje

- [x] Backend start (FastAPI)
- [x] Postgres + docker compose dla backendu
- [x] Migracje (Alembic) lub prosty init schema
- [x] Endpoint healthcheck `/health`
      **Done:** `docker compose up` i `/health` działa.

## Dzień 4 — Auth + User

- [x] Rejestracja / login (JWT)
- [x] Tabela users
- [x] Endpoint `/me`
      **Done:** możesz stworzyć konto, zalogować się, dostać `me`.

## Dzień 5 — City: zapis i odczyt miasta

- [x] Endpoint: `GET /city` (zwraca grid + budynki + zasoby)
- [x] Endpoint: `POST /city/build` (stawia budynek na polu)
- [x] Walidacja: pole wolne, typ budynku dozwolony
      **Done:** z Postmana/Insomnii stawiasz budynek i widzisz go w `GET /city`.

## Dzień 6 — Produkcja zasobów (serwerowa, nie „fejk timer”)

- [x] Dodaj `last_collected_at`
- [x] Endpoint: `POST /city/collect`
  - nalicza produkcję od ostatniego collect
  - aktualizuje zasoby

- [x] Prosty cap na gold (Storage)
      **Done:** mija czas → collect daje więcej gold.

## Dzień 7 — Frontend: minimalny UI (brzydkie, ale działa)

- [x] Login/register
- [x] Ekran miasta: grid 12×12 (proste kwadraty)
- [x] Klik na pole → buduj (dropdown 7 budynków)
- [x] Przycisk „Collect”
- [x] Wyświetl zasoby (gold/pop/power/prestige)
      **Done:** da się grać w „stawiam, collectuję” z UI.

## Dzień 8 — Staty: Power i Defense z miasta

- [x] Na backendzie licz:
  - `attack_power = sum(Barracks level bonus)`
  - `defense_power = attack_power + (Wall/Tower bonus)`

- [x] Endpoint `/stats`
- [ ] Front pokazuje Attack/Defense
      **Done:** budynki realnie zmieniają siłę.

## Dzień 9 — PvP: endpoint ataku (1v1 asynchro)

- [x] Endpoint: `POST /pvp/attack {defender_id}`
- [x] Walidacja:
  - cooldown 30 min na tego samego obrońcę
  - limit 20 ataków/dzień

- [x] Wynik walki:
  - porównanie attack vs defense + losowość ±10%

- [x] Zapisz AttackLog
      **Done:** możesz zaatakować, dostać wynik, zapis w DB.

## Dzień 10 — Prestiż (model prosty i czytelny)

- [x] Implementuj ELO-light (na start):
  - win vs wyżej: +30
  - win vs niżej: +10
  - lose vs wyżej: -10
  - lose vs niżej: -25

- [x] Aktualizacja prestiżu obu stron (opcjonalnie tylko atakującego w MVP, ale lepiej obu)
      **Done:** ataki realnie ruszają ranking.

## Dzień 11 — Ranking + „sąsiedzi”

- [x] Endpoint `GET /rank/top` (Top 10)
- [x] Endpoint `GET /rank/near` (±3 wokół Ciebie)
- [x] Front: ekran Rankingu
- [x] Front: przycisk „Attack” przy graczach z listy
      **Done:** pętla „ranking → atak” istnieje.

## Dzień 12 — Historia ataków (retencja)

- [x] Endpoint `GET /pvp/log`
- [x] Front: lista ostatnich ataków (kto, wynik, delta prestiżu, kiedy)
- [x] Front: komunikat „spadłeś / wzrosłeś”
      **Done:** gracz wie, co się dzieje i dlaczego.

## Dzień 13 — Sezon (wersja 1)

- [x] Tabela Season + start/end
- [x] Komenda admin / endpoint do startu nowego sezonu (na MVP ręcznie)
- [x] „Reset prestiżu do 1000” dla wszystkich przy rollover
- [x] Front: licznik sezonu (nawet statyczny)
      **Done:** potrafisz odpalić reset i ranking startuje od nowa.

## Dzień 14 — Stabilizacja + test „czy to jest gra?”

- [x] Test scenariusza:
  - nowe konto → budowa → collect → atak → ranking → log

- [x] Napraw 5 największych bugów
- [x] README: jak odpalić lokalnie
- [x] Lista „Milestone 2” (gildie + mapa sektorów później)
      **Done:** ktoś obcy odpala i rozumie w 2 minuty „co tu się robi”.

---

## Zasady, żebyś tego nie spalił

- Każdy dzień kończy się **commitem** (`dayXX: ...`).
- Jak zaczniesz grzebać w UI / grafice przed Dniem 11 → sabotujesz projekt.
- Jak dopiszesz „tylko jeszcze gildie” przed Dniem 14 → zabijasz MVP.

---
