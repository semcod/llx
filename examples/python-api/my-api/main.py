from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI(title="My Project")

# In-memory storage
items_db: Dict[int, "Item"] = {}
next_id = 1
class ItemBase(BaseModel):
    name: str
    description: str | None = None
class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int


@app.post("/items/", response_model=Item, status_code=201)
def create_item(item: ItemCreate):
    global next_id
    item_obj = Item(id=next_id, **item.dict())
    items_db[next_id] = item_obj
    next_id += 1
    return item_obj


@app.get("/items/", response_model=List[Item])
def read_items():
    return list(items_db.values())


@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]


@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, item: ItemCreate):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = Item(id=item_id, **item.dict())
    items_db[item_id] = updated
    return updated


@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    del items_db[item_id]
    return None


@app.get("/health")
def health():
    return {"status": "ok"}