from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class CartShareItem(BaseModel):
    """Item in a shared cart snapshot."""
    product_id: str
    quantity: int
    price_at_share: float
    title: str


class CartShare(BaseModel):
    """Model for shareable cart links."""
    id: Optional[str] = Field(None, alias="_id")
    share_code: str = Field(min_length=8, max_length=8)
    cart_snapshot: List[CartShareItem] = Field(default_factory=list)
    user_id: str
    expires_at: Optional[datetime] = None
    view_count: int = Field(default=0)
    import_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "share_code": "ABC12XYZ",
                "cart_snapshot": [
                    {
                        "product_id": "prod123",
                        "quantity": 2,
                        "price_at_share": 299.99,
                        "title": "Smartphone XYZ"
                    }
                ],
                "user_id": "user123",
                "expires_at": "2024-01-08T00:00:00",
                "view_count": 0,
                "import_count": 0
            }
        }


class ProductShare(BaseModel):
    """Model for product share tracking."""
    id: Optional[str] = Field(None, alias="_id")
    product_id: str
    share_code: str = Field(min_length=8, max_length=8)
    user_id: str
    view_count: int = Field(default=0)
    conversion_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "product_id": "prod123",
                "share_code": "XYZ789AB",
                "user_id": "user123",
                "view_count": 0,
                "conversion_count": 0
            }
        }


class MerchantShare(BaseModel):
    """Model for merchant shop share tracking."""
    id: Optional[str] = Field(None, alias="_id")
    merchant_id: str
    share_code: str = Field(min_length=8, max_length=8)
    user_id: str
    view_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "merchant_id": "merchant123",
                "share_code": "MER456XY",
                "user_id": "user123",
                "view_count": 0
            }
        }
