from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.user import Location


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    title: str
    description: str
    price: float = Field(gt=0)
    images: List[str] = []
    stock: int = Field(ge=0)
    category: str
    delivery_days: int = Field(default=3, ge=1, le=30)
    age_restricted: bool = False
    location: Optional[Location] = None
    # Additional product attributes
    sku: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    material: Optional[str] = None


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    images: Optional[List[str]] = None
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    delivery_days: Optional[int] = Field(None, ge=1, le=30)
    age_restricted: Optional[bool] = None
    location: Optional[Location] = None
    # Additional product attributes
    sku: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    material: Optional[str] = None


class ProductImport(BaseModel):
    """Schema for importing a product from AliExpress/Alibaba."""
    source_product_id: str
    source_platform: str  # "AliExpress" or "Alibaba"
    margin_percentage: float = Field(default=20.0, ge=0, le=100)
    stock: int = Field(default=0, ge=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_product_id": "12345678",
                "source_platform": "AliExpress",
                "margin_percentage": 25.0,
                "stock": 100
            }
        }


class ProductResponse(BaseModel):
    """Schema for product response."""
    id: str
    title: str
    description: str
    price: float
    original_price: Optional[float] = None
    images: List[str]
    stock: int
    category: str
    merchant_id: str
    is_imported: bool
    source_platform: Optional[str] = None
    source_product_id: Optional[str] = None
    delivery_days: int
    age_restricted: bool
    location: Optional[Location] = None
    # Additional product attributes
    sku: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    material: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
