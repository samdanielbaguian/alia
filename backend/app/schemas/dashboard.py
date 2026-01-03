"""Schemas for merchant dashboard."""

from datetime import date, datetime
from typing import List, Optional
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


# New schemas for additional dashboard endpoints

class OrderStatsPoint(BaseModel):
    """Single data point for order stats time series."""
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    orders_count: int = Field(default=0, description="Number of orders on this date")
    total_amount: float = Field(default=0.0, description="Total sales amount for this date")
    orders_pending: int = Field(default=0, description="Pending orders")
    orders_confirmed: int = Field(default=0, description="Confirmed orders")
    orders_shipped: int = Field(default=0, description="Shipped orders")
    orders_delivered: int = Field(default=0, description="Delivered orders")
    orders_cancelled: int = Field(default=0, description="Cancelled orders")


class OrderStatsResponse(BaseModel):
    """Response schema for order statistics time series."""
    period: DashboardPeriod = Field(..., description="Period for the statistics")
    stats: List[OrderStatsPoint] = Field(..., description="Time series data points")
    summary: dict = Field(..., description="Summary statistics for the period")
    
    class Config:
        json_schema_extra = {
            "example": {
                "period": {
                    "from": "2026-01-01",
                    "to": "2026-01-31"
                },
                "stats": [
                    {
                        "date": "2026-01-01",
                        "orders_count": 5,
                        "total_amount": 125000,
                        "orders_pending": 1,
                        "orders_confirmed": 2,
                        "orders_shipped": 1,
                        "orders_delivered": 1,
                        "orders_cancelled": 0
                    }
                ],
                "summary": {
                    "total_orders": 133,
                    "total_sales": 4590000,
                    "avg_order_value": 34511.28
                }
            }
        }


class BestsellerProduct(BaseModel):
    """Single bestseller product."""
    product_id: str = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    quantity_sold: int = Field(..., description="Total quantity sold")
    revenue: float = Field(..., description="Total revenue from this product")
    orders_count: int = Field(..., description="Number of orders containing this product")
    image_url: Optional[str] = Field(None, description="Product image URL")


class BestsellerCategory(BaseModel):
    """Single bestseller category."""
    category: str = Field(..., description="Category name")
    quantity_sold: int = Field(..., description="Total quantity sold in category")
    revenue: float = Field(..., description="Total revenue from category")
    products_count: int = Field(..., description="Number of different products sold")


class BestsellersResponse(BaseModel):
    """Response schema for bestsellers."""
    period: DashboardPeriod = Field(..., description="Period for the bestsellers data")
    top_products: List[BestsellerProduct] = Field(..., description="Top selling products")
    top_categories: List[BestsellerCategory] = Field(..., description="Top selling categories")
    
    class Config:
        json_schema_extra = {
            "example": {
                "period": {
                    "from": "2026-01-01",
                    "to": "2026-01-31"
                },
                "top_products": [
                    {
                        "product_id": "prod123",
                        "title": "Smartphone XYZ",
                        "quantity_sold": 45,
                        "revenue": 2250000,
                        "orders_count": 42,
                        "image_url": "https://example.com/image.jpg"
                    }
                ],
                "top_categories": [
                    {
                        "category": "Electronics",
                        "quantity_sold": 120,
                        "revenue": 5400000,
                        "products_count": 15
                    }
                ]
            }
        }


class Alert(BaseModel):
    """Single alert for merchant."""
    type: str = Field(..., description="Alert type: pending_orders, low_stock, high_refunds, etc.")
    severity: str = Field(..., description="Alert severity: info, warning, critical")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    count: Optional[int] = Field(None, description="Count associated with alert")
    action_url: Optional[str] = Field(None, description="URL to resolve the alert")
    created_at: datetime = Field(..., description="When alert was generated")


class AlertsResponse(BaseModel):
    """Response schema for merchant alerts."""
    alerts: List[Alert] = Field(..., description="List of current alerts")
    total: int = Field(..., description="Total number of alerts")
    
    class Config:
        json_schema_extra = {
            "example": {
                "alerts": [
                    {
                        "type": "pending_orders",
                        "severity": "warning",
                        "title": "Pending Orders",
                        "message": "You have 8 orders pending confirmation",
                        "count": 8,
                        "action_url": "/api/merchants/me/orders?status=pending",
                        "created_at": "2026-01-03T10:30:00"
                    },
                    {
                        "type": "low_stock",
                        "severity": "critical",
                        "title": "Low Stock Alert",
                        "message": "3 products are running low on stock",
                        "count": 3,
                        "action_url": "/api/products?low_stock=true",
                        "created_at": "2026-01-03T10:30:00"
                    }
                ],
                "total": 2
            }
        }


class ActivityItem(BaseModel):
    """Single activity item."""
    type: str = Field(..., description="Activity type: order, refund, product_update, etc.")
    title: str = Field(..., description="Activity title")
    description: str = Field(..., description="Activity description")
    timestamp: datetime = Field(..., description="When activity occurred")
    reference_id: Optional[str] = Field(None, description="Reference ID (order_id, product_id, etc.)")
    amount: Optional[float] = Field(None, description="Amount if relevant")
    status: Optional[str] = Field(None, description="Status if relevant")


class RecentActivityResponse(BaseModel):
    """Response schema for recent merchant activity."""
    activities: List[ActivityItem] = Field(..., description="List of recent activities")
    total: int = Field(..., description="Total number of activities")
    
    class Config:
        json_schema_extra = {
            "example": {
                "activities": [
                    {
                        "type": "order",
                        "title": "New Order Received",
                        "description": "Order #123 from customer John",
                        "timestamp": "2026-01-03T09:45:00",
                        "reference_id": "order123",
                        "amount": 45000,
                        "status": "pending"
                    },
                    {
                        "type": "refund",
                        "title": "Refund Processed",
                        "description": "Refund for order #120",
                        "timestamp": "2026-01-03T08:30:00",
                        "reference_id": "ref_abc123",
                        "amount": 32000,
                        "status": "completed"
                    }
                ],
                "total": 2
            }
        }


class ExportOrdersRequest(BaseModel):
    """Request schema for exporting orders."""
    from_date: Optional[date] = Field(None, alias="from", description="Start date (YYYY-MM-DD)")
    to_date: Optional[date] = Field(None, alias="to", description="End date (YYYY-MM-DD)")
    status: Optional[str] = Field(None, description="Filter by order status")
    format: str = Field(default="csv", description="Export format (csv only for now)")
    
    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "from": "2026-01-01",
                "to": "2026-01-31",
                "status": "delivered",
                "format": "csv"
            }
        }


class ExportOrdersResponse(BaseModel):
    """Response schema for export orders."""
    filename: str = Field(..., description="Generated filename")
    content: str = Field(..., description="CSV content")
    rows_count: int = Field(..., description="Number of rows exported")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "orders_2026-01-01_2026-01-31.csv",
                "content": "order_id,date,customer,total,status\n...",
                "rows_count": 133
            }
        }
