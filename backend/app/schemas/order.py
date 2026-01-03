from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class OrderProductCreate(BaseModel):
    """Schema for product in order creation."""
    product_id: str
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    """Schema for creating an order."""
    products: List[OrderProductCreate]
    payment_method: str  # "orange_money", "moov_money", "wave", "stripe"
    
    class Config:
        json_schema_extra = {
            "example": {
                "products": [
                    {"product_id": "prod123", "quantity": 2}
                ],
                "payment_method": "orange_money"
            }
        }


class OrderProductResponse(BaseModel):
    """Schema for product in order response."""
    product_id: str
    quantity: int
    price: float
    title: str


class StatusHistoryResponse(BaseModel):
    """Schema for status history entry."""
    status: str
    changed_at: datetime
    changed_by: str
    note: Optional[str] = None


class OrderResponse(BaseModel):
    """Schema for order response."""
    id: str
    user_id: str
    merchant_id: str
    products: List[OrderProductResponse]
    total_amount: float
    status: str
    payment_method: str
    created_at: datetime
    updated_at: datetime
    
    # New fields
    status_history: Optional[List[StatusHistoryResponse]] = None
    cancelled_by: Optional[str] = None
    cancellation_reason: Optional[str] = None
    tracking_number: Optional[str] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class StatusUpdateRequest(BaseModel):
    """Schema for updating order status."""
    status: str = Field(..., description="New status: confirmed, shipped, delivered, cancelled")
    note: Optional[str] = Field(None, description="Optional note about status change")
    tracking_number: Optional[str] = Field(None, description="Tracking number (required for shipped status)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "confirmed",
                "note": "Order confirmed, preparing shipment"
            }
        }


class ShipOrderRequest(BaseModel):
    """Schema for shipping an order."""
    tracking_number: str = Field(..., description="Shipping tracking number")
    carrier: Optional[str] = Field(None, description="Shipping carrier (e.g., DHL Express)")
    note: Optional[str] = Field(None, description="Optional note about shipment")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tracking_number": "TRACK123456",
                "carrier": "DHL Express",
                "note": "Shipped via DHL"
            }
        }


class CancelOrderRequest(BaseModel):
    """Schema for cancelling an order."""
    reason: str = Field(..., description="Reason for cancellation")
    details: Optional[str] = Field(None, description="Optional detailed explanation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Product out of stock",
                "details": "The item is currently unavailable"
            }
        }


class ConfirmOrderRequest(BaseModel):
    """Schema for confirming an order."""
    note: Optional[str] = Field(None, description="Optional note about confirmation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "note": "Order confirmed, preparing shipment"
            }
        }


class DeliverOrderRequest(BaseModel):
    """Schema for marking order as delivered."""
    note: Optional[str] = Field(None, description="Optional note about delivery")
    
    class Config:
        json_schema_extra = {
            "example": {
                "note": "Delivered to customer"
            }
        }


class OrderHistoryResponse(BaseModel):
    """Schema for order status history response."""
    order_id: str
    current_status: str
    history: List[StatusHistoryResponse]


class HeatmapZone(BaseModel):
    """Schema for a single heatmap zone with sales data."""
    city: Optional[str] = None
    region: Optional[str] = None
    orders: int
    total_sales: float
    lat: float
    lng: float


class SalesHeatmapResponse(BaseModel):
    """Schema for sales heatmap response."""
    heatmap: List[HeatmapZone]
    top_zone: Optional[HeatmapZone] = None
