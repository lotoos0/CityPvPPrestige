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


def test_army_contracts_end_to_end() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"army_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)
    headers = {"Authorization": f"Bearer {token}"}

    army = client.get("/army", headers=headers)
    assert army.status_code == 200, army.text
    body = army.json()
    codes = {unit["code"] for unit in body["units"]}
    assert {"raider", "guardian"}.issubset(codes)

    train = client.post(
        "/barracks/train",
        json={"unit_code": "raider", "qty": 2},
        headers=headers,
    )
    assert train.status_code == 200, train.text
    train_body = train.json()
    assert train_body["status"] == "running"

    queue = client.get("/barracks/queue", headers=headers)
    assert queue.status_code == 200
    queue_body = queue.json()
    assert queue_body["status"] == "running"

    db = SessionLocal()
    try:
        job = (
            db.query(models.TrainingJob)
            .filter(models.TrainingJob.user_id == user_id)
            .order_by(models.TrainingJob.id.desc())
            .first()
        )
        assert job is not None
        job.completes_at = datetime.now(SERVER_TZ) - timedelta(seconds=1)
        db.add(job)
        db.commit()
    finally:
        db.close()

    queue_done = client.get("/barracks/queue", headers=headers)
    assert queue_done.status_code == 200
    assert queue_done.json()["status"] == "done"

    claim = client.post("/barracks/claim", headers=headers)
    assert claim.status_code == 200
    claim_body = claim.json()
    assert claim_body["claimed"] is True
    assert claim_body["unit_code"] == "raider"
    assert claim_body["qty"] == 2

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
        db.query(models.TrainingJob).filter(models.TrainingJob.user_id == user_id).delete()
        db.query(models.UserUnit).filter(models.UserUnit.user_id == user_id).delete()
        db.query(models.UserBuilding).filter(models.UserBuilding.user_id == user_id).delete()
        db.query(models.City).filter(models.City.user_id == user_id).delete()
        db.query(models.User).filter(models.User.id == user_id).delete()
        db.commit()
    finally:
        db.close()
