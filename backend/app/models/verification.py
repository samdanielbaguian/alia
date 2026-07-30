"""
Verification code model for phone number verification during authentication.

Stores temporary verification codes sent to users' phone numbers.
"""

from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field


class VerificationCode(BaseModel):
    """Model for phone verification code."""
    
    phone_number: str = Field(..., description="Phone number to verify (+225XXXXXXXXXX format)")
    code: str = Field(..., description="6-digit verification code")
    expires_at: datetime = Field(
        default_factory=lambda: datetime.utcnow() + timedelta(minutes=5),
        description="Expiration timestamp (default: +5 minutes)"
    )
    attempts: int = Field(default=0, ge=0, description="Number of failed verification attempts")
    max_attempts: int = Field(default=3, ge=1, description="Maximum allowed attempts before blocking")
    blocked_until: Optional[datetime] = Field(
        default=None,
        description="Timestamp until which further attempts are blocked"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+2250712345678",
                "code": "123456",
                "expires_at": "2024-01-15T10:30:00Z",
                "attempts": 0,
                "max_attempts": 3,
                "blocked_until": None
            }
        }
