"""
Admin schemas for administrative operations.

Includes schemas for:
- Creating merchants (admin-side creation)
- Managing users, merchants, products, orders
"""

from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.user import Location


class MerchantCreateByAdmin(BaseModel):
    """Schema for creating a merchant account by admin."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    first_name: str = Field(..., description="First name of merchant owner")
    last_name: Optional[str] = Field(None, description="Last name of merchant owner")
    shop_name: str = Field(..., description="Name of the merchant shop")
    description: Optional[str] = Field(None, description="Shop description")
    location: Optional[Location] = Field(None, description="Shop location coordinates")
    age: Optional[int] = Field(None, ge=18, le=120, description="Age of merchant owner")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "merchant@shop.com",
                "password": "SecurePass123!",
                "first_name": "Jean",
                "last_name": "Dupont",
                "shop_name": "Tech Store Dakar",
                "description": "Electronics and gadgets",
                "location": {"lat": 14.6937, "lng": -17.4441},
                "age": 35
            }
        }
