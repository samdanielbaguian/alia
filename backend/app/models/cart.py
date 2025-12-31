from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class CartItem(BaseModel):
    """Item in a shopping cart."""
    product_id: str
    quantity: int = Field(gt=0)
    price_at_add: float = Field(gt=0)
    added_at: datetime = Field(default_factory=datetime.utcnow)


class Cart(BaseModel):
    """Shopping cart model for MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    items: List[CartItem] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None  # For guest carts
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "items": [
                    {
                        "product_id": "prod123",
                        "quantity": 2,
                        "price_at_add": 299.99,
                        "added_at": "2024-01-01T00:00:00"
                    }
                ],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
