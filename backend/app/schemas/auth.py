from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data schema."""
    email: Optional[str] = None
    user_id: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "strongpassword123"
            }
        }


class RegisterRequest(BaseModel):
    """Register request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    role: str  # "merchant" or "buyer"
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    birth_date: Optional[str] = None  # ISO format: YYYY-MM-DD
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    preferences: List[str] = []
    shop_name: Optional[str] = None  # Required for merchants
    description: Optional[str] = None  # Optional for merchants
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "merchant@example.com",
                "password": "strongpassword123",
                "role": "merchant",
                "first_name": "Jean",
                "last_name": "Dupont",
                "age": 30,
                "phone": "+221771234567",
                "address": "123 Rue de la Paix",
                "city": "Dakar",
                "country": "Senegal",
                "preferences": ["electronics"],
                "shop_name": "Tech Store",
                "description": "Leading electronics retailer"
            }
        }
