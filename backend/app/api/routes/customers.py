from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.schemas.wishlist import (
    AddToWishlistRequest,
    WishlistResponse
)
from app.schemas.user import UserResponse, UserUpdate
from app.services.wishlist_service import WishlistService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_customer_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the current customer's profile.
    
    Returns complete user information including preferences and location.
    """
    return UserResponse(
        id=str(current_user["_id"]),
        email=current_user["email"],
        role=current_user["role"],
        age=current_user.get("age"),
        preferences=current_user.get("preferences", []),
        good_rate=current_user.get("good_rate", 50.0),
        location=current_user.get("location"),
        created_at=current_user["created_at"]
    )


@router.put("/me", response_model=UserResponse)
async def update_customer_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update the current customer's profile.
    
    Allows updating:
    - age
    - preferences
    - location
    """
    user_id = str(current_user["_id"])
    
    # Build update document
    update_dict = {}
    if update_data.age is not None:
        update_dict["age"] = update_data.age
    if update_data.preferences is not None:
        update_dict["preferences"] = update_data.preferences
    if update_data.location is not None:
        update_dict["location"] = update_data.location.model_dump()
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    update_dict["updated_at"] = datetime.utcnow()
    
    # Update user
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_dict}
    )
    
    # Fetch updated user
    updated_user = await db.users.find_one({"_id": ObjectId(user_id)})
    
    return UserResponse(
        id=str(updated_user["_id"]),
        email=updated_user["email"],
        role=updated_user["role"],
        age=updated_user.get("age"),
        preferences=updated_user.get("preferences", []),
        good_rate=updated_user.get("good_rate", 50.0),
        location=updated_user.get("location"),
        created_at=updated_user["created_at"]
    )


@router.get("/me/wishlist", response_model=WishlistResponse)
async def get_wishlist(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the current user's wishlist with full product details.
    
    Returns:
    - All wishlist items with current product information
    - Total items count
    """
    user_id = str(current_user["_id"])
    return await WishlistService.get_wishlist(user_id, db)


@router.post("/me/wishlist", status_code=status.HTTP_201_CREATED)
async def add_to_wishlist(
    request: AddToWishlistRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Add a product to the current user's wishlist.
    
    Validates:
    - Product exists
    - Not already in wishlist
    """
    user_id = str(current_user["_id"])
    return await WishlistService.add_to_wishlist(user_id, request.product_id, db)


@router.delete("/me/wishlist/{product_id}")
async def remove_from_wishlist(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Remove a product from the current user's wishlist.
    """
    user_id = str(current_user["_id"])
    return await WishlistService.remove_from_wishlist(user_id, product_id, db)
