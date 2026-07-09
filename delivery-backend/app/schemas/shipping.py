from pydantic import BaseModel, Field
from typing import Optional, Tuple
from enum import Enum


class DeliveryMethod(str, Enum):
    MOTORBIKE = "Motorbike"
    BICYCLE = "Bicycle"
    CAR = "Car"
    TRUCK = "Truck"


class ShippingQuoteRequest(BaseModel):
    """Request model for shipping quote calculation"""
    article_weight: float = Field(..., gt=0, description="Article weight in kg")
    delivery_address: str = Field(..., description="Delivery address")
    delivery_city: str = Field(..., description="Delivery city")
    stock_city: str = Field(..., description="Stock/origin city")
    distance: float = Field(..., gt=0, description="Distance in km")
    delivery_rating: float = Field(default=5.0, ge=0, le=5, description="Delivery rating 0-5")


class ShippingQuoteResponse(BaseModel):
    """Response model for shipping quote"""
    delivery_price: float = Field(..., description="Delivery price")
    delivery_time: Tuple[int, int] = Field(..., description="Delivery time range in days (min, max)")
    delivery_method: Optional[DeliveryMethod] = Field(None, description="Recommended delivery method")
    commission: float = Field(..., description="Commission at 25%")
    zone_allowed: bool = Field(..., description="Whether delivery zone is allowed")
    details: str = Field(..., description="Calculation details")
