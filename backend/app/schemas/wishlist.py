from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class AddToWishlistRequest(BaseModel):
    """Request to add a product to wishlist."""
    product_id: str = Field(..., description="Product ID to add to wishlist")
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "507f1f77bcf86cd799439011"
            }
        }


class WishlistItemResponse(BaseModel):
    """Response model for a single wishlist item with product details."""
    product_id: str
    title: str
    price: float
    images: List[str] = Field(default_factory=list)
    stock: int
    merchant_id: str
    added_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "507f1f77bcf86cd799439011",
                "title": "Wireless Headphones",
                "price": 59.99,
                "images": ["https://example.com/image1.jpg"],
                "stock": 10,
                "merchant_id": "507f1f77bcf86cd799439012",
                "added_at": "2024-01-15T10:30:00"
            }
        }


class WishlistResponse(BaseModel):
    """Response model for user's wishlist."""
    items: List[WishlistItemResponse] = Field(default_factory=list)
    total_items: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total_items": 0
            }
        }
