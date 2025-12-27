from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderProduct(BaseModel):
    """Product item in an order."""
    product_id: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
    title: str


class Order(BaseModel):
    """Order model for MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    merchant_id: str
    products: List[OrderProduct]
    total_amount: float = Field(gt=0)
    status: OrderStatus = OrderStatus.PENDING
    payment_method: str  # "orange_money", "moov_money", "wave", "stripe"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "merchant_id": "merchant123",
                "products": [
                    {
                        "product_id": "prod123",
                        "quantity": 2,
                        "price": 299.99,
                        "title": "Smartphone XYZ"
                    }
                ],
                "total_amount": 599.98,
                "status": "pending",
                "payment_method": "orange_money"
            }
        }
