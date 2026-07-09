from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.driver import DriverStatus


class DriverCreate(BaseModel):
    name: str
    phone: str
    email: str
    license_number: str
    vehicle_number: str
    vehicle_type: str


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[DriverStatus] = None
    available_for_delivery: Optional[bool] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None


class DriverResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: str
    license_number: str
    vehicle_number: str
    vehicle_type: str
    status: DriverStatus
    current_latitude: Optional[float]
    current_longitude: Optional[float]
    available_for_delivery: bool
    total_deliveries: int
    rating: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
