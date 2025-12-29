from typing import Optional
from pydantic import BaseModel


class ProductShareResponse(BaseModel):
    """Schema for product share response."""
    share_link: str
    share_code: str
    whatsapp_link: str
    qr_code: str  # Base64 encoded PNG
    
    class Config:
        from_attributes = True


class ProductShareStatsResponse(BaseModel):
    """Schema for product share statistics."""
    total_shares: int
    views_from_shares: int
    conversions_from_shares: int
    conversion_rate: str
    
    class Config:
        from_attributes = True


class MerchantShareResponse(BaseModel):
    """Schema for merchant share response."""
    share_link: str
    share_code: str
    whatsapp_link: str
    
    class Config:
        from_attributes = True
