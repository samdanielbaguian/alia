from typing import Dict, List, Optional
from bson import ObjectId
from app. core.database import get_database
from app.utils.geolocation import calculate_distance


async def calculate_buybox_winner(product_title: str, user_location:  Optional[Dict[str, float]] = None) -> Dict:
    """
    Calculate the Buy Box winner for a product based on multiple factors. 
    
    The Buy Box algorithm determines which merchant should be featured for a product
    by considering stock availability, geographic proximity, and merchant rating. 
    
    Algorithm:
        - Stock availability: 40% weight (more stock = better)
        - Geographic distance: 35% weight (closer = better)
        - Merchant good_rate: 25% weight (higher rating = better)
        
    Args:
        product_title: Title of the product to find merchants for
        user_location: User's location as {"lat":  float, "lng": float}
        
    Returns:
        Dictionary containing:
            - winner: The winning merchant's product details
            - all_offers: List of all merchants selling this product with scores
            
    Example:
        {
            "winner": {
                "product_id": "123",
                "merchant_id": "merchant1",
                "price": 299.99,
                "score":  87.5
            },
            "all_offers": [...]
        }
    """
    db = get_database()
    
    # Normalize title for search (case-insensitive, similar titles)
    title_words = product_title.lower().split()
    
    # Find all products with similar titles
    all_products = await db.products.find({}).to_list(length=1000)
    
    matching_products = []
    for product in all_products:
        product_title_words = set(product["title"].lower().split())
        search_title_words = set(title_words)
        
        # Check if there's significant overlap in words
        common_words = len(product_title_words.intersection(search_title_words))
        if common_words >= min(2, len(search_title_words) * 0.5):
            matching_products.append(product)
    
    if not matching_products:
        return {
            "winner": None,
            "all_offers": [],
            "total_merchants": 0
        }
    
    # Calculate scores for each merchant
    offers = []
    
    for product in matching_products:
        # Get merchant information
        merchant = await db.merchants.find_one({"user_id": product["merchant_id"]})
        
        # Convert merchant_id string to ObjectId for user lookup
        try: 
            user_object_id = ObjectId(product["merchant_id"])
            user = await db.users.find_one({"_id": user_object_id})
        except Exception:
            user = None
        
        if not user:
            continue
        
        good_rate = user.get("good_rate", 50.0)
        
        # Calculate stock score (0-100)
        # More stock = better, but with diminishing returns
        stock = product.get("stock", 0)
        if stock == 0:
            stock_score = 0
        else:
            # Normalize stock to 0-100 scale (assuming 100+ stock is "perfect")
            stock_score = min(stock, 100)
        
        # Calculate distance score (0-100)
        distance_score = 100  # Default if no location
        if user_location and product.get("location"):
            try:
                distance_km = calculate_distance(user_location, product["location"])
                # Closer = better. 0km = 100 points, 50km = 50 points, 100+km = 0 points
                distance_score = max(0, 100 - distance_km)
            except Exception: 
                distance_score = 50  # Default if calculation fails
        
        # Calculate weighted total score
        # Stock: 40%, Distance: 35%, Rating: 25%
        total_score = (
            (stock_score * 0.40) +
            (distance_score * 0.35) +
            (good_rate * 0.25)
        )
        
        # Get merchant info for display
        shop_name = merchant.get("shop_name", "Unknown Shop") if merchant else "Unknown Shop"
        
        offers.append({
            "product_id": str(product["_id"]),
            "merchant_id": product["merchant_id"],
            "shop_name": shop_name,
            "title": product["title"],
            "price": product["price"],
            "stock": stock,
            "delivery_days": product.get("delivery_days", 7),
            "good_rate": good_rate,
            "distance_km": calculate_distance(user_location, product["location"]) if user_location and product. get("location") else None,
            "scores": {
                "stock": round(stock_score, 2),
                "distance":  round(distance_score, 2),
                "rating": round(good_rate, 2),
                "total": round(total_score, 2)
            }
        })
    
    # Sort by total score (highest first)
    offers.sort(key=lambda x: x["scores"]["total"], reverse=True)
    
    winner = offers[0] if offers else None
    
    return {
        "winner": winner,
        "all_offers": offers,
        "total_merchants":  len(offers)
    }
