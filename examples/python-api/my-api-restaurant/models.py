from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class MenuItem(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: float
    category: str


class OrderItem(BaseModel):
    menu_item_id: int
    quantity: int
    notes: Optional[str] = None


class OrderCreate(BaseModel):
    customer_name: str
    customer_phone: str
    items: List[OrderItem]
    table_number: Optional[int] = None
    delivery_address: Optional[str] = None


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    items: Optional[List[OrderItem]] = None
    table_number: Optional[int] = None
    delivery_address: Optional[str] = None
    status: Optional[str] = None


class Order(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    items: List[OrderItem]
    table_number: Optional[int] = None
    delivery_address: Optional[str] = None
    status: str
    total_price: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: str