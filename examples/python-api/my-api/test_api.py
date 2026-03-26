import pytest
from fastapi.testclient import TestClient
from my_project.main import app  # Adjust the import to match your project structure

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to My Project"}


def test_create_item():
    response = client.post("/items/", json={"name": "Test Item", "description": "A test"})
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert "id" in data


def test_get_item():
    # Create an item first
    create_resp = client.post("/items/", json={"name": "Fetch Item", "description": ""})
    item_id = create_resp.json()["id"]
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_update_item():
    # Create an item first
    create_resp = client.post("/items/", json={"name": "Old", "description": "old"})
    item_id = create_resp.json()["id"]
    response = client.put(f"/items/{item_id}", json={"name": "New", "description": "updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "New"


def test_delete_item():
    # Create an item first
    create_resp = client.post("/items/", json={"name": "To Delete", "description": ""})
    item_id = create_resp.json()["id"]
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 204
    # Verify deletion
    get_resp = client.get(f"/items/{item_id}")
    assert get_resp.status_code == 404