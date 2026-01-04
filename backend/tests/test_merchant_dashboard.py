"""
Tests for merchant dashboard overview endpoint.
"""
import pytest
from datetime import datetime, date
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, status
from app.api.routes.merchants import get_dashboard_overview
from app.schemas.dashboard import DashboardOverviewResponse, DashboardPeriod


class TestDashboardOverview:
    """Test merchant dashboard overview endpoint."""
    
    @pytest.mark.asyncio
    async def test_dashboard_overview_with_explicit_dates(self):
        """Test dashboard overview with explicit date range."""
        # Mock database
        mock_db = MagicMock()
        
        # Mock merchant
        mock_merchant = {
            "_id": "merchant_obj_id",
            "user_id": "merchant123",
            "shop_name": "Test Shop"
        }
        mock_db.merchants.find_one = AsyncMock(return_value=mock_merchant)
        
        # Mock orders aggregation result
        mock_orders_cursor = MagicMock()
        mock_orders_cursor.to_list = AsyncMock(return_value=[{
            "total_orders": 133,
            "orders_pending": 11,
            "orders_confirmed": 10,
            "orders_shipped": 72,
            "orders_delivered": 30,
            "orders_canceled": 10,
            "unique_customers": ["user1", "user2", "user3"]
        }])
        mock_db.orders.aggregate = MagicMock(return_value=mock_orders_cursor)
        
        # Mock payments aggregation result
        mock_payments_cursor = MagicMock()
        mock_payments_cursor.to_list = AsyncMock(return_value=[{
            "total_sales": 4590000.0
        }])
        mock_db.payments.aggregate = MagicMock(return_value=mock_payments_cursor)
        
        # Mock refunds aggregation result
        mock_refunds_cursor = MagicMock()
        mock_refunds_cursor.to_list = AsyncMock(return_value=[{
            "refunds_count": 5,
            "refunds_total": 86000.0
        }])
        mock_db.refunds.aggregate = MagicMock(return_value=mock_refunds_cursor)
        
        # Mock count for refunded orders
        mock_db.orders.count_documents = AsyncMock(return_value=5)
        
        # Mock first order check for new customers
        mock_db.orders.find_one = AsyncMock(return_value={
            "_id": "order1",
            "user_id": "user1",
            "created_at": datetime(2026, 1, 15)
        })
        
        # Mock products aggregation result
        mock_products_cursor = MagicMock()
        mock_products_cursor.to_list = AsyncMock(return_value=[{
            "products_in_stock": 78,
            "low_stock": 5
        }])
        mock_db.products.aggregate = MagicMock(return_value=mock_products_cursor)
        
        # Mock current user (merchant)
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        # Call the endpoint
        from_date = date(2026, 1, 1)
        to_date = date(2026, 1, 31)
        
        result = await get_dashboard_overview(
            from_date=from_date,
            to_date=to_date,
            current_user=mock_current_user,
            db=mock_db
        )
        
        # Assertions
        assert isinstance(result, DashboardOverviewResponse)
        assert result.total_sales == 4590000.0
        assert result.orders_count == 133
        assert result.orders_pending == 11
        assert result.orders_shipped == 72
        assert result.orders_canceled == 10
        assert result.orders_refunded == 5
        assert result.refunds_total == 86000.0
        assert result.new_customers == 3  # All 3 customers are new
        assert result.products_in_stock == 78
        assert result.low_stock == 5
        assert result.period.from_date == from_date
        assert result.period.to_date == to_date
    
    @pytest.mark.asyncio
    async def test_dashboard_overview_with_default_dates(self):
        """Test dashboard overview with default date range (current month)."""
        # Mock database
        mock_db = MagicMock()
        
        # Mock merchant
        mock_merchant = {
            "_id": "merchant_obj_id",
            "user_id": "merchant123",
            "shop_name": "Test Shop"
        }
        mock_db.merchants.find_one = AsyncMock(return_value=mock_merchant)
        
        # Mock aggregation results with minimal data
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[{
            "total_orders": 0,
            "orders_pending": 0,
            "orders_confirmed": 0,
            "orders_shipped": 0,
            "orders_delivered": 0,
            "orders_canceled": 0,
            "unique_customers": []
        }])
        mock_db.orders.aggregate = MagicMock(return_value=mock_cursor)
        
        mock_payments_cursor = MagicMock()
        mock_payments_cursor.to_list = AsyncMock(return_value=[])
        mock_db.payments.aggregate = MagicMock(return_value=mock_payments_cursor)
        
        mock_refunds_cursor = MagicMock()
        mock_refunds_cursor.to_list = AsyncMock(return_value=[])
        mock_db.refunds.aggregate = MagicMock(return_value=mock_refunds_cursor)
        
        mock_db.orders.count_documents = AsyncMock(return_value=0)
        
        mock_products_cursor = MagicMock()
        mock_products_cursor.to_list = AsyncMock(return_value=[{
            "products_in_stock": 10,
            "low_stock": 2
        }])
        mock_db.products.aggregate = MagicMock(return_value=mock_products_cursor)
        
        # Mock current user (merchant)
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        # Call the endpoint without dates (should use defaults)
        result = await get_dashboard_overview(
            from_date=None,
            to_date=None,
            current_user=mock_current_user,
            db=mock_db
        )
        
        # Assertions - verify defaults were used
        assert isinstance(result, DashboardOverviewResponse)
        assert result.total_sales == 0.0
        assert result.orders_count == 0
        assert result.products_in_stock == 10
        assert result.low_stock == 2
        # Verify period was set to current month
        now = datetime.utcnow()
        assert result.period.from_date.year == now.year
        assert result.period.from_date.month == now.month
        assert result.period.from_date.day == 1
    
    @pytest.mark.asyncio
    async def test_dashboard_overview_merchant_not_found(self):
        """Test dashboard overview when merchant profile not found."""
        # Mock database
        mock_db = MagicMock()
        mock_db.merchants.find_one = AsyncMock(return_value=None)
        
        # Mock current user (merchant)
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        # Call the endpoint and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_dashboard_overview(
                from_date=date(2026, 1, 1),
                to_date=date(2026, 1, 31),
                current_user=mock_current_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Merchant profile not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_dashboard_overview_empty_period(self):
        """Test dashboard overview with no data in period."""
        # Mock database
        mock_db = MagicMock()
        
        # Mock merchant
        mock_merchant = {
            "_id": "merchant_obj_id",
            "user_id": "merchant123",
            "shop_name": "Test Shop"
        }
        mock_db.merchants.find_one = AsyncMock(return_value=mock_merchant)
        
        # Mock empty aggregation results
        mock_orders_cursor = MagicMock()
        mock_orders_cursor.to_list = AsyncMock(return_value=[])
        mock_db.orders.aggregate = MagicMock(return_value=mock_orders_cursor)
        
        mock_payments_cursor = MagicMock()
        mock_payments_cursor.to_list = AsyncMock(return_value=[])
        mock_db.payments.aggregate = MagicMock(return_value=mock_payments_cursor)
        
        mock_refunds_cursor = MagicMock()
        mock_refunds_cursor.to_list = AsyncMock(return_value=[])
        mock_db.refunds.aggregate = MagicMock(return_value=mock_refunds_cursor)
        
        mock_db.orders.count_documents = AsyncMock(return_value=0)
        
        mock_products_cursor = MagicMock()
        mock_products_cursor.to_list = AsyncMock(return_value=[])
        mock_db.products.aggregate = MagicMock(return_value=mock_products_cursor)
        
        # Mock current user (merchant)
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        # Call the endpoint
        from_date = date(2025, 12, 1)
        to_date = date(2025, 12, 31)
        
        result = await get_dashboard_overview(
            from_date=from_date,
            to_date=to_date,
            current_user=mock_current_user,
            db=mock_db
        )
        
        # Assertions - all values should be 0
        assert isinstance(result, DashboardOverviewResponse)
        assert result.total_sales == 0.0
        assert result.orders_count == 0
        assert result.orders_pending == 0
        assert result.orders_shipped == 0
        assert result.orders_canceled == 0
        assert result.orders_refunded == 0
        assert result.refunds_total == 0.0
        assert result.new_customers == 0
        assert result.products_in_stock == 0
        assert result.low_stock == 0
