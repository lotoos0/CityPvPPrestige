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


def test_city_build_contract_shape() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"city_build_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)

    seed_city_gold(user_id, 10000)

    response = client.post(
        "/city/build",
        json={"type": "gold_mine", "x": 2, "y": 3},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    body = response.json()

    assert "id" in body
    assert "grid_size" in body
    assert "gold" in body
    assert "pop" in body
    assert "power" in body
    assert "prestige" in body
    assert "buildings" in body
    assert isinstance(body["buildings"], list)

    placed = [b for b in body["buildings"] if b["x"] == 2 and b["y"] == 3]
    assert placed
    assert placed[0]["type"] == "gold_mine"
    assert placed[0]["level"] == 1

    cleanup_test_data(user_id)


def test_city_build_rejects_occupied_tile() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"city_occupied_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)

    seed_city_gold(user_id, 10000)

    response = client.post(
        "/city/build",
        json={"type": "gold_mine", "x": 1, "y": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    response = client.post(
        "/city/build",
        json={"type": "house", "x": 1, "y": 1},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409, response.text
    assert response.json().get("error", {}).get("code") == "TILE_OCCUPIED"

    cleanup_test_data(user_id)


def test_city_upgrade_rejects_max_level() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"city_max_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)

    seed_city_gold(user_id, 10000)
    create_building(user_id, "gold_mine", 3, 0, 0)

    response = client.post(
        "/city/upgrade",
        json={"x": 0, "y": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400, response.text
    assert response.json().get("error", {}).get("code") == "MAX_LEVEL"

    cleanup_test_data(user_id)


def test_city_build_rejects_insufficient_gold() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"city_gold_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)

    seed_city_gold(user_id, 0)

    response = client.post(
        "/city/build",
        json={"type": "gold_mine", "x": 4, "y": 4},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403, response.text
    assert response.json().get("error", {}).get("code") == "INSUFFICIENT_GOLD"

    cleanup_test_data(user_id)


def test_city_build_rejects_power_plant() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"city_power_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)

    seed_city_gold(user_id, 10000)

    response = client.post(
        "/city/build",
        json={"type": "power_plant", "x": 5, "y": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 400, response.text
    assert response.json().get("error", {}).get("code") == "BUILDING_TYPE_NOT_ALLOWED"

    cleanup_test_data(user_id)


def test_city_build_accepts_tower_alias() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"city_tower_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)

    seed_city_gold(user_id, 10000)

    response = client.post(
        "/city/build",
        json={"type": "scout_tower", "x": 8, "y": 8},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201, response.text
    body = response.json()

    placed = [b for b in body["buildings"] if b["x"] == 8 and b["y"] == 8]
    assert placed
    assert placed[0]["type"] == "tower"

    cleanup_test_data(user_id)


def test_city_build_rejects_second_town_hall() -> None:
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    email = f"city_town_hall_{suffix}@example.com"
    password = "TestPass123!"

    user_id = register_user(client, email, password)
    token = login_user(client, email, password)

    seed_city_gold(user_id, 10000)

    response = client.post(
        "/city/build",
        json={"type": "town_hall", "x": 0, "y": 0},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409, response.text
    assert response.json().get("error", {}).get("code") == "TOWN_HALL_ALREADY_EXISTS"

    cleanup_test_data(user_id)
