"""
Admin User Management Routes
Endpoints for admin to manage users (view, edit, suspend, ban, reset passwords)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr

from app.api.deps import get_db, get_current_admin
from app.core.security import get_password_hash

router = APIRouter()


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    age: Optional[int] = None
    preferences: Optional[List[str]] = None
    good_rate: Optional[float] = None


class PasswordResetRequest(BaseModel):
    new_password: str


class UserStatusRequest(BaseModel):
    is_suspended: bool
    reason: Optional[str] = None


class UserBanRequest(BaseModel):
    is_banned: bool
    reason: Optional[str] = None


@router.get("")
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role: merchant, buyer, admin"),
    is_suspended: Optional[bool] = Query(None, description="Filter by suspension status"),
    is_banned: Optional[bool] = Query(None, description="Filter by ban status"),
    search: Optional[str] = Query(None, description="Search by email"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """List all users with filters and pagination."""
    query = {}
    
    if role:
        query["role"] = role
    if is_suspended is not None:
        query["is_suspended"] = is_suspended
    if is_banned is not None:
        query["is_banned"] = is_banned
    if search:
        query["email"] = {"$regex": search, "$options": "i"}
    
    users = await db.users.find(query).skip(skip).limit(limit).to_list(limit)
    total = await db.users.count_documents(query)
    
    # Remove sensitive data
    for user in users:
        user["_id"] = str(user["_id"])
        user.pop("password_hash", None)
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Get detailed user information."""
    try:
        user = await db.users.find_one({"_id": ObjectId(user_id)})
    except Exception:
        user = await db.users.find_one({"_id": user_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user["_id"] = str(user["_id"])
    user.pop("password_hash", None)
    
    # Get additional info based on role
    if user.get("role") == "merchant":
        merchant = await db.merchants.find_one({"user_id": str(user["_id"])})
        if merchant:
            merchant["_id"] = str(merchant["_id"])
            user["merchant_profile"] = merchant
    
    # Get user's orders count
    orders_count = await db.orders.count_documents({"user_id": str(user["_id"])})
    user["orders_count"] = orders_count
    
    return user


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Update user information."""
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        user_obj_id = user_id
    
    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build update data
    update_data = {}
    if request.email is not None:
        # Check if email is already taken
        existing = await db.users.find_one({"email": request.email, "_id": {"$ne": user_obj_id}})
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
        update_data["email"] = request.email
    
    if request.role is not None:
        if request.role not in ["merchant", "buyer", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role"
            )
        update_data["role"] = request.role
    
    if request.age is not None:
        update_data["age"] = request.age
    if request.preferences is not None:
        update_data["preferences"] = request.preferences
    if request.good_rate is not None:
        update_data["good_rate"] = request.good_rate
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by"] = str(admin["_id"])
    
    await db.users.update_one({"_id": user_obj_id}, {"$set": update_data})
    
    return {"ok": True, "user_id": user_id, "updated_fields": list(update_data.keys())}


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    request: PasswordResetRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Reset user password (admin only)."""
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        user_obj_id = user_id
    
    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Hash new password
    new_password_hash = get_password_hash(request.new_password)
    
    await db.users.update_one(
        {"_id": user_obj_id},
        {
            "$set": {
                "password_hash": new_password_hash,
                "password_reset_at": datetime.utcnow(),
                "password_reset_by": str(admin["_id"])
            }
        }
    )
    
    return {"ok": True, "user_id": user_id, "message": "Password reset successfully"}


@router.post("/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    request: UserStatusRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Suspend or unsuspend a user."""
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        user_obj_id = user_id
    
    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = {
        "is_suspended": request.is_suspended,
        "suspended_at": datetime.utcnow() if request.is_suspended else None,
        "suspended_by": str(admin["_id"]) if request.is_suspended else None,
        "suspension_reason": request.reason if request.is_suspended else None,
        "updated_at": datetime.utcnow()
    }
    
    await db.users.update_one({"_id": user_obj_id}, {"$set": update_data})
    
    action = "suspended" if request.is_suspended else "unsuspended"
    return {"ok": True, "user_id": user_id, "action": action}


@router.post("/{user_id}/ban")
async def ban_user(
    user_id: str,
    request: UserBanRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Ban or unban a user."""
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        user_obj_id = user_id
    
    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = {
        "is_banned": request.is_banned,
        "banned_at": datetime.utcnow() if request.is_banned else None,
        "banned_by": str(admin["_id"]) if request.is_banned else None,
        "ban_reason": request.reason if request.is_banned else None,
        "updated_at": datetime.utcnow()
    }
    
    await db.users.update_one({"_id": user_obj_id}, {"$set": update_data})
    
    action = "banned" if request.is_banned else "unbanned"
    return {"ok": True, "user_id": user_id, "action": action}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Delete a user (permanent action)."""
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        user_obj_id = user_id
    
    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deleting admin accounts
    if user.get("role") == "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete admin users"
        )
    
    # Delete related data
    await db.users.delete_one({"_id": user_obj_id})
    await db.merchants.delete_many({"user_id": str(user_obj_id)})
    
    # Note: Consider soft-deleting orders or reassigning them
    # await db.orders.update_many({"user_id": str(user_obj_id)}, {"$set": {"user_deleted": True}})
    
    return {"ok": True, "user_id": user_id, "message": "User deleted successfully"}


@router.get("/{user_id}/activity")
async def get_user_activity(
    user_id: str,
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Get user activity logs (orders, logins, etc.)."""
    try:
        user_obj_id = ObjectId(user_id)
    except Exception:
        user_obj_id = user_id
    
    user = await db.users.find_one({"_id": user_obj_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's orders
    orders = await db.orders.find({"user_id": str(user_obj_id)}).sort("created_at", -1).limit(limit).to_list(limit)
    for order in orders:
        order["_id"] = str(order["_id"])
    
    # Get merchant products if applicable
    products = []
    if user.get("role") == "merchant":
        products = await db.products.find({"merchant_id": str(user_obj_id)}).sort("created_at", -1).limit(limit).to_list(limit)
        for product in products:
            product["_id"] = str(product["_id"])
    
    return {
        "user_id": user_id,
        "orders": orders,
        "products": products,
        "orders_count": len(orders),
        "products_count": len(products)
    }
