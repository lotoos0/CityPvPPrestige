from datetime import datetime
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

os.environ["APP_ENV"] = "test"

from app import models
from app.db import SessionLocal
from app.main import app
from app.pvp_constants import PRESTIGE_GAIN_CAP, PRESTIGE_LOSS_CAP, SERVER_TZ


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


def upsert_daily_stats(db, user_id, day, attacks_used, prestige_gain, prestige_loss):
    stats = (
        db.query(models.PvpDailyStats)
        .filter(
            models.PvpDailyStats.user_id == user_id,
            models.PvpDailyStats.day == day,
        )
        .first()
    )
    if not stats:
        stats = models.PvpDailyStats(user_id=user_id, day=day)
        db.add(stats)
    stats.attacks_used = attacks_used
    stats.prestige_gain = prestige_gain
    stats.prestige_loss = prestige_loss
    db.commit()


def test_gain_clamp_applies_remaining_only():
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    attacker_email = f"gain_attacker_{suffix}@example.com"
    defender_email = f"gain_defender_{suffix}@example.com"
    password = "TestPass123!"

    attacker_id = register_user(client, attacker_email, password)
    defender_id = register_user(client, defender_email, password)
    token = login_user(client, attacker_email, password)
    seed_units(attacker_id, 10)

    today = datetime.now(SERVER_TZ).date()
    db = SessionLocal()
    try:
        upsert_daily_stats(
            db,
            attacker_id,
            today,
            attacks_used=0,
            prestige_gain=PRESTIGE_GAIN_CAP - 5,
            prestige_loss=0,
        )
    finally:
        db.close()

    idempotency_key = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key,
        "X-Test-Force-Result": "win",
        "X-Test-Force-Delta": "30",
        "X-Test-Ignore-Cooldowns": "true",
    }

    response = client.post("/pvp/attack", json={"defender_id": defender_id}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["prestige"]["delta"] == 5

    limits = client.get("/pvp/limits", headers={"Authorization": f"Bearer {token}"}).json()
    assert limits["limits"]["prestige_gain_left"] == 0

    cleanup_test_data(attacker_id, defender_id)


def test_loss_clamp_applies_remaining_only():
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    attacker_email = f"loss_attacker_{suffix}@example.com"
    defender_email = f"loss_defender_{suffix}@example.com"
    password = "TestPass123!"

    attacker_id = register_user(client, attacker_email, password)
    defender_id = register_user(client, defender_email, password)
    token = login_user(client, attacker_email, password)
    seed_units(attacker_id, 10)

    today = datetime.now(SERVER_TZ).date()
    db = SessionLocal()
    try:
        upsert_daily_stats(
            db,
            attacker_id,
            today,
            attacks_used=0,
            prestige_gain=0,
            prestige_loss=PRESTIGE_LOSS_CAP - 5,
        )
    finally:
        db.close()

    idempotency_key = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": idempotency_key,
        "X-Test-Force-Result": "loss",
        "X-Test-Force-Delta": "-40",
        "X-Test-Ignore-Cooldowns": "true",
    }

    response = client.post("/pvp/attack", json={"defender_id": defender_id}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["prestige"]["delta"] == -5

    limits = client.get("/pvp/limits", headers={"Authorization": f"Bearer {token}"}).json()
    assert limits["limits"]["prestige_loss_left"] == 0

    cleanup_test_data(attacker_id, defender_id)


@pytest.mark.anyio
async def test_parallel_attacks_increment_attacks_used():
    suffix = uuid.uuid4().hex[:8]
    attacker_email = f"parallel_attacker_{suffix}@example.com"
    defender_email = f"parallel_defender_{suffix}@example.com"
    password = "TestPass123!"

    client = TestClient(app)
    attacker_id = register_user(client, attacker_email, password)
    defender_id = register_user(client, defender_email, password)
    token = login_user(client, attacker_email, password)
    seed_units(attacker_id, 100)
    seed_units(defender_id, 100)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        headers = {"Authorization": f"Bearer {token}"}
        limits_before = await async_client.get("/pvp/limits", headers=headers)
        attacks_before = limits_before.json()["limits"]["attacks_used"]

        async def do_attack(key: str):
            return await async_client.post(
                "/pvp/attack",
                json={"defender_id": defender_id},
                headers={
                    "Authorization": f"Bearer {token}",
                    "Idempotency-Key": key,
                    "X-Test-Force-Result": "win",
                    "X-Test-Force-Delta": "1",
                    "X-Test-Ignore-Cooldowns": "true",
                },
            )

        import asyncio

        r1, r2 = await asyncio.gather(
            do_attack(str(uuid.uuid4())),
            do_attack(str(uuid.uuid4())),
        )
        assert r1.status_code == 200
        assert r2.status_code == 200

        limits_after = await async_client.get("/pvp/limits", headers=headers)
        attacks_after = limits_after.json()["limits"]["attacks_used"]
        assert attacks_after - attacks_before == 2

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
