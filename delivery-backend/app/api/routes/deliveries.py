from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.delivery import DeliveryCreate, DeliveryUpdate, DeliveryResponse

router = APIRouter()

# Mock database (replace with real DB later)
deliveries_db = {}


@router.post("/", response_model=DeliveryResponse)
async def create_delivery(delivery: DeliveryCreate):
    """Create a new delivery"""
    delivery_dict = delivery.dict()
    delivery_dict["id"] = len(deliveries_db) + 1
    delivery_dict["status"] = "pending"
    delivery_dict["assigned_at"] = None
    delivery_dict["picked_up_at"] = None
    delivery_dict["delivered_at"] = None
    delivery_dict["failed_reason"] = None
    delivery_dict["delivery_proof_image"] = None
    delivery_dict["receiver_name"] = None
    delivery_dict["receiver_signature"] = None
    delivery_dict["delivery_attempts"] = 0
    
    deliveries_db[delivery_dict["id"]] = delivery_dict
    return delivery_dict


@router.get("/", response_model=List[DeliveryResponse])
async def get_deliveries(status: str = None):
    """Get all deliveries or filter by status"""
    if status:
        return [d for d in deliveries_db.values() if d["status"] == status]
    return list(deliveries_db.values())


@router.get("/{delivery_id}", response_model=DeliveryResponse)
async def get_delivery(delivery_id: int):
    """Get delivery by ID"""
    if delivery_id not in deliveries_db:
        raise HTTPException(status_code=404, detail="Delivery not found")
    return deliveries_db[delivery_id]


@router.put("/{delivery_id}", response_model=DeliveryResponse)
async def update_delivery(delivery_id: int, delivery_update: DeliveryUpdate):
    """Update delivery"""
    if delivery_id not in deliveries_db:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    delivery = deliveries_db[delivery_id]
    update_data = delivery_update.dict(exclude_unset=True)
    delivery.update(update_data)
    return delivery


@router.delete("/{delivery_id}")
async def delete_delivery(delivery_id: int):
    """Delete delivery"""
    if delivery_id not in deliveries_db:
        raise HTTPException(status_code=404, detail="Delivery not found")
    
    del deliveries_db[delivery_id]
    return {"message": "Delivery deleted successfully"}
