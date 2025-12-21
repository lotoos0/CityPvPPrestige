import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient

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


def seed_logs(attacker_id, defender_id) -> None:
    now = datetime.now(SERVER_TZ)
    db = SessionLocal()
    try:
        db.add(
            models.AttackLog(
                attacker_id=attacker_id,
                defender_id=defender_id,
                result="win",
                prestige_delta_attacker=15,
                prestige_delta_defender=0,
                expected_win=0.6,
                attacker_prestige_before=1200,
                defender_prestige_before=1180,
                attacker_attack_power=10,
                defender_defense_power=8,
                created_at=now,
            )
        )
        db.add(
            models.AttackLog(
                attacker_id=defender_id,
                defender_id=attacker_id,
                result="win",
                prestige_delta_attacker=20,
                prestige_delta_defender=-12,
                expected_win=0.7,
                attacker_prestige_before=1300,
                defender_prestige_before=1290,
                attacker_attack_power=12,
                defender_defense_power=9,
                created_at=now - timedelta(minutes=1),
            )
        )
        db.commit()
    finally:
        db.close()


def cleanup_test_data(attacker_id, defender_id) -> None:
    db = SessionLocal()
    try:
        db.query(models.AttackLog).filter(
            models.AttackLog.attacker_id.in_([attacker_id, defender_id])
            | models.AttackLog.defender_id.in_([attacker_id, defender_id])
        ).delete(synchronize_session=False)
        db.query(models.PvpIdempotency).filter(
            models.PvpIdempotency.attacker_id.in_([attacker_id, defender_id])
        ).delete(synchronize_session=False)
        db.query(models.PvpAttackCooldown).filter(
            models.PvpAttackCooldown.attacker_id.in_([attacker_id, defender_id])
        ).delete(synchronize_session=False)
        db.query(models.PvpDailyStats).filter(
            models.PvpDailyStats.user_id.in_([attacker_id, defender_id])
        ).delete(synchronize_session=False)
        db.query(models.UserUnit).filter(
            models.UserUnit.user_id.in_([attacker_id, defender_id])
        ).delete(synchronize_session=False)
        db.query(models.UserBuilding).filter(
            models.UserBuilding.user_id.in_([attacker_id, defender_id])
        ).delete(synchronize_session=False)
        db.query(models.City).filter(
            models.City.user_id.in_([attacker_id, defender_id])
        ).delete(synchronize_session=False)
        db.query(models.User).filter(models.User.id.in_([attacker_id, defender_id])).delete(
            synchronize_session=False
        )
        db.commit()
    finally:
        db.close()


def test_pvp_log_contract() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    attacker_email = f"log_attacker_{suffix}@example.com"
    defender_email = f"log_defender_{suffix}@example.com"
    password = "TestPass123!"

    attacker_id = register_user(client, attacker_email, password)
    defender_id = register_user(client, defender_email, password)
    token = login_user(client, attacker_email, password)

    seed_logs(attacker_id, defender_id)

    response = client.get(
        "/pvp/log?limit=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "items" in body
    assert "next_cursor" in body
    assert len(body["items"]) == 1

    response = client.get(
        "/pvp/log?limit=20",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "items" in body
    assert "next_cursor" in body

    items = body["items"]
    assert items
    for item in items:
        assert "battle_id" in item
        assert item["result"] in ("win", "loss")
        assert isinstance(item["prestige_delta"], int)
        assert "attacker_email" in item
        assert "defender_email" in item
        assert "created_at" in item

    attacker_view = next(
        entry for entry in items if entry["attacker_id"] == attacker_id
    )
    assert attacker_view["result"] == "win"
    assert attacker_view["prestige_delta"] == 15

    defender_view = next(
        entry for entry in items if entry["defender_id"] == attacker_id
    )
    assert defender_view["result"] == "loss"
    assert defender_view["prestige_delta"] == -12

    cleanup_test_data(attacker_id, defender_id)
