"""
Tests for sales heatmap endpoint.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.api.routes.merchants import get_sales_heatmap
from app.schemas.order import SalesHeatmapResponse, HeatmapZone


@pytest.mark.asyncio
async def test_sales_heatmap_no_orders():
    """Test heatmap with no orders."""
    # Mock dependencies
    current_user = {"_id": "merchant_123", "role": "merchant"}
    
    db = MagicMock()
    db.orders.find.return_value.to_list = AsyncMock(return_value=[])
    
    # Call the endpoint
    result = await get_sales_heatmap(
        from_date=None,
        to_date=None,
        current_user=current_user,
        db=db
    )
    
    # Verify response
    assert isinstance(result, SalesHeatmapResponse)
    assert result.heatmap == []
    assert result.top_zone is None


@pytest.mark.asyncio
async def test_sales_heatmap_with_orders():
    """Test heatmap with orders having location data."""
    # Mock dependencies
    current_user = {"_id": "merchant_123", "role": "merchant"}
    
    # Mock orders
    mock_orders = [
        {
            "_id": "order_1",
            "user_id": "user_1",
            "merchant_id": "merchant_123",
            "total_amount": 100000.0,
            "created_at": datetime(2024, 1, 15)
        },
        {
            "_id": "order_2",
            "user_id": "user_1",
            "merchant_id": "merchant_123",
            "total_amount": 50000.0,
            "created_at": datetime(2024, 1, 20)
        },
        {
            "_id": "order_3",
            "user_id": "user_2",
            "merchant_id": "merchant_123",
            "total_amount": 75000.0,
            "created_at": datetime(2024, 1, 25)
        }
    ]
    
    # Mock users with locations
    mock_users = {
        "user_1": {
            "_id": "user_1",
            "location": {"lat": 5.3556, "lng": -3.9907}  # Abidjan
        },
        "user_2": {
            "_id": "user_2",
            "location": {"lat": 7.6833, "lng": -5.0167}  # Bouaké
        }
    }
    
    db = MagicMock()
    db.orders.find.return_value.to_list = AsyncMock(return_value=mock_orders)
    db.users.find_one = AsyncMock(side_effect=lambda query: mock_users.get(query["_id"]))
    
    # Call the endpoint
    result = await get_sales_heatmap(
        from_date=None,
        to_date=None,
        current_user=current_user,
        db=db
    )
    
    # Verify response
    assert isinstance(result, SalesHeatmapResponse)
    assert len(result.heatmap) == 2
    
    # First zone should be Abidjan (2 orders)
    assert result.heatmap[0].orders == 2
    assert result.heatmap[0].total_sales == 150000.0
    assert result.heatmap[0].lat == 5.3556
    assert result.heatmap[0].lng == -3.9907
    
    # Second zone should be Bouaké (1 order)
    assert result.heatmap[1].orders == 1
    assert result.heatmap[1].total_sales == 75000.0
    assert result.heatmap[1].lat == 7.6833
    assert result.heatmap[1].lng == -5.0167
    
    # Top zone should be Abidjan
    assert result.top_zone is not None
    assert result.top_zone.orders == 2
    assert result.top_zone.lat == 5.3556


@pytest.mark.asyncio
async def test_sales_heatmap_skip_orders_without_location():
    """Test that orders without location data are skipped."""
    current_user = {"_id": "merchant_123", "role": "merchant"}
    
    # Mock orders
    mock_orders = [
        {
            "_id": "order_1",
            "user_id": "user_1",
            "merchant_id": "merchant_123",
            "total_amount": 100000.0,
            "created_at": datetime(2024, 1, 15)
        },
        {
            "_id": "order_2",
            "user_id": "user_2",
            "merchant_id": "merchant_123",
            "total_amount": 50000.0,
            "created_at": datetime(2024, 1, 20)
        }
    ]
    
    # Mock users - user_1 has location, user_2 doesn't
    mock_users = {
        "user_1": {
            "_id": "user_1",
            "location": {"lat": 5.3556, "lng": -3.9907}
        },
        "user_2": {
            "_id": "user_2"
            # No location
        }
    }
    
    db = MagicMock()
    db.orders.find.return_value.to_list = AsyncMock(return_value=mock_orders)
    db.users.find_one = AsyncMock(side_effect=lambda query: mock_users.get(query["_id"]))
    
    # Call the endpoint
    result = await get_sales_heatmap(
        from_date=None,
        to_date=None,
        current_user=current_user,
        db=db
    )
    
    # Verify response - only one zone (user_1)
    assert len(result.heatmap) == 1
    assert result.heatmap[0].orders == 1
    assert result.heatmap[0].lat == 5.3556


@pytest.mark.asyncio
async def test_sales_heatmap_with_date_filter():
    """Test heatmap with date filtering."""
    current_user = {"_id": "merchant_123", "role": "merchant"}
    
    db = MagicMock()
    db.orders.find.return_value.to_list = AsyncMock(return_value=[])
    
    # Call with date filters
    await get_sales_heatmap(
        from_date="2024-01-01T00:00:00Z",
        to_date="2024-01-31T23:59:59Z",
        current_user=current_user,
        db=db
    )
    
    # Verify the filter query includes dates
    call_args = db.orders.find.call_args[0][0]
    assert "created_at" in call_args
    assert "$gte" in call_args["created_at"]
    assert "$lte" in call_args["created_at"]


@pytest.mark.asyncio
async def test_sales_heatmap_invalid_date_format():
    """Test that invalid date format raises error."""
    current_user = {"_id": "merchant_123", "role": "merchant"}
    db = MagicMock()
    
    # Test with invalid from date
    with pytest.raises(HTTPException) as exc_info:
        await get_sales_heatmap(
            from_date="invalid-date",
            to_date=None,
            current_user=current_user,
            db=db
        )
    assert exc_info.value.status_code == 400
    assert "Invalid 'from' date format" in exc_info.value.detail
    
    # Test with invalid to date
    with pytest.raises(HTTPException) as exc_info:
        await get_sales_heatmap(
            from_date=None,
            to_date="invalid-date",
            current_user=current_user,
            db=db
        )
    assert exc_info.value.status_code == 400
    assert "Invalid 'to' date format" in exc_info.value.detail


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
