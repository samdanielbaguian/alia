from typing import Dict, Optional
from datetime import datetime, date, timedelta
import calendar
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from bson.errors import InvalidId

from app.api.deps import get_db, get_current_user, get_current_merchant
from app.schemas.share import MerchantShareResponse
from app.schemas.order import OrderResponse, OrderProductResponse, StatusHistoryResponse
from app.schemas.dashboard import (
    DashboardOverviewResponse, DashboardPeriod,
    OrderStatsResponse, OrderStatsPoint,
    BestsellersResponse, BestsellerProduct, BestsellerCategory,
    AlertsResponse, Alert,
    RecentActivityResponse, ActivityItem,
    ExportOrdersRequest, ExportOrdersResponse
)
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


@router.get("/me/orders/stats", response_model=OrderStatsResponse)
async def get_orders_stats(
    from_date: Optional[date] = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get order statistics time series for merchant dashboard charts.
    
    Returns daily statistics including:
    - Number of orders per day
    - Total sales amount per day
    - Orders breakdown by status per day
    
    Query params:
    - from: Start date (YYYY-MM-DD), defaults to 30 days ago
    - to: End date (YYYY-MM-DD), defaults to today
    
    Requires merchant authentication.
    """
    user_id = str(current_user["_id"])
    
    # Set default period to last 30 days if not provided
    now = datetime.utcnow()
    if not to_date:
        to_date = date(now.year, now.month, now.day)
    if not from_date:
        # 30 days ago
        thirty_days_ago = now - timedelta(days=30)
        from_date = date(thirty_days_ago.year, thirty_days_ago.month, thirty_days_ago.day)
    
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
    
    # Aggregate orders by date
    pipeline = [
        {
            "$match": {
                "merchant_id": user_id,
                "created_at": {"$gte": start_datetime, "$lte": end_datetime}
            }
        },
        {
            "$project": {
                "date": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}
                },
                "total_amount": 1,
                "status": 1
            }
        },
        {
            "$group": {
                "_id": "$date",
                "orders_count": {"$sum": 1},
                "total_amount": {"$sum": "$total_amount"},
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
                "orders_cancelled": {
                    "$sum": {"$cond": [{"$eq": ["$status", "cancelled"]}, 1, 0]}
                }
            }
        },
        {
            "$sort": {"_id": 1}
        }
    ]
    
    results = await db.orders.aggregate(pipeline).to_list(length=None)
    
    # Convert to response format
    stats = [
        OrderStatsPoint(
            date=r["_id"],
            orders_count=r["orders_count"],
            total_amount=r["total_amount"],
            orders_pending=r["orders_pending"],
            orders_confirmed=r["orders_confirmed"],
            orders_shipped=r["orders_shipped"],
            orders_delivered=r["orders_delivered"],
            orders_cancelled=r["orders_cancelled"]
        )
        for r in results
    ]
    
    # Calculate summary
    total_orders = sum(s.orders_count for s in stats)
    total_sales = sum(s.total_amount for s in stats)
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0.0
    
    summary = {
        "total_orders": total_orders,
        "total_sales": total_sales,
        "avg_order_value": round(avg_order_value, 2)
    }
    
    return OrderStatsResponse(
        period=DashboardPeriod(**{"from": from_date, "to": to_date}),
        stats=stats,
        summary=summary
    )


@router.get("/me/bestsellers", response_model=BestsellersResponse)
async def get_bestsellers(
    from_date: Optional[date] = Query(None, alias="from", description="Start date (YYYY-MM-DD)"),
    to_date: Optional[date] = Query(None, alias="to", description="End date (YYYY-MM-DD)"),
    limit: int = Query(10, ge=1, le=50, description="Number of top items to return"),
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get bestselling products and categories for merchant dashboard.
    
    Returns:
    - Top selling products by quantity and revenue
    - Top selling categories by quantity and revenue
    
    Query params:
    - from: Start date (YYYY-MM-DD), defaults to first day of current month
    - to: End date (YYYY-MM-DD), defaults to today
    - limit: Number of top items to return (default: 10, max: 50)
    
    Requires merchant authentication.
    """
    user_id = str(current_user["_id"])
    
    # Set default period to current month if not provided
    now = datetime.utcnow()
    if not from_date:
        from_date = date(now.year, now.month, 1)
    if not to_date:
        to_date = date(now.year, now.month, now.day)
    
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
    
    # Get orders in period
    orders = await db.orders.find({
        "merchant_id": user_id,
        "created_at": {"$gte": start_datetime, "$lte": end_datetime}
    }).to_list(length=None)
    
    # Aggregate product sales
    product_sales = {}
    for order in orders:
        for product in order["products"]:
            product_id = product["product_id"]
            if product_id not in product_sales:
                product_sales[product_id] = {
                    "product_id": product_id,
                    "title": product["title"],
                    "quantity_sold": 0,
                    "revenue": 0.0,
                    "orders_count": 0,
                    "order_ids": set()
                }
            product_sales[product_id]["quantity_sold"] += product["quantity"]
            product_sales[product_id]["revenue"] += product["price"] * product["quantity"]
            product_sales[product_id]["order_ids"].add(str(order["_id"]))
    
    # Convert to list and add orders_count
    for ps in product_sales.values():
        ps["orders_count"] = len(ps["order_ids"])
        del ps["order_ids"]
    
    # Sort by revenue and get top products
    top_products_data = sorted(
        product_sales.values(),
        key=lambda x: x["revenue"],
        reverse=True
    )[:limit]
    
    # Batch fetch product details to avoid N+1 queries
    product_ids = []
    for pd in top_products_data:
        try:
            product_ids.append(ObjectId(pd["product_id"]))
        except (InvalidId, ValueError, TypeError):
            # If product_id is not a valid ObjectId, skip
            pass
    
    # Fetch all products in a single query
    products_cursor = db.products.find({"_id": {"$in": product_ids}})
    products = await products_cursor.to_list(length=len(product_ids))
    
    # Create a lookup map for quick access
    products_map = {str(p["_id"]): p for p in products}
    
    # Build top products list with images
    top_products = []
    for pd in top_products_data:
        product = products_map.get(pd["product_id"])
        image_url = None
        if product and product.get("images"):
            image_url = product["images"][0] if isinstance(product["images"], list) else product["images"]
        
        top_products.append(BestsellerProduct(
            product_id=pd["product_id"],
            title=pd["title"],
            quantity_sold=pd["quantity_sold"],
            revenue=pd["revenue"],
            orders_count=pd["orders_count"],
            image_url=image_url
        ))
    
    # Aggregate category sales using the same products map
    category_sales = {}
    for product_id, ps in product_sales.items():
        product = products_map.get(product_id)
        
        if product:
            category = product.get("category", "Uncategorized")
        else:
            category = "Uncategorized"
        
        if category not in category_sales:
            category_sales[category] = {
                "category": category,
                "quantity_sold": 0,
                "revenue": 0.0,
                "products": set()
            }
        category_sales[category]["quantity_sold"] += ps["quantity_sold"]
        category_sales[category]["revenue"] += ps["revenue"]
        category_sales[category]["products"].add(product_id)
    
    # Convert to list and add products_count
    for cs in category_sales.values():
        cs["products_count"] = len(cs["products"])
        del cs["products"]
    
    # Sort by revenue and get top categories
    top_categories = [
        BestsellerCategory(**cs)
        for cs in sorted(
            category_sales.values(),
            key=lambda x: x["revenue"],
            reverse=True
        )[:limit]
    ]
    
    return BestsellersResponse(
        period=DashboardPeriod(**{"from": from_date, "to": to_date}),
        top_products=top_products,
        top_categories=top_categories
    )


@router.get("/me/alerts", response_model=AlertsResponse)
async def get_alerts(
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get real-time alerts for merchant dashboard.
    
    Returns alerts for:
    - Pending orders waiting for confirmation
    - Low stock products
    - High refund rate
    - Other important notifications
    
    Requires merchant authentication.
    """
    user_id = str(current_user["_id"])
    
    # Get merchant profile
    merchant = await db.merchants.find_one({"user_id": user_id})
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    alerts = []
    now = datetime.utcnow()
    
    # Check pending orders
    pending_count = await db.orders.count_documents({
        "merchant_id": user_id,
        "status": "pending"
    })
    
    if pending_count > 0:
        severity = "critical" if pending_count > 10 else "warning"
        alerts.append(Alert(
            type="pending_orders",
            severity=severity,
            title="Pending Orders",
            message=f"You have {pending_count} order{'s' if pending_count > 1 else ''} pending confirmation",
            count=pending_count,
            action_url="/api/merchants/me/orders?status=pending",
            created_at=now
        ))
    
    # Check low stock products
    low_stock_count = await db.products.count_documents({
        "merchant_id": user_id,
        "stock": {"$gt": 0, "$lte": 5}
    })
    
    if low_stock_count > 0:
        alerts.append(Alert(
            type="low_stock",
            severity="warning",
            title="Low Stock Alert",
            message=f"{low_stock_count} product{'s are' if low_stock_count > 1 else ' is'} running low on stock",
            count=low_stock_count,
            action_url="/api/products?merchant_id=" + user_id + "&low_stock=true",
            created_at=now
        ))
    
    # Check out of stock products
    out_of_stock_count = await db.products.count_documents({
        "merchant_id": user_id,
        "stock": 0
    })
    
    if out_of_stock_count > 0:
        alerts.append(Alert(
            type="out_of_stock",
            severity="critical",
            title="Out of Stock",
            message=f"{out_of_stock_count} product{'s are' if out_of_stock_count > 1 else ' is'} out of stock",
            count=out_of_stock_count,
            action_url="/api/products?merchant_id=" + user_id + "&out_of_stock=true",
            created_at=now
        ))
    
    # Check recent refunds (last 7 days)
    seven_days_ago = now - timedelta(days=7)
    recent_refunds_count = await db.refunds.count_documents({
        "merchant_id": user_id,
        "created_at": {"$gte": seven_days_ago}
    })
    
    if recent_refunds_count > 5:
        alerts.append(Alert(
            type="high_refunds",
            severity="warning",
            title="High Refund Rate",
            message=f"{recent_refunds_count} refunds in the last 7 days",
            count=recent_refunds_count,
            action_url="/api/merchants/me/recent-activity?type=refund",
            created_at=now
        ))
    
    # Check old pending orders (>3 days)
    three_days_ago = now - timedelta(days=3)
    old_pending_count = await db.orders.count_documents({
        "merchant_id": user_id,
        "status": "pending",
        "created_at": {"$lte": three_days_ago}
    })
    
    if old_pending_count > 0:
        alerts.append(Alert(
            type="old_pending_orders",
            severity="critical",
            title="Old Pending Orders",
            message=f"{old_pending_count} order{'s have' if old_pending_count > 1 else ' has'} been pending for more than 3 days",
            count=old_pending_count,
            action_url="/api/merchants/me/orders?status=pending",
            created_at=now
        ))
    
    return AlertsResponse(
        alerts=alerts,
        total=len(alerts)
    )


@router.get("/me/recent-activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=100, description="Number of activities to return"),
    activity_type: Optional[str] = Query(None, alias="type", description="Filter by activity type"),
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get recent activity for merchant dashboard.
    
    Returns recent:
    - New orders
    - Refunds processed
    - Order status changes
    - Product updates
    
    Query params:
    - limit: Number of activities to return (default: 20, max: 100)
    - type: Filter by activity type (order, refund, status_change)
    
    Requires merchant authentication.
    """
    user_id = str(current_user["_id"])
    
    # Get merchant profile
    merchant = await db.merchants.find_one({"user_id": user_id})
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant profile not found"
        )
    
    activities = []
    
    # Get recent orders
    if not activity_type or activity_type == "order":
        recent_orders = await db.orders.find({
            "merchant_id": user_id
        }).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        # Batch fetch customer information to avoid N+1 queries
        customer_ids = []
        for order in recent_orders:
            if ObjectId.is_valid(order["user_id"]):
                try:
                    customer_ids.append(ObjectId(order["user_id"]))
                except (InvalidId, ValueError, TypeError):
                    pass
        
        # Fetch all customers in a single query
        customers_cursor = db.users.find({"_id": {"$in": customer_ids}})
        customers = await customers_cursor.to_list(length=len(customer_ids))
        customers_map = {str(c["_id"]): c for c in customers}
        
        for order in recent_orders:
            # Get customer info from map
            customer = customers_map.get(order["user_id"])
            customer_name = customer.get("username", "Unknown") if customer else "Unknown"
            
            activities.append(ActivityItem(
                type="order",
                title="New Order Received",
                description=f"Order from {customer_name}",
                timestamp=order["created_at"],
                reference_id=str(order["_id"]),
                amount=order["total_amount"],
                status=order["status"]
            ))
    
    # Get recent refunds
    if not activity_type or activity_type == "refund":
        recent_refunds = await db.refunds.find({
            "merchant_id": user_id
        }).sort("created_at", -1).limit(limit).to_list(length=limit)
        
        for refund in recent_refunds:
            activities.append(ActivityItem(
                type="refund",
                title="Refund " + refund["status"].title(),
                description=f"Refund for order {refund['order_id']}: {refund['reason']}",
                timestamp=refund["created_at"],
                reference_id=refund.get("refund_id", str(refund["_id"])),
                amount=refund["amount"],
                status=refund["status"]
            ))
    
    # Sort all activities by timestamp descending
    activities.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Limit to requested number
    activities = activities[:limit]
    
    return RecentActivityResponse(
        activities=activities,
        total=len(activities)
    )


@router.post("/me/exports/orders", response_model=ExportOrdersResponse)
async def export_orders(
    request: ExportOrdersRequest,
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Export orders to CSV for merchant dashboard.
    
    Returns CSV file content with order data for the specified period.
    
    Request body:
    - from: Start date (YYYY-MM-DD), defaults to first day of current month
    - to: End date (YYYY-MM-DD), defaults to today
    - status: Filter by order status (optional)
    - format: Export format (csv only for now)
    
    Requires merchant authentication.
    """
    user_id = str(current_user["_id"])
    
    # Set default period to current month if not provided
    now = datetime.utcnow()
    from_date = request.from_date
    to_date = request.to_date
    
    if not from_date:
        from_date = date(now.year, now.month, 1)
    if not to_date:
        to_date = date(now.year, now.month, now.day)
    
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
    
    # Build query
    query = {
        "merchant_id": user_id,
        "created_at": {"$gte": start_datetime, "$lte": end_datetime}
    }
    
    if request.status:
        query["status"] = request.status
    
    # Get orders
    orders = await db.orders.find(query).sort("created_at", -1).to_list(length=None)
    
    # Generate CSV content
    csv_lines = ["Order ID,Date,Customer ID,Total Amount,Status,Payment Method,Products Count"]
    
    for order in orders:
        order_id = str(order["_id"])
        order_date = order["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        customer_id = order["user_id"]
        total_amount = order["total_amount"]
        status = order["status"]
        payment_method = order["payment_method"]
        products_count = len(order["products"])
        
        csv_lines.append(
            f"{order_id},{order_date},{customer_id},{total_amount},{status},{payment_method},{products_count}"
        )
    
    csv_content = "\n".join(csv_lines)
    filename = f"orders_{from_date}_{to_date}.csv"
    
    return ExportOrdersResponse(
        filename=filename,
        content=csv_content,
        rows_count=len(orders)
    )
