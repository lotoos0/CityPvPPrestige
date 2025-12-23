import uuid

from fastapi.testclient import TestClient

from app.main import app


def test_buildings_catalog_contract_shape() -> None:
    client = TestClient(app)

    response = client.get("/city/buildings/catalog")
    assert response.status_code == 200, response.text
    body = response.json()

    assert "items" in body
    items = body["items"]
    assert isinstance(items, list)
    assert items

    item = items[0]
    assert "type" in item
    assert "display_name" in item
    assert "levels" in item

    levels = item["levels"]
    assert isinstance(levels, list)
    assert levels

    level = levels[0]
    assert "level" in level
    assert "effects" in level
    assert "cost_gold" in level
    assert isinstance(level["effects"], dict)
    assert isinstance(level["cost_gold"], int)
