from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.user import Location


class UserPreferences(BaseModel):
    """User preferences schema."""
    preferences: List[str]


class UserCreate(BaseModel):
    """Schema for creating a user."""
    email: EmailStr
    password: str
    role: str
    age: Optional[int] = None
    preferences: List[str] = []
    location: Optional[Location] = None


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    age: Optional[int] = None
    preferences: Optional[List[str]] = None
    location: Optional[Location] = None
    good_rate: Optional[float] = None


class UserResponse(BaseModel):
    """Schema for user response."""
    id: str
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    age: Optional[int] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    preferences: List[str] = []
    good_rate: float
    location: Optional[Location] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "user123",
                "email": "user@example.com",
                "first_name": "Jean",
                "last_name": "Dupont",
                "role": "buyer",
                "age": 25,
                "phone": "+221771234567",
                "address": "123 Rue de la Paix",
                "city": "Dakar",
                "country": "Senegal",
                "preferences": ["electronics", "fashion"],
                "good_rate": 85.5,
                "location": {"lat": 14.6937, "lng": -17.4441},
                "created_at": "2024-01-01T00:00:00"
            }
        }
