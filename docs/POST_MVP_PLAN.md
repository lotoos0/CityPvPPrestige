# Post-MVP plan (notatki robocze)

Założenie: mamy działające MVP. Ten dokument zbiera pomysły, kierunek i priorytety po MVP.

---

## Kierunek wizualny

- Izometryczny styl 2.5D.
- Referencja wizualna: „Forge of Empires” (układ miasta, czytelność, estetyka).
- Cyberpunk / futurystyczny klimat (neony, metal, szkło, technologia).
- Modele budynków jako PNG (sprite'y) z przezroczystością.
- Spójna skala budynków i wspólna „siatka izometryczna”.
- Delikatne cienie pod budynkami dla czytelności.

---

## Filary rozwoju po MVP

1. Lepsza czytelność miasta (grafika + UI).
2. Głębszy gameplay (progresja, strategie, powody do powrotu).
3. Społeczność (guildy / współpraca).
4. Sezony z różnymi zasadami.

---

## Kandydaci na funkcje (bez kolejności)

### Miasto i budynki

- Więcej poziomów budynków (np. 1–10) + bardziej wyraźne różnice.
- Rozbudowa gridu (np. 12x12 -> 16x16) wraz z progresją.
- Dekoracje / skórki (wizualne, bez wpływu na balans).
- Ulepszenia pasywne (np. „district bonuses”).

### PvP i ranking

- Matchmaking po „mocy” (nie tylko prestiż).
- Obrona pasywna (np. garnizon, pułapki).
- Walki asynchro w „trybie sektorów” (z `MILESTONE2.md`).
- Raport walki z prostą wizualizacją (ikonki, dmg, log).

### Społeczność

- Guildy: role, chat, wspólne cele.
- Wspólne zadania sezonowe (np. „zbierz X złota jako gildia”).

### Sezony i eventy

- Rotujące modyfikatory (np. +20% produkcji, -10% kosztów).
- Nagrody sezonowe (kosmetyka, tytuły).
- Reset wybranych aspektów (nie tylko prestiżu).

---

## Grafika 2.5D (praktyczne notatki)

- Format assetów: PNG 512x512 lub 256x256 (do decyzji).
- Każdy budynek ma min. 3 poziomy (osobny sprite na lvl).
- Nazewnictwo plików: `building_{type}_lvl{n}.png`.
- Zasady anchor point: wspólny punkt „podstawy” na siatce.

---

## Tech / pipeline

- Loader assetów + cache sprite'ów.
- Warstwy renderu: podłoże -> budynki -> efekty -> UI.
- Prosty edytor / podgląd siatki do pozycjonowania.

---

## Ryzyka / uwagi

- Izometryczny grid komplikuje klikalne pola (potrzebna dobra mapa hitboxów).
- Rozmiar assetów może podnieść wagę frontu.
- Balans po zwiększeniu poziomów wymaga nowych tabel.
