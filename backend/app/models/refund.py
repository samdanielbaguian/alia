"""Refund model for MongoDB."""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field
import secrets


class RefundStatus(str, Enum):
    """Refund status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


def generate_refund_id() -> str:
    """Generate a unique refund ID."""
    return f"ref_{secrets.token_urlsafe(16)}"


class Refund(BaseModel):
    """Refund model for MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    refund_id: str = Field(default_factory=generate_refund_id)
    
    # References
    payment_id: str
    order_id: str
    user_id: str  # Customer
    merchant_id: str
    initiated_by: str  # merchant user_id who initiated refund
    
    # Refund Details
    amount: float = Field(gt=0)
    currency: str = "XOF"
    reason: str
    note: Optional[str] = None
    
    # Status
    status: RefundStatus = RefundStatus.PENDING
    failure_reason: Optional[str] = None
    
    # Provider info
    provider: str
    provider_refund_id: Optional[str] = None
    transaction_id: Optional[str] = None  # Original payment transaction ID
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "refund_id": "ref_abc123xyz",
                "payment_id": "pay_xyz789",
                "order_id": "695318db0f5f01144f5b4fb0",
                "user_id": "user123",
                "merchant_id": "merchant123",
                "initiated_by": "merchant123",
                "amount": 46000,
                "currency": "XOF",
                "reason": "Customer requested refund",
                "note": "Product defective",
                "status": "completed",
                "provider": "orange_money"
            }
        }
