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
    seed_units(attacker_id, 10)

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

    # Test A: losses field contract
    assert "losses" in body
    assert "attacker" in body["losses"]
    assert "defender" in body["losses"]
    assert "raider" in body["losses"]["attacker"]
    assert "guardian" in body["losses"]["attacker"]
    assert "raider" in body["losses"]["defender"]
    assert "guardian" in body["losses"]["defender"]
    assert body["losses"]["attacker"]["raider"] >= 0
    assert body["losses"]["attacker"]["guardian"] >= 0
    assert body["losses"]["defender"]["raider"] >= 0
    assert body["losses"]["defender"]["guardian"] >= 0

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
            models.UserUnit.user_id.in_([attacker_id, defender_id])
        ).delete()
        db.query(models.City).filter(models.City.user_id.in_([attacker_id, defender_id])).delete()
        db.query(models.User).filter(models.User.id.in_([attacker_id, defender_id])).delete()
        db.commit()
    finally:
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


def get_user_units(user_id):
    """Get user's unit counts as dict {unit_code: qty}"""
    db = SessionLocal()
    try:
        units = (
            db.query(models.UserUnit, models.UnitType)
            .join(models.UnitType, models.UserUnit.unit_type_id == models.UnitType.id)
            .filter(models.UserUnit.user_id == user_id)
            .all()
        )
        return {unit_type.code: user_unit.qty for user_unit, unit_type in units}
    finally:
        db.close()


def test_inventory_decreases_exactly_by_losses() -> None:
    """Test B: Verify inventory decreases by exact loss amounts"""
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    attacker_email = f"inv_attacker_{suffix}@example.com"
    defender_email = f"inv_defender_{suffix}@example.com"
    password = "TestPass123!"

    attacker_id = register_user(client, attacker_email, password)
    defender_id = register_user(client, defender_email, password)
    token = login_user(client, attacker_email, password)

    # Seed both users with units
    seed_units(attacker_id, 100)
    seed_units(defender_id, 100)

    # Snapshot before attack
    attacker_before = get_user_units(attacker_id)
    defender_before = get_user_units(defender_id)

    # Attack
    key = str(uuid.uuid4())
    response = client.post(
        "/pvp/attack",
        json={"defender_id": defender_id},
        headers={
            "Authorization": f"Bearer {token}",
            "Idempotency-Key": key,
            "X-Test-Ignore-Cooldowns": "true",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()

    # Extract losses from response
    losses_att = body["losses"]["attacker"]
    losses_def = body["losses"]["defender"]

    # Snapshot after attack
    attacker_after = get_user_units(attacker_id)
    defender_after = get_user_units(defender_id)

    # Verify: attacker_after = attacker_before - losses_attacker
    expected_att_raider = attacker_before.get("raider", 0) - losses_att["raider"]
    expected_att_guardian = attacker_before.get("guardian", 0) - losses_att["guardian"]
    assert attacker_after.get("raider", 0) == expected_att_raider, (
        f"Attacker raider mismatch: expected {expected_att_raider}, got {attacker_after.get('raider', 0)}"
    )
    assert attacker_after.get("guardian", 0) == expected_att_guardian, (
        f"Attacker guardian mismatch: expected {expected_att_guardian}, got {attacker_after.get('guardian', 0)}"
    )

    # Verify: defender_after = defender_before - losses_defender
    expected_def_raider = defender_before.get("raider", 0) - losses_def["raider"]
    expected_def_guardian = defender_before.get("guardian", 0) - losses_def["guardian"]
    assert defender_after.get("raider", 0) == expected_def_raider, (
        f"Defender raider mismatch: expected {expected_def_raider}, got {defender_after.get('raider', 0)}"
    )
    assert defender_after.get("guardian", 0) == expected_def_guardian, (
        f"Defender guardian mismatch: expected {expected_def_guardian}, got {defender_after.get('guardian', 0)}"
    )

    cleanup_test_data(attacker_id, defender_id)
