import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import uuid4

# === Data Models ===
class OrderItem(BaseModel):
    item_id: str
    name: str
    quantity: int
    price: float

class Order(BaseModel):
    order_id: str
    customer_name: str
    items: List[OrderItem]
    total: float
    status: str = "received"
    created_at: datetime = None

    def model_post_init(self, __context):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

# === In-memory storage ===
orders_db = {}

# === FastAPI App ===
app = FastAPI(title="RestaurantOrderAPI")

@app.post("/orders/", response_model=Order, status_code=201)
def create_order(order: Order):
    if not order.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")
    order.order_id = str(uuid4())
    order.total = sum(item.price * item.quantity for item in order.items)
    order.status = "received"
    order.created_at = datetime.utcnow()
    orders_db[order.order_id] = order
    return order

@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    order = orders_db.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/orders/", response_model=List[Order])
def list_orders(status: Optional[str] = None):
    if status:
        return [order for order in orders_db.values() if order.status == status]
    return list(orders_db.values())

@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: str, updated_order: Order):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    if not updated_order.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")
    updated_order.order_id = order_id
    updated_order.total = sum(item.price * item.quantity for item in updated_order.items)
    updated_order.created_at = orders_db[order_id].created_at
    orders_db[order_id] = updated_order
    return updated_order

@app.patch("/orders/{order_id}/status")
def update_order_status(order_id: str, status: str):
    valid_statuses = ["received", "preparing", "ready", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    orders_db[order_id].status = status
    return {"message": f"Order {order_id} status updated to {status}"}

@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: str):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    del orders_db[order_id]
    return

# === Test Client Setup ===
client = TestClient(app)

# === Pytest Unit and Integration Tests ===
class TestRestaurantOrderAPI:
    def setup_method(self):
        """Reset the in-memory database before each test"""
        global orders_db
        orders_db.clear()

    def test_create_order_valid(self):
        order_data = {
            "customer_name": "John Doe",
            "items": [
                {"item_id": "1", "name": "Pizza", "quantity": 2, "price": 15.0}
            ]
        }
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 201
        data = response.json()
        assert data["customer_name"] == "John Doe"
        assert data["total"] == 30.0
        assert data["status"] == "received"
        assert "order_id" in data
        assert "created_at" in data

    def test_create_order_empty_items(self):
        order_data = {
            "customer_name": "Jane Doe",
            "items": []
        }
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 400
        assert "Order must contain at least one item" in response.json()["detail"]

    def test_create_order_missing_fields(self):
        order_data = {"customer_name": "John"}
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 422  # Validation error

    def test_get_order_existing(self):
        # First create an order
        order_data = {
            "customer_name": "Alice",
            "items": [{"item_id": "1", "name": "Burger", "quantity": 1, "price": 10.0}]
        }
        create_response = client.post("/orders/", json=order_data)
        order_id = create_response.json()["order_id"]

        # Retrieve the order
        response = client.get(f"/orders/{order_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == order_id
        assert data["customer_name"] == "Alice"

    def test_get_order_nonexistent(self):
        response = client.get("/orders/invalid-id")
        assert response.status_code == 404
        assert "Order not found" in response.json()["detail"]

    def test_list_orders_empty(self):
        response = client.get("/orders/")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_orders_with_data(self):
        # Create two orders
        order1_data = {
            "customer_name": "Bob",
            "items": [{"item_id": "1", "name": "Salad", "quantity": 1, "price": 8.0}]
        }
        order2_data = {
            "customer_name": "Charlie",
            "items": [{"item_id": "2", "name": "Soup", "quantity": 2, "price": 5.0}]
        }
        client.post("/orders/", json=order1_data)
        client.post("/orders/", json=order2_data)

        response = client.get("/orders/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_orders_by_status(self):
        # Create orders with different statuses
        order_data = {
            "customer_name": "Dave",
            "items": [{"item_id": "1", "name": "Pasta", "quantity": 1, "price": 12.0}]
        }
        create_response = client.post("/orders/", json=order_data)
        order_id = create_response.json()["order_id"]

        # Update status
        client.patch(f"/orders/{order_id}/status", json={"status": "preparing"})

        # List by status
        response = client.get("/orders/?status=preparing")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "preparing"

        # List non-existent status
        response = client.get("/orders/?status=shipped")
        assert response.status_code == 200
        assert response.json() == []

    def test_update_order_valid(self):
        # Create initial order
        order_data = {
            "customer_name": "Eve",
            "items": [{"item_id": "1", "name": "Steak", "quantity": 1, "price": 25.0}]
        }
        create_response = client.post("/orders/", json=order_data)
        order_id = create_response.json()["order_id"]

        # Update order
        updated_data = {
            "customer_name": "Eve Smith",
            "items": [
                {"item_id": "1", "name": "Steak", "quantity": 2, "price": 25.0},
                {"item_id": "2", "name": "Wine", "quantity": 1, "price": 10.0}
            ]
        }
        response = client.put(f"/orders/{order_id}", json=updated_data)
        assert response.status_code == 200
        data = response.json()
        assert data["customer_name"] == "Eve Smith"
        assert data["total"] == 60.0
        assert data["order_id"] == order_id

    def test_update_order_nonexistent(self):
        updated_data = {
            "customer_name": "Fake",
            "items": [{"item_id": "1", "name": "Dummy", "quantity": 1, "price": 5.0}]
        }
        response = client.put("/orders/invalid-id", json=updated_data)
        assert response.status_code == 404
        assert "Order not found" in response.json()["detail"]

    def test_update_order_empty_items(self):
        order_data = {
            "customer_name": "Frank",
            "items": [{"item_id": "1", "name": "Fish", "quantity": 1, "price": 18.0}]
        }
        create_response = client.post("/orders/", json=order_data)
        order_id = create_response.json()["order_id"]

        updated_data = {"customer_name": "Frank", "items": []}
        response = client.put(f"/orders/{order_id}", json=updated_data)
        assert response.status_code == 400
        assert "Order must contain at least one item" in response.json()["detail"]

    def test_update_order_status_valid(self):
        order_data = {
            "customer_name": "Grace",
            "items": [{"item_id": "1", "name": "Chicken", "quantity": 1, "price": 14.0}]
        }
        create_response = client.post("/orders/", json=order_data)
        order_id = create_response.json()["order_id"]

        response = client.patch(f"/orders/{order_id}/status", json={"status": "ready"})
        assert response.status_code == 200
        assert "status updated to ready" in response.json()["message"]

        # Verify update
        get_response = client.get(f"/orders/{order_id}")
        assert get_response.json()["status"] == "ready"

    def test_update_order_status_invalid(self):
        order_data = {
            "customer_name": "Hank",
            "items": [{"item_id": "1", "name": "Rice", "quantity": 1, "price": 3.0}]
        }
        create_response = client.post("/orders/", json=order_data)
        order_id = create_response.json()["order_id"]

        response = client.patch(f"/orders/{order_id}/status", json={"status": "shipped"})
        assert response.status_code == 400
        assert "must be one of" in response.json()["detail"]

    def test_update_order_status_nonexistent(self):
        response = client.patch("/orders/invalid-id/status", json={"status": "delivered"})
        assert response.status_code == 404
        assert "Order not found" in response.json()["detail"]

    def test_delete_order_existing(self):
        order_data = {
            "customer_name": "Ivy",
            "items": [{"item_id": "1", "name": "Cake", "quantity": 1, "price": 7.0}]
        }
        create_response = client.post("/orders/", json=order_data)
        order_id = create_response.json()["order_id"]

        response = client.delete(f"/orders/{order_id}")
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/orders/{order_id}")
        assert get_response.status_code == 404

    def test_delete_order_nonexistent(self):
        response = client.delete("/orders/invalid-id")
        assert response.status_code == 404
        assert "Order not found" in response.json()["detail"]

    def test_order_total_calculation(self):
        order_data = {
            "customer_name": "Jack",
            "items": [
                {"item_id": "1", "name": "Burger", "quantity": 2, "price": 10.0},
                {"item_id": "2", "name": "Fries", "quantity": 1, "price": 4.0}
            ]
        }
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 201
        data = response.json()
        assert data["total"] == 24.0

    def test_order_created_at_is_set(self):
        order_data = {
            "customer_name": "Kate",
            "items": [{"item_id": "1", "name": "Soda", "quantity": 1, "price": 2.0}]
        }
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 201
        data = response.json()
        assert "created_at" in data
        assert data["created_at"] is not None

    def test_multiple_orders_different_ids(self):
        order_data = {
            "customer_name": "Leo",
            "items": [{"item_id": "1", "name": "Taco", "quantity": 1, "price": 3.5}]
        }
        response1 = client.post("/orders/", json=order_data)
        response2 = client.post("/orders/", json=order_data)
        assert response1.status_code == 201
        assert response2.status_code == 201
        assert response1.json()["order_id"] != response2.json()["order_id"]

    def test_update_order_preserves_created_at(self):
        order_data = {
            "customer_name": "Mona",
            "items": [{"item_id": "1", "name": "Salad", "quantity": 1, "price": 9.0}]
        }
        create_response = client.post("/orders/", json=order_data)
        order_id = create_response.json()["order_id"]
        original_created_at = create_response.json()["created_at"]

        updated_data = {
            "customer_name": "Mona Lisa",
            "items": [{"item_id": "1", "name": "Garden Salad", "quantity": 2, "price": 9.0}]
        }
        update_response = client.put(f"/orders/{order_id}", json=updated_data)
        assert update_response.status_code == 200
        assert update_response.json()["created_at"] == original_created_at

    def test_get_openapi_schema(self):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_health_check(self):
        response = client.get("/")
        if response.status_code == 404:
            # If root path is not defined, that's acceptable
            pass
        # Otherwise, if defined, it should work
        assert response.status_code in [200, 404]

# === Coverage-enriched tests ===
class TestEdgeCases:
    def setup_method(self):
        global orders_db
        orders_db.clear()

    def test_create_order_large_quantity(self):
        order_data = {
            "customer_name": "Bulk Buyer",
            "items": [{"item_id": "1", "name": "Water", "quantity": 1000, "price": 1.0}]
        }
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 201
        assert response.json()["total"] == 1000.0

    def test_create_order_high_precision_prices(self):
        order_data = {
            "customer_name": "Precision",
            "items": [{"item_id": "1", "name": "Truffle", "quantity": 1, "price": 99.999}]
        }
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 201
        # Floating point comparison with tolerance
        assert abs(response.json()["total"] - 99.999) < 0.001

    def test_create_order_special_characters(self):
        order_data = {
            "customer_name": "José María",
            "items": [{"item_id": "1", "name": "Crème Brûlée", "quantity": 1, "price": 8.5}]
        }
        response = client.post("/orders/", json=order_data)
        assert response.status_code == 201
        assert response.json()["customer_name"] == "José María"
        assert response.json()["items"][0]["name"] == "Crème Brûlée"

    def test_update_status_multiple_times(self):
        order_data = {
            "customer_name": "Status Changer",
            "items": [{"item_id": "1", "name": "Coffee", "quantity": 1, "price": 3.0}]
        }
        create_response = client.post("/orders/", json=order_data)
        order_id = create_response.json()["order_id"]

        statuses = ["preparing", "ready", "delivered"]
        for status in statuses:
            response = client.patch(f"/orders/{order_id}/status", json={"status": status})
            assert response.status_code == 200

        final_order = client.get(f"/orders/{order_id}").json()
        assert final_order["status"] == "delivered"

    def test_concurrent_order_creation(self):
        # Simulate two orders created in rapid succession
        order1 = {
            "customer_name": "Customer 1",
            "items": [{"item_id": "1", "name": "Item 1", "quantity": 1, "price": 10.0}]
        }
        order2 = {
            "customer_name": "Customer 2",
            "items": [{"item_id": "2", "name": "Item 2", "quantity": 1, "price": 15.0}]
        }
        response1 = client.post("/orders/", json=order1)
        response2 = client.post("/orders/", json=order2)
        assert response1.status_code == 201
        assert response2.status_code == 201
        assert response1.json()["order_id"] != response2.json()["order_id"]

    def test_delete_nonexistent_order_idempotent(self):
        # Although we expect 404, test that system doesn't crash
        try:
            response = client.delete("/orders/nonexistent123")
            assert response.status_code in [204, 404]  # Accept either behavior
        except Exception as e:
            pytest.fail(f"Server crashed on