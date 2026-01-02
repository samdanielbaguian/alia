from typing import Dict, Optional
from datetime import datetime, date
import calendar
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.deps import get_db, get_current_user, get_current_merchant
from app.schemas.share import MerchantShareResponse
from app.schemas.order import OrderResponse, OrderProductResponse, StatusHistoryResponse
from app.schemas.dashboard import DashboardOverviewResponse, DashboardPeriod
from app.services.share_service import ShareService
from app.services.order_service import OrderService

router = APIRouter()


@router.get("/{merchant_id}")
async def get_merchant(
    merchant_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get merchant profile by ID."""
    merchant = await db.merchants.find_one({"user_id": merchant_id})
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    return {
        "id": str(merchant["_id"]),
        "user_id": merchant["user_id"],
        "shop_name": merchant["shop_name"],
        "description": merchant.get("description", ""),
        "location": merchant.get("location"),
        "total_sales": merchant.get("total_sales", 0.0),
        "rating": merchant.get("rating", 50.0),
        "created_at": merchant["created_at"]
    }


@router.put("/{merchant_id}")
async def update_merchant(
    merchant_id: str,
    update_data: Dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update merchant profile (merchant only, own profile only)."""
    user_id = str(current_user["_id"])
    
    if current_user["role"] != "merchant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only merchants can update merchant profiles"
        )
    
    if merchant_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own merchant profile"
        )
    
    merchant = await db.merchants.find_one({"user_id": merchant_id})
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    # Only allow updating certain fields
    allowed_fields = ["shop_name", "description", "location"]
    update_fields = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid fields to update"
        )
    
    await db.merchants.update_one(
        {"user_id": merchant_id},
        {"$set": update_fields}
    )
    
    updated_merchant = await db.merchants.find_one({"user_id": merchant_id})
    
    return {
        "id": str(updated_merchant["_id"]),
        "user_id": updated_merchant["user_id"],
        "shop_name": updated_merchant["shop_name"],
        "description": updated_merchant.get("description", ""),
        "location": updated_merchant.get("location"),
        "total_sales": updated_merchant.get("total_sales", 0.0),
        "rating": updated_merchant.get("rating", 50.0),
        "created_at": updated_merchant["created_at"]
    }


@router.get("/{merchant_id}/dashboard")
async def get_merchant_dashboard(
    merchant_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get merchant dashboard with analytics.
    
    Returns:
    - Total sales
    - Products count
    - Orders count
    - Revenue
    - Top selling products
    - Demand zones (orders grouped by location)
    """
    user_id = str(current_user["_id"])
    
    if current_user["role"] != "merchant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only merchants can access dashboard"
        )
    
    if merchant_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own dashboard"
        )
    
    # Get merchant info
    merchant = await db.merchants.find_one({"user_id": merchant_id})
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    # Get products count
    products_count = await db.products.count_documents({"merchant_id": merchant_id})
    
    # Get orders
    orders = await db.orders.find({"merchant_id": merchant_id}).to_list(length=1000)
    orders_count = len(orders)
    
    # Calculate total revenue
    revenue = sum(order["total_amount"] for order in orders)
    
    # Get top selling products
    product_sales = {}
    for order in orders:
        for product in order["products"]:
            product_id = product["product_id"]
            if product_id not in product_sales:
                product_sales[product_id] = {
                    "product_id": product_id,
                    "title": product["title"],
                    "quantity_sold": 0,
                    "revenue": 0.0
                }
            product_sales[product_id]["quantity_sold"] += product["quantity"]
            product_sales[product_id]["revenue"] += product["price"] * product["quantity"]
    
    top_products = sorted(
        product_sales.values(),
        key=lambda x: x["quantity_sold"],
        reverse=True
    )[:10]
    
    # Orders by status breakdown
    orders_by_status = {
        "pending": 0,
        "confirmed": 0,
        "shipped": 0,
        "delivered": 0,
        "cancelled": 0
    }
    for order in orders:
        order_status = order.get("status", "pending")
        if order_status in orders_by_status:
            orders_by_status[order_status] += 1
    
    # Recent orders (last 5)
    recent_orders = sorted(orders, key=lambda x: x.get("created_at"), reverse=True)[:5]
    recent_orders_list = [
        {
            "id": str(order["_id"]),
            "total_amount": order["total_amount"],
            "status": order["status"],
            "created_at": order["created_at"]
        }
        for order in recent_orders
    ]
    
    # Analyze demand zones (group orders by user location)
    # TODO: Get user locations from orders
    demand_zones = []
    
    return {
        "merchant_id": merchant_id,
        "shop_name": merchant["shop_name"],
        "total_sales": merchant.get("total_sales", 0.0),
        "rating": merchant.get("rating", 50.0),
        "products_count": products_count,
        "orders_count": orders_count,
        "revenue": revenue,
        "top_products": top_products,
        "orders_by_status": orders_by_status,
        "recent_orders": recent_orders_list,
        "pending_orders_count": orders_by_status["pending"],
        "demand_zones": demand_zones
    }


@router.post("/{merchant_id}/share", response_model=MerchantShareResponse)
async def share_merchant(
    merchant_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generate a shareable link for a merchant shop.
    
    Returns:
    - Direct share link
    - WhatsApp pre-filled message link
    """
    user_id = str(current_user["_id"])
    
    return await ShareService.create_merchant_share(
        merchant_id=merchant_id,
        user_id=user_id,
        db=db
    )


@router.get("/share/{share_code}")
async def view_shared_merchant(
    share_code: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    View a shared merchant shop (public endpoint).
    
    No authentication required.
    Increments view count and returns merchant profile.
    """
    merchant = await ShareService.get_shared_merchant(share_code, db)
    
    # Get merchant products
    products = await db.products.find({"merchant_id": merchant["user_id"]}).limit(20).to_list(length=20)
    
    return {
        "id": str(merchant["_id"]),
        "user_id": merchant["user_id"],
        "shop_name": merchant["shop_name"],
        "description": merchant.get("description", ""),
        "location": merchant.get("location"),
        "total_sales": merchant.get("total_sales", 0.0),
        "rating": merchant.get("rating", 50.0),
        "created_at": merchant["created_at"],
        "products_count": len(products),
        "products": [
            {
                "id": str(p["_id"]),
                "title": p["title"],
                "price": p["price"],
                "images": p.get("images", [])
            }
            for p in products
        ]
    }


@router.get("/me/orders")
async def get_merchant_orders(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by order status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get orders received by the current merchant.
    
    Query params:
    - status: Filter by order status (pending, confirmed, shipped, delivered, cancelled)
    - limit: Number of orders to return (default: 20, max: 100)
    - offset: Number of orders to skip for pagination (default: 0)
    
    Returns paginated list of orders with customer info.
    """
    user_id = str(current_user["_id"])
    
    # Get merchant profile
    merchant = await OrderService.get_merchant_by_user_id(user_id, db)
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    # Build filter query
    filter_query = {"merchant_id": merchant["user_id"]}
    
    if status_filter:
        filter_query["status"] = status_filter
    
    # Query orders with pagination
    orders = await db.orders.find(filter_query).skip(offset).limit(limit).to_list(length=limit)
    total = await db.orders.count_documents(filter_query)
    
    # Build order responses
    order_responses = []
    for order in orders:
        order_response = OrderResponse(
            id=str(order["_id"]),
            user_id=order["user_id"],
            merchant_id=order["merchant_id"],
            products=[
                OrderProductResponse(
                    product_id=p["product_id"],
                    quantity=p["quantity"],
                    price=p["price"],
                    title=p["title"]
                )
                for p in order["products"]
            ],
            total_amount=order["total_amount"],
            status=order["status"],
            payment_method=order["payment_method"],
            created_at=order["created_at"],
            updated_at=order.get("updated_at", order["created_at"]),
            status_history=[
                StatusHistoryResponse(**h) for h in order.get("status_history", [])
            ] if order.get("status_history") else None,
            cancelled_by=order.get("cancelled_by"),
            cancellation_reason=order.get("cancellation_reason"),
            tracking_number=order.get("tracking_number"),
            shipped_at=order.get("shipped_at"),
            delivered_at=order.get("delivered_at")
        )
        
        order_responses.append(order_response)
    
    return {
        "orders": order_responses,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/me/dashboard-overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    from_date: Optional[date] = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get merchant dashboard overview with activity summary for a given period.
    
    Returns comprehensive analytics including:
    - Total sales (completed orders)
    - Orders count and status breakdown
    - Refunds information
    - New customers
    - Stock information
    
    Query params:
    - from: Start date (YYYY-MM-DD), defaults to first day of current month
    - to: End date (YYYY-MM-DD), defaults to last day of current month
    
    Requires merchant authentication.
    """
    user_id = str(current_user["_id"])
    
    # Set default period to current month if not provided
    now = datetime.utcnow()
    if not from_date:
        from_date = date(now.year, now.month, 1)
    if not to_date:
        # Last day of current month using calendar module
        last_day = calendar.monthrange(now.year, now.month)[1]
        to_date = date(now.year, now.month, last_day)
    
    # Convert dates to datetime for MongoDB queries
    start_datetime = datetime.combine(from_date, datetime.min.time())
    end_datetime = datetime.combine(to_date, datetime.max.time())
    
    # Get merchant profile
    merchant = await db.merchants.find_one({"user_id": user_id})
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    # Build aggregation pipeline for orders
    orders_pipeline = [
        {
            "$match": {
                "merchant_id": user_id,
                "created_at": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "orders_pending": {
                    "$sum": {"$cond": [{"$eq": ["$status", "pending"]}, 1, 0]}
                },
                "orders_confirmed": {
                    "$sum": {"$cond": [{"$eq": ["$status", "confirmed"]}, 1, 0]}
                },
                "orders_shipped": {
                    "$sum": {"$cond": [{"$eq": ["$status", "shipped"]}, 1, 0]}
                },
                "orders_delivered": {
                    "$sum": {"$cond": [{"$eq": ["$status", "delivered"]}, 1, 0]}
                },
                "orders_canceled": {
                    # Note: Status in DB is "cancelled" (British), but response field is "canceled" (American) per spec
                    "$sum": {"$cond": [{"$eq": ["$status", "cancelled"]}, 1, 0]}
                },
                "unique_customers": {"$addToSet": "$user_id"}
            }
        }
    ]
    
    orders_result = await db.orders.aggregate(orders_pipeline).to_list(length=1)
    orders_stats = orders_result[0] if orders_result else {
        "total_orders": 0,
        "orders_pending": 0,
        "orders_confirmed": 0,
        "orders_shipped": 0,
        "orders_delivered": 0,
        "orders_canceled": 0,
        "unique_customers": []
    }
    
    # Calculate total sales from completed payments (status: completed)
    payments_pipeline = [
        {
            "$match": {
                "merchant_id": user_id,
                "status": "completed",
                "initiated_at": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": None,
                "total_sales": {"$sum": "$amount"}
            }
        }
    ]
    
    payments_result = await db.payments.aggregate(payments_pipeline).to_list(length=1)
    total_sales = payments_result[0]["total_sales"] if payments_result else 0.0
    
    # Get refunds information
    refunds_pipeline = [
        {
            "$match": {
                "merchant_id": user_id,
                "created_at": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$group": {
                "_id": None,
                "refunds_count": {"$sum": 1},
                "refunds_total": {"$sum": "$amount"}
            }
        }
    ]
    
    refunds_result = await db.refunds.aggregate(refunds_pipeline).to_list(length=1)
    refunds_stats = refunds_result[0] if refunds_result else {
        "refunds_count": 0,
        "refunds_total": 0.0
    }
    
    # Count orders with refunded status
    orders_refunded = await db.orders.count_documents({
        "merchant_id": user_id,
        "created_at": {"$gte": start_datetime, "$lte": end_datetime},
        "status": "refunded"
    })
    
    # Get new customers (users who made their first order in this period)
    # Find all customers who ordered in the period
    customer_ids = orders_stats.get("unique_customers", [])
    
    # For each customer, check if they have orders before the period start
    new_customers_count = 0
    for customer_id in customer_ids:
        # Check if this is their first order
        first_order = await db.orders.find_one(
            {"user_id": customer_id},
            sort=[("created_at", 1)]
        )
        if first_order and first_order["created_at"] >= start_datetime:
            new_customers_count += 1
    
    # Get product stock information
    products_pipeline = [
        {
            "$match": {"merchant_id": user_id}
        },
        {
            "$group": {
                "_id": None,
                "products_in_stock": {
                    "$sum": {"$cond": [{"$gt": ["$stock", 0]}, 1, 0]}
                },
                "low_stock": {
                    "$sum": {"$cond": [{"$and": [{"$gt": ["$stock", 0]}, {"$lte": ["$stock", 5]}]}, 1, 0]}
                }
            }
        }
    ]
    
    products_result = await db.products.aggregate(products_pipeline).to_list(length=1)
    products_stats = products_result[0] if products_result else {
        "products_in_stock": 0,
        "low_stock": 0
    }
    
    return DashboardOverviewResponse(
        total_sales=total_sales,
        orders_count=orders_stats["total_orders"],
        orders_pending=orders_stats["orders_pending"],
        orders_shipped=orders_stats["orders_shipped"],
        orders_canceled=orders_stats["orders_canceled"],
        orders_refunded=orders_refunded,
        refunds_total=refunds_stats["refunds_total"],
        new_customers=new_customers_count,
        products_in_stock=products_stats["products_in_stock"],
        low_stock=products_stats["low_stock"],
        period=DashboardPeriod(**{"from": from_date, "to": to_date})
    )
