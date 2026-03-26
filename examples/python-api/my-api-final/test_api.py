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
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["name"] == test_item["name"]
    assert response_data["description"] == test_item["description"]
    assert response_data["price"] == test_item["price"]
    assert response_data["tax"] == test_item["tax"]
    assert "id" in response_data

def test_get_item():
    """Test retrieving a specific item"""
    # First create an item
    test_item = {"name": "Get Test Item", "description": "Get test", "price": 5.99, "tax": 0.50}
    create_response = client.post("/items/", json=test_item)
    item_id = create_response.json()["id"]
    
    # Then retrieve it
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["id"] == item_id
    assert response_data["name"] == test_item["name"]

def test_get_nonexistent_item():
    """Test retrieving a non-existent item"""
    response = client.get("/items/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_update_item():
    """Test updating an existing item"""
    # First create an item
    test_item = {"name": "Update Test Item", "description": "Update test", "price": 8.99, "tax": 0.75}
    create_response = client.post("/items/", json=test_item)
    item_id = create_response.json()["id"]
    
    # Update the item
    updated_item = {
        "name": "Updated Item",
        "description": "This item has been updated",
        "price": 15.99,
        "tax": 2.00
    }
    
    response = client.put(f"/items/{item_id}", json=updated_item)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == updated_item["name"]
    assert response_data["description"] == updated_item["description"]
    assert response_data["price"] == updated_item["price"]
    assert response_data["tax"] == updated_item["tax"]

def test_update_nonexistent_item():
    """Test updating a non-existent item"""
    updated_item = {"name": "Updated", "description": "Updated", "price": 1.0, "tax": 0.1}
    response = client.put("/items/99999", json=updated_item)
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_delete_item():
    """Test deleting an item"""
    # First create an item
    test_item = {"name": "Delete Test Item", "description": "Delete test", "price": 3.99, "tax": 0.25}
    create_response = client.post("/items/", json=test_item)
    item_id = create_response.json()["id"]
    
    # Delete the item
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json() == {"message": f"Item {item_id} deleted successfully"}

def test_delete_nonexistent_item():
    """Test deleting a non-existent item"""
    response = client.delete("/items/99999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_list_items():
    """Test listing all items"""
    # Create a few items first
    items_to_create = [
        {"name": "List Item 1", "description": "First item", "price": 1.99, "tax": 0.10},
        {"name": "List Item 2", "description": "Second item", "price": 2.99, "tax": 0.20}
    ]
    
    for item in items_to_create:
        client.post("/items/", json=item)
    
    # Get all items
    response = client.get("/items/")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) >= 2  # At least the two we created
    
    # Check that the created items are in the response
    item_names = [item["name"] for item in items]
    for item in items_to_create:
        assert item["name"] in item_names

def test_create_item_validation():
    """Test item creation with invalid data"""
    # Test with negative price
    invalid_item = {
        "name": "Invalid Item",
        "description": "This has negative price",
        "price": -5.99,
        "tax": 0.50
    }
    
    response = client.post("/items/", json=invalid_item)
    assert response.status_code == 422  # Unprocessable Entity
    
    # Test with empty name
    invalid_item = {
        "name": "",
        "description": "This has empty name",
        "price": 5.99,
        "tax": 0.50
    }
    
    response = client.post("/items/", json=invalid_item)
    assert response.status_code == 422

def test_get_items_pagination():
    """Test items listing with pagination parameters"""
    # Create multiple items for pagination testing
    for i in range(15):
        item = {
            "name": f"Paginated Item {i}",
            "description": f"Item for pagination test {i}",
            "price": float(i),
            "tax": 0.1
        }
        client.post("/items/", json=item)
    
    # Test limit and offset
    response = client.get("/items/?limit=5&offset=0")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 5
    
    response = client.get("/items/?limit=5&offset=5")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 5

@pytest.mark.parametrize("invalid_id", ["abc", "-1", "0", "1.5"])
def test_get_item_invalid_id(invalid_id):
    """Test retrieving an item with invalid ID format"""
    response = client.get(f"/items/{invalid_id}")
    assert response.status_code in [422, 404]  # Either validation error or not found

def test_options_request():
    """Test OPTIONS request for CORS or API discovery"""
    response = client.options("/items/")
    assert response.status_code == 200
    # Note: The actual headers depend on your CORS configuration