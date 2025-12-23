import uuid
from datetime import datetime, timedelta, timezone

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


def seed_city(user_id: str, last_collected_at: datetime) -> None:
    db = SessionLocal()
    try:
        city = db.query(models.City).filter(models.City.user_id == user_id).first()
        assert city is not None
        city.gold = 0
        city.last_collected_at = last_collected_at
        db.commit()
    finally:
        db.close()


def create_building(user_id: str, building_type: str, level: int, x: int, y: int) -> None:
    db = SessionLocal()
    try:
        city = db.query(models.City).filter(models.City.user_id == user_id).first()
        assert city is not None
        db.add(
            models.Building(
                city_id=city.id,
                type=building_type,
                level=level,
                x=x,
                y=y,
            )
        )
        db.commit()
    finally:
        db.close()


def get_city_state(user_id: str) -> models.City:
    db = SessionLocal()
    try:
        city = db.query(models.City).filter(models.City.user_id == user_id).first()
        assert city is not None
        db.refresh(city)
        return city
    finally:
        db.close()


def cleanup_test_data(user_id: str) -> None:
    db = SessionLocal()
    try:
        db.query(models.Building).filter(
            models.Building.city_id.in_(
                db.query(models.City.id).filter(models.City.user_id == user_id)
            )
        ).delete(synchronize_session=False)
        db.query(models.UserBuilding).filter(models.UserBuilding.user_id == user_id).delete()
        db.query(models.City).filter(models.City.user_id == user_id).delete()
        db.query(models.User).filter(models.User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


def test_city_production_accrues_on_get() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"city_tick_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)

    two_hours_ago = datetime.now(timezone.utc) - timedelta(hours=2)
    seed_city(user_id, two_hours_ago)
    create_building(user_id, "gold_mine", 1, 2, 2)

    before_request = datetime.now(timezone.utc)
    response = client.get("/city", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["gold"] == 40

    city = get_city_state(user_id)
    assert city.last_collected_at is not None
    assert city.last_collected_at >= before_request

    cleanup_test_data(user_id)
