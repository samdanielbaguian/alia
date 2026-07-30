"""
Admin routes for merchant management.

Provides administrative endpoints for:
- Listing all merchants with filtering
- Viewing merchant details
- Verifying/unverifying merchants
- Disabling/enabling merchant accounts
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.deps import get_db, get_current_admin
from app.schemas.admin import MerchantCreateByAdmin
from app.core.security import get_password_hash
from app.models.user import UserRole

router = APIRouter()


@router.post("", status_code=201, tags=["Admin - Merchants"])
async def create_merchant_by_admin(
    data: MerchantCreateByAdmin,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Create a new merchant account by admin.
    
    **Admin only**
    
    Args:
        data: Merchant creation data including email, password, names, shop info
        
    Returns:
        Confirmation with created merchant details
    """
    # Verify email is unique
    existing_user = await db.users.find_one({"email": data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )
    
    # Hash password
    hashed_password = get_password_hash(data.password)
    
    # Create user document
    user_data = {
        "email": data.email,
        "password_hash": hashed_password,
        "role": UserRole.MERCHANT,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "age": data.age,
        "location": data.location,
        "preferences": [],
        "good_rate": 50.0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    user_result = await db.users.insert_one(user_data)
    user_id = str(user_result.inserted_id)
    
    # Create merchant document
    merchant_data = {
        "user_id": user_id,
        "shop_name": data.shop_name,
        "description": data.description or "",
        "location": data.location,
        "total_sales": 0.0,
        "rating": 50.0,
        "verified": False,
        "is_active": True,
        "created_by_admin_id": current_admin.get("_id"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    merchant_result = await db.merchants.insert_one(merchant_data)
    merchant_id = str(merchant_result.inserted_id)
    
    return {
        "message": "Marchand créé avec succès",
        "user_id": user_id,
        "merchant_id": merchant_id,
        "email": data.email,
        "shop_name": data.shop_name,
        "status": "created"
    }


@router.get("", tags=["Admin - Merchants"])
async def list_all_merchants(
    verified: Optional[bool] = Query(None, description="Filter by verification status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by shop name"),
    sort_by: Optional[str] = Query(None, description="Sort by: rating_desc, sales_desc, newest"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all merchants with optional filtering and pagination.
    Enhanced response includes owner name and product count.
    
    **Admin only**
    
    Args:
        verified: Filter by verification status
        is_active: Filter by active status
        search: Search by shop name
        sort_by: Sort order
        limit: Maximum number of results (1-100)
        skip: Number of results to skip (for pagination)
    
    Returns:
        List of merchants with total count, owner details, and product count
    """
    # Build the match query
    match_query = {}
    
    if verified is not None:
        match_query["verified"] = verified
    
    if is_active is not None:
        match_query["is_active"] = is_active
    
    if search:
        match_query["shop_name"] = {"$regex": search, "$options": "i"}
    
    # Determine sort
    sort_field = "created_at"
    sort_direction = -1
    
    if sort_by == "rating_desc":
        sort_field = "rating"
        sort_direction = -1
    elif sort_by == "rating_asc":
        sort_field = "rating"
        sort_direction = 1
    elif sort_by == "sales_desc":
        sort_field = "total_sales"
        sort_direction = -1
    elif sort_by == "newest":
        sort_field = "created_at"
        sort_direction = -1
    
    # Build aggregation pipeline
    pipeline = [
        {
            "$match": match_query
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user"
            }
        },
        {
            "$unwind": {
                "path": "$user",
                "preserveNullAndEmptyArrays": True
            }
        },
        {
            "$lookup": {
                "from": "products",
                "localField": "user_id",     # ← au lieu de "_id"
                "foreignField": "merchant_id",
                "as": "products"
            }
        },
        {
            "$addFields": {
                "products_count": {"$size": "$products"},
                "owner_name": {
                    "$concat": [
                        {"$ifNull": ["$user.first_name", ""]},
                        " ",
                        {"$ifNull": ["$user.last_name", ""]}
                    ]
                },
                "owner_email": "$user.email",
                "logo": "$logo"
            }
        },
        {
            "$lookup": {
                "from": "reviews",
                "localField": "user_id",
                "foreignField": "merchant_id",
                "as": "reviews"
            }
        },
        {
            "$addFields": {
                "avg_rating": {
                    "$cond": {
                        "if": {"$gt": [{"$size": "$reviews"}, 0]},
                        "then": {"$avg": "$reviews.rating"},
                        "else": 0
                    }
                }
            }
        },
        {
            "$sort": {sort_field: sort_direction}
        },
        {
            "$skip": skip
        },
        {
            "$limit": limit
        },
        {
            "$project": {
                "id": {"$toString": "$_id"},
                "_id": 0,
                "user_id": 1,
                "shop_name": 1,
                "description": 1,
                "owner_name": 1,
                "owner_email": 1,
                "phone": 1,
                "address": 1,
                "city": 1,
                "country": 1,
                "rating": 1,
                "total_sales": 1,
                "verified": 1,
                "is_active": 1,
                "products_count": 1,
                "created_at": 1,
                "updated_at": 1
            }
        }
    ]
    
    # Get total count
    count_pipeline = [
        {
            "$match": match_query
        },
        {
            "$count": "total"
        }
    ]
    
    count_result = await db.merchants.aggregate(count_pipeline).to_list(length=1)
    total = count_result[0]["total"] if count_result else 0
    
    # Get merchants with aggregation
    merchants = await db.merchants.aggregate(pipeline).to_list(length=limit)
    
    return {
        "merchants": merchants,
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.get("/{merchant_id}", tags=["Admin - Merchants"])
async def get_merchant_detail(
    merchant_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get detailed information about a specific merchant.
    
    **Admin only**
    
    Args:
        merchant_id: The merchant ID
    
    Returns:
        Complete merchant details with statistics
    """
    try:
        obj_id = ObjectId(merchant_id)
    except Exception:
        obj_id = merchant_id
    
    merchant = await db.merchants.find_one({"_id": obj_id})
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    # Get merchant user info
    user_id = merchant.get("user_id")
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        user_obj_id = user_id
    
    user = await db.users.find_one({"_id": user_obj_id})
    
    # Get merchant statistics
    products_count = await db.products.count_documents({"merchant_id": str(obj_id)})
    orders_count = await db.orders.count_documents({"merchant_id": str(obj_id)})
    
    # Get order statistics
    pipeline = [
        {"$match": {"merchant_id": str(obj_id)}},
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$merchant_payout"},
                "completed_orders": {
                    "$sum": {"$cond": [{"$eq": ["$status", "delivered"]}, 1, 0]}
                }
            }
        }
    ]
    stats_results = await db.orders.aggregate(pipeline).to_list(None)
    stats = stats_results[0] if stats_results else {"total_revenue": 0, "completed_orders": 0}
    
    return {
        "id": str(merchant["_id"]),
        "user_id": merchant.get("user_id"),
        "user_email": user.get("email") if user else None,
        "shop_name": merchant.get("shop_name"),
        "description": merchant.get("description", ""),
        "logo": merchant.get("logo"),
        "location": merchant.get("location"),
        "rating": merchant.get("rating", 50.0),
        "total_sales": merchant.get("total_sales", 0),
        "verified": merchant.get("verified", False),
        "verified_at": merchant.get("verified_at"),
        "is_active": merchant.get("is_active", True),
        "created_at": merchant.get("created_at"),
        "updated_at": merchant.get("updated_at"),
        "statistics": {
            "products_count": products_count,
            "orders_count": orders_count,
            "completed_orders": stats.get("completed_orders", 0),
            "total_revenue": stats.get("total_revenue", 0)
        }
    }


@router.post("/{merchant_id}/verify", tags=["Admin - Merchants"])
async def verify_merchant(
    merchant_id: str,
    reason: Optional[str] = Query(None, description="Reason for verification"),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Verify a merchant account (validate shop).
    
    **Admin only**
    
    Args:
        merchant_id: The merchant ID
        reason: Optional reason for verification
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(merchant_id)
    except Exception:
        obj_id = merchant_id
    
    merchant = await db.merchants.find_one({"_id": obj_id})
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    if merchant.get("verified"):
        return {
            "message": "Merchant is already verified",
            "merchant_id": str(obj_id)
        }
    
    # Verify merchant
    result = await db.merchants.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "verified": True,
                "verified_at": datetime.utcnow(),
                "verified_by_admin_id": current_admin.get("_id"),
                "verification_reason": reason,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to verify merchant"
        )
    
    return {
        "message": "Merchant verified successfully",
        "merchant_id": str(obj_id),
        "verified_at": datetime.utcnow(),
        "reason": reason
    }


@router.post("/{merchant_id}/unverify", tags=["Admin - Merchants"])
async def unverify_merchant(
    merchant_id: str,
    reason: Optional[str] = Query(None, description="Reason for unverification"),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Unverify a merchant account (revoke verification).
    
    **Admin only**
    
    Args:
        merchant_id: The merchant ID
        reason: Optional reason for unverification
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(merchant_id)
    except Exception:
        obj_id = merchant_id
    
    merchant = await db.merchants.find_one({"_id": obj_id})
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    if not merchant.get("verified"):
        return {
            "message": "Merchant is not verified",
            "merchant_id": str(obj_id)
        }
    
    # Unverify merchant
    result = await db.merchants.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "verified": False,
                "unverified_at": datetime.utcnow(),
                "unverified_by_admin_id": current_admin.get("_id"),
                "unverification_reason": reason,
                "updated_at": datetime.utcnow()
            },
            "$unset": {
                "verified_at": "",
                "verified_by_admin_id": ""
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to unverify merchant"
        )
    
    return {
        "message": "Merchant unverified successfully",
        "merchant_id": str(obj_id),
        "unverified_at": datetime.utcnow(),
        "reason": reason
    }


@router.post("/{merchant_id}/disable", tags=["Admin - Merchants"])
async def disable_merchant(
    merchant_id: str,
    reason: Optional[str] = Query(None, description="Reason for disabling"),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Disable a merchant account (suspend shop operations).
    
    **Admin only**
    
    Args:
        merchant_id: The merchant ID
        reason: Optional reason for disabling
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(merchant_id)
    except Exception:
        obj_id = merchant_id
    
    merchant = await db.merchants.find_one({"_id": obj_id})
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    if not merchant.get("is_active"):
        return {
            "message": "Merchant account is already disabled",
            "merchant_id": str(obj_id)
        }
    
    # Disable merchant
    result = await db.merchants.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "is_active": False,
                "disabled_at": datetime.utcnow(),
                "disabled_by_admin_id": current_admin.get("_id"),
                "disable_reason": reason,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to disable merchant"
        )
    
    return {
        "message": "Merchant disabled successfully",
        "merchant_id": str(obj_id),
        "disabled_at": datetime.utcnow(),
        "reason": reason
    }


@router.post("/{merchant_id}/enable", tags=["Admin - Merchants"])
async def enable_merchant(
    merchant_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Enable a disabled merchant account (resume shop operations).
    
    **Admin only**
    
    Args:
        merchant_id: The merchant ID
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(merchant_id)
    except Exception:
        obj_id = merchant_id
    
    merchant = await db.merchants.find_one({"_id": obj_id})
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    if merchant.get("is_active"):
        return {
            "message": "Merchant account is already enabled",
            "merchant_id": str(obj_id)
        }
    
    # Enable merchant
    result = await db.merchants.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "is_active": True,
                "enabled_at": datetime.utcnow(),
                "enabled_by_admin_id": current_admin.get("_id"),
                "updated_at": datetime.utcnow()
            },
            "$unset": {
                "disabled_at": "",
                "disabled_by_admin_id": ""
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to enable merchant"
        )
    
    return {
        "message": "Merchant enabled successfully",
        "merchant_id": str(obj_id),
        "enabled_at": datetime.utcnow()
    }

@router.delete("/{merchant_id}", tags=["Admin - Merchants"])
async def delete_merchant(
    merchant_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    current_admin: dict = Depends(get_current_admin)
):
    """
    Delete a merchant and optionally deactivate the associated user.
    
    **Admin only**
    
    Args:
        merchant_id: The merchant ID (ObjectId as string)
    
    Returns:
        Confirmation message
    """
    # Convertir l'ID en ObjectId
    try:
        obj_id = ObjectId(merchant_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid merchant ID format"
        )
    
    # Vérifier que le marchand existe
    merchant = await db.merchants.find_one({"_id": obj_id})
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant not found"
        )
    
    # Récupérer l'user_id associé
    user_id = merchant.get("user_id")
    
    # Supprimer le document merchant
    delete_result = await db.merchants.delete_one({"_id": obj_id})
    if delete_result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete merchant"
        )
    
    # Optionnel : supprimer ou désactiver l'utilisateur associé
    if user_id:
        # Vous pouvez choisir de supprimer l'utilisateur ou de le désactiver
        # Ici, nous le désactivons (soft delete)
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "deleted_at": datetime.utcnow()}}
        )
    
    return {
        "message": "Merchant deleted successfully",
        "merchant_id": merchant_id,
        "deleted_at": datetime.utcnow()
    }