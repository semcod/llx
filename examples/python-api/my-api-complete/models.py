from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    ready = "ready"
    delivered = "delivered"
    cancelled = "cancelled"

class MenuItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)
    category: str = Field(..., min_length=1, max_length=50)

class MenuItemCreate(MenuItem):
    pass

class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    price: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, min_length=1, max_length=50)

class MenuItemInDB(MenuItem):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class OrderItem(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=200)

    @validator('quantity')
    def validate_quantity(cls, v):
        if v > 100:
            raise ValueError('Quantity cannot exceed 100')
        return v

class OrderItemInDB(OrderItem):
    id: int
    price_at_time: float = Field(..., gt=0)

    class Config:
        from_attributes = True

class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_phone: str = Field(..., min_length=6, max_length=20)
    customer_email: Optional[str] = Field(None, max_length=100)
    table_number: Optional[int] = Field(None, ge=1)
    items: List[OrderItem] = Field(..., min_items=1)
    special_requests: Optional[str] = Field(None, max_length=500)

    @validator('customer_phone')
    def validate_phone(cls, v):
        # Basic phone number validation (digits, +, spaces, hyphens, parentheses)
        import re
        if not re.match(r'^[+\d\s\-\(\)]+$', v):
            raise ValueError('Invalid phone number format')
        return v

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    table_number: Optional[int] = Field(None, ge=1)
    special_requests: Optional[str] = Field(None, max_length=500)
    items: Optional[List[OrderItem]] = None

class OrderInDB(BaseModel):
    id: int
    order_number: str = Field(..., min_length=8, max_length=20)
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    table_number: Optional[int]
    status: OrderStatus
    special_requests: Optional[str]
    total_amount: float = Field(..., ge=0)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderWithItems(OrderInDB):
    items: List[OrderItemInDB]

class OrderSummary(BaseModel):
    id: int
    order_number: str
    customer_name: str
    status: OrderStatus
    total_amount: float
    created_at: datetime

    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    detail: str

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime