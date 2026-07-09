from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from app.api.deps import get_current_user, get_db
from app.schemas.user import UserUpdate

router = APIRouter()


class WishlistRequest(BaseModel):
    product_id: str


@router.get("/me")
async def get_customer_profile(
    current_user: dict = Depends(get_current_user)
):
    """Get the current customer profile."""
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "role": current_user["role"],
        "age": current_user.get("age"),
        "preferences": current_user.get("preferences", []),
        "good_rate": current_user.get("good_rate", 50.0),
        "location": current_user.get("location"),
        "wishlist": current_user.get("wishlist", []),
        "created_at": current_user["created_at"]
    }


@router.put("/me")
async def update_customer_profile(
    request: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update customer profile fields."""
    update_fields = request.model_dump(exclude_none=True)
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update"
        )

    update_fields["updated_at"] = datetime.utcnow()
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": update_fields}
    )

    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    return {
        "id": str(updated_user["_id"]),
        "email": updated_user["email"],
        "role": updated_user["role"],
        "age": updated_user.get("age"),
        "preferences": updated_user.get("preferences", []),
        "good_rate": updated_user.get("good_rate", 50.0),
        "location": updated_user.get("location"),
        "wishlist": updated_user.get("wishlist", []),
        "created_at": updated_user["created_at"]
    }


@router.get("/me/wishlist")
async def get_my_wishlist(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get wishlist products for current customer."""
    wishlist_ids = current_user.get("wishlist", [])
    object_ids = []
    for product_id in wishlist_ids:
        try:
            object_ids.append(ObjectId(product_id))
        except Exception:
            continue

    if not object_ids:
        return {"wishlist": [], "total": 0}

    products = await db.products.find({"_id": {"$in": object_ids}}).to_list(length=len(object_ids))
    ordered_products = {str(product["_id"]): product for product in products}

    return {
        "wishlist": [
            {
                "id": product_id,
                "title": ordered_products[product_id]["title"],
                "price": ordered_products[product_id]["price"],
                "images": ordered_products[product_id].get("images", []),
                "stock": ordered_products[product_id].get("stock", 0),
                "merchant_id": ordered_products[product_id].get("merchant_id")
            }
            for product_id in wishlist_ids
            if product_id in ordered_products
        ],
        "total": len([product_id for product_id in wishlist_ids if product_id in ordered_products])
    }


@router.post("/me/wishlist")
async def add_to_wishlist(
    request: WishlistRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Add a product to customer wishlist."""
    try:
        product = await db.products.find_one({"_id": ObjectId(request.product_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$addToSet": {"wishlist": request.product_id}}
    )

    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    return {
        "message": "Product added to wishlist",
        "wishlist": updated_user.get("wishlist", [])
    }


@router.delete("/me/wishlist/{product_id}")
async def remove_from_wishlist(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Remove a product from customer wishlist."""
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$pull": {"wishlist": product_id}}
    )

    updated_user = await db.users.find_one({"_id": current_user["_id"]})
    return {
        "message": "Product removed from wishlist",
        "wishlist": updated_user.get("wishlist", [])
    }
