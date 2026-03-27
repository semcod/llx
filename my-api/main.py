"""
FastAPI main.py for the API.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# In-memory storage
data = {
    "users": [
        {"id": 1, "name": "John Doe", "email": "john@example.com"},
        {"id": 2, "name": "Jane Doe", "email": "jane@example.com"},
    ],
    "products": [
        {"id": 1, "name": "Product 1", "price": 10.99},
        {"id": 2, "name": "Product 2", "price": 9.99},
    ],
}

class User(BaseModel):
    id: int
    name: str
    email: str

class Product(BaseModel):
    id: int
    name: str
    price: float

# Health endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# Users endpoints
@app.get("/users/")
async def read_users():
    return data["users"]

@app.get("/users/{user_id}")
async def read_user(user_id: int):
    for user in data["users"]:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.post("/users/")
async def create_user(user: User):
    data["users"].append(user.dict())
    return user

@app.put("/users/{user_id}")
async def update_user(user_id: int, user: User):
    for i, u in enumerate(data["users"]):
        if u["id"] == user_id:
            data["users"][i] = user.dict()
            return user
    raise HTTPException(status_code=404, detail="User not found")

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    for i, user in enumerate(data["users"]):
        if user["id"] == user_id:
            del data["users"][i]
            return {"message": "User deleted"}
    raise HTTPException(status_code=404, detail="User not found")

# Products endpoints
@app.get("/products/")
async def read_products():
    return data["products"]

@app.get("/products/{product_id}")
async def read_product(product_id: int):
    for product in data["products"]:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.post("/products/")
async def create_product(product: Product):
    data["products"].append(product.dict())
    return product

@app.put("/products/{product_id}")
async def update_product(product_id: int, product: Product):
    for i, p in enumerate(data["products"]):
        if p["id"] == product_id:
            data["products"][i] = product.dict()
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.delete("/products/{product_id}")
async def delete_product(product_id: int):
    for i, product in enumerate(data["products"]):
        if product["id"] == product_id:
            del data["products"][i]
            return {"message": "Product deleted"}
    raise HTTPException(status_code=404, detail="Product not found")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)