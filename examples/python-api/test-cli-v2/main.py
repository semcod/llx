from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# In-memory storage
data = {
    1: {"name": "John", "age": 30},
    2: {"name": "Jane", "age": 25},
}

class User(BaseModel):
    id: int
    name: str
    age: int

class UserCreate(BaseModel):
    name: str
    age: int

class UserUpdate(BaseModel):
    name: str | None
    age: int | None

# /health endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# GET /users
@app.get("/users", response_model=List[User])
async def read_users():
    return list(data.values())

# GET /users/{user_id}
@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: int):
    user = data.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# POST /users
@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    new_id = max(data.keys()) + 1
    data[new_id] = user.dict()
    return data[new_id]

# PUT /users/{user_id}
@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user: UserUpdate):
    if user_id not in data:
        raise HTTPException(status_code=404, detail="User not found")
    data[user_id] = {**data[user_id], **user.dict()}
    return data[user_id]

# DELETE /users/{user_id}
@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    if user_id not in data:
        raise HTTPException(status_code=404, detail="User not found")
    del data[user_id]
    return {"message": "User deleted"}

This code includes:

1.  A FastAPI application instance.
2.  In-memory storage for users, represented as a dictionary.
3.  A `User` Pydantic model for user data.
4.  A `UserCreate` Pydantic model for creating new users.
5.  A `UserUpdate` Pydantic model for updating existing users.
6.  A `/health` endpoint to check the application's status.
7.  A `/users` endpoint to retrieve all users.
8.  A `/users/{user_id}` endpoint to retrieve a specific user by ID.
9.  A `/users` endpoint to create a new user.
10. A `/users/{user_id}` endpoint to update an existing user.
11. A `/users/{user_id}` endpoint to delete a user by ID.

The code uses proper error handling with HTTP exceptions for missing users or invalid requests. The `response_model` parameter is used to specify the expected response model for each endpoint. The `response_model` parameter is used to specify the expected response model for each endpoint.