"""Payment schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PaymentInitiateRequest(BaseModel):
    """Schema for initiating a payment."""
    order_id: str
    phone_number: str  # Mobile Money number (+225XXXXXXXXXX)
    
    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "695318db0f5f01144f5b4fb0",
                "phone_number": "+2250707123456"
            }
        }


class PaymentInitiateResponse(BaseModel):
    """Schema for payment initiation response."""
    payment_id: str
    status: str
    amount: float
    currency: str
    provider: str
    transaction_id: Optional[str] = None
    message: str
    ussd_code: str
    expires_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "payment_id": "pay_abc123xyz",
                "status": "pending",
                "amount": 92000,
                "currency": "XOF",
                "provider": "orange_money",
                "transaction_id": "OM123456789",
                "message": "Veuillez composer *144# pour confirmer le paiement de 92000 FCFA",
                "ussd_code": "*144#",
                "expires_at": "2025-12-30T00:22:11Z"
            }
        }


class PaymentStatusResponse(BaseModel):
    """Schema for payment status response."""
    payment_id: str
    order_id: str
    status: str
    amount: float
    currency: str
    provider: str
    transaction_id: Optional[str] = None
    phone_number: Optional[str] = None
    initiated_at: datetime
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "payment_id": "pay_abc123xyz",
                "order_id": "695318db0f5f01144f5b4fb0",
                "status": "completed",
                "amount": 92000,
                "currency": "XOF",
                "provider": "orange_money",
                "transaction_id": "OM123456789",
                "phone_number": "+2250707******",
                "initiated_at": "2025-12-30T00:12:11Z",
                "completed_at": "2025-12-30T00:15:32Z"
            }
        }


class PaymentHistoryItem(BaseModel):
    """Schema for payment history item."""
    payment_id: str
    order_id: str
    amount: float
    status: str
    provider: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class PaymentHistoryResponse(BaseModel):
    """Schema for payment history response."""
    payments: List[PaymentHistoryItem]
    total: int
    limit: int
    offset: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "payments": [
                    {
                        "payment_id": "pay_abc123xyz",
                        "order_id": "695318db0f5f01144f5b4fb0",
                        "amount": 92000,
                        "status": "completed",
                        "provider": "orange_money",
                        "created_at": "2025-12-30T00:12:11Z",
                        "completed_at": "2025-12-30T00:15:32Z"
                    }
                ],
                "total": 1,
                "limit": 20,
                "offset": 0
            }
        }


class CancelPaymentResponse(BaseModel):
    """Schema for payment cancellation response."""
    message: str
    payment_id: str
    status: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Payment cancelled successfully",
                "payment_id": "pay_abc123xyz",
                "status": "cancelled"
            }
        }


class RefundRequest(BaseModel):
    """Schema for refund request."""
    reason: str
    amount: Optional[float] = None  # Optional for partial refund
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Product out of stock",
                "amount": 92000
            }
        }


class RefundResponse(BaseModel):
    """Schema for refund response."""
    message: str
    refund_id: str
    status: str
    amount: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Refund initiated",
                "refund_id": "ref_xyz789",
                "status": "processing",
                "amount": 92000
            }
        }


class WebhookResponse(BaseModel):
    """Schema for webhook response."""
    message: str
    payment_id: Optional[str] = None
    status: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Webhook processed successfully",
                "payment_id": "pay_abc123xyz",
                "status": "completed"
            }
        }


class SimulatePaymentResponse(BaseModel):
    """Schema for simulated payment response (admin only)."""
    message: str
    payment_id: str
    status: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Payment simulated successfully",
                "payment_id": "pay_abc123xyz",
                "status": "completed"
            }
        }
