from typing import List
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
    
    class Config:
        from_attributes = True
