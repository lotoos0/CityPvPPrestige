import os
import uuid

from fastapi.testclient import TestClient

os.environ["APP_ENV"] = "test"

from app import models
from app.db import SessionLocal
from app.main import app


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


def test_pvp_attack_matches_contract_shape() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    attacker_email = f"contract_attacker_{suffix}@example.com"
    defender_email = f"contract_defender_{suffix}@example.com"
    password = "TestPass123!"

    attacker_id = register_user(client, attacker_email, password)
    defender_id = register_user(client, defender_email, password)
    token = login_user(client, attacker_email, password)

    key = str(uuid.uuid4())
    response = client.post(
        "/pvp/attack",
        json={"defender_id": defender_id},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": key,
            "X-Test-Force-Result": "win",
            "X-Test-Force-Delta": "30",
            "X-Test-Ignore-Cooldowns": "true",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    assert "battle_id" in body
    assert body["result"] in ("win", "loss")
    assert 0.0 <= body["expected_win"] <= 1.0

    assert "prestige" in body
    assert isinstance(body["prestige"]["delta"], int)

    assert "limits" in body
    assert "reset_at" in body["limits"]
    assert "attacks_left" in body["limits"]

    assert "cooldowns" in body
    assert "messages" in body
    assert isinstance(body["messages"], list)

    cleanup_test_data(attacker_id, defender_id)


def cleanup_test_data(attacker_id, defender_id):
    db = SessionLocal()
    try:
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
    finally:
        db.close()
