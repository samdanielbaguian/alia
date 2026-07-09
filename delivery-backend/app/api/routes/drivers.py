from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse

router = APIRouter()

# Mock database (replace with real DB later)
drivers_db = {}


@router.post("/", response_model=DriverResponse)
async def create_driver(driver: DriverCreate):
    """Create a new driver"""
    driver_dict = driver.dict()
    driver_dict["id"] = len(drivers_db) + 1
    driver_dict["status"] = "off_duty"
    driver_dict["current_latitude"] = None
    driver_dict["current_longitude"] = None
    driver_dict["available_for_delivery"] = False
    driver_dict["total_deliveries"] = 0
    driver_dict["rating"] = 0.0
    
    drivers_db[driver_dict["id"]] = driver_dict
    return driver_dict


@router.get("/", response_model=List[DriverResponse])
async def get_drivers(status: str = None):
    """Get all drivers or filter by status"""
    if status:
        return [d for d in drivers_db.values() if d["status"] == status]
    return list(drivers_db.values())


@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: int):
    """Get driver by ID"""
    if driver_id not in drivers_db:
        raise HTTPException(status_code=404, detail="Driver not found")
    return drivers_db[driver_id]


@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(driver_id: int, driver_update: DriverUpdate):
    """Update driver"""
    if driver_id not in drivers_db:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    driver = drivers_db[driver_id]
    update_data = driver_update.dict(exclude_unset=True)
    driver.update(update_data)
    return driver


@router.delete("/{driver_id}")
async def delete_driver(driver_id: int):
    """Delete driver"""
    if driver_id not in drivers_db:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    del drivers_db[driver_id]
    return {"message": "Driver deleted successfully"}
