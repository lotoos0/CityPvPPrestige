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


def seed_city_gold(user_id: str, amount: int) -> None:
    db = SessionLocal()
    try:
        city = db.query(models.City).filter(models.City.user_id == user_id).first()
        assert city is not None
        city.gold = amount
        db.commit()
    finally:
        db.close()


def get_occupancy_count(building_id) -> int:
    db = SessionLocal()
    try:
        return (
            db.query(models.BuildingOccupancy)
            .filter(models.BuildingOccupancy.building_id == building_id)
            .count()
        )
    finally:
        db.close()


def get_building_at(user_id: str, x: int, y: int):
    db = SessionLocal()
    try:
        city = db.query(models.City).filter(models.City.user_id == user_id).first()
        assert city is not None
        return (
            db.query(models.Building)
            .filter(
                models.Building.city_id == city.id,
                models.Building.x == x,
                models.Building.y == y,
            )
            .first()
        )
    finally:
        db.close()


def cleanup_test_data(user_id: str) -> None:
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
        db.query(models.UserBuilding).filter(models.UserBuilding.user_id == user_id).delete()
        db.query(models.City).filter(models.City.user_id == user_id).delete()
        db.query(models.User).filter(models.User.id == user_id).delete()
        db.commit()
    finally:
        db.close()


def test_building_footprint_occupancy_blocks_overlap() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"footprint_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)
    seed_city_gold(user_id, 10000)

    response = client.post(
        "/city/build",
        json={"type": "barracks", "x": 0, "y": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text

    building = get_building_at(user_id, 0, 0)
    assert building is not None
    assert get_occupancy_count(building.id) == 4

    response = client.post(
        "/city/build",
        json={"type": "house", "x": 1, "y": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409, response.text
    assert response.json().get("error", {}).get("code") == "TILE_OCCUPIED"

    cleanup_test_data(user_id)


def test_building_footprint_out_of_bounds() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"footprint_bounds_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)
    seed_city_gold(user_id, 10000)

    response = client.post(
        "/city/build",
        json={"type": "barracks", "x": 11, "y": 11},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400, response.text
    assert response.json().get("error", {}).get("code") == "TILE_OUT_OF_BOUNDS"

    cleanup_test_data(user_id)


def test_building_footprint_rotation_blocks_overlap() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"footprint_rotate_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)
    seed_city_gold(user_id, 10000)

    response = client.post(
        "/city/build",
        json={"type": "wall", "x": 0, "y": 0, "rotation": 90},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text

    response = client.post(
        "/city/build",
        json={"type": "house", "x": 0, "y": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409, response.text
    assert response.json().get("error", {}).get("code") == "TILE_OCCUPIED"

    cleanup_test_data(user_id)


def test_building_rotation_out_of_bounds() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"footprint_rotate_bounds_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)
    seed_city_gold(user_id, 10000)

    response = client.post(
        "/city/build",
        json={"type": "wall", "x": 11, "y": 11, "rotation": 90},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400, response.text
    assert response.json().get("error", {}).get("code") == "TILE_OUT_OF_BOUNDS"

    cleanup_test_data(user_id)
