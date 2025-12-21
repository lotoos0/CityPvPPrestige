# To Test

## Backend - /pvp/attack
- Wynik ataku ma wartosc `win` albo `loss`.
- Nowy wpis w `attack_logs` ma `result` = `win` lub `loss`.

## Backend - /pvp/log
- GET `/pvp/log` zwraca obiekt z polami `items` i `next_cursor`.
- Kazdy element `items` ma: `battle_id`, `attacker_id`, `attacker_email`, `defender_id`, `defender_email`, `result`, `prestige_delta`, `created_at`.
- `prestige_delta` i `result` sa liczone z perspektywy aktualnego uzytkownika.
- `next_cursor` jest `null` przy ostatniej stronie; przy wiekszej liczbie wpisow zwraca poprawny cursor.
- GET `/pvp/log?limit=1` zwraca jedna pozycje.
- GET `/pvp/log?cursor=<invalid>` zwraca 400.

## Frontend - Attack History
- Historia atakow pokazuje ostatnie wpisy z `/pvp/log` (bez bledow w konsoli).
- W liscie jest poprawny przeciwnik (email) i wynik (`win`/`loss`).
- Delta prestizu ma poprawny znak (+/-) zgodny z backendem.
