from app.schemas.shipping import ShippingQuoteRequest, ShippingQuoteResponse, DeliveryMethod


class ShippingAlgorithm:
    """
    Shipping Algorithm for West African delivery zones
    
    Calculates delivery price, time, method, and commission based on:
    - Article weight
    - Delivery distance
    - Delivery zone
    - Delivery rating
    """
    
    # Allowed delivery zones
    ALLOWED_ZONES = {
        "Burkina Faso",
        "Mali",
        "Niger",
        "Ivory Coast",
        "Togo",
        "Benin",
        "Ghana"
    }
    
    COMMISSION_PERCENTAGE = 25  # 25% commission
    MAX_BICYCLE_DISTANCE_KM = 10
    MAX_MOTORBIKE_DISTANCE_KM = 40
    
    @staticmethod
    def check_zone_allowed(address: str) -> bool:
        """Check if delivery address is in allowed zone"""
        return address in ShippingAlgorithm.ALLOWED_ZONES
    
    @staticmethod
    def calculate_shipping_quote(request: ShippingQuoteRequest) -> ShippingQuoteResponse:
        """
        Calculate shipping quote based on algorithm
        
        Algorithm Logic:
        1. Check if delivery zone is allowed
        2. Apply PRIMARY algorithm for distances <= 60km
        3. Apply SECONDARY algorithm for distances > 60km
        4. Apply THIRD algorithm for distances 100-800km
        5. Select delivery method based on weight and rating
        6. Calculate commission (25%)
        """
        
        # Initialize variables
        wa = request.article_weight  # kg
        aa = request.delivery_address  # delivery address
        vaa = request.delivery_city  # delivery city
        vpa = request.stock_city  # stock city
        ra = request.distance  # km
        mlr = request.delivery_rating  # rating
        
        # Check delivery zone
        za = ShippingAlgorithm.check_zone_allowed(aa)
        
        # Initialize outputs
        pl = 0  # delivery price
        tl_min, tl_max = 0, 0  # delivery time range
        ml = None  # delivery method
        details = ""
        
        if not za:
            # Zone not allowed
            details = f"Delivery zone '{aa}' is not in allowed zones"
            cpa = 0
            return ShippingQuoteResponse(
                delivery_price=pl,
                delivery_time=(tl_min, tl_max),
                delivery_method=ml,
                commission=cpa,
                zone_allowed=za,
                details=details
            )
        
        # === PRIMARY ALGORITHM ===
        # Short distance, same city, light weight
        if za and ra <= 30 and vaa == vpa and wa <= 1:
            pl = 2000
            tl_min, tl_max = 1, 3
            details = "PRIMARY ALGORITHM: Local delivery (same city, <= 1kg, <= 30km)"
        
        # === PRIMARY ALGORITHM (variant) ===
        # Medium distance
        elif za and 30 < ra <= 60:
            pl = 3500
            tl_min, tl_max = 1, 3
            details = "PRIMARY ALGORITHM: Regional delivery (30km < distance <= 60km)"
        
        # === SECONDARY ALGORITHM ===
        # Long distance
        elif za and ra > 60:
            if (vaa != vpa and wa <= 1) or (vaa == vpa):
                pl = 5000
                tl_min, tl_max = 2, 4
                details = "SECONDARY ALGORITHM: Long distance delivery (> 60km, light weight)"
            
            elif wa > 1 and wa <= 2:
                pl = 5000
                tl_min, tl_max = 2, 4
                ml = DeliveryMethod.CAR
                details = "SECONDARY ALGORITHM: Long distance delivery (> 60km, 1-2kg)"
        
        # === THIRD ALGORITHM ===
        # Very long distance
        if za and 100 <= ra <= 800:
            if wa <= 5:
                pl = 7000
                tl_min, tl_max = 3, 7
                ml = DeliveryMethod.CAR
                details = "THIRD ALGORITHM: Very long distance delivery (100-800km, <= 5kg)"
            else:
                pl = 10000
                tl_min, tl_max = 5, 10
                ml = DeliveryMethod.TRUCK
                details = "THIRD ALGORITHM: Very long distance delivery (100-800km, > 5kg)"
        
        # === DELIVERY METHOD SELECTION ===
        # High rating delivery method optimization with two-wheeler distance caps
        if za and mlr >= 4.5 and ml is None:
            if wa <= 1:
                if ra <= ShippingAlgorithm.MAX_BICYCLE_DISTANCE_KM and vaa == vpa:
                    ml = DeliveryMethod.BICYCLE
                    details += " | High rating: Bicycle recommended (short same-city distance)"
                elif ra <= ShippingAlgorithm.MAX_MOTORBIKE_DISTANCE_KM:
                    ml = DeliveryMethod.MOTORBIKE
                    details += " | High rating: Motorbike recommended (within safe two-wheeler range)"
                else:
                    ml = DeliveryMethod.CAR
                    details += " | High rating: Car recommended (distance too far for bicycle/motorbike)"
            else:
                ml = DeliveryMethod.CAR
                details += " | High rating: Car recommended"
        
        # Commission calculation (25%)
        cpa = (pl * ShippingAlgorithm.COMMISSION_PERCENTAGE) / 100
        
        return ShippingQuoteResponse(
            delivery_price=pl,
            delivery_time=(tl_min, tl_max),
            delivery_method=ml,
            commission=cpa,
            zone_allowed=za,
            details=details
        )
