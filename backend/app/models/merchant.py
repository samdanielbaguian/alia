from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.user import Location


class Merchant(BaseModel):
    """Merchant model for MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    shop_name: str
    description: Optional[str] = None
    location: Optional[Location] = None
    total_sales: float = Field(default=0.0, ge=0)
    rating: float = Field(default=50.0, ge=0, le=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "shop_name": "Tech Store",
                "description": "Best electronics in town",
                "location": {"lat": 14.6937, "lng": -17.4441},
                "total_sales": 15000.0,
                "rating": 92.5
            }
        }
