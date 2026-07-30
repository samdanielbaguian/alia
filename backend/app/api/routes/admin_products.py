"""
Admin routes for product management.

Provides administrative endpoints for:
- Listing all products with filtering and pagination
- Viewing product details
- Featuring/unfeaturing products
- Deleting products
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.api.deps import get_db, get_current_admin

router = APIRouter()


@router.get("", tags=["Admin - Products"])
async def list_all_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    merchant_id: Optional[str] = Query(None, description="Filter by merchant ID"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    search: Optional[str] = Query(None, description="Search by product title"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    List all products with optional filtering and pagination.
    
    **Admin only**
    
    Args:
        category: Filter by product category
        merchant_id: Filter by merchant ID
        is_featured: Filter by featured status
        search: Search by product title
        limit: Maximum number of results (1-100)
        skip: Number of results to skip (for pagination)
    
    Returns:
        List of products with total count
    """
    query = {}
    
    # Add category filter
    if category:
        query["category"] = category
    
    # Add merchant filter
    if merchant_id:
        try:
            query["merchant_id"] = ObjectId(merchant_id)
        except Exception:
            query["merchant_id"] = merchant_id
    
    # Add featured filter
    if is_featured is not None:
        query["is_featured"] = is_featured
    
    # Add search filter
    if search:
        query["title"] = {"$regex": search, "$options": "i"}
    
    # Count total
    total = await db.products.count_documents(query)
    
    # Get products
    products = await db.products.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    
    return {
        "products": [
            {
                "id": str(product["_id"]),
                "title": product.get("title"),
                "price": product.get("price"),
                "stock": product.get("stock", 0),
                "category": product.get("category"),
                "merchant_id": product.get("merchant_id"),
                "is_featured": product.get("is_featured", False),
                "rating": product.get("rating", 0),
                "created_at": product.get("created_at"),
                "updated_at": product.get("updated_at")
            }
            for product in products
        ],
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.get("/{product_id}", tags=["Admin - Products"])
async def get_product_detail(
    product_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get detailed information about a specific product.
    
    **Admin only**
    
    Args:
        product_id: The product ID
    
    Returns:
        Complete product details
    """
    try:
        obj_id = ObjectId(product_id)
    except Exception:
        obj_id = product_id
    
    product = await db.products.find_one({"_id": obj_id})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Get sales statistics
    sales_count = await db.orders.count_documents(
        {"items._id": obj_id}
    )
    
    return {
        "id": str(product["_id"]),
        "title": product.get("title"),
        "description": product.get("description"),
        "price": product.get("price"),
        "cost_price": product.get("cost_price"),
        "stock": product.get("stock", 0),
        "category": product.get("category"),
        "merchant_id": product.get("merchant_id"),
        "images": product.get("images", []),
        "is_featured": product.get("is_featured", False),
        "rating": product.get("rating", 0),
        "reviews_count": product.get("reviews_count", 0),
        "created_at": product.get("created_at"),
        "updated_at": product.get("updated_at"),
        "sales_count": sales_count,
        "source_product_id": product.get("source_product_id")
    }


@router.post("/{product_id}/feature", tags=["Admin - Products"])
async def feature_product(
    product_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Feature a product (increase visibility).
    
    **Admin only**
    
    Args:
        product_id: The product ID
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(product_id)
    except Exception:
        obj_id = product_id
    
    product = await db.products.find_one({"_id": obj_id})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if product.get("is_featured"):
        return {
            "message": "Product is already featured",
            "product_id": str(obj_id)
        }
    
    # Feature product
    result = await db.products.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "is_featured": True,
                "featured_at": datetime.utcnow(),
                "featured_by_admin_id": current_admin.get("_id"),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to feature product"
        )
    
    return {
        "message": "Product featured successfully",
        "product_id": str(obj_id),
        "featured_at": datetime.utcnow()
    }


@router.post("/{product_id}/unfeature", tags=["Admin - Products"])
async def unfeature_product(
    product_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Unfeature a product (reduce visibility).
    
    **Admin only**
    
    Args:
        product_id: The product ID
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(product_id)
    except Exception:
        obj_id = product_id
    
    product = await db.products.find_one({"_id": obj_id})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if not product.get("is_featured"):
        return {
            "message": "Product is not featured",
            "product_id": str(obj_id)
        }
    
    # Unfeature product
    result = await db.products.update_one(
        {"_id": obj_id},
        {
            "$set": {
                "is_featured": False,
                "unfeatured_at": datetime.utcnow(),
                "unfeatured_by_admin_id": current_admin.get("_id"),
                "updated_at": datetime.utcnow()
            },
            "$unset": {
                "featured_at": "",
                "featured_by_admin_id": ""
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to unfeature product"
        )
    
    return {
        "message": "Product unfeatured successfully",
        "product_id": str(obj_id),
        "unfeatured_at": datetime.utcnow()
    }


@router.delete("/{product_id}", tags=["Admin - Products"])
async def delete_product(
    product_id: str,
    current_admin: dict = Depends(get_current_admin),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a product (hard delete - cannot be recovered).
    
    **Admin only** - Use with extreme caution!
    
    Args:
        product_id: The product ID to delete
    
    Returns:
        Confirmation message
    """
    try:
        obj_id = ObjectId(product_id)
    except Exception:
        obj_id = product_id
    
    product = await db.products.find_one({"_id": obj_id})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Store product data in deleted_products collection for audit trail
    deleted_product = product.copy()
    deleted_product["deleted_at"] = datetime.utcnow()
    deleted_product["deleted_by_admin_id"] = current_admin.get("_id")
    
    await db.deleted_products.insert_one(deleted_product)
    
    # Delete from main collection
    result = await db.products.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete product"
        )
    
    return {
        "message": "Product deleted successfully",
        "product_id": str(obj_id),
        "deleted_at": datetime.utcnow()
    }
