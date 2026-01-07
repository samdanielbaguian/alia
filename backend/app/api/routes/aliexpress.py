from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_db, get_current_merchant
from app.schemas.product import ProductImport, ProductResponse
from app.services.aliexpress_service import search_aliexpress, import_product, sync_product
from app.services.duplicate_detection import detect_duplicate_product
from datetime import datetime

router = APIRouter()


@router.post("/search")
async def search_aliexpress_products(
    query: str,
    current_user: dict = Depends(get_current_merchant)
):
    """
    Search for products on AliExpress.
    
    Returns a list of products available for import.
    """
    results = await search_aliexpress(query)
    return {
        "query": query,
        "results": results,
        "count": len(results)
    }


@router.post("/import", response_model=Dict)
async def import_aliexpress_product(
    import_request: ProductImport,
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Import a product from AliExpress/Alibaba.
    
    Before importing, checks for duplicate local products and alerts the merchant.
    """
    merchant_id = str(current_user["_id"])
    
    # Import the product
    imported_product = await import_product(
        source_product_id=import_request.source_product_id,
        merchant_id=merchant_id,
        margin_percentage=import_request.margin_percentage,
        source_platform=import_request.source_platform
    )
    
    # Check for duplicate local products
    duplicates = await detect_duplicate_product(
        title=imported_product["title"],
        description=imported_product["description"]
    )
    
    # Update stock if provided
    if import_request.stock > 0:
        from bson import ObjectId
        await db.products.update_one(
            {"_id": imported_product["_id"]},
            {"$set": {"stock": import_request.stock}}
        )
        imported_product["stock"] = import_request.stock
    
    return {
        "product": ProductResponse(
            id=str(imported_product["_id"]),
            title=imported_product["title"],
            description=imported_product["description"],
            price=imported_product["price"],
            original_price=imported_product.get("original_price"),
            images=imported_product["images"],
            stock=imported_product["stock"],
            category=imported_product["category"],
            merchant_id=imported_product["merchant_id"],
            is_imported=imported_product["is_imported"],
            source_platform=imported_product["source_platform"],
            source_product_id=imported_product["source_product_id"],
            delivery_days=imported_product["delivery_days"],
            age_restricted=imported_product["age_restricted"],
            location=imported_product.get("location"),
            sku=imported_product.get("sku"),
            size=imported_product.get("size"),
            color=imported_product.get("color"),
            weight=imported_product.get("weight"),
            dimensions=imported_product.get("dimensions"),
            material=imported_product.get("material"),
            created_at=imported_product["created_at"],
            updated_at=imported_product["updated_at"]
        ),
        "duplicate_warning": {
            "found": len(duplicates) > 0,
            "count": len(duplicates),
            "similar_products": duplicates[:5]  # Show top 5 most similar
        }
    }


@router.get("/sync/{product_id}")
async def sync_aliexpress_product(
    product_id: str,
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Manually sync a product's price and stock from AliExpress/Alibaba.
    """
    from bson import ObjectId
    
    # Verify product exists and belongs to merchant
    try:
        product = await db.products.find_one({"_id": ObjectId(product_id)})
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
    
    merchant_id = str(current_user["_id"])
    if product["merchant_id"] != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only sync your own products"
        )
    
    # Sync product
    result = await sync_product(product_id)
    
    return result
