"""Schemas for merchant dashboard."""

from datetime import date
from pydantic import BaseModel, Field


class DashboardPeriod(BaseModel):
    """Schema for dashboard period."""
    from_date: date = Field(..., alias="from", description="Start date (YYYY-MM-DD)")
    to_date: date = Field(..., alias="to", description="End date (YYYY-MM-DD)")
    
    class Config:
        populate_by_name = True


class DashboardOverviewResponse(BaseModel):
    """Schema for merchant dashboard overview response."""
    total_sales: float = Field(
        ...,
        description="Total sales amount in XOF (completed orders)"
    )
    orders_count: int = Field(..., description="Total number of orders in period")
    orders_pending: int = Field(..., description="Number of pending orders")
    orders_shipped: int = Field(..., description="Number of shipped orders")
    orders_canceled: int = Field(..., description="Number of canceled orders")
    orders_refunded: int = Field(..., description="Number of refunded orders")
    refunds_total: float = Field(..., description="Total refunds amount in XOF")
    new_customers: int = Field(
        ...,
        description="Number of new customers (first order in period)"
    )
    products_in_stock: int = Field(..., description="Number of products in stock")
    low_stock: int = Field(
        ...,
        description="Number of products with low stock (stock <= 5)"
    )
    period: DashboardPeriod = Field(..., description="Period for the dashboard data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_sales": 4590000,
                "orders_count": 133,
                "orders_pending": 11,
                "orders_shipped": 72,
                "orders_canceled": 10,
                "orders_refunded": 5,
                "refunds_total": 86000,
                "new_customers": 23,
                "products_in_stock": 78,
                "low_stock": 5,
                "period": {
                    "from": "2026-01-01",
                    "to": "2026-01-31"
                }
            }
        }
