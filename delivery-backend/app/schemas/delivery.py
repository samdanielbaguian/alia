from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.delivery import DeliveryStatus


class DeliveryCreate(BaseModel):
    shipment_id: int
    driver_id: Optional[int] = None
    estimated_delivery_time: Optional[datetime] = None


class DeliveryUpdate(BaseModel):
    status: Optional[DeliveryStatus] = None
    driver_id: Optional[int] = None
    receiver_name: Optional[str] = None
    delivery_proof_image: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: int
    shipment_id: int
    driver_id: Optional[int]
    status: DeliveryStatus
    assigned_at: Optional[datetime]
    picked_up_at: Optional[datetime]
    delivered_at: Optional[datetime]
    failed_reason: Optional[str]
    delivery_proof_image: Optional[str]
    receiver_name: Optional[str]
    delivery_attempts: int
    estimated_delivery_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
