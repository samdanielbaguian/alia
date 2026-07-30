"""
Admin routes for order management.

Provides administrative endpoints for:
- Listing all orders with pagination and filtering
- Viewing order details
- Forcing status changes (bypasses business rules)
- Deleting orders
- Viewing global statistics
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.deps import get_db, get_current_admin
from app.schemas.order import OrderResponse, StatusHistoryResponse

router = APIRouter()


@router.get("", tags=["Admin - Orders"])
async def list_all_orders(
    status_filter: Optional[str] = Query(None, description="Filter by status: pending, confirmed, shipped, delivered, cancelled"),
    search: Optional[str] = Query(None, description="Search by order ID"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all orders with optional filtering and pagination.
    
    **Admin only**
    
    Args:
        status_filter: Filter orders by status
        search: Search by order ID
        limit: Maximum number of results (1-100)
        skip: Number of results to skip (for pagination)
    
    Returns:
        List of orders with total count
    """
    query = {}
    
    # Add status filter
    if status_filter:
        query["status"] = status_filter
    
    # Add search filter
    if search:
        try:
            query["_id"] = ObjectId(search)
        except Exception:
            query["_id"] = search
    
    # Count total
    total = await db.orders.count_documents(query)
    
    # Get orders
    orders = await db.orders.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    return {
        "orders": [
            {
                "id": str(order["_id"]),
                "buyer_id": order.get("buyer_id"),
                "merchant_id": order.get("merchant_id"),
                "total_amount": order.get("total_amount", 0),
                "status": order.get("status", "pending"),
                "created_at": order.get("created_at"),
                "updated_at": order.get("updated_at"),
                "items_count": len(order.get("items", []))
            }
            for order in orders
        ],
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.get("/stats", tags=["Admin - Orders"])
async def get_order_statistics(
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get global order statistics.
    
    **Admin only**
    
    Returns:
        Order statistics including totals, status breakdown, and revenue
    """
    # Get total orders
    total_orders = await db.orders.count_documents({})
    
    # Get orders by status
    status_stats = {}
    for status in ["pending", "confirmed", "shipped", "delivered", "cancelled"]:
        count = await db.orders.count_documents({"status": status})
        status_stats[status] = count
    
    # Get revenue stats
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "total_revenue": {"$sum": "$total_amount"},
                "avg_order_value": {"$avg": "$total_amount"},
                "count": {"$sum": 1}
            }
        }
    ]
    revenue_results = await db.orders.aggregate(pipeline).to_list(None)
    
    total_revenue = sum(r["total_revenue"] for r in revenue_results)
    # Aggregate platform and gateway fees from orders collection (delivered or confirmed)
    fees_pipeline = [
        {"$match": {"status": {"$in": ["delivered", "confirmed"]}}},
        {"$group": {
            "_id": None,
            "total_gross_revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
            "total_platform_fees": {"$sum": {"$ifNull": ["$platform_fee", 0]}},
            "total_gateway_fees": {"$sum": {"$ifNull": ["$payment_gateway_fee", 0]}},
            "total_merchant_payout": {"$sum": {"$ifNull": ["$merchant_payout", 0]}},
            "orders_count": {"$sum": 1},
        }},
        {"$project": {
            "_id": 0,
            "total_gross_revenue": 1,
            "total_platform_fees": 1,
            "total_gateway_fees": 1,
            "total_merchant_payout": 1,
            "orders_count": 1,
            "avg_fee_percentage": {"$cond": [{"$gt": ["$total_gross_revenue", 0]}, {"$divide": ["$total_platform_fees", "$total_gross_revenue"]}, 0]}
        }}
    ]
    fees_res = await db.orders.aggregate(fees_pipeline).to_list(length=1)
    fees_summary = fees_res[0] if fees_res else {"total_gross_revenue": 0.0, "total_platform_fees": 0.0, "total_gateway_fees": 0.0, "total_merchant_payout": 0.0, "orders_count": 0, "avg_fee_percentage": 0.0}
    # If the aggregation returned zero fees, try a fallback that sums orders where fees exist (covers migrated orders in any status)
    if fees_summary.get("total_platform_fees", 0) == 0:
        try:
            orders_fee_pipeline = [
                {"$match": {"platform_fee": {"$exists": True}}},
                {"$group": {
                    "_id": None,
                    "total_gross_revenue": {"$sum": {"$ifNull": ["$total_amount", 0]}},
                    "total_platform_fees": {"$sum": {"$ifNull": ["$platform_fee", 0]}},
                    "total_gateway_fees": {"$sum": {"$ifNull": ["$payment_gateway_fee", 0]}},
                    "total_merchant_payout": {"$sum": {"$ifNull": ["$merchant_payout", 0]}},
                    "orders_count": {"$sum": 1}
                }},
                {"$project": {"_id": 0, "total_gross_revenue": 1, "total_platform_fees": 1, "total_gateway_fees": 1, "total_merchant_payout": 1, "orders_count": 1}}
            ]
            orders_fee_res = await db.orders.aggregate(orders_fee_pipeline).to_list(length=1)
            if orders_fee_res:
                of = orders_fee_res[0]
                fees_summary["total_platform_fees"] = of.get("total_platform_fees", fees_summary.get("total_platform_fees", 0.0))
                fees_summary["total_gross_revenue"] = of.get("total_gross_revenue", fees_summary.get("total_gross_revenue", 0.0))
                fees_summary["total_gateway_fees"] = of.get("total_gateway_fees", fees_summary.get("total_gateway_fees", 0.0))
                fees_summary["total_merchant_payout"] = of.get("total_merchant_payout", fees_summary.get("total_merchant_payout", 0.0))
                fees_summary["orders_count"] = of.get("orders_count", fees_summary.get("orders_count", 0))
                gross = fees_summary.get("total_gross_revenue", 0) or 0
                fees = fees_summary.get("total_platform_fees", 0) or 0
                fees_summary["avg_fee_percentage"] = (fees / gross) if gross > 0 else 0.0
        except Exception:
            pass
    # If orders do not contain fee fields (legacy data), fallback to aggregating from payments
    if not fees_summary or (fees_summary.get("total_platform_fees", 0) == 0):
        try:
            payments_pipeline = [
                {
                    "$lookup": {
                        "from": "orders",
                        "let": {"orderId": "$order_id"},
                        "pipeline": [
                            {"$addFields": {"_id_str": {"$toString": "$_id"}}},
                            {"$match": {"$expr": {"$eq": ["$_id_str", "$$orderId"]}}},
                            {"$project": {"status": 1}}
                        ],
                        "as": "order_ref"
                    }
                },
                {"$unwind": {"path": "$order_ref", "preserveNullAndEmptyArrays": False}},
                {"$match": {"order_ref.status": {"$in": ["delivered", "confirmed"]}}},
                {"$group": {
                    "_id": None,
                    "total_gross_revenue": {"$sum": {"$ifNull": ["$gross_amount", 0]}},
                    "total_platform_fees": {"$sum": {"$ifNull": ["$platform_fee", 0]}},
                    "total_gateway_fees": {"$sum": {"$ifNull": ["$payment_gateway_fee", 0]}},
                    "total_merchant_payout": {"$sum": {"$ifNull": ["$merchant_payout", 0]}},
                    "payments_count": {"$sum": 1}
                }},
                {"$project": {"_id": 0, "total_gross_revenue": 1, "total_platform_fees": 1, "total_gateway_fees": 1, "total_merchant_payout": 1, "payments_count": 1}}
            ]
            pay_res = await db.payments.aggregate(payments_pipeline).to_list(length=1)
            if pay_res:
                pay_summary = pay_res[0]
                # Only override missing values
                if fees_summary.get("total_gross_revenue", 0) == 0:
                    fees_summary["total_gross_revenue"] = pay_summary.get("total_gross_revenue", 0.0)
                if fees_summary.get("total_platform_fees", 0) == 0:
                    fees_summary["total_platform_fees"] = pay_summary.get("total_platform_fees", 0.0)
                if fees_summary.get("total_gateway_fees", 0) == 0:
                    fees_summary["total_gateway_fees"] = pay_summary.get("total_gateway_fees", 0.0)
                if fees_summary.get("total_merchant_payout", 0) == 0:
                    fees_summary["total_merchant_payout"] = pay_summary.get("total_merchant_payout", 0.0)
                # recompute avg_fee_percentage safely
                gross = fees_summary.get("total_gross_revenue", 0) or 0
                fees = fees_summary.get("total_platform_fees", 0) or 0
                fees_summary["avg_fee_percentage"] = (fees / gross) if gross > 0 else 0.0
        except Exception:
            # If aggregation fails for any reason, keep original fees_summary
            pass

    return {
        "total_orders": total_orders,
        "status_breakdown": status_stats,
        "total_revenue": total_revenue,
        "total_gross_revenue": fees_summary.get("total_gross_revenue", total_revenue),
        "platform_net_revenue": fees_summary.get("total_platform_fees", 0.0),
        "revenue_by_status": {
            r["_id"]: {
                "total": r["total_revenue"],
                "average": r["avg_order_value"],
                "count": r["count"]
            }
            for r in revenue_results
        },
        "total_platform_fees": fees_summary.get("total_platform_fees", 0.0),
        "total_gateway_fees": fees_summary.get("total_gateway_fees", 0.0),
        "total_merchant_payout": fees_summary.get("total_merchant_payout", 0.0),
        "avg_fee_percentage": fees_summary.get("avg_fee_percentage", 0.0),
        "orders_count": fees_summary.get("orders_count", 0)
    }


@router.get("/{order_id}", tags=["Admin - Orders"])
async def get_order_detail(
    order_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get detailed information about a specific order.
    
    **Admin only**
    
    Args:
        order_id: The order ID
    
    Returns:
        Complete order details
    """
    try:
        obj_id = ObjectId(order_id)
    except Exception:
        obj_id = order_id
    
    order = await db.orders.find_one({"_id": obj_id})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return {
        "id": str(order["_id"]),
        "buyer_id": order.get("buyer_id"),
        "merchant_id": order.get("merchant_id"),
        "total_amount": order.get("total_amount", 0),
        "platform_fee": order.get("platform_fee", 0),
        "merchant_payout": order.get("merchant_payout", 0),
        "status": order.get("status", "pending"),
        "items": order.get("items", []),
        "shipping_address": order.get("shipping_address"),
        "payment_id": order.get("payment_id"),
        "status_history": order.get("status_history", []),
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at")
    }


@router.patch("/{order_id}/status", tags=["Admin - Orders"])
async def force_update_order_status(
    order_id: str,
    new_status: str = Query(..., description="New status: pending, confirmed, shipped, delivered, cancelled"),
    reason: Optional[str] = Query(None, description="Reason for status change"),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Force update an order status (bypasses normal business rules).
    
    **Admin only** - Use with caution!
    
    Args:
        order_id: The order ID
        new_status: The new status
        reason: Optional reason for the change
    
    Returns:
        Updated order with new status
    """
    valid_statuses = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    try:
        obj_id = ObjectId(order_id)
    except Exception:
        obj_id = order_id
    
    order = await db.orders.find_one({"_id": obj_id})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Add to status history
    status_history = order.get("status_history", [])
    status_history.append({
        "status": new_status,
        "changed_by": "admin",
        "admin_id": current_admin.get("_id"),
        "reason": reason or "Admin override",
        "timestamp": datetime.utcnow()
    })
    
    # Update order
    result = await db.orders.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "status": new_status,
                "status_history": status_history,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update order"
        )
    
    updated_order = await db.orders.find_one({"_id": obj_id})
    
    return {
        "message": f"Order status updated to {new_status}",
        "order_id": str(updated_order["_id"]),
        "previous_status": order.get("status"),
        "new_status": new_status,
        "reason": reason
    }


@router.delete("/{order_id}", tags=["Admin - Orders"])
async def delete_order(
    order_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete an order (hard delete - cannot be recovered).
    
    **Admin only** - Use with extreme caution!
    
    Args:
        order_id: The order ID to delete
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(order_id)
    except Exception:
        obj_id = order_id
    
    order = await db.orders.find_one({"_id": obj_id})
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Store order data in deleted_orders collection for audit trail
    deleted_order = order.copy()
    deleted_order["deleted_at"] = datetime.utcnow()
    deleted_order["deleted_by_admin_id"] = current_admin.get("_id")
    
    await db.deleted_orders.insert_one(deleted_order)
    
    # Delete from main collection
    result = await db.orders.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete order"
        )
    
    return {
        "message": "Order deleted successfully",
        "order_id": str(obj_id),
        "deleted_at": datetime.utcnow()
    }
