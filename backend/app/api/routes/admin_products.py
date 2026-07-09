"""
Admin Product Management Routes
Endpoints for admin to manage products (approve, reject, moderate, bulk operations)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

from app.api.deps import get_db, get_current_admin

router = APIRouter()


class ProductApprovalRequest(BaseModel):
    is_approved: bool
    reason: Optional[str] = None


class ProductUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None


class BulkApprovalRequest(BaseModel):
    product_ids: List[str]
    is_approved: bool
    reason: Optional[str] = None


@router.get("")
async def list_products(
    status_filter: Optional[str] = Query(None, description="Filter: pending, approved, rejected"),
    is_active: Optional[bool] = Query(None),
    merchant_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="Search by title"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """List all products with filters."""
    query = {}
    
    if status_filter:
        if status_filter == "pending":
            query["is_approved"] = False
            query["is_rejected"] = {"$ne": True}
        elif status_filter == "approved":
            query["is_approved"] = True
        elif status_filter == "rejected":
            query["is_rejected"] = True
    
    if is_active is not None:
        query["is_active"] = is_active
    if merchant_id:
        query["merchant_id"] = merchant_id
    if category:
        query["category"] = category
    if search:
        query["title"] = {"$regex": search, "$options": "i"}
    
    products = await db.products.find(query).skip(skip).limit(limit).to_list(limit)
    total = await db.products.count_documents(query)
    
    for product in products:
        product["_id"] = str(product["_id"])
        if "merchant_id" in product:
            # Get merchant name
            try:
                merchant = await db.merchants.find_one({"user_id": product["merchant_id"]})
                if merchant:
                    product["merchant_name"] = merchant.get("shop_name", "Unknown")
            except:
                pass
    
    return {
        "products": products,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/pending")
async def list_pending_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """List products pending approval."""
    query = {
        "is_approved": False,
        "is_rejected": {"$ne": True}
    }
    
    products = await db.products.find(query).skip(skip).limit(limit).to_list(limit)
    total = await db.products.count_documents(query)
    
    for product in products:
        product["_id"] = str(product["_id"])
    
    return {
        "products": products,
        "total": total
    }


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Get detailed product information."""
    try:
        product = await db.products.find_one({"_id": ObjectId(product_id)})
    except Exception:
        product = await db.products.find_one({"_id": product_id})
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product["_id"] = str(product["_id"])
    
    # Get merchant info
    if product.get("merchant_id"):
        merchant = await db.merchants.find_one({"user_id": product["merchant_id"]})
        if merchant:
            merchant["_id"] = str(merchant["_id"])
            product["merchant"] = merchant
    
    return product


@router.post("/{product_id}/approve")
async def approve_product(
    product_id: str,
    request: ProductApprovalRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Approve or reject a product."""
    try:
        product_obj_id = ObjectId(product_id)
    except Exception:
        product_obj_id = product_id
    
    product = await db.products.find_one({"_id": product_obj_id})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_data = {
        "is_approved": request.is_approved,
        "is_rejected": not request.is_approved,
        "approval_status": "approved" if request.is_approved else "rejected",
        "approved_by": str(admin["_id"]),
        "approved_at": datetime.utcnow(),
        "approval_reason": request.reason,
        "updated_at": datetime.utcnow()
    }
    
    # If rejecting, set is_active to False
    if not request.is_approved:
        update_data["is_active"] = False
    
    await db.products.update_one({"_id": product_obj_id}, {"$set": update_data})
    
    action = "approved" if request.is_approved else "rejected"
    return {"ok": True, "product_id": product_id, "action": action}


@router.put("/{product_id}")
async def update_product(
    product_id: str,
    request: ProductUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Update product information (admin override)."""
    try:
        product_obj_id = ObjectId(product_id)
    except Exception:
        product_obj_id = product_id
    
    product = await db.products.find_one({"_id": product_obj_id})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    update_data = {}
    if request.title is not None:
        update_data["title"] = request.title
    if request.description is not None:
        update_data["description"] = request.description
    if request.price is not None:
        update_data["price"] = request.price
    if request.stock is not None:
        update_data["stock"] = request.stock
    if request.category is not None:
        update_data["category"] = request.category
    if request.is_active is not None:
        update_data["is_active"] = request.is_active
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )
    
    update_data["updated_at"] = datetime.utcnow()
    update_data["updated_by_admin"] = str(admin["_id"])
    
    await db.products.update_one({"_id": product_obj_id}, {"$set": update_data})
    
    return {"ok": True, "product_id": product_id, "updated_fields": list(update_data.keys())}


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    reason: Optional[str] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Delete/remove a product (for inappropriate content)."""
    try:
        product_obj_id = ObjectId(product_id)
    except Exception:
        product_obj_id = product_id
    
    product = await db.products.find_one({"_id": product_obj_id})
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Soft delete - mark as deleted instead of removing
    await db.products.update_one(
        {"_id": product_obj_id},
        {
            "$set": {
                "is_deleted": True,
                "is_active": False,
                "deleted_by": str(admin["_id"]),
                "deleted_at": datetime.utcnow(),
                "deletion_reason": reason,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {"ok": True, "product_id": product_id, "message": "Product removed successfully"}


@router.post("/bulk/approve")
async def bulk_approve_products(
    request: BulkApprovalRequest,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Bulk approve or reject products."""
    if not request.product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No product IDs provided"
        )
    
    # Convert IDs to ObjectIds where possible
    object_ids = []
    for pid in request.product_ids:
        try:
            object_ids.append(ObjectId(pid))
        except:
            object_ids.append(pid)
    
    update_data = {
        "is_approved": request.is_approved,
        "is_rejected": not request.is_approved,
        "approval_status": "approved" if request.is_approved else "rejected",
        "approved_by": str(admin["_id"]),
        "approved_at": datetime.utcnow(),
        "approval_reason": request.reason,
        "updated_at": datetime.utcnow()
    }
    
    if not request.is_approved:
        update_data["is_active"] = False
    
    result = await db.products.update_many(
        {"_id": {"$in": object_ids}},
        {"$set": update_data}
    )
    
    action = "approved" if request.is_approved else "rejected"
    return {
        "ok": True,
        "action": action,
        "modified_count": result.modified_count,
        "requested_count": len(request.product_ids)
    }


@router.post("/bulk/delete")
async def bulk_delete_products(
    product_ids: List[str],
    reason: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Bulk delete products."""
    if not product_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No product IDs provided"
        )
    
    object_ids = []
    for pid in product_ids:
        try:
            object_ids.append(ObjectId(pid))
        except:
            object_ids.append(pid)
    
    result = await db.products.update_many(
        {"_id": {"$in": object_ids}},
        {
            "$set": {
                "is_deleted": True,
                "is_active": False,
                "deleted_by": str(admin["_id"]),
                "deleted_at": datetime.utcnow(),
                "deletion_reason": reason,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    return {
        "ok": True,
        "modified_count": result.modified_count,
        "requested_count": len(product_ids)
    }


@router.get("/stats/overview")
async def get_products_stats(
    db: AsyncIOMotorDatabase = Depends(get_db),
    admin: dict = Depends(get_current_admin)
):
    """Get product statistics overview."""
    total = await db.products.count_documents({})
    pending = await db.products.count_documents({"is_approved": False, "is_rejected": {"$ne": True}})
    approved = await db.products.count_documents({"is_approved": True})
    rejected = await db.products.count_documents({"is_rejected": True})
    active = await db.products.count_documents({"is_active": True})
    deleted = await db.products.count_documents({"is_deleted": True})
    
    return {
        "total": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "active": active,
        "deleted": deleted
    }
