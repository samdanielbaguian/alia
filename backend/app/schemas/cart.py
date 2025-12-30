from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AddToCartRequest(BaseModel):
    """Schema for adding a product to cart."""
    product_id: str
    quantity: int = Field(gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod123",
                "quantity": 2
            }
        }


class UpdateCartItemRequest(BaseModel):
    """Schema for updating cart item quantity."""
    quantity: int = Field(gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "quantity": 3
            }
        }


class CartItemResponse(BaseModel):
    """Schema for cart item response."""
    product_id: str
    quantity: int
    price_at_add: float
    current_price: float
    title: str
    image: Optional[str] = None
    stock: int
    subtotal: float
    price_changed: bool = False
    stock_warning: bool = False
    
    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    """Schema for cart response."""
    items: List[CartItemResponse]
    total_amount: float
    total_items: int
    
    class Config:
        from_attributes = True


class CreateShareRequest(BaseModel):
    """Schema for creating a shareable cart link."""
    expires_in_hours: Optional[int] = Field(default=24, ge=1, le=720)  # Max 30 days
    
    class Config:
        json_schema_extra = {
            "example": {
                "expires_in_hours": 24
            }
        }


class ShareResponse(BaseModel):
    """Schema for share response."""
    share_link: str
    share_code: str
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SharedCartItemResponse(BaseModel):
    """Schema for shared cart item."""
    product_id: str
    quantity: int
    price: float
    title: str
    subtotal: float


class SharedCartResponse(BaseModel):
    """Schema for shared cart view."""
    items: List[SharedCartItemResponse]
    total_amount: float
    total_items: int
    shared_by: str  # Anonymized username
    expires_at: Optional[datetime] = None
    is_expired: bool = False
    
    class Config:
        from_attributes = True


class OrderFromCartRequest(BaseModel):
    """Schema for creating order from cart."""
    payment_method: str  # "orange_money", "mtn_money", "moov_money"
    
    class Config:
        json_schema_extra = {
            "example": {
                "payment_method": "orange_money"
            }
        }
