import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import Dict, List

app = FastAPI()

# Mock database
mock_orders = {}
order_counter = 1

@app.post("/orders/", status_code=201)
def create_order(items: List[Dict]):
    global order_counter
    order_id = order_counter
    order_counter += 1
    mock_orders[order_id] = {
        "id": order_id,
        "items": items,
        "status": "received"
    }
    return mock_orders[order_id]

@app.get("/orders/{order_id}")
def get_order(order_id: int):
    return mock_orders.get(order_id)

@app.get("/orders/")
def list_orders():
    return list(mock_orders.values())

@app.put("/orders/{order_id}")
def update_order(order_id: int, items: List[Dict]):
    if order_id not in mock_orders:
        return {"detail": "Order not found"}, 404
    mock_orders[order_id]["items"] = items
    mock_orders[order_id]["status"] = "updated"
    return mock_orders[order_id]

@app.patch("/orders/{order_id}")
def patch_order(order_id: int, status: str = None):
    if order_id not in mock_orders:
        return {"detail": "Order not found"}, 404
    if status:
        mock_orders[order_id]["status"] = status
    return mock_orders[order_id]

@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: int):
    if order_id not in mock_orders:
        return {"detail": "Order not found"}, 404
    del mock_orders[order_id]
    return

client = TestClient(app)

def test_create_order():
    response = client.post("/orders/", json=[
        {"name": "Pizza", "quantity": 2},
        {"name": "Cola", "quantity": 1}
    ])
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["status"] == "received"
    assert len(data["items"]) == 2

def test_get_order():
    # Create an order first
    client.post("/orders/", json=[{"name": "Burger", "quantity": 1}])
    
    response = client.get("/orders/2")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 2
    assert data["items"][0]["name"] == "Burger"

def test_get_nonexistent_order():
    response = client.get("/orders/999")
    assert response.status_code == 404

def test_list_orders():
    # Create a few orders
    client.post("/orders/", json=[{"name": "Salad", "quantity": 1}])
    
    response = client.get("/orders/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # At least 3 orders created in tests so far
    assert any(order["id"] == 3 for order in data)

def test_update_order():
    # Create order to update
    client.post("/orders/", json=[{"name": "Pasta", "quantity": 2}])
    
    response = client.put("/orders/4", json=[
        {"name": "Pasta", "quantity": 3},
        {"name": "Garlic Bread", "quantity": 2}
    ])
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    assert len(data["items"]) == 2
    assert data["items"][1]["name"] == "Garlic Bread"

def test_update_nonexistent_order():
    response = client.put("/orders/999", json=[{"name": "Test", "quantity": 1}])
    assert response.status_code == 404

def test_patch_order_status():
    # Create order to patch
    client.post("/orders/", json=[{"name": "Soup", "quantity": 1}])
    
    response = client.patch("/orders/5", json={"status": "preparing"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "preparing"

def test_patch_nonexistent_order():
    response = client.patch("/orders/999", json={"status": "preparing"})
    assert response.status_code == 404

def test_delete_order():
    # Create order to delete
    client.post("/orders/", json=[{"name": "Dessert", "quantity": 1}])
    
    response = client.delete("/orders/6")
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = client.get("/orders/6")
    assert get_response.status_code == 404

def test_delete_nonexistent_order():
    response = client.delete("/orders/999")
    assert response.status_code == 404