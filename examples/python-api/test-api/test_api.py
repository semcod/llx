import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
from uuid import uuid4
import json

# -----------------------------
# Application Code (TodoAPI)
# -----------------------------

app = FastAPI()

class TodoCreate(BaseModel):
    title: str
    description: str = ""
    completed: bool = False

class TodoUpdate(BaseModel):
    title: str = None
    description: str = None
    completed: bool = None

class Todo(TodoCreate):
    id: str
    created_at: datetime
    updated_at: datetime

# In-memory storage (for testing purposes)
todos_db: Dict[str, Todo] = {}

@app.post("/todos/", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate):
    todo_id = str(uuid4())
    now = datetime.utcnow()
    new_todo = Todo(
        id=todo_id,
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        created_at=now,
        updated_at=now
    )
    todos_db[todo_id] = new_todo
    return new_todo

@app.get("/todos/", response_model=List[Todo])
def read_todos(skip: int = 0, limit: int = 100):
    return list(todos_db.values())[skip: skip + limit]

@app.get("/todos/{todo_id}", response_model=Todo)
def read_todo(todo_id: str):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todos_db[todo_id]

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: str, todo_update: TodoUpdate):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    existing_todo = todos_db[todo_id]
    update_data = todo_update.dict(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(existing_todo, key, value)
    
    existing_todo.updated_at = datetime.utcnow()
    todos_db[todo_id] = existing_todo
    return existing_todo

@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: str):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    del todos_db[todo_id]
    return

@app.patch("/todos/{todo_id}/complete", response_model=Todo)
def complete_todo(todo_id: str):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    todos_db[todo_id].completed = True
    todos_db[todo_id].updated_at = datetime.utcnow()
    return todos_db[todo_id]

# -----------------------------
# Pytest Test Suite
# -----------------------------

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_todos():
    """Clear todos_db before each test"""
    todos_db.clear()

def create_sample_todo(client: TestClient, title: str = "Test Todo", description: str = "Test Description") -> Dict[str, Any]:
    """Helper function to create a todo"""
    response = client.post("/todos/", json={"title": title, "description": description})
    assert response.status_code == 201
    return response.json()

# -----------------------------
# Unit Tests
# -----------------------------

def test_todo_create_model():
    """Unit test for TodoCreate model validation"""
    todo = TodoCreate(title="Buy milk")
    assert todo.title == "Buy milk"
    assert todo.description == ""
    assert todo.completed is False

def test_todo_update_model():
    """Unit test for TodoUpdate model partial updates"""
    update = TodoUpdate(title="Updated", completed=True)
    data = update.dict(exclude_unset=True)
    assert "title" in data
    assert "completed" in data
    assert "description" not in data

def test_todo_model_with_defaults():
    """Unit test for Todo model with all fields"""
    now = datetime.utcnow()
    todo = Todo(
        id="123",
        title="Test",
        description="Desc",
        completed=False,
        created_at=now,
        updated_at=now
    )
    assert todo.id == "123"
    assert todo.title == "Test"
    assert todo.completed is False
    assert todo.created_at == now

# -----------------------------
# Integration Tests
# -----------------------------

def test_create_todo():
    """Test creating a new todo item"""
    response = client.post(
        "/todos/",
        json={"title": "Learn FastAPI", "description": "Build APIs quickly"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Learn FastAPI"
    assert data["description"] == "Build APIs quickly"
    assert data["completed"] is False
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_create_todo_missing_title():
    """Test creating todo without title (should fail)"""
    response = client.post("/todos/", json={"description": "No title"})
    assert response.status_code == 422  # Validation error

def test_create_todo_with_empty_title():
    """Test creating todo with empty title (should fail)"""
    response = client.post("/todos/", json={"title": ""})
    assert response.status_code == 422

def test_read_todos_empty():
    """Test reading todos when none exist"""
    response = client.get("/todos/")
    assert response.status_code == 200
    assert response.json() == []

def test_read_todos_with_items():
    """Test reading todos with existing items"""
    create_sample_todo(client, "Todo 1")
    create_sample_todo(client, "Todo 2")
    
    response = client.get("/todos/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Todo 1"
    assert data[1]["title"] == "Todo 2"

def test_read_todos_with_pagination():
    """Test pagination parameters"""
    for i in range(5):
        create_sample_todo(client, f"Todo {i}")
    
    # Test skip and limit
    response = client.get("/todos/?skip=2&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Todo 2"

def test_read_single_todo():
    """Test reading a single todo by ID"""
    todo_data = create_sample_todo(client)
    todo_id = todo_data["id"]
    
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == todo_id
    assert data["title"] == "Test Todo"

def test_read_nonexistent_todo():
    """Test reading a todo that doesn't exist"""
    response = client.get("/todos/invalid-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}

def test_update_todo():
    """Test updating a todo item"""
    todo_data = create_sample_todo(client)
    todo_id = todo_data["id"]
    
    update_data = {
        "title": "Updated Title",
        "description": "Updated Description",
        "completed": True
    }
    
    response = client.put(f"/todos/{todo_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"
    assert data["completed"] is True
    assert data["updated_at"] != todo_data["updated_at"]  # Updated timestamp changed

def test_partial_update_todo():
    """Test partial update of a todo item"""
    todo_data = create_sample_todo(client, "Original Title")
    todo_id = todo_data["id"]
    
    # Only update title
    response = client.put(f"/todos/{todo_id}", json={"title": "Partial Update"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Partial Update"
    assert data["description"] == "Test Description"  # Unchanged
    assert data["completed"] is False  # Unchanged

def test_update_nonexistent_todo():
    """Test updating a todo that doesn't exist"""
    response = client.put("/todos/invalid-id", json={"title": "Updated"})
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}

def test_delete_todo():
    """Test deleting a todo item"""
    todo_data = create_sample_todo(client)
    todo_id = todo_data["id"]
    
    response = client.delete(f"/todos/{todo_id}")
    assert response.status_code == 204
    
    # Verify it's actually deleted
    response = client.get(f"/todos/{todo_id}")
    assert response.status_code == 404

def test_delete_nonexistent_todo():
    """Test deleting a todo that doesn't exist"""
    response = client.delete("/todos/invalid-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}

def test_complete_todo():
    """Test marking a todo as complete"""
    todo_data = create_sample_todo(client)
    todo_id = todo_data["id"]
    
    assert todo_data["completed"] is False
    
    response = client.patch(f"/todos/{todo_id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["updated_at"] != todo_data["updated_at"]

def test_complete_nonexistent_todo():
    """Test completing a todo that doesn't exist"""
    response = client.patch("/todos/invalid-id/complete")
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo not found"}

# -----------------------------
# Edge Case and Validation Tests
# -----------------------------

def test_create_todo_with_long_title():
    """Test creating todo with very long title"""
    long_title = "x" * 500
    response = client.post("/todos/", json={"title": long_title})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == long_title

def test_create_todo_with_special_chars():
    """Test creating todo with special characters"""
    special_title = "Test @#$%^&*() _+{}|:<>?[]\\;',./\""
    response = client.post("/todos/", json={"title": special_title})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == special_title

def test_update_todo_with_invalid_json():
    """Test updating todo with invalid JSON"""
    todo_data = create_sample_todo(client)
    todo_id = todo_data["id"]
    
    headers = {"Content-Type": "application/json"}
    response = client.put(f"/todos/{todo_id}", content="invalid json", headers=headers)
    assert response.status_code == 422

def test_get_todo_with_invalid_uuid():
    """Test getting todo with invalid UUID format"""
    response = client.get("/todos/invalid-uuid-format")
    # Note: FastAPI will return 422 for path parameter validation error
    assert response.status_code == 422

def test_create_multiple_todos():
    """Test creating multiple todos and verifying uniqueness"""
    todo_ids = set()
    titles = [f"Todo {i}" for i in range(10)]
    
    for title in titles:
        response = client.post("/todos/", json={"title": title})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == title
        assert data["id"] not in todo_ids  # Ensure unique IDs
        todo_ids.add(data["id"])

# -----------------------------
# Test Coverage Enhancement
# -----------------------------

def test_todo_timestamps():
    """Test that timestamps are properly set and updated"""
    import time
    
    # Create todo
    response = client.post("/todos/", json={"title": "Timestamp Test"})
    assert response.status_code == 201
    data = response.json()
    
    created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00")).replace(tzinfo=None)
    updated_at = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")).replace(tzinfo=None)
    
    # created_at and updated_at should be nearly identical on creation
    assert abs((created_at - updated_at).total_seconds()) < 1
    
    # Wait a moment and update
    time.sleep(0.1)
    response = client.put(f"/todos/{data['id']}", json={"title": "Updated"})
    assert response.status_code == 200
    updated_data = response.json()
    
    new_updated_at = datetime.fromisoformat(updated_data["updated_at"].replace("Z", "+00:00")).replace(tzinfo=None)
    # updated_at should be newer than original updated_at
    assert new_updated_at > updated_at

def test_complete_todo_idempotent():
    """Test that completing a todo multiple times works correctly"""
    todo_data = create_sample_todo(client)
    todo_id = todo_data["id"]
    
    # Complete once
    response1 = client.patch(f"/todos/{todo_id}/complete")
    assert response1.status_code == 200
    assert response1.json()["completed"] is True
    
    # Complete again (should still work)
    response2 = client.patch(f"/todos/{todo_id}/complete")
    assert response2.status_code == 200
    assert response2.json()["completed"] is True

def test_update_nonexistent_fields():
    """Test updating with nonexistent fields (should ignore them)"""
    todo_data = create_sample_todo(client)
    todo_id = todo_data["id"]
    
    # Include a field that doesn't exist in the model
    update_data = {
        "title": "Valid Update",
        "nonexistent_field": "should be ignored"
    }
    
    response = client.put(f"/todos/{todo_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Valid Update"
    # The response shouldn't contain the nonexistent field
    assert "nonexistent_field" not in data

def test_get_all_todos_exceeding_limit():
    """Test getting todos when limit exceeds actual count"""
    # Create 5 todos
    for i in range(5):
        create_sample_todo(client, f"Todo {i}")
    
    # Request 100 todos (more than exist)
    response = client.get("/todos/?limit=100")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5  # Should return all available, not 100

def test_create_todo_with_boolean_strings():
    """Test creating todo with string representation of boolean"""
    # This should fail as FastAPI will try to convert and validate
    response = client.post("/todos/", json={
        "title": "Test",
        "completed": "true"  # String instead of boolean
    })
    # FastAPI should convert string "true" to boolean True
    assert response.status_code == 201
    data = response.json()
    assert data["completed"] is True

# -----------------------------
# Performance and Stress Tests
# -----------------------------

def test_create_many_todos():
    """Test creating many todos to check performance"""
    num_todos = 50
    created_ids = []
    
    for i in range(num_todos):
        response = client.post("/todos/", json={"title": f"Stress Test {i}"})
        assert response.status_code == 201
        data = response.json()
        created_ids.append(data["id"])
    
    # Verify all were created
    response = client.get("/todos/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == num_todos

# -----------------------------
# Schema and Response Validation
# -----------------------------

def test_create_todo_response_schema():
    """Test that create todo response matches expected schema"""
    response = client.post("/todos/", json={"title": "Schema Test"})
    assert response.status_code == 201
    data = response.json()
    
    required_fields = ["id", "title", "description", "completed", "created_at", "updated_at"]
    for field in required_fields:
        assert field in data
    
    # Validate field types
    assert isinstance(data["id"], str)
    assert isinstance(data["title"], str)
    assert isinstance(data["description"], str)
    assert isinstance(data["completed"], bool)
    assert isinstance(data["created_at"], str)  # ISO format string
    assert isinstance(data["updated_at"], str)  # ISO format string

def test_get_todo_response_schema():
    """Test that get todo response matches expected schema"""
    todo_data = create_sample_todo(client)
    response = client.get(f"/todos/{todo_data['id']}")
    assert response.status_code == 200
    data = response.json()
    
    required_fields = ["id", "title", "description", "completed", "created_at", "updated_at"]
    for field in required_fields:
        assert field in data

# -----------------------------
# Error Handling Tests
# -----------------------------

def test_method_not_allowed():
    """Test that unsupported HTTP methods return 405"""
    # Assuming GET is not allowed on /todos/{id} - but it is, so test a different approach
    # Instead, test that a completely wrong method on an existing endpoint returns 405
    # FastAPI typically returns 405 for unsupported methods
    response = client.patch("/todos/")
    assert response.status_code in [405, 422]  # 405 Method Not Allowed or 422 if it tries to parse

def test_unsupported_media_type():
    """Test sending unsupported media type"""
    headers = {"Content-Type": "text/plain"}
    response = client.post("/todos/", content='{"title": "Test"}', headers=headers)
    # FastAPI may still process this or return 415 - behavior depends on configuration
    # More likely to get 422 due to parsing issues
    assert response.status_code in [415, 422]

# -----------------------------
# Final Integration Test
# -----------------------------

def test_full_todo_lifecycle():
    """Test the complete lifecycle of a todo item"""
    # 1. Create
    create_response = client.post(
        "/todos/",