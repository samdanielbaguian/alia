from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.shipment import ShipmentCreate, ShipmentUpdate, ShipmentResponse
from app.models.shipment import ShipmentStatus
import uuid

router = APIRouter()

# Mock database (replace with real DB later)
shipments_db = {}


@router.post("/", response_model=ShipmentResponse)
async def create_shipment(shipment: ShipmentCreate):
    """Create a new shipment"""
    tracking_number = f"TRK-{uuid.uuid4().hex[:8].upper()}"
    shipment_dict = shipment.dict()
    shipment_dict["id"] = len(shipments_db) + 1
    shipment_dict["tracking_number"] = tracking_number
    shipment_dict["status"] = ShipmentStatus.PENDING
    shipment_dict["actual_delivery"] = None
    
    shipments_db[shipment_dict["id"]] = shipment_dict
    return shipment_dict


@router.get("/", response_model=List[ShipmentResponse])
async def get_shipments():
    """Get all shipments"""
    return list(shipments_db.values())


@router.get("/{shipment_id}", response_model=ShipmentResponse)
async def get_shipment(shipment_id: int):
    """Get shipment by ID"""
    if shipment_id not in shipments_db:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipments_db[shipment_id]


@router.get("/tracking/{tracking_number}", response_model=ShipmentResponse)
async def get_shipment_by_tracking(tracking_number: str):
    """Get shipment by tracking number"""
    for shipment in shipments_db.values():
        if shipment["tracking_number"] == tracking_number:
            return shipment
    raise HTTPException(status_code=404, detail="Shipment not found")


@router.put("/{shipment_id}", response_model=ShipmentResponse)
async def update_shipment(shipment_id: int, shipment_update: ShipmentUpdate):
    """Update shipment"""
    if shipment_id not in shipments_db:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    shipment = shipments_db[shipment_id]
    update_data = shipment_update.dict(exclude_unset=True)
    shipment.update(update_data)
    return shipment


@router.delete("/{shipment_id}")
async def delete_shipment(shipment_id: int):
    """Delete shipment"""
    if shipment_id not in shipments_db:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    del shipments_db[shipment_id]
    return {"message": "Shipment deleted successfully"}
