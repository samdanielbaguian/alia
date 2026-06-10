from pydantic import BaseModel, Field


class SendPhoneCodeRequest(BaseModel):
    """Request to send verification code to phone."""
    phone_number: str = Field(..., description="Phone number in E.164 format (e.g., +12125551234)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+12125551234"
            }
        }


class VerifyPhoneCodeRequest(BaseModel):
    """Request to verify phone code."""
    phone_number: str = Field(..., description="Phone number in E.164 format")
    code: str = Field(..., description="6-digit verification code")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phone_number": "+12125551234",
                "code": "123456"
            }
        }
