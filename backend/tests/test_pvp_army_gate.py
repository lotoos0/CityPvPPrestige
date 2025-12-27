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


def test_pvp_attack_requires_minimum_army() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    attacker_email = f"army_gate_attacker_{suffix}@example.com"
    defender_email = f"army_gate_defender_{suffix}@example.com"
    password = "TestPass123!"

    attacker_id = register_user(client, attacker_email, password)
    defender_id = register_user(client, defender_email, password)
    token = login_user(client, attacker_email, password)

    response = client.post(
        "/pvp/attack",
        json={"defender_id": defender_id},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 403, response.text
    body = response.json()
    assert body["error"]["code"] == "INSUFFICIENT_ARMY"

    cleanup_test_data(attacker_id, defender_id)


def test_pvp_attack_allows_with_minimum_army() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    attacker_email = f"army_gate_pass_{suffix}@example.com"
    defender_email = f"army_gate_def_{suffix}@example.com"
    password = "TestPass123!"

    attacker_id = register_user(client, attacker_email, password)
    defender_id = register_user(client, defender_email, password)
    token = login_user(client, attacker_email, password)

    db = SessionLocal()
    try:
        unit_type = db.query(models.UnitType).filter(models.UnitType.code == "raider").first()
        assert unit_type is not None
        db.add(
            models.UserUnit(
                user_id=attacker_id,
                unit_type_id=unit_type.id,
                qty=10,
            )
        )
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/pvp/attack",
        json={"defender_id": defender_id},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": str(uuid.uuid4()),
            "X-Test-Force-Result": "win",
            "X-Test-Force-Delta": "10",
            "X-Test-Ignore-Cooldowns": "true",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "limits" in body
    assert "prestige" in body

    cleanup_test_data(attacker_id, defender_id)


def cleanup_test_data(attacker_id, defender_id):
    db = SessionLocal()
    try:
        building_ids = (
            db.query(models.Building.id)
            .join(models.City, models.Building.city_id == models.City.id)
            .filter(models.City.user_id.in_([attacker_id, defender_id]))
            .all()
        )
        for (building_id,) in building_ids:
            db.query(models.BuildingOccupancy).filter(
                models.BuildingOccupancy.building_id == building_id
            ).delete()
        db.query(models.Building).filter(
            models.Building.city_id.in_(
                db.query(models.City.id).filter(
                    models.City.user_id.in_([attacker_id, defender_id])
                )
            )
        ).delete(synchronize_session=False)
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
        db.query(models.UserUnit).filter(
            models.UserUnit.user_id == attacker_id
        ).delete()
        db.query(models.TrainingJob).filter(
            models.TrainingJob.user_id == attacker_id
        ).delete()
        db.query(models.UserBuilding).filter(
            models.UserBuilding.user_id.in_([attacker_id, defender_id])
        ).delete()
        db.query(models.City).filter(
            models.City.user_id.in_([attacker_id, defender_id])
        ).delete()
        db.query(models.User).filter(
            models.User.id.in_([attacker_id, defender_id])
        ).delete()
        db.commit()
    finally:
        db.close()
