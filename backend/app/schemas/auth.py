from typing import List, Optional
from pydantic import BaseModel, EmailStr


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
    password: str
    role: str  # "merchant" or "buyer"
    age: Optional[int] = None
    preferences: List[str] = []
    shop_name: Optional[str] = None  # Required for merchants
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "merchant@example.com",
                "password": "strongpassword123",
                "role": "merchant",
                "age": 30,
                "preferences": ["electronics"],
                "shop_name": "Tech Store"
            }
        }
