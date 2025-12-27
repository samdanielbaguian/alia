from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    """User role enumeration."""
    MERCHANT = "merchant"
    BUYER = "buyer"


class Location(BaseModel):
    """Geographic location model."""
    lat: float
    lng: float


class User(BaseModel):
    """User model for MongoDB."""
    id: Optional[str] = Field(None, alias="_id")
    email: EmailStr
    password_hash: str
    role: UserRole
    age: Optional[int] = None
    preferences: List[str] = Field(default_factory=list)
    good_rate: float = Field(default=50.0, ge=0, le=100)  # Rating from 0-100
    location: Optional[Location] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "role": "buyer",
                "age": 25,
                "preferences": ["electronics", "fashion"],
                "good_rate": 85.5,
                "location": {"lat": 14.6937, "lng": -17.4441}
            }
        }
