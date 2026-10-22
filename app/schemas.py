
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# =========================
# PRODUCT SCHEMAS
# =========================

class ProductCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=150)
    price: float = Field(gt=0)
    description: str = ""
    stock: int = Field(default=0, ge=0)


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_name: str
    price: float
    description: str
    stock: int
    created_date: datetime


# =========================
# ORDER SCHEMAS
# =========================

class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=3, max_length=40)
    address: str = Field(min_length=3, max_length=300)
    product_id: int = Field(gt=0)
    quantity: int = Field(default=1, ge=1)


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    phone: str
    address: str
    product_id: int
    quantity: int
    total_price: float
    order_status: str
    created_date: datetime


class OrderStatusUpdate(BaseModel):
    order_status: str


# =========================
# AI CHAT SCHEMAS
# =========================

class ChatRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    facts: str = Field(default="", max_length=4000)
    order_id: int | None = None


class ChatResponse(BaseModel):
    answer: str
    source: str
