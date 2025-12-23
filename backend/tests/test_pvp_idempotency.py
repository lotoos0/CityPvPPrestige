from datetime import datetime
import os
import uuid

from fastapi.testclient import TestClient

os.environ["APP_ENV"] = "test"

from app import models
from app.db import SessionLocal
from app.main import app
from app.pvp_constants import SERVER_TZ


def register_user(client: TestClient, email: str, password: str) -> str:
    response = client.post("/auth/register", json={"email": email, "password": password})
    assert response.status_code == 201
    return response.json()["id"]


def login_user(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_pvp_attack_idempotency():
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    attacker_email = f"attacker_{suffix}@example.com"
    defender_email = f"defender_{suffix}@example.com"
    password = "TestPass123!"

    attacker_id = register_user(client, attacker_email, password)
    defender_id = register_user(client, defender_email, password)
    token = login_user(client, attacker_email, password)
    seed_units(attacker_id, 100)
    seed_units(defender_id, 100)

    idempotency_key = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key,
        "X-Test-Ignore-Cooldowns": "true",
    }
    payload = {"defender_id": defender_id}

    response_1 = client.post("/pvp/attack", json=payload, headers=headers)
    assert response_1.status_code == 200
    body_1 = response_1.json()

    response_2 = client.post("/pvp/attack", json=payload, headers=headers)
    assert response_2.status_code == 200
    body_2 = response_2.json()

    assert body_1 == body_2

    db = SessionLocal()
    try:
        today = datetime.now(SERVER_TZ).date()
        logs = (
            db.query(models.AttackLog)
            .filter(
                models.AttackLog.attacker_id == attacker_id,
                models.AttackLog.defender_id == defender_id,
            )
            .all()
        )
        assert len(logs) == 1

        stats = (
            db.query(models.PvpDailyStats)
            .filter(
                models.PvpDailyStats.user_id == attacker_id,
                models.PvpDailyStats.day == today,
            )
            .first()
        )
        assert stats is not None
        assert stats.attacks_used == 1

        key_row = (
            db.query(models.PvpIdempotency)
            .filter(
                models.PvpIdempotency.attacker_id == attacker_id,
                models.PvpIdempotency.idempotency_key == idempotency_key,
            )
            .first()
        )
        assert key_row is not None
        assert key_row.status == "completed"
    finally:
        db.query(models.PvpIdempotency).filter(
            models.PvpIdempotency.attacker_id == attacker_id
        ).delete()
        db.query(models.PvpAttackCooldown).filter(
            models.PvpAttackCooldown.attacker_id == attacker_id
        ).delete()
        db.query(models.PvpDailyStats).filter(
            models.PvpDailyStats.user_id == attacker_id
        ).delete()
        db.query(models.AttackLog).filter(
            models.AttackLog.attacker_id == attacker_id
        ).delete()
        db.query(models.City).filter(models.City.user_id.in_([attacker_id, defender_id])).delete()
        db.query(models.User).filter(models.User.id.in_([attacker_id, defender_id])).delete()
        db.commit()
        db.close()


def seed_units(user_id, qty):
    db = SessionLocal()
    try:
        unit_type = db.query(models.UnitType).filter(models.UnitType.code == "raider").first()
        if not unit_type:
            raise AssertionError("Unit type 'raider' missing")
        db.add(
            models.UserUnit(
                user_id=user_id,
                unit_type_id=unit_type.id,
                qty=qty,
            )
        )
        db.commit()
    finally:
        db.close()
