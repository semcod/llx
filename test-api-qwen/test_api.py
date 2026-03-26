import pytest
from fastapi.testclient import TestClient
from main import app  # Assuming the FastAPI app instance is in main.py

client = TestClient(app)

def test_read_root():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "Welcome to My Project API"

def test_read_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_create_item():
    """Test creating a new item"""
    test_item = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 10.99,
        "tax": 1.50
    }
    
    response = client.post("/items/", json=test_item)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == test_item["name"]
    assert data["description"] == test_item["description"]
    assert data["price"] == test_item["price"]
    assert data["tax"] == test_item["tax"]
    assert "id" in data

def test_get_item():
    """Test retrieving a specific item"""
    item_id = 1
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == item_id

def test_get_item_not_found():
    """Test retrieving a non-existent item"""
    item_id = 999
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_get_items():
    """Test retrieving all items"""
    response = client.get("/items/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_update_item():
    """Test updating an existing item"""
    item_id = 1
    update_data = {
        "name": "Updated Item",
        "description": "This item has been updated",
        "price": 15.99,
        "tax": 2.00
    }
    
    response = client.put(f"/items/{item_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert data["price"] == update_data["price"]
    assert data["tax"] == update_data["tax"]

def test_update_item_not_found():
    """Test updating a non-existent item"""
    item_id = 999
    update_data = {
        "name": "Non-existent Item",
        "description": "This should not be updated",
        "price": 99.99
    }
    
    response = client.put(f"/items/{item_id}", json=update_data)
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_delete_item():
    """Test deleting an item"""
    item_id = 1
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Item {item_id} deleted successfully"}

def test_delete_item_not_found():
    """Test deleting a non-existent item"""
    item_id = 999
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_invalid_item_data():
    """Test creating an item with invalid data"""
    invalid_item = {
        "name": "",
        "description": "Invalid item with empty name",
        "price": -10.00,  # Negative price
        "tax": -1.00      # Negative tax
    }
    
    response = client.post("/items/", json=invalid_item)
    assert response.status_code == 422  # Unprocessable Entity

@pytest.mark.parametrize("name,price,expected_status", [
    ("Valid Item", 10.0, 200),
    ("", 10.0, 422),
    ("Item", -5.0, 422),
])
def test_create_item_parametrized(name, price, expected_status):
    """Parametrized test for item creation with various inputs"""
    item_data = {
        "name": name,
        "description": "Test description",
        "price": price,
        "tax": 1.0
    }
    
    response = client.post("/items/", json=item_data)
    assert response.status_code == expected_status

def test_read_users():
    """Test retrieving users list"""
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_user():
    """Test creating a new user"""
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "full_name": "Test User"
    }
    
    response = client.post("/users/", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "id" in data

def test_get_user():
    """Test retrieving a specific user"""
    user_id = 1
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["id"] == user_id

def test_get_user_not_found():
    """Test retrieving a non-existent user"""
    user_id = 999
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "User not found"}