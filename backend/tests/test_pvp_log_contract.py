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
        logs = [
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
            ),
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
                created_at=now,
            ),
            models.AttackLog(
                attacker_id=attacker_id,
                defender_id=defender_id,
                result="win",
                prestige_delta_attacker=8,
                prestige_delta_defender=0,
                expected_win=0.55,
                attacker_prestige_before=1210,
                defender_prestige_before=1190,
                attacker_attack_power=11,
                defender_defense_power=9,
                created_at=now - timedelta(minutes=1),
            ),
            models.AttackLog(
                attacker_id=defender_id,
                defender_id=attacker_id,
                result="win",
                prestige_delta_attacker=5,
                prestige_delta_defender=-4,
                expected_win=0.52,
                attacker_prestige_before=1250,
                defender_prestige_before=1240,
                attacker_attack_power=9,
                defender_defense_power=10,
                created_at=now - timedelta(minutes=2),
            ),
            models.AttackLog(
                attacker_id=attacker_id,
                defender_id=defender_id,
                result="win",
                prestige_delta_attacker=3,
                prestige_delta_defender=0,
                expected_win=0.51,
                attacker_prestige_before=1220,
                defender_prestige_before=1210,
                attacker_attack_power=10,
                defender_defense_power=10,
                created_at=now - timedelta(minutes=3),
            ),
        ]
        db.add_all(logs)
        db.commit()
    finally:
        db.close()


def _assert_desc_order(items) -> None:
    last_dt = None
    for item in items:
        current_dt = datetime.fromisoformat(item["created_at"])
        if last_dt is not None:
            assert current_dt <= last_dt
        last_dt = current_dt


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
        "/pvp/log?limit=2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    page1 = response.json()
    assert "items" in page1
    assert "next_cursor" in page1
    assert len(page1["items"]) == 2
    assert page1["next_cursor"]

    response = client.get(
        f"/pvp/log?limit=2&cursor={page1['next_cursor']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    page2 = response.json()
    assert "items" in page2
    assert "next_cursor" in page2
    assert len(page2["items"]) == 2

    page1_ids = {item["battle_id"] for item in page1["items"]}
    page2_ids = {item["battle_id"] for item in page2["items"]}
    assert page1_ids.isdisjoint(page2_ids)
    _assert_desc_order(page1["items"])
    _assert_desc_order(page2["items"])

    response = client.get(
        "/pvp/log?limit=20",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    items = body["items"]
    assert items
    _assert_desc_order(items)

    for item in items:
        assert "battle_id" in item
        assert item["result"] in ("win", "loss")
        assert isinstance(item["prestige_delta"], int)
        assert "attacker_email" in item
        assert "defender_email" in item
        assert "expected_win" in item
        if item["expected_win"] is not None:
            assert 0.0 <= item["expected_win"] <= 1.0
        assert "created_at" in item

        # Test D: losses fields are normalized (always present with full shape)
        assert "units_lost_attacker" in item
        assert "units_lost_defender" in item
        assert "raider" in item["units_lost_attacker"]
        assert "guardian" in item["units_lost_attacker"]
        assert "raider" in item["units_lost_defender"]
        assert "guardian" in item["units_lost_defender"]
        assert item["units_lost_attacker"]["raider"] >= 0
        assert item["units_lost_attacker"]["guardian"] >= 0
        assert item["units_lost_defender"]["raider"] >= 0
        assert item["units_lost_defender"]["guardian"] >= 0

    attacker_view = next(
        entry for entry in items if entry["attacker_id"] == attacker_id
    )
    assert attacker_view["result"] == "win"
    assert attacker_view["prestige_delta"] == 15
    assert attacker_view["expected_win"] == 0.6

    defender_view = next(
        entry for entry in items if entry["defender_id"] == attacker_id
    )
    assert defender_view["result"] == "loss"
    assert defender_view["prestige_delta"] == -12
    assert defender_view["expected_win"] == 0.7

    cleanup_test_data(attacker_id, defender_id)
