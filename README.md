# CityPvPPrestige

Browser-based city-builder PvP MVP focused on prestige ranking and async battles.

## Requirements

- Docker + Docker Compose
- Python 3 (for static frontend server)

## Run backend (API + Postgres)

```bash
docker compose up -d --build
docker compose exec -T api alembic upgrade head
```

API will be at `http://localhost:8000`.

## Run frontend (static)

```bash
cd frontend
python -m http.server 8080
```

Open `http://localhost:8080` in your browser.
Set API base to `http://localhost:8000` if needed.

## Quick manual test

1. Register and login.
2. Build one building on the grid.
3. Collect resources.
4. Attack another player from ranking.
5. Check ranking + attack history.

## Admin / maintenance

- Start a new season (resets prestige):

```bash
curl -X POST http://localhost:8000/season/start \
  -H "Authorization: Bearer <token>"
```

## Notes

- Set a strong `JWT_SECRET` in production.
- This MVP intentionally excludes guilds, events, and monetization.
