from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.api.deps import get_db, get_current_admin

router = APIRouter()


@router.get("")
async def list_pending_orders(db: AsyncIOMotorDatabase = Depends(get_db), admin: dict = Depends(get_current_admin)):
    """List orders pending admin review (payment or shipping approval)."""
    # Get orders that need admin review
    query = {
        "$or": [
            {"payment_approved": False, "status": {"$in": ["pending", "payment_pending"]}},
            {"shipping_approved": False, "status": {"$in": ["confirmed", "ready_to_ship"]}}
        ]
    }
    
    orders = await db.orders.find(query).sort("created_at", -1).to_list(100)
    
    # Convert ObjectId to string for JSON serialization
    for order in orders:
        order["_id"] = str(order["_id"])
        if "merchant_id" in order:
            order["merchant_id"] = str(order["merchant_id"])
        if "buyer_id" in order:
            order["buyer_id"] = str(order["buyer_id"])
    
    return {"orders": orders}


@router.post("/{order_id}/approve-payment")
async def approve_payment(order_id: str, db: AsyncIOMotorDatabase = Depends(get_db), admin: dict = Depends(get_current_admin)):
    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    update = {
        "payment_approved": True,
        "payment_approved_by": str(admin.get("_id")),
        "payment_approved_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    if order.get("status") == "pending":
        update["status"] = "confirmed"
        history = order.get("status_history", [])
        history.append({
            "status": "confirmed",
            "changed_at": datetime.utcnow(),
            "changed_by": str(admin.get("_id")),
            "note": "Payment approved by admin"
        })
        update["status_history"] = history

    await db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": update})

    return {"ok": True, "order_id": order_id}


@router.post("/{order_id}/reject-payment")
async def reject_payment(order_id: str, payload: dict, db: AsyncIOMotorDatabase = Depends(get_db), admin: dict = Depends(get_current_admin)):
    reason = payload.get("reason") if isinstance(payload, dict) else None
    if not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rejection reason required")

    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    update = {
        "payment_approved": False,
        "payment_rejection_reason": reason,
        "payment_approved_by": str(admin.get("_id")),
        "payment_approved_at": datetime.utcnow(),
        "status": "payment_rejected",
        "updated_at": datetime.utcnow()
    }

    history = order.get("status_history", [])
    history.append({
        "status": "payment_rejected",
        "changed_at": datetime.utcnow(),
        "changed_by": str(admin.get("_id")),
        "note": f"Payment rejected: {reason}"
    })
    update["status_history"] = history

    await db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": update})

    return {"ok": True, "order_id": order_id}


@router.post("/{order_id}/approve-shipping")
async def approve_shipping(order_id: str, db: AsyncIOMotorDatabase = Depends(get_db), admin: dict = Depends(get_current_admin)):
    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    update = {
        "shipping_approved": True,
        "shipping_approved_by": str(admin.get("_id")),
        "shipping_approved_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    if order.get("status") in ["confirmed", "ready_to_ship"]:
        update["status"] = "shipped"
        history = order.get("status_history", [])
        history.append({
            "status": "shipped",
            "changed_at": datetime.utcnow(),
            "changed_by": str(admin.get("_id")),
            "note": "Shipping approved by admin"
        })
        update["status_history"] = history

    await db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": update})

    return {"ok": True, "order_id": order_id}


@router.post("/{order_id}/reject-shipping")
async def reject_shipping(order_id: str, payload: dict, db: AsyncIOMotorDatabase = Depends(get_db), admin: dict = Depends(get_current_admin)):
    reason = payload.get("reason") if isinstance(payload, dict) else None
    if not reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rejection reason required")

    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    update = {
        "shipping_approved": False,
        "shipping_rejection_reason": reason,
        "shipping_approved_by": str(admin.get("_id")),
        "shipping_approved_at": datetime.utcnow(),
        "status": "shipping_rejected",
        "updated_at": datetime.utcnow()
    }

    history = order.get("status_history", [])
    history.append({
        "status": "shipping_rejected",
        "changed_at": datetime.utcnow(),
        "changed_by": str(admin.get("_id")),
        "note": f"Shipping rejected: {reason}"
    })
    update["status_history"] = history

    await db.orders.update_one({"_id": ObjectId(order_id)}, {"$set": update})

    return {"ok": True, "order_id": order_id}
