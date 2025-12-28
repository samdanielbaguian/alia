from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.models.user import Location


class Product(BaseModel):
    """Product model for MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    title: str
    description: str
    price: float = Field(gt=0)
    original_price: Optional[float] = None  # For imported products with margin
    images: List[str] = Field(default_factory=list)
    stock: int = Field(ge=0)
    category: str
    merchant_id: str
    is_imported: bool = False
    source_platform: Optional[str] = None  # "AliExpress" or "Alibaba"
    source_product_id: Optional[str] = None
    delivery_days: int = Field(default=7, ge=1, le=30)  # 1-3 local, 7-21 imported
    age_restricted: bool = False
    location: Optional[Location] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "title": "Smartphone XYZ",
                "description": "High-end smartphone with great features",
                "price": 299.99,
                "original_price": 250.00,
                "images": ["https://example.com/image1.jpg"],
                "stock": 50,
                "category": "electronics",
                "merchant_id": "merchant123",
                "is_imported": True,
                "source_platform": "AliExpress",
                "delivery_days": 14,
                "age_restricted": False
            }
        }
