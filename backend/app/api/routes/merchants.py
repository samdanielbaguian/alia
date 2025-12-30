from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.deps import get_db, get_current_user
from app.schemas.share import MerchantShareResponse
from app.services.share_service import ShareService

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
