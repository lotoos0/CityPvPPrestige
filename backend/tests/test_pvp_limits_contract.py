import uuid

from fastapi.testclient import TestClient

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


def test_pvp_limits_matches_contract_shape() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"limits_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)

    response = client.get("/pvp/limits", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text
    body = response.json()

    assert "limits" in body
    limits = body["limits"]

    assert "reset_at" in limits
    assert "attacks_used" in limits
    assert "attacks_left" in limits
    assert "prestige_gain_today" in limits
    assert "prestige_gain_left" in limits
    assert "prestige_loss_today" in limits
    assert "prestige_loss_left" in limits

    assert isinstance(limits["attacks_used"], int)
    assert isinstance(limits["attacks_left"], int)
    assert isinstance(limits["prestige_gain_today"], int)
    assert isinstance(limits["prestige_gain_left"], int)
    assert isinstance(limits["prestige_loss_today"], int)
    assert isinstance(limits["prestige_loss_left"], int)

    assert "cooldowns" in body
    cooldowns = body["cooldowns"]
    assert "global_remaining_sec" in cooldowns
    assert isinstance(cooldowns["global_remaining_sec"], int)
    assert cooldowns["global_remaining_sec"] >= 0

    cleanup_test_data(user_id)


def cleanup_test_data(user_id):
    db = SessionLocal()
    try:
        building_ids = (
            db.query(models.Building.id)
            .join(models.City, models.Building.city_id == models.City.id)
            .filter(models.City.user_id == user_id)
            .all()
        )
        for (building_id,) in building_ids:
            db.query(models.BuildingOccupancy).filter(
                models.BuildingOccupancy.building_id == building_id
            ).delete()
        db.query(models.Building).filter(
            models.Building.city_id.in_(
                db.query(models.City.id).filter(models.City.user_id == user_id)
            )
        ).delete(synchronize_session=False)
        db.query(models.PvpDailyStats).filter(
            models.PvpDailyStats.user_id == user_id
        ).delete()
        db.query(models.PvpIdempotency).filter(
            models.PvpIdempotency.attacker_id == user_id
        ).delete()
        db.query(models.PvpAttackCooldown).filter(
            models.PvpAttackCooldown.attacker_id == user_id
        ).delete()
        db.query(models.AttackLog).filter(
            models.AttackLog.attacker_id == user_id
        ).delete()
        db.query(models.City).filter(models.City.user_id == user_id).delete()
        db.query(models.User).filter(models.User.id == user_id).delete()
        db.commit()
    finally:
        db.close()
