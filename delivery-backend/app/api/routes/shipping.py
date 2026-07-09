from fastapi import APIRouter, HTTPException
from app.schemas.shipping import ShippingQuoteRequest, ShippingQuoteResponse
from app.services.shipping_algorithm import ShippingAlgorithm

router = APIRouter()


@router.post("/calculate-quote", response_model=ShippingQuoteResponse)
async def calculate_shipping_quote(request: ShippingQuoteRequest):
    """
    Calculate shipping quote based on the algorithm
    
    Algorithm Parameters:
    - article_weight: Weight in kg
    - delivery_address: Destination country
    - delivery_city: Destination city
    - stock_city: Origin/Stock city
    - distance: Distance in km
    - delivery_rating: Rating (0-5)
    
    Returns:
    - delivery_price: Calculated price
    - delivery_time: Time range in days
    - delivery_method: Recommended method (Motorbike, Bicycle, Car, Truck)
    - commission: 25% commission
    - zone_allowed: Whether zone is allowed
    """
    try:
        quote = ShippingAlgorithm.calculate_shipping_quote(request)
        
        if not quote.zone_allowed and quote.delivery_price == 0:
            raise HTTPException(
                status_code=400,
                detail=f"Delivery to '{request.delivery_address}' is not available. "
                       f"Allowed zones: Burkina Faso, Mali, Niger, Ivory Coast, Togo, Benin, Ghana"
            )
        
        return quote
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/allowed-zones")
async def get_allowed_zones():
    """Get list of allowed delivery zones"""
    return {
        "allowed_zones": list(ShippingAlgorithm.ALLOWED_ZONES),
        "commission_percentage": ShippingAlgorithm.COMMISSION_PERCENTAGE
    }


@router.post("/validate-address")
async def validate_delivery_address(address: str):
    """Validate if delivery address is in allowed zone"""
    is_allowed = ShippingAlgorithm.check_zone_allowed(address)
    
    return {
        "address": address,
        "is_allowed": is_allowed,
        "message": "Address is in allowed zone" if is_allowed else "Address is not in allowed zone"
    }
