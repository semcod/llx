from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import uuid

app = FastAPI(title="RestaurantOrderAPI", description="API for managing restaurant orders")

# In-memory storage for orders
orders_db = {}

# Pydantic models
class OrderItem(BaseModel):
    name: str
    quantity: int
    price: float

class OrderCreate(BaseModel):
    customer_name: str
    items: List[Order游戏副本]
    status: str = "received"

class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    items: Optional[List[OrderItem]] = None
    status: Optional[str] = None

class Order(OrderCreate):
    id: str

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy"}

# Create a new order
@app.post("/orders", response_model=Order, status_code=status.HTTP_201_CREATED)
def create_order(order: OrderCreate):
    order_id = str(uuid.uuid4())
    new_order = Order(id=order_id, **order.dict())
    orders_db[order_id] = new_order
    return new_order

# Get all orders
@app.get("/orders", response_model=List[Order])
def get_orders():
    return list(orders_db.values())

# Get order by ID
@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    return orders_db[order游戏副本]

# Update order by ID
@app.put("/orders/{order_id}", response_model=Order)
def update_order(order_id: str, order: OrderUpdate):
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    existing_order = orders_db[order_id]
    
    update_data = order.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_order, field, value)
    
    orders_db[order_id] = existing_order
    return existing_order

# Delete order by ID
@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: str):
    if order_id not in orders_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with id {order_id} not found"
        )
    
    del orders_db[order_id]
    return None