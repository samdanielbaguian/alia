"""Payment model for MongoDB."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import secrets


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentProvider(str, Enum):
    """Payment provider enumeration."""
    ORANGE_MONEY = "orange_money"
    MTN_MONEY = "mtn_money"
    MOOV_MONEY = "moov_money"


def generate_payment_id() -> str:
    """Generate a unique payment ID."""
    return f"pay_{secrets.token_urlsafe(16)}"


class Payment(BaseModel):
    """Payment model for MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    payment_id: str = Field(default_factory=generate_payment_id)
    
    # References
    order_id: str
    user_id: str
    merchant_id: str
    
    # Payment Details
    amount: float = Field(gt=0)
    currency: str = "XOF"  # West African CFA franc
    provider: PaymentProvider
    phone_number: str  # Format: +225XXXXXXXXXX
    
    # Transaction Information
    transaction_id: Optional[str] = None  # Provider's transaction ID
    status: PaymentStatus = PaymentStatus.PENDING
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Fee Breakdown
    gross_amount: float = Field(gt=0)  # Original order amount
    platform_fee: float = Field(default=0.0, ge=0)  # Alia's commission
    payment_gateway_fee: float = Field(default=0.0, ge=0)  # Provider's fee
    merchant_payout: float = Field(default=0.0, ge=0)  # Amount merchant receives
    
    # Timestamps
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=10)
    )
    webhook_received_at: Optional[datetime] = None
    
    # Retry and Tracking
    retry_count: int = Field(default=0, ge=0)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "payment_id": "pay_abc123xyz",
                "order_id": "695318db0f5f01144f5b4fb0",
                "user_id": "user123",
                "merchant_id": "merchant123",
                "amount": 92000,
                "currency": "XOF",
                "provider": "orange_money",
                "phone_number": "+2250707123456",
                "transaction_id": "OM123456789",
                "status": "pending",
                "gross_amount": 92000,
                "platform_fee": 2300,
                "payment_gateway_fee": 1380,
                "merchant_payout": 88320,
                "initiated_at": "2025-12-30T00:12:11Z",
                "expires_at": "2025-12-30T00:22:11Z",
                "retry_count": 0
            }
        }


class Refund(BaseModel):
    """Refund model for MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    refund_id: str = Field(default_factory=lambda: f"ref_{secrets.token_urlsafe(16)}")
    
    # References
    payment_id: str
    order_id: str
    user_id: str
    merchant_id: str
    
    # Refund Details
    amount: float = Field(gt=0)  # Refund amount (can be partial)
    currency: str = "XOF"
    reason: str
    status: PaymentStatus = PaymentStatus.PROCESSING
    
    # Transaction Information
    provider_refund_id: Optional[str] = None
    failure_reason: Optional[str] = None
    
    # Timestamps
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "refund_id": "ref_xyz789",
                "payment_id": "pay_abc123xyz",
                "order_id": "695318db0f5f01144f5b4fb0",
                "user_id": "user123",
                "merchant_id": "merchant123",
                "amount": 92000,
                "currency": "XOF",
                "reason": "Product out of stock",
                "status": "processing",
                "requested_at": "2025-12-30T00:12:11Z"
            }
        }
