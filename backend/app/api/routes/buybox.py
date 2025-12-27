from typing import Optional
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_db
from app.services.buybox_service import calculate_buybox_winner

router = APIRouter()


@router.get("/{product_title}")
async def get_buybox_winner(
    product_title: str,
    user_lat: Optional[float] = Query(None),
    user_lng: Optional[float] = Query(None),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get the Buy Box winner for a product.
    
    The Buy Box algorithm determines which merchant should be featured for a product
    based on stock availability, geographic proximity, and merchant rating.
    
    Query Parameters:
    - user_lat: User's latitude (optional)
    - user_lng: User's longitude (optional)
    
    If user location is not provided, distance scoring will use a default value.
    """
    user_location = None
    if user_lat is not None and user_lng is not None:
        user_location = {"lat": user_lat, "lng": user_lng}
    
    result = await calculate_buybox_winner(product_title, user_location)
    
    return result
