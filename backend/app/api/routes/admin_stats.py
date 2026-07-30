"""
Admin routes for global statistics.

Provides administrative endpoints for:
- Total users, merchants, products, orders
- Revenue, fees, payouts
"""

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.api.deps import get_db, get_current_admin

router = APIRouter()


@router.get("/stats", tags=["Admin - Stats"])
async def get_global_stats(
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """Get global platform statistics."""
    # Count users
    total_users = await db.users.count_documents({})
    
    # Count merchants (users with role "merchant")
    total_merchants = await db.users.count_documents({"role": "merchant"})
    
    # Count products
    total_products = await db.products.count_documents({})
    
    # Count orders
    total_orders = await db.orders.count_documents({})
    
    # Get order status breakdown
    status_stats = {}
    for status in ["pending", "confirmed", "shipped", "delivered", "cancelled"]:
        status_stats[status] = await db.orders.count_documents({"status": status})
    
    # Calculate revenue
    pipeline = [
        {"$match": {"status": {"$in": ["delivered", "confirmed"]}}},
        {"$group": {
            "_id": None,
            "total_gross_revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
            "total_platform_fees": {"$sum": {"$ifNull": ["$platform_fee", 0]}},
            "total_merchant_payout": {"$sum": {"$ifNull": ["$merchant_payout", 0]}},
            "orders_count": {"$sum": 1},
        }}
    ]
    result = await db.orders.aggregate(pipeline).to_list(length=1)
    fees_summary = result[0] if result else {
        "total_gross_revenue": 0.0,
        "total_platform_fees": 0.0,
        "total_merchant_payout": 0.0,
        "orders_count": 0
    }
    
    # Calculate average commission
    gross = fees_summary.get("total_gross_revenue", 0) or 0
    fees = fees_summary.get("total_platform_fees", 0) or 0
    avg_fee = (fees / gross) * 100 if gross > 0 else 0
    
    return {
        "total_users": total_users,
        "total_merchants": total_merchants,
        "total_products": total_products,
        "total_orders": total_orders,
        "total_gross_revenue": fees_summary.get("total_gross_revenue", 0.0),
        "total_platform_fees": fees_summary.get("total_platform_fees", 0.0),
        "total_merchant_payout": fees_summary.get("total_merchant_payout", 0.0),
        "avg_fee_percentage": avg_fee,
        "orders_by_status": status_stats,
    }