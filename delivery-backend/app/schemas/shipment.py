from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.shipment import ShipmentStatus


class ShipmentCreate(BaseModel):
    origin_address: str
    destination_address: str
    sender_name: str
    sender_phone: str
    recipient_name: str
    recipient_phone: str
    weight: float = Field(..., gt=0)
    dimensions: Optional[str] = None
    estimated_delivery: datetime
    notes: Optional[str] = None


class ShipmentUpdate(BaseModel):
    status: Optional[ShipmentStatus] = None
    estimated_delivery: Optional[datetime] = None
    notes: Optional[str] = None


class ShipmentResponse(BaseModel):
    id: int
    tracking_number: str
    origin_address: str
    destination_address: str
    sender_name: str
    sender_phone: str
    recipient_name: str
    recipient_phone: str
    weight: float
    dimensions: Optional[str]
    status: ShipmentStatus
    estimated_delivery: datetime
    actual_delivery: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    notes: Optional[str]
    
    class Config:
        from_attributes = True
