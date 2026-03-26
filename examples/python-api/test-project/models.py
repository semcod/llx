from pydantic importBaseModel, Field, validator, EmailStr, conint, confloat
from datetime import datetimefrom enum import Enum as PyEnum
from typing import List, Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship, declarative_base

# -------------------------
# Enums
# -------------------------
class OrderStatus(str, PyEnum):
    PENDING = "pending"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# -------------------------
# Pydantic Models
# -------------------------
class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    price: confloat(gt=0) = Field(..., description="Price must be greater than zero")
    category: Optional[str] = Field(None, max_length=50)

    class Config:
        orm_mode = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    price: Optional[confloat(gt=0)] = None
    category: Optional[str] = Field(None, max_length=50)


class MenuItemResponse(MenuItemBase):
    id: int


class OrderItemBase(BaseModel):
    menu_item_id: int = Field(..., gt=0)
    quantity: conint(gt=0) = Field(..., description="Quantity must be positive")
    unit_price: confloat(gt=0) = Field(..., description="Unit price must be greater than zero")

    @validator("unit_price")
    def unit_price_must_match_menu_item(cls, v, values):
        # This validator is a placeholder; actual check would be done in service layer.
        return v


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemResponse(OrderItemBase):
    id: int
    order_id: int
    subtotal: confloat(gt=0) = Field(..., description="Calculated as quantity * unit_price")


class OrderBase(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_phone: str = Field(..., min_length=9, max_length=20)
    customer_email: EmailStr
    status: OrderStatus = OrderStatus.PENDING


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_items=1)


class OrderUpdate(BaseModel):
    customer_name: Optional[str] = Field(None, min_length=1, max_length=100)
    customer_phone: Optional[str] = Field(None, min_length=9, max_length=20)
    customer_email: Optional[EmailStr] = None    status: Optional[OrderStatus] = None


class OrderResponse(OrderBase):
    id: int
    order_time: datetime
    total_amount: confloat(gt=0, allow_inf=False) = Field(
        ..., description="Sum of all order items subtotals"
    )
    items: List[OrderItemResponse] = []

    class Config:
        orm_mode = True


# -------------------------
# SQLAlchemy Models
# -------------------------
Base = declarative_base()


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(50), nullable=True, index=True)

    order_items = relationship("OrderItem", back_populates="menu_item")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(20), nullable=False)
    customer_email = Column(String(100), nullable=False)
    order_time = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    total_amount = Column(Numeric(12, 2), nullable=False)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(12, 2), nullable=False)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")