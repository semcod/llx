from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

class ItemCreate(Item):
    pass

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None

class ItemResponse(Item):
    id: int

    class Config:
        orm_mode = True

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify the service is running
    """
    return {
        "status": "healthy",
        "service": "My Project",
        "version": "1.0.0"
    }

# CRUD endpoints
@app.post("/items", response_model=ItemResponse, status_code=201, tags=["Items"])
def create_item(item: ItemCreate):
    """
    Create a new item
    """
    global next_id
    item_id = next_id
    next_id += 1
    
    items[item_id] = {**item.dict(), "id": item_id}
    
    logger.info(f"Created item with id: {item_id}")
    return items[item_id]

@app.get("/items", response_model=List[ItemResponse], tags=["Items"])
def read_items():
    """
    Get all items
    """
    return list(items.values())

@app.get("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
def read_item(item_id: int):
    """
    Get an item by ID
    """
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return items[item_id]

@app.put("/items/{item_id}", response_model=ItemResponse, tags=["Items"])
def update_item(item_id: int, item: ItemUpdate):
    """
    Update an item by ID
    """
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update only the fields that are provided
    update_data = item.dict(exclude_unset=True)
    for field, value in update_data.items():
        items[item_id][field] = value
    
    logger.info(f"Updated item with id: {item_id}")
    return items[item_id]

@app.delete("/items/{item_id}", status_code=204, tags=["Items"])
def delete_item(item_id: int):
    """
    Delete an item by ID
    """
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    del items[item_id]
    logger.info(f"Deleted item with id: {item_id}")
    return

# If running directly with uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)