from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    preparing = "preparing"
    ready = "ready"
    delivered = "delivered"
    cancelled = "cancelled"

class PaymentStatus(str, Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    refunded = "refunded"

class MenuItem(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)
    category: str = Field(..., min_length=1, max_length=50)

class MenuItemCreate(MenuItem):
    pass

class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=50)

class MenuItemResponse(MenuItem):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class OrderItem(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=200)

class OrderItemResponse(OrderItem):
    id: int
    price_at_time: float = Field(..., gt=0)

    class Config:
        orm_mode = True

class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_phone: str = Field(..., min_length=6, max_length=20)
    customer_email: Optional[str] = Field(None, max_length=100)
    table_number: Optional[int] = Field(None, ge=1)
    items: List[OrderItem] = Field(..., min_items=1)
    special_instructions: Optional[str] = Field(None, max_length=500)

    @validator('customer_email')
    def validate_email(cls, v):
        if v is not None and '@' not in v:
            raise ValueError('Invalid email format')
        return v

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    table_number: Optional[int] = Field(None, ge=1)
    special_instructions: Optional[str] = Field(None, max_length=500)
    items: Optional[List[OrderItem]] = None

class OrderResponse(BaseModel):
    id: int
    order_number: str = Field(..., min_length=1)
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    table_number: Optional[int]
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: float = Field(..., ge=0)
    special_instructions: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    class Config:
        orm_mode = True

class OrderSummary(BaseModel):
    id: int
    order_number: str
    customer_name: str
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: float
    created_at: datetime

    class Config:
        orm_mode = True

class PaymentCreate(BaseModel):
    amount: float = Field(..., gt=0)
    method: str = Field(..., min_length=1, max_length=50)
    transaction_id: Optional[str] = Field(None, max_length=100)

class PaymentResponse(BaseModel):
    id: int
    order_id: int
    amount: float
    method: str
    status: PaymentStatus
    transaction_id: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True

# Database schemas (SQLAlchemy-inspired, but kept in Pydantic style)
class DBMenuItem(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    category: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DBOrder(BaseModel):
    id: int
    order_number: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str]
    table_number: Optional[int]
    status: OrderStatus
    payment_status: PaymentStatus
    total_amount: float
    special_instructions: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DBOrderItem(BaseModel):
    id: int
    order_id: int
    menu_item_id: int
    quantity: int
    price_at_time: float
    notes: Optional[str]

    class Config:
        orm_mode = True

class DBPayment(BaseModel):
    id: int
    order_id: int
    amount: float
    method: str
    status: PaymentStatus
    transaction_id: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True