"""
Admin routes for user management.

Provides administrative endpoints for:
- Listing all users with filtering by role
- Viewing user details
- Changing user roles
- Suspending/activating users
- Deleting users
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.deps import get_db, get_current_admin

router = APIRouter()


@router.get("", tags=["Admin - Users"])
async def list_all_users(
    role_filter: Optional[str] = Query(None, description="Filter by role: buyer, merchant, admin"),
    search: Optional[str] = Query(None, description="Search by email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all users with optional filtering and pagination.
    
    **Admin only**
    
    Args:
        role_filter: Filter by user role (buyer, merchant, admin)
        search: Search by email address
        is_active: Filter by active/inactive status
        limit: Maximum number of results (1-100)
        skip: Number of results to skip (for pagination)
    
    Returns:
        List of users with total count
    """
    query = {}
    
    # Add role filter
    if role_filter:
        query["role"] = role_filter
    
    # Add email search
    if search:
        query["email"] = {"$regex": search, "$options": "i"}
    
    # Add active status filter
    if is_active is not None:
        query["is_active"] = is_active
    
    # Count total
    total = await db.users.count_documents(query)
    
    # Get users
    users = await db.users.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    return {
        "users": [
            {
                "id": str(user["_id"]),
                "email": user.get("email"),
                "role": user.get("role"),
                "age": user.get("age"),
                "is_active": user.get("is_active", True),
                "good_rate": user.get("good_rate", 50.0),
                "created_at": user.get("created_at"),
                "updated_at": user.get("updated_at")
            }
            for user in users
        ],
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.get("/{user_id}", tags=["Admin - Users"])
async def get_user_detail(
    user_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get detailed information about a specific user.
    
    **Admin only**
    
    Args:
        user_id: The user ID
    
    Returns:
        Complete user details
    """
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        obj_id = user_id
    
    user = await db.users.find_one({"_id": obj_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get related data
    orders_count = await db.orders.count_documents({"buyer_id": str(obj_id)})
    merchant_profile = await db.merchants.find_one({"user_id": str(obj_id)})
    
    return {
        "id": str(user["_id"]),
        "email": user.get("email"),
        "role": user.get("role"),
        "age": user.get("age"),
        "preferences": user.get("preferences", []),
        "good_rate": user.get("good_rate", 50.0),
        "is_active": user.get("is_active", True),
        "location": user.get("location"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
        "orders_count": orders_count,
        "merchant_profile": {
            "id": str(merchant_profile["_id"]),
            "shop_name": merchant_profile.get("shop_name"),
            "verified": merchant_profile.get("verified", False),
            "rating": merchant_profile.get("rating", 50.0)
        } if merchant_profile else None
    }


@router.patch("/{user_id}/role", tags=["Admin - Users"])
async def change_user_role(
    user_id: str,
    new_role: str = Query(..., description="New role: buyer, merchant, admin"),
    reason: Optional[str] = Query(None, description="Reason for role change"),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Change a user's role.
    
    **Admin only**
    
    Args:
        user_id: The user ID
        new_role: The new role (buyer, merchant, admin)
        reason: Optional reason for the change
    
    Returns:
        Updated user with new role
    """
    valid_roles = ["buyer", "merchant", "admin"]
    if new_role not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join(valid_roles)}"
        )
    
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        obj_id = user_id
    
    user = await db.users.find_one({"_id": obj_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    old_role = user.get("role")
    
    # If upgrading to merchant, create merchant profile
    if new_role == "merchant" and old_role != "merchant":
        merchant_exists = await db.merchants.find_one({"user_id": str(obj_id)})
        if not merchant_exists:
            merchant_data = {
                "user_id": str(obj_id),
                "shop_name": f"Store - {user.get('email')}",
                "rating": 50.0,
                "total_sales": 0,
                "verified": False,
                "created_at": datetime.utcnow()
            }
            await db.merchants.insert_one(merchant_data)
    
    # Update user role
    result = await db.users.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "role": new_role,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user role"
        )
    
    return {
        "message": f"User role updated to {new_role}",
        "user_id": str(obj_id),
        "previous_role": old_role,
        "new_role": new_role,
        "reason": reason
    }


@router.post("/{user_id}/suspend", tags=["Admin - Users"])
async def suspend_user(
    user_id: str,
    reason: Optional[str] = Query(None, description="Reason for suspension"),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Suspend (deactivate) a user account.
    
    **Admin only**
    
    Args:
        user_id: The user ID
        reason: Optional reason for suspension
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        obj_id = user_id
    
    user = await db.users.find_one({"_id": obj_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.get("is_active", True):
        return {
            "message": "User is already suspended",
            "user_id": str(obj_id)
        }
    
    # Suspend user
    result = await db.users.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "is_active": False,
                "suspended_at": datetime.utcnow(),
                "suspension_reason": reason,
                "suspended_by_admin_id": current_admin.get("_id"),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to suspend user"
        )
    
    return {
        "message": "User suspended successfully",
        "user_id": str(obj_id),
        "suspended_at": datetime.utcnow(),
        "reason": reason
    }


@router.post("/{user_id}/activate", tags=["Admin - Users"])
async def activate_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Activate a suspended user account.
    
    **Admin only**
    
    Args:
        user_id: The user ID
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        obj_id = user_id
    
    user = await db.users.find_one({"_id": obj_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.get("is_active", True):
        return {
            "message": "User is already active",
            "user_id": str(obj_id)
        }
    
    # Activate user
    result = await db.users.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "is_active": True,
                "activated_at": datetime.utcnow(),
                "activated_by_admin_id": current_admin.get("_id"),
                "updated_at": datetime.utcnow()
            },
            "$unset": {
                "suspended_at": "",
                "suspension_reason": ""
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to activate user"
        )
    
    return {
        "message": "User activated successfully",
        "user_id": str(obj_id),
        "activated_at": datetime.utcnow()
    }


@router.delete("/{user_id}", tags=["Admin - Users"])
async def delete_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a user account (hard delete - cannot be recovered).
    
    **Admin only** - Use with extreme caution!
    
    Args:
        user_id: The user ID to delete
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        obj_id = user_id
    
    user = await db.users.find_one({"_id": obj_id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Store user data in deleted_users collection for audit trail
    deleted_user = user.copy()
    deleted_user["deleted_at"] = datetime.utcnow()
    deleted_user["deleted_by_admin_id"] = current_admin.get("_id")
    
    await db.deleted_users.insert_one(deleted_user)
    
    # Delete from main collection
    result = await db.users.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )
    
    return {
        "message": "User deleted successfully",
        "user_id": str(obj_id),
        "deleted_at": datetime.utcnow()
    }
