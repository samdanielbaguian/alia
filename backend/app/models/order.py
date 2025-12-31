from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"  # Payment confirmed, order ready to process
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Payment status enumeration for orders."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StatusHistory(BaseModel):
    """Status history entry for tracking order status changes."""
    status: str  # pending, confirmed, shipped, delivered, cancelled
    changed_at: datetime
    changed_by: str  # user_id or "system"
    note: Optional[str] = None  # Optional note about the change


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
    payment_method: str  # "orange_money", "mtn_money", "moov_money"
    payment_status: Optional[str] = None  # Tracks payment status separately
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # New fields for order management
    status_history: List[StatusHistory] = Field(default_factory=list)
    cancelled_by: Optional[str] = None  # "customer" or "merchant"
    cancellation_reason: Optional[str] = None  # Why was it cancelled
    tracking_number: Optional[str] = None  # Shipping tracking number
    shipped_at: Optional[datetime] = None  # When order was shipped
    delivered_at: Optional[datetime] = None  # When order was delivered
    
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
