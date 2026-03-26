Here is a complete `main.py` file for a FastAPI project named "My Project":
# main.py
from fastapi import FastAPI, status
from pydantic import BaseModel
from typing import List

app = FastAPI()

# In-memory storage
data = {
    "users": [
        {"id": 1, "name": "John Doe", "email": "john@example.com"},
        {"id": 2, "name": "Jane Doe", "email": "jane@example.com"},
    ],
    "posts": [
        {"id": 1, "title": "My First Post", "content": "Hello, World!"},
        {"id": 2, "title": "My Second Post", "content": "This is my second post."},
    ],
}

class User(BaseModel):
    id: int
    name: str
    email: str

class Post(BaseModel):
    id: int
    title: str
    content: str

# Health endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# Users endpoint
@app.get("/users/")
async def read_users():
    return data["users"]

@app.post("/users/")
async def create_user(user: User):
    data["users"].append(user.dict())
    return user

@app.get("/users/{user_id}")
async def read_user(user_id: int):
    for user in data["users"]:
        if user["id"] == user_id:
            return user
    return {"error": "User not found"}

@app.put("/users/{user_id}")
async def update_user(user_id: int, user: User):
    for i, u in enumerate(data["users"]):
        if u["id"] == user_id:
            data["users"][i] = user.dict()
            return user
    return {"error": "User not found"}

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    for i, u in enumerate(data["users"]):
        if u["id"] == user_id:
            del data["users"][i]
            return {"message": "User deleted"}
    return {"error": "User not found"}

# Posts endpoint
@app.get("/posts/")
async def read_posts():
    return data["posts"]

@app.post("/posts/")
async def create_post(post: Post):
    data["posts"].append(post.dict())
    return post

@app.get("/posts/{post_id}")
async def read_post(post_id: int):
    for post in data["posts"]:
        if post["id"] == post_id:
            return post
    return {"error": "Post not found"}

@app.put("/posts/{post_id}")
async def update_post(post_id: int, post: Post):
    for i, p in enumerate(data["posts"]):
        if p["id"] == post_id:
            data["posts"][i] = post.dict()
            return post
    return {"error": "Post not found"}

@app.delete("/posts/{post_id}")
async def delete_post(post_id: int):
    for i, p in enumerate(data["posts"]):
        if p["id"] == post_id:
            del data["posts"][i]
            return {"message": "Post deleted"}
    return {"error": "Post not found"}

# Error handling
@app.exception_handler(Exception)
async def http_exception_handler(request, exc):
    return {"error": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
This code includes:

1. A FastAPI app instance
2. In-memory storage for users and posts
3. CRUD endpoints for users and posts
4. A health endpoint
5. Proper error handling using a custom exception handler
6. Automatic reloading of the app when code changes

Note that this is a basic example and you should consider using a database instead of in-memory storage for a production-ready application.