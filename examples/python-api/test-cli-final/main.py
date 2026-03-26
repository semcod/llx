from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI(title="My Project", description="My Project API")

# In-memory storage
data = {
    1: {"name": "John", "age": 30},
    2: {"name": "Alice", "age": 25},
}

class User(BaseModel):
    id: int
    name: str
    age: int

class UserUpdate(BaseModel):
    name: str
    age: int

# /health endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# GET /users
@app.get("/users", response_model=List[User])
async def get_users():
    return list(data.values())

# GET /users/{user_id}
@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    if user_id not in data:
        raise HTTPException(status_code=404, detail="User not found")
    return data[user_id]

# POST /users
@app.post("/users", response_model=User)
async def create_user(user: User):
    data[len(data) + 1] = user.dict()
    return user

# PUT /users/{user_id}
@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserUpdate):
    if user_id not in data:
        raise HTTPException(status_code=404, detail="User not found")
    data[user_id]["name"] = user.name
    data[user_id]["age"] = user.age
    return data[user_id]

# DELETE /users/{user_id}
@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    if user_id not in data:
        raise HTTPException(status_code=404, detail="User not found")
    del data[user_id]
    return {"message": "User deleted"}

# Error handling
@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return {"error": str(exc)}

This code includes:

*   A FastAPI application with a title and description
*   In-memory storage for users
*   CRUD endpoints for users:
    *   GET /users: Returns a list of all users
    *   GET /users/{user_id}: Returns a specific user by ID
    *   POST /users: Creates a new user
    *   PUT /users/{user_id}: Updates an existing user
    *   DELETE /users/{user_id}: Deletes a user
*   A /health endpoint to check the application's status
*   Proper error handling with a custom exception handler

You can run this code with `uvicorn main:app --reload` and access the API endpoints at `http://localhost:8000`.