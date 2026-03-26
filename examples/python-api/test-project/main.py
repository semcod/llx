from fastapiimport FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
import uuid

app = FastAPI(
    title="RestaurantOrderAPI",
    description="REST API for managing restaurant orders with in‑memory storage.",
    version="1.0.0",
)

# ----- Pydantic Models -----
class OrderItem(BaseModel):
    name: str = Field(..., example="Margherita Pizza")
    quantity: int = Field(..., gt=0, example=2)
    unit_price: float = Field(..., gt=0, example=12.5)

class OrderBase(BaseModel):
    items: List[OrderItem]
    status: str = Field(default="placed", regex="^(placed|preparing|ready|delivered|cancelled)$")

class OrderCreate(OrderBase):
    passclass OrderUpdate(BaseModel):
    items: List[OrderItem] | None = None
    status: str | None = Field(None, regex="^(placed|preparing|ready|delivered|cancelled)$")

class OrderInDB(OrderBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ----- In‑memory storage -----
orders: Dict[str, OrderInDB] = {}

# ----- Helper -----
def get_order_or_404(order_id: str) -> OrderInDB:
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found")
    return order

# ----- Endpoints -----
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

@app.post("/orders", response_model=OrderInDB, status_code=status.HTTP_201_CREATED, tags=["Orders"])
def create_order(order: OrderCreate):
    order_in_db = OrderInDB(**order.dict())
    orders[order_in_db.id] = order_in_db
    return order_in_db

@app.get("/orders", response_model=List[OrderInDB], tags=["Orders"])
def list_orders():
    return list(orders.values())

@app.get("/orders/{order_id}", response_model=OrderInDB, tags=["Orders"])
def read_order(order_id: str):
    return get_order_or_404(order_id)

@app.put("/orders/{order_id}", response_model=OrderInDB, tags=["Orders"])
def update_order(order_id: str, order_update: OrderUpdate):
    stored = get_order_or_404(order_id)
    update_data = order_update.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")
    updated = stored.copy(update=update_data)
    orders[order_id] = updated
    return updated

@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Orders"])
def delete_order(order_id: str):
    if order_id not in orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order {order_id} not found")
    del orders[order_id]
    return None