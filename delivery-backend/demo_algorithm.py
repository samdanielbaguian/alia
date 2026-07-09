#!/usr/bin/env python
"""
Shipping Algorithm Demo - Test the algorithm directly
"""

from app.schemas.shipping import ShippingQuoteRequest
from app.services.shipping_algorithm import ShippingAlgorithm


def print_quote(title: str, request: ShippingQuoteRequest):
    """Print a formatted shipping quote"""
    quote = ShippingAlgorithm.calculate_shipping_quote(request)
    
    print(f"\n{'='*60}")
    print(f"📦 {title}")
    print(f"{'='*60}")
    print(f"  Weight:           {request.article_weight} kg")
    print(f"  From:             {request.stock_city}")
    print(f"  To:               {request.delivery_city}, {request.delivery_address}")
    print(f"  Distance:         {request.distance} km")
    print(f"  Rating:           {request.delivery_rating} ⭐")
    print(f"\n  Zone Allowed:     {'✅ Yes' if quote.zone_allowed else '❌ No'}")
    print(f"  Price:            {quote.delivery_price:,} CFA")
    print(f"  Time:             {quote.delivery_time[0]}-{quote.delivery_time[1]} days")
    print(f"  Method:           {quote.delivery_method or 'Not assigned'}")
    print(f"  Commission (25%): {quote.commission:,} CFA")
    print(f"  Details:          {quote.details}")


def main():
    """Run demo scenarios"""
    
    print("\n" + "="*60)
    print("🚚 SHIPPING ALGORITHM DEMONSTRATION")
    print("="*60)
    print("\nThe algorithm calculates shipping prices for West African zones")
    print("based on weight, distance, location, and delivery ratings.")
    
    # Test Case 1: Primary Algorithm - Local Delivery
    print_quote(
        "PRIMARY ALGORITHM: Local Delivery (Same City)",
        ShippingQuoteRequest(
            article_weight=0.5,
            delivery_address="Burkina Faso",
            delivery_city="Ouagadougou",
            stock_city="Ouagadougou",
            distance=10.0,
            delivery_rating=4.8
        )
    )
    
    # Test Case 2: Primary Algorithm - Regional
    print_quote(
        "PRIMARY ALGORITHM: Regional Delivery (30-60km)",
        ShippingQuoteRequest(
            article_weight=2.0,
            delivery_address="Mali",
            delivery_city="Kayes",
            stock_city="Bamako",
            distance=45.0,
            delivery_rating=4.0
        )
    )
    
    # Test Case 3: Secondary Algorithm - Long Distance Light
    print_quote(
        "SECONDARY ALGORITHM: Long Distance - Light Weight",
        ShippingQuoteRequest(
            article_weight=0.8,
            delivery_address="Niger",
            delivery_city="Niamey",
            stock_city="Maradi",
            distance=75.0,
            delivery_rating=4.5
        )
    )
    
    # Test Case 4: Secondary Algorithm - Long Distance Medium
    print_quote(
        "SECONDARY ALGORITHM: Long Distance - Medium Weight",
        ShippingQuoteRequest(
            article_weight=1.5,
            delivery_address="Ivory Coast",
            delivery_city="Abidjan",
            stock_city="Yamoussoukro",
            distance=70.0,
            delivery_rating=3.0
        )
    )
    
    # Test Case 5: Third Algorithm - Very Long Light
    print_quote(
        "THIRD ALGORITHM: Very Long Distance - Light Weight (≤5kg)",
        ShippingQuoteRequest(
            article_weight=3.5,
            delivery_address="Ghana",
            delivery_city="Accra",
            stock_city="Kumasi",
            distance=250.0,
            delivery_rating=4.2
        )
    )
    
    # Test Case 6: Third Algorithm - Very Long Heavy
    print_quote(
        "THIRD ALGORITHM: Very Long Distance - Heavy Weight (>5kg)",
        ShippingQuoteRequest(
            article_weight=8.0,
            delivery_address="Togo",
            delivery_city="Lome",
            stock_city="Kara",
            distance=300.0,
            delivery_rating=3.5
        )
    )
    
    # Test Case 7: Zone Not Allowed
    print_quote(
        "INVALID ZONE: Delivery Outside Allowed Areas",
        ShippingQuoteRequest(
            article_weight=2.0,
            delivery_address="France",
            delivery_city="Paris",
            stock_city="Lyon",
            distance=500.0,
            delivery_rating=5.0
        )
    )
    
    # Test Case 8: High Rating - Motorbike
    print_quote(
        "HIGH RATING: Excellent Rating with Light Weight",
        ShippingQuoteRequest(
            article_weight=0.5,
            delivery_address="Benin",
            delivery_city="Porto-Novo",
            stock_city="Cotonou",
            distance=20.0,
            delivery_rating=4.9
        )
    )
    
    # Summary
    print("\n" + "="*60)
    print("📊 ALGORITHM SUMMARY")
    print("="*60)
    print("\nAllowed Zones:", ", ".join(ShippingAlgorithm.ALLOWED_ZONES))
    print("\nCommission Rate: 25%")
    print("\nPrice Tiers:")
    print("  🟢 Local (same city, ≤1kg, ≤30km):           2,000 CFA")
    print("  🟡 Regional (30-60km):                         3,500 CFA")
    print("  🟠 Long Distance (>60km):                      5,000 CFA")
    print("  🔴 Very Long Distance (100-800km, ≤5kg):      7,000 CFA")
    print("  🔴 Very Long Distance (100-800km, >5kg):     10,000 CFA")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
