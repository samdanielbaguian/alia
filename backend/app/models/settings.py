from pydantic import BaseModel, Field
from typing import Optional

class SettingsModel(BaseModel):
    maintenance_mode: bool = Field(default=False)
    platform_fee_percentage: float = Field(default=2.5, ge=0)
    orange_gateway_fee_percent: Optional[float] = Field(default=None)
    mtn_gateway_fee_percent: Optional[float] = Field(default=None)
    moov_gateway_fee_percent: Optional[float] = Field(default=None)
    min_order_amount: Optional[int] = Field(default=1000)
    max_order_amount: Optional[int] = Field(default=500000)
    free_shipping_threshold: Optional[int] = Field(default=50000)
    enable_notifications: Optional[bool] = Field(default=True)
    enable_two_factor: Optional[bool] = Field(default=True)

    class Config:
        schema_extra = {
            "example": {
                "maintenance_mode": False,
                "platform_fee_percentage": 2.5,
                "orange_gateway_fee_percent": 1.5,
                "mtn_gateway_fee_percent": 1.8,
                "moov_gateway_fee_percent": 2.0,
                "min_order_amount": 1000,
                "max_order_amount": 9999999999,
                "free_shipping_threshold": 250000,
                "enable_notifications": True,
                "enable_two_factor": True
            }
        }