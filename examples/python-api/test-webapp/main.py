from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

app = FastAPI()

# In-memory storage
data = {
    1: {"name": "Item 1", "description": "This is item 1"},
    2: {"name": "Item 2", "description": "This is item 2"},
}

class Item(BaseModel):
    name: str
    description: str

class ItemResponse(Item):
    id: int

# /health endpoint
@app.get("/health")
async def health():
    return {"status": "ok"}

# GET /items
@app.get("/items", response_model=List[ItemResponse])
async def read_items():
    return [{"id": id, **item} for id, item in data.items()]

# GET /items/{item_id}
@app.get("/items/{item_id}", response_model=ItemResponse)
async def read_item(item_id: int):
    if item_id not in data:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": item_id, **data[item_id]}

# POST /items
@app.post("/items", response_model=ItemResponse)
async def create_item(item: Item):
    new_id = max(data.keys()) + 1
    data[new_id] = item.dict()
    return {"id": new_id, **item.dict()}

# PUT /items/{item_id}
@app.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(item_id: int, item: Item):
    if item_id not in data:
        raise HTTPException(status_code=404, detail="Item not found")
    data[item_id] = item.dict()
    return {"id": item_id, **item.dict()}

# DELETE /items/{item_id}
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if item_id not in data:
        raise HTTPException(status_code=404, detail="Item not found")
    del data[item_id]
    return {"message": "Item deleted"}

This code includes:

*   A FastAPI application with a main.py file
*   In-memory storage for items
*   CRUD endpoints for items:
    *   GET /items: Returns a list of all items
    *   GET /items/{item_id}: Returns a single item by ID
    *   POST /items: Creates a new item
    *   PUT /items/{item_id}: Updates an existing item
    *   DELETE /items/{item_id}: Deletes an item
*   A /health endpoint to check the application's status
*   Proper error handling for 404 errors when an item is not found
*   Pydantic models for item data
*   Type hints for function parameters and return types
*   Response models for API responses