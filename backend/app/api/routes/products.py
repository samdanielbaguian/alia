from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.api.deps import get_db, get_current_user, get_current_merchant
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.share import ProductShareResponse, ProductShareStatsResponse
from app.services.share_service import ShareService
from app.utils.helpers import format_document

router = APIRouter()


@router.get("", response_model=List[ProductResponse])
async def get_products(
    category: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    age_restricted: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get list of products with optional filters.
    
    Filters:
    - category: Filter by product category
    - price_min: Minimum price
    - price_max: Maximum price
    - age_restricted: Filter by age restriction
    """
    query = {}
    
    if category:
        query["category"] = category
    if price_min is not None:
        query.setdefault("price", {})["$gte"] = price_min
    if price_max is not None:
        query.setdefault("price", {})["$lte"] = price_max
    if age_restricted is not None:
        query["age_restricted"] = age_restricted
    
    products = await db.products.find(query).skip(skip).limit(limit).to_list(length=limit)
    
    return [
        ProductResponse(
            id=str(product["_id"]),
            title=product["title"],
            description=product["description"],
            price=product["price"],
            original_price=product.get("original_price"),
            images=product.get("images", []),
            stock=product["stock"],
            category=product["category"],
            merchant_id=product["merchant_id"],
            is_imported=product.get("is_imported", False),
            source_platform=product.get("source_platform"),
            source_product_id=product.get("source_product_id"),
            delivery_days=product.get("delivery_days", 7),
            age_restricted=product.get("age_restricted", False),
            location=product.get("location"),
            sku=product.get("sku"),
            size=product.get("size"),
            color=product.get("color"),
            weight=product.get("weight"),
            dimensions=product.get("dimensions"),
            material=product.get("material"),
            created_at=product["created_at"],
            updated_at=product.get("updated_at", product["created_at"])
        )
        for product in products
    ]


@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    q: str = Query(..., min_length=1),
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Search products by title, shop name, or category.
    
    Uses text search on product titles and descriptions.
    """
    query = {
        "$or": [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}}
        ]
    }
    
    if category:
        query["category"] = category
    
    products = await db.products.find(query).skip(skip).limit(limit).to_list(length=limit)
    
    return [
        ProductResponse(
            id=str(product["_id"]),
            title=product["title"],
            description=product["description"],
            price=product["price"],
            original_price=product.get("original_price"),
            images=product.get("images", []),
            stock=product["stock"],
            category=product["category"],
            merchant_id=product["merchant_id"],
            is_imported=product.get("is_imported", False),
            source_platform=product.get("source_platform"),
            source_product_id=product.get("source_product_id"),
            delivery_days=product.get("delivery_days", 7),
            age_restricted=product.get("age_restricted", False),
            location=product.get("location"),
            sku=product.get("sku"),
            size=product.get("size"),
            color=product.get("color"),
            weight=product.get("weight"),
            dimensions=product.get("dimensions"),
            material=product.get("material"),
            created_at=product["created_at"],
            updated_at=product.get("updated_at", product["created_at"])
        )
        for product in products
    ]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a single product by ID."""
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
    
    return ProductResponse(
        id=str(product["_id"]),
        title=product["title"],
        description=product["description"],
        price=product["price"],
        original_price=product.get("original_price"),
        images=product.get("images", []),
        stock=product["stock"],
        category=product["category"],
        merchant_id=product["merchant_id"],
        is_imported=product.get("is_imported", False),
        source_platform=product.get("source_platform"),
        source_product_id=product.get("source_product_id"),
        delivery_days=product.get("delivery_days", 7),
        age_restricted=product.get("age_restricted", False),
        location=product.get("location"),
        sku=product.get("sku"),
        size=product.get("size"),
        color=product.get("color"),
        weight=product.get("weight"),
        dimensions=product.get("dimensions"),
        material=product.get("material"),
        created_at=product["created_at"],
        updated_at=product.get("updated_at", product["created_at"])
    )


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new product (merchants only).
    
    The product will be associated with the current merchant.
    """
    merchant_id = str(current_user["_id"])
    
    product_data = {
        "title": product.title,
        "description": product.description,
        "price": product.price,
        "images": product.images,
        "stock": product.stock,
        "category": product.category,
        "merchant_id": merchant_id,
        "is_imported": False,
        "delivery_days": product.delivery_days,
        "age_restricted": product.age_restricted,
        "location": product.location.dict() if product.location else None,
        "sku": product.sku,
        "size": product.size,
        "color": product.color,
        "weight": product.weight,
        "dimensions": product.dimensions,
        "material": product.material,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.products.insert_one(product_data)
    product_data["_id"] = result.inserted_id
    
    return ProductResponse(
        id=str(product_data["_id"]),
        title=product_data["title"],
        description=product_data["description"],
        price=product_data["price"],
        original_price=product_data.get("original_price"),
        images=product_data["images"],
        stock=product_data["stock"],
        category=product_data["category"],
        merchant_id=product_data["merchant_id"],
        is_imported=product_data["is_imported"],
        source_platform=product_data.get("source_platform"),
        source_product_id=product_data.get("source_product_id"),
        delivery_days=product_data["delivery_days"],
        age_restricted=product_data["age_restricted"],
        location=product_data.get("location"),
        sku=product_data.get("sku"),
        size=product_data.get("size"),
        color=product_data.get("color"),
        weight=product_data.get("weight"),
        dimensions=product_data.get("dimensions"),
        material=product_data.get("material"),
        created_at=product_data["created_at"],
        updated_at=product_data["updated_at"]
    )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update a product (merchants only, own products only).
    """
    merchant_id = str(current_user["_id"])
    
    try:
        existing_product = await db.products.find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if existing_product["merchant_id"] != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own products"
        )
    
    # Build update data
    update_data = {"updated_at": datetime.utcnow()}
    
    if product_update.title is not None:
        update_data["title"] = product_update.title
    if product_update.description is not None:
        update_data["description"] = product_update.description
    if product_update.price is not None:
        update_data["price"] = product_update.price
    if product_update.images is not None:
        update_data["images"] = product_update.images
    if product_update.stock is not None:
        update_data["stock"] = product_update.stock
    if product_update.category is not None:
        update_data["category"] = product_update.category
    if product_update.delivery_days is not None:
        update_data["delivery_days"] = product_update.delivery_days
    if product_update.age_restricted is not None:
        update_data["age_restricted"] = product_update.age_restricted
    if product_update.location is not None:
        update_data["location"] = product_update.location.dict()
    if product_update.sku is not None:
        update_data["sku"] = product_update.sku
    if product_update.size is not None:
        update_data["size"] = product_update.size
    if product_update.color is not None:
        update_data["color"] = product_update.color
    if product_update.weight is not None:
        update_data["weight"] = product_update.weight
    if product_update.dimensions is not None:
        update_data["dimensions"] = product_update.dimensions
    if product_update.material is not None:
        update_data["material"] = product_update.material
    
    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": update_data}
    )
    
    # Fetch updated product
    updated_product = await db.products.find_one({"_id": ObjectId(product_id)})
    
    return ProductResponse(
        id=str(updated_product["_id"]),
        title=updated_product["title"],
        description=updated_product["description"],
        price=updated_product["price"],
        original_price=updated_product.get("original_price"),
        images=updated_product["images"],
        stock=updated_product["stock"],
        category=updated_product["category"],
        merchant_id=updated_product["merchant_id"],
        is_imported=updated_product.get("is_imported", False),
        source_platform=updated_product.get("source_platform"),
        source_product_id=updated_product.get("source_product_id"),
        delivery_days=updated_product["delivery_days"],
        age_restricted=updated_product["age_restricted"],
        location=updated_product.get("location"),
        sku=updated_product.get("sku"),
        size=updated_product.get("size"),
        color=updated_product.get("color"),
        weight=updated_product.get("weight"),
        dimensions=updated_product.get("dimensions"),
        material=updated_product.get("material"),
        created_at=updated_product["created_at"],
        updated_at=updated_product["updated_at"]
    )


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Delete a product (merchants only, own products only).
    """
    merchant_id = str(current_user["_id"])
    
    try:
        existing_product = await db.products.find_one({"_id": ObjectId(product_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid product ID"
        )
    
    if not existing_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check ownership
    if existing_product["merchant_id"] != merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own products"
        )
    
    await db.products.delete_one({"_id": ObjectId(product_id)})
    
    return None


@router.post("/{product_id}/share", response_model=ProductShareResponse)
async def share_product(
    product_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Generate a shareable link for a product.
    
    Returns:
    - Direct share link
    - WhatsApp pre-filled message link
    - QR code (base64 encoded PNG)
    """
    user_id = str(current_user["_id"])
    
    return await ShareService.create_product_share(
        product_id=product_id,
        user_id=user_id,
        db=db
    )


@router.get("/share/{share_code}")
async def view_shared_product(
    share_code: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    View a shared product (public endpoint).
    
    No authentication required.
    Increments view count and redirects to product detail page.
    """
    product = await ShareService.get_shared_product(share_code, db)
    
    # In a real app, this would redirect to the frontend product page
    # For now, return the product details
    return ProductResponse(
        id=str(product["_id"]),
        title=product["title"],
        description=product["description"],
        price=product["price"],
        original_price=product.get("original_price"),
        images=product.get("images", []),
        stock=product["stock"],
        category=product["category"],
        merchant_id=product["merchant_id"],
        is_imported=product.get("is_imported", False),
        source_platform=product.get("source_platform"),
        source_product_id=product.get("source_product_id"),
        delivery_days=product.get("delivery_days", 7),
        age_restricted=product.get("age_restricted", False),
        location=product.get("location"),
        sku=product.get("sku"),
        size=product.get("size"),
        color=product.get("color"),
        weight=product.get("weight"),
        dimensions=product.get("dimensions"),
        material=product.get("material"),
        created_at=product["created_at"],
        updated_at=product.get("updated_at", product["created_at"])
    )


@router.get("/{product_id}/share/stats", response_model=ProductShareStatsResponse)
async def get_product_share_stats(
    product_id: str,
    current_user: dict = Depends(get_current_merchant),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get share statistics for a product (merchant only).
    
    Returns:
    - Total shares
    - Views from shares
    - Conversions from shares
    - Conversion rate
    """
    merchant_id = str(current_user["_id"])
    
    return await ShareService.get_product_share_stats(
        product_id=product_id,
        merchant_id=merchant_id,
        db=db
    )
