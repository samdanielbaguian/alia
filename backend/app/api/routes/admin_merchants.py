"""
Admin Merchant Management Routes
Endpoints for admin to manage merchants (verify, suspend, commission rates)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.api.deps import get_db, get_current_admin

router = APIRouter()


class MerchantVerificationRequest(BaseModel):
    is_verified: bool
    reason: Optional[str] = None


class MerchantStatusRequest(BaseModel):
    is_suspended: bool
    reason: Optional[str] = None


class MerchantCommissionRequest(BaseModel):
    commission_rate: float  # Percentage (e.g., 15.0 for 15%)


class MerchantUpdateRequest(BaseModel):
    shop_name: Optional[str] = None
    description: Optional[str] = None
    rating: Optional[float] = None


@router.get("")
async def list_merchants(
    is_verified: Optional[bool] = Query(None),
    is_suspended: Optional[bool] = Query(None),
    search: Optional[str] = Query(None, description="Search by shop name or email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """List all merchants with filters."""
    # Build query
    query = {}
    
    if is_verified is not None:
        query["is_verified"] = is_verified
    if is_suspended is not None:
        query["is_suspended"] = is_suspended
    if search:
        query["$or"] = [
            {"shop_name": {"$regex": search, "$options": "i"}},
            {"user_id": {"$regex": search, "$options": "i"}}
        ]
    
    merchants = await db.merchants.find(query).skip(skip).limit(limit).to_list(limit)
    total = await db.merchants.count_documents(query)
    
    # Enrich with user data
    for merchant in merchants:
        merchant["_id"] = str(merchant["_id"])
        
        # Get user info
        try:
            user = await db.users.find_one({"_id": ObjectId(merchant["user_id"])})
        except:
            user = await db.users.find_one({"_id": merchant["user_id"]})
        
        if user:
            merchant["email"] = user.get("email")
            merchant["user_role"] = user.get("role")
            merchant["user_created_at"] = user.get("created_at")
        
        # Get products count
        products_count = await db.products.count_documents({"merchant_id": merchant["user_id"]})
        merchant["products_count"] = products_count
        
        # Get orders count
        orders_count = await db.orders.count_documents({"merchant_id": merchant["user_id"]})
        merchant["orders_count"] = orders_count
    
    return {
        "merchants": merchants,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/pending")
async def list_pending_merchants(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """List merchants pending verification."""
    query = {"is_verified": False}
    
    merchants = await db.merchants.find(query).skip(skip).limit(limit).to_list(limit)
    total = await db.merchants.count_documents(query)
    
    for merchant in merchants:
        merchant["_id"] = str(merchant["_id"])
        
        # Get user info
        try:
            user = await db.users.find_one({"_id": ObjectId(merchant["user_id"])})
        except:
            user = await db.users.find_one({"_id": merchant["user_id"]})
        
        if user:
            merchant["email"] = user.get("email")
    
    return {
        "merchants": merchants,
        "total": total
    }


@router.get("/{merchant_id}")
async def get_merchant(
    merchant_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Get detailed merchant information."""
    try:
        merchant = await db.merchants.find_one({"_id": ObjectId(merchant_id)})
    except Exception:
        merchant = await db.merchants.find_one({"user_id": merchant_id})
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    merchant["_id"] = str(merchant["_id"])
    
    # Get user info
    try:
        user = await db.users.find_one({"_id": ObjectId(merchant["user_id"])})
    except:
        user = await db.users.find_one({"_id": merchant["user_id"]})
    
    if user:
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
        merchant["user"] = user
    
    # Get products
    products = await db.products.find({"merchant_id": merchant["user_id"]}).limit(10).to_list(10)
    for product in products:
        product["_id"] = str(product["_id"])
    merchant["recent_products"] = products
    
    # Get orders
    orders = await db.orders.find({"merchant_id": merchant["user_id"]}).limit(10).to_list(10)
    for order in orders:
        order["_id"] = str(order["_id"])
    merchant["recent_orders"] = orders
    
    # Get stats
    merchant["products_count"] = await db.products.count_documents({"merchant_id": merchant["user_id"]})
    merchant["orders_count"] = await db.orders.count_documents({"merchant_id": merchant["user_id"]})
    
    # Calculate total revenue
    pipeline = [
        {"$match": {"merchant_id": merchant["user_id"], "status": {"$in": ["shipped", "delivered"]}}},
        {"$group": {"_id": None, "total_revenue": {"$sum": "$total"}}}
    ]
    revenue_result = await db.orders.aggregate(pipeline).to_list(1)
    merchant["total_revenue"] = revenue_result[0]["total_revenue"] if revenue_result else 0.0
    
    return merchant


@router.post("/{merchant_id}/verify")
async def verify_merchant(
    merchant_id: str,
    request: MerchantVerificationRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Verify or reject a merchant."""
    try:
        merchant_obj_id = ObjectId(merchant_id)
        merchant = await db.merchants.find_one({"_id": merchant_obj_id})
    except Exception:
        merchant = await db.merchants.find_one({"user_id": merchant_id})
        merchant_obj_id = merchant.get("_id") if merchant else None
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    update_data = {
        "is_verified": request.is_verified,
        "verified_by": str(admin["_id"]),
        "verified_at": datetime.utcnow(),
        "verification_reason": request.reason,
        "updated_at": datetime.utcnow()
    }
    
    await db.merchants.update_one({"_id": merchant_obj_id}, {"$set": update_data})
    
    action = "verified" if request.is_verified else "rejected"
    return {"ok": True, "merchant_id": merchant_id, "action": action}


@router.post("/{merchant_id}/suspend")
async def suspend_merchant(
    merchant_id: str,
    request: MerchantStatusRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Suspend or unsuspend a merchant."""
    try:
        merchant_obj_id = ObjectId(merchant_id)
        merchant = await db.merchants.find_one({"_id": merchant_obj_id})
    except Exception:
        merchant = await db.merchants.find_one({"user_id": merchant_id})
        merchant_obj_id = merchant.get("_id") if merchant else None
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    update_data = {
        "is_suspended": request.is_suspended,
        "suspended_at": datetime.utcnow() if request.is_suspended else None,
        "suspended_by": str(admin["_id"]) if request.is_suspended else None,
        "suspension_reason": request.reason if request.is_suspended else None,
        "updated_at": datetime.utcnow()
    }
    
    # Also update user account
    try:
        user_id = ObjectId(merchant["user_id"])
    except:
        user_id = merchant["user_id"]
    
    await db.users.update_one({"_id": user_id}, {"$set": {"is_suspended": request.is_suspended}})
    
    await db.merchants.update_one({"_id": merchant_obj_id}, {"$set": update_data})
    
    # If suspending, deactivate all products
    if request.is_suspended:
        await db.products.update_many(
            {"merchant_id": merchant["user_id"]},
            {"$set": {"is_active": False, "suspended_at": datetime.utcnow()}}
        )
    
    action = "suspended" if request.is_suspended else "unsuspended"
    return {"ok": True, "merchant_id": merchant_id, "action": action}


@router.put("/{merchant_id}")
async def update_merchant(
    merchant_id: str,
    request: MerchantUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Update merchant information."""
    try:
        merchant_obj_id = ObjectId(merchant_id)
        merchant = await db.merchants.find_one({"_id": merchant_obj_id})
    except Exception:
        merchant = await db.merchants.find_one({"user_id": merchant_id})
        merchant_obj_id = merchant.get("_id") if merchant else None
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    update_data = {}
    if request.shop_name is not None:
        update_data["shop_name"] = request.shop_name
    if request.description is not None:
        update_data["description"] = request.description
    if request.rating is not None:
        update_data["rating"] = request.rating
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by_admin"] = str(admin["_id"])
    
    await db.merchants.update_one({"_id": merchant_obj_id}, {"$set": update_data})
    
    return {"ok": True, "merchant_id": merchant_id, "updated_fields": list(update_data.keys())}


@router.post("/{merchant_id}/commission")
async def set_merchant_commission(
    merchant_id: str,
    request: MerchantCommissionRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Set commission rate for a merchant."""
    if request.commission_rate < 0 or request.commission_rate > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Commission rate must be between 0 and 100"
        )
    
    try:
        merchant_obj_id = ObjectId(merchant_id)
        merchant = await db.merchants.find_one({"_id": merchant_obj_id})
    except Exception:
        merchant = await db.merchants.find_one({"user_id": merchant_id})
        merchant_obj_id = merchant.get("_id") if merchant else None
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    await db.merchants.update_one(
        {"_id": merchant_obj_id},
        {
            "$set": {
                "commission_rate": request.commission_rate,
                "commission_set_by": str(admin["_id"]),
                "commission_set_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"ok": True, "merchant_id": merchant_id, "commission_rate": request.commission_rate}


@router.get("/stats/overview")
async def get_merchants_stats(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Get merchant statistics overview."""
    total = await db.merchants.count_documents({})
    verified = await db.merchants.count_documents({"is_verified": True})
    pending = await db.merchants.count_documents({"is_verified": False})
    suspended = await db.merchants.count_documents({"is_suspended": True})
    
    # Get top merchants by revenue
    pipeline = [
        {"$match": {"status": {"$in": ["shipped", "delivered"]}}},
        {"$group": {
            "_id": "$merchant_id",
            "total_revenue": {"$sum": "$total"},
            "order_count": {"$sum": 1}
        }},
        {"$sort": {"total_revenue": -1}},
        {"$limit": 10}
    ]
    top_merchants = await db.orders.aggregate(pipeline).to_list(10)
    
    return {
        "total": total,
        "verified": verified,
        "pending": pending,
        "suspended": suspended,
        "top_merchants": top_merchants
    }
