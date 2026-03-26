from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4, UUID

app = FastAPI(title="RestaurantOrderAPI", description="REST API for managing restaurant orders")

# In-memory storage
orders_db = {}

# Models
class OrderItem(BaseModel):
    name: str
    quantity: int
    price: float

class OrderCreate(BaseModel):
    customer_name: str
    items: List[OrderItem]
    status: str = "received"

class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    items: Optional[List[OrderItem]] = None
    status: Optional[str] = None

class Order(OrderCreate):
    id: UUID

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Create order
@app.post("/orders", response_model=Order, status_code=201)
def create_order(order: OrderCreate):
    order_id = uuid4()
    new_order = Order(id=order_id, **order.dict())
    orders_db[order_id] = new_order
    return new_order

# Get all orders
@app.get("/orders", response_model=List[Order])
def get_orders():
    return list(orders_db.values())

# Get order by ID
@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: UUID):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]

# Update order
@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: UUID, order_update: OrderUpdate):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    existing_order = orders_db[order_id]
    
    if order_update.customer_name is not None:
        existing_order.customer_name = order_update.customer_name
    if order_update.items is not None:
        existing_order.items = order_update.items
    if order_update.status is not None:
        existing_order.status = order_update.status
    
    orders_db[order_id] = existing_order
    return existing_order

# Delete order
@app.delete("/orders/{order_id}", status_code=204)
def delete_order(order_id: UUID):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    
    del orders_db[order_id]
    return None