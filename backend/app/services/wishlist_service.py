from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import List
import logging

logger = logging.getLogger(__name__)


class WishlistService:
    """Service for managing user wishlists."""
    
    @staticmethod
    async def add_to_wishlist(
        user_id: str,
        product_id: str,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """
        Add a product to user's wishlist.
        
        Args:
            user_id: User ID
            product_id: Product ID to add
            db: Database connection
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If product doesn't exist or already in wishlist
        """
        # Validate product exists
        try:
            product = await db.products.find_one({"_id": ObjectId(product_id)})
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid product ID format"
            )
            
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check if already in wishlist
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        wishlist = user.get("wishlist", [])
        
        # Check if product already in wishlist
        for item in wishlist:
            if item.get("product_id") == product_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Product already in wishlist"
                )
        
        # Add to wishlist
        wishlist_item = {
            "product_id": product_id,
            "added_at": datetime.utcnow()
        }
        
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$push": {"wishlist": wishlist_item},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        logger.info(f"User {user_id} added product {product_id} to wishlist")
        
        return {"message": "Product added to wishlist successfully"}
    
    @staticmethod
    async def get_wishlist(
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """
        Get user's wishlist with full product details.
        
        Args:
            user_id: User ID
            db: Database connection
            
        Returns:
            Wishlist with product details
        """
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        wishlist = user.get("wishlist", [])
        
        if not wishlist:
            return {
                "items": [],
                "total_items": 0
            }
        
        # Fetch full product details
        items = []
        for item in wishlist:
            try:
                product = await db.products.find_one({"_id": ObjectId(item["product_id"])})
                if product:
                    items.append({
                        "product_id": str(product["_id"]),
                        "title": product.get("title", ""),
                        "price": product.get("price", 0),
                        "images": product.get("images", []),
                        "stock": product.get("stock", 0),
                        "merchant_id": product.get("merchant_id", ""),
                        "added_at": item.get("added_at", datetime.utcnow())
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch product {item['product_id']}: {e}")
                continue
        
        return {
            "items": items,
            "total_items": len(items)
        }
    
    @staticmethod
    async def remove_from_wishlist(
        user_id: str,
        product_id: str,
        db: AsyncIOMotorDatabase
    ) -> dict:
        """
        Remove a product from user's wishlist.
        
        Args:
            user_id: User ID
            product_id: Product ID to remove
            db: Database connection
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If product not in wishlist
        """
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        wishlist = user.get("wishlist", [])
        
        # Check if product in wishlist
        found = False
        for item in wishlist:
            if item.get("product_id") == product_id:
                found = True
                break
        
        if not found:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not in wishlist"
            )
        
        # Remove from wishlist
        await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {
                "$pull": {"wishlist": {"product_id": product_id}},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        logger.info(f"User {user_id} removed product {product_id} from wishlist")
        
        return {"message": "Product removed from wishlist successfully"}
