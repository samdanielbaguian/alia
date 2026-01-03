"""
Tests for new merchant dashboard endpoints.
"""
import pytest
from datetime import datetime, date, timedelta
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException, status
from bson import ObjectId

from app.api.routes.merchants import (
    get_orders_stats,
    get_bestsellers,
    get_alerts,
    get_recent_activity,
    export_orders
)
from app.schemas.dashboard import (
    OrderStatsResponse,
    BestsellersResponse,
    AlertsResponse,
    RecentActivityResponse,
    ExportOrdersResponse,
    ExportOrdersRequest
)


class TestOrdersStats:
    """Test orders stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_orders_stats_with_explicit_dates(self):
        """Test orders stats with explicit date range."""
        # Mock database
        mock_db = MagicMock()
        
        # Mock merchant
        mock_merchant = {
            "_id": "merchant_obj_id",
            "user_id": "merchant123",
            "shop_name": "Test Shop"
        }
        mock_db.merchants.find_one = AsyncMock(return_value=mock_merchant)
        
        # Mock aggregation result
        mock_cursor = MagicMock()
        mock_cursor.to_list = AsyncMock(return_value=[
            {
                "_id": "2026-01-01",
                "orders_count": 5,
                "total_amount": 125000.0,
                "orders_pending": 1,
                "orders_confirmed": 2,
                "orders_shipped": 1,
                "orders_delivered": 1,
                "orders_cancelled": 0
            },
            {
                "_id": "2026-01-02",
                "orders_count": 8,
                "total_amount": 200000.0,
                "orders_pending": 2,
                "orders_confirmed": 3,
                "orders_shipped": 2,
                "orders_delivered": 1,
                "orders_cancelled": 0
            }
        ])
        mock_db.orders.aggregate = MagicMock(return_value=mock_cursor)
        
        # Mock current user
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        # Call the endpoint
        from_date = date(2026, 1, 1)
        to_date = date(2026, 1, 31)
        
        result = await get_orders_stats(
            from_date=from_date,
            to_date=to_date,
            current_user=mock_current_user,
            db=mock_db
        )
        
        # Assertions
        assert isinstance(result, OrderStatsResponse)
        assert result.period.from_date == from_date
        assert result.period.to_date == to_date
        assert len(result.stats) == 2
        assert result.stats[0].date == "2026-01-01"
        assert result.stats[0].orders_count == 5
        assert result.stats[0].total_amount == 125000.0
        assert result.summary["total_orders"] == 13
        assert result.summary["total_sales"] == 325000.0
    
    @pytest.mark.asyncio
    async def test_orders_stats_merchant_not_found(self):
        """Test orders stats when merchant not found."""
        mock_db = MagicMock()
        mock_db.merchants.find_one = AsyncMock(return_value=None)
        
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await get_orders_stats(
                from_date=date(2026, 1, 1),
                to_date=date(2026, 1, 31),
                current_user=mock_current_user,
                db=mock_db
            )
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestBestsellers:
    """Test bestsellers endpoint."""
    
    @pytest.mark.asyncio
    async def test_bestsellers_with_products(self):
        """Test bestsellers with product data."""
        # Mock database
        mock_db = MagicMock()
        
        # Mock merchant
        mock_merchant = {
            "_id": "merchant_obj_id",
            "user_id": "merchant123",
            "shop_name": "Test Shop"
        }
        mock_db.merchants.find_one = AsyncMock(return_value=mock_merchant)
        
        # Mock orders
        mock_orders_cursor = MagicMock()
        mock_orders_cursor.to_list = AsyncMock(return_value=[
            {
                "_id": ObjectId(),
                "merchant_id": "merchant123",
                "products": [
                    {
                        "product_id": "prod1",
                        "title": "Product 1",
                        "quantity": 5,
                        "price": 10000.0
                    },
                    {
                        "product_id": "prod2",
                        "title": "Product 2",
                        "quantity": 3,
                        "price": 15000.0
                    }
                ],
                "created_at": datetime(2026, 1, 15)
            },
            {
                "_id": ObjectId(),
                "merchant_id": "merchant123",
                "products": [
                    {
                        "product_id": "prod1",
                        "title": "Product 1",
                        "quantity": 2,
                        "price": 10000.0
                    }
                ],
                "created_at": datetime(2026, 1, 16)
            }
        ])
        mock_db.orders.find = MagicMock(return_value=mock_orders_cursor)
        
        # Mock batch product lookup
        mock_products_cursor = MagicMock()
        mock_products_cursor.to_list = AsyncMock(return_value=[])  # No products found (edge case test)
        mock_db.products.find = MagicMock(return_value=mock_products_cursor)
        
        # Mock current user
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        # Call the endpoint
        result = await get_bestsellers(
            from_date=date(2026, 1, 1),
            to_date=date(2026, 1, 31),
            limit=10,
            current_user=mock_current_user,
            db=mock_db
        )
        
        # Assertions
        assert isinstance(result, BestsellersResponse)
        assert len(result.top_products) > 0
        assert result.top_products[0].quantity_sold == 7  # 5 + 2
        assert len(result.top_categories) > 0


class TestAlerts:
    """Test alerts endpoint."""
    
    @pytest.mark.asyncio
    async def test_alerts_with_pending_orders(self):
        """Test alerts with pending orders."""
        # Mock database
        mock_db = MagicMock()
        
        # Mock merchant
        mock_merchant = {
            "_id": "merchant_obj_id",
            "user_id": "merchant123",
            "shop_name": "Test Shop"
        }
        mock_db.merchants.find_one = AsyncMock(return_value=mock_merchant)
        
        # Mock counts
        mock_db.orders.count_documents = AsyncMock(return_value=8)
        mock_db.products.count_documents = AsyncMock(side_effect=[3, 2])  # low_stock, out_of_stock
        mock_db.refunds.count_documents = AsyncMock(return_value=2)
        
        # Mock current user
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        # Call the endpoint
        result = await get_alerts(
            current_user=mock_current_user,
            db=mock_db
        )
        
        # Assertions
        assert isinstance(result, AlertsResponse)
        assert result.total > 0
        assert any(alert.type == "pending_orders" for alert in result.alerts)
        pending_alert = next(a for a in result.alerts if a.type == "pending_orders")
        assert pending_alert.count == 8
        assert pending_alert.severity == "warning"
    
    @pytest.mark.asyncio
    async def test_alerts_critical_pending_orders(self):
        """Test alerts with critical number of pending orders."""
        mock_db = MagicMock()
        
        mock_merchant = {
            "_id": "merchant_obj_id",
            "user_id": "merchant123",
            "shop_name": "Test Shop"
        }
        mock_db.merchants.find_one = AsyncMock(return_value=mock_merchant)
        
        # Mock counts - more than 10 pending orders
        mock_db.orders.count_documents = AsyncMock(return_value=15)
        mock_db.products.count_documents = AsyncMock(side_effect=[0, 0])
        mock_db.refunds.count_documents = AsyncMock(return_value=0)
        
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        result = await get_alerts(
            current_user=mock_current_user,
            db=mock_db
        )
        
        pending_alert = next(a for a in result.alerts if a.type == "pending_orders")
        assert pending_alert.severity == "critical"


class TestRecentActivity:
    """Test recent activity endpoint."""
    
    @pytest.mark.asyncio
    async def test_recent_activity_with_orders(self):
        """Test recent activity with orders."""
        # Mock database
        mock_db = MagicMock()
        
        # Mock merchant
        mock_merchant = {
            "_id": "merchant_obj_id",
            "user_id": "merchant123",
            "shop_name": "Test Shop"
        }
        mock_db.merchants.find_one = AsyncMock(return_value=mock_merchant)
        
        # Mock orders cursor
        mock_orders_cursor = MagicMock()
        mock_orders_cursor.sort = MagicMock(return_value=mock_orders_cursor)
        mock_orders_cursor.limit = MagicMock(return_value=mock_orders_cursor)
        mock_orders_cursor.to_list = AsyncMock(return_value=[
            {
                "_id": ObjectId(),
                "user_id": "user123",
                "total_amount": 45000.0,
                "status": "pending",
                "created_at": datetime(2026, 1, 3, 9, 45)
            }
        ])
        mock_db.orders.find = MagicMock(return_value=mock_orders_cursor)
        
        # Mock batch user lookup
        mock_users_cursor = MagicMock()
        mock_users_cursor.to_list = AsyncMock(return_value=[
            {
                "_id": ObjectId(),
                "username": "John Doe"
            }
        ])
        mock_db.users.find = MagicMock(return_value=mock_users_cursor)
        
        # Mock refunds cursor (empty)
        mock_refunds_cursor = MagicMock()
        mock_refunds_cursor.sort = MagicMock(return_value=mock_refunds_cursor)
        mock_refunds_cursor.limit = MagicMock(return_value=mock_refunds_cursor)
        mock_refunds_cursor.to_list = AsyncMock(return_value=[])
        mock_db.refunds.find = MagicMock(return_value=mock_refunds_cursor)
        
        # Mock current user
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        # Call the endpoint
        result = await get_recent_activity(
            limit=20,
            activity_type=None,
            current_user=mock_current_user,
            db=mock_db
        )
        
        # Assertions
        assert isinstance(result, RecentActivityResponse)
        assert result.total > 0
        assert result.activities[0].type == "order"
        assert result.activities[0].amount == 45000.0


class TestExportOrders:
    """Test export orders endpoint."""
    
    @pytest.mark.asyncio
    async def test_export_orders_csv(self):
        """Test export orders to CSV."""
        # Mock database
        mock_db = MagicMock()
        
        # Mock merchant
        mock_merchant = {
            "_id": "merchant_obj_id",
            "user_id": "merchant123",
            "shop_name": "Test Shop"
        }
        mock_db.merchants.find_one = AsyncMock(return_value=mock_merchant)
        
        # Mock orders cursor
        mock_orders_cursor = MagicMock()
        mock_orders_cursor.sort = MagicMock(return_value=mock_orders_cursor)
        mock_orders_cursor.to_list = AsyncMock(return_value=[
            {
                "_id": ObjectId(),
                "user_id": "user123",
                "total_amount": 45000.0,
                "status": "delivered",
                "payment_method": "orange_money",
                "products": [{"product_id": "p1", "quantity": 2}],
                "created_at": datetime(2026, 1, 15, 10, 30)
            },
            {
                "_id": ObjectId(),
                "user_id": "user456",
                "total_amount": 32000.0,
                "status": "delivered",
                "payment_method": "wave",
                "products": [{"product_id": "p2", "quantity": 1}],
                "created_at": datetime(2026, 1, 20, 14, 15)
            }
        ])
        mock_db.orders.find = MagicMock(return_value=mock_orders_cursor)
        
        # Mock current user
        mock_current_user = {
            "_id": "merchant123",
            "role": "merchant"
        }
        
        # Create request
        request = ExportOrdersRequest(
            **{
                "from": date(2026, 1, 1),
                "to": date(2026, 1, 31),
                "status": "delivered",
                "format": "csv"
            }
        )
        
        # Call the endpoint
        result = await export_orders(
            request=request,
            current_user=mock_current_user,
            db=mock_db
        )
        
        # Assertions
        assert isinstance(result, ExportOrdersResponse)
        assert result.rows_count == 2
        assert "Order ID,Date,Customer ID,Total Amount,Status,Payment Method,Products Count" in result.content
        assert "45000" in result.content
        assert "32000" in result.content
        assert result.filename.startswith("orders_")
        assert result.filename.endswith(".csv")
