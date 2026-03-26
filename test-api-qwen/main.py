from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from datetime import datetime

app = FastAPI(
    title="My Project",
    description="A simple CRUD API for My Project with in-memory storage",
    version="1.0.0"
)

# In-memory storage
items = {}
next_id = 1

# Pydantic models
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    in_stock: bool = True

class ItemResponse(Item):
    id: int
    created_at: datetime
    updated_at: datetime

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify the service is running
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "service": "My Project"
    }

# Create an item
@app.post("/items", response_model=ItemResponse, status_code=201, tags=["Items"])
def create_item(item: Item):
    """
    Create a new item in the system
    """
    global next_id
    item_id = next_id
    next_id += 1
    
    created_item = {
        "id": item_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "in_stock": item.in_stock,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    items[item_id] = created_item
    return created_item

# Get all items
@app.get("/items", response_model=List[ItemResponse], tags=["Items"])
def get_items():
    """
    Retrieve all items from the system
    """
    return list(items.values())

# Get item by ID
@app.get("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
def get_item(item_id: int):
    """
    Retrieve a specific item by ID
    """
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]

# Update an item
@app.put("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
def update_item(item_id: int, item_update: ItemUpdate):
    """
    Update an existing item by ID
    """
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = items[item_id]
    update_data = item_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field in item:
            item[field] = value
    
    item["updated_at"] = datetime.now()
    items[item_id] = item
    
    return item

# Delete an item
@app.delete("/items/{item_id}", status_code=204, tags=["Items"])
def delete_item(item_id: int):
    """
    Delete an item by ID
    """
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    del items[item_id]
    return None

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)