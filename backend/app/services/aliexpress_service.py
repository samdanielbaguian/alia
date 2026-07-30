from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Mock AliExpress product database for development
MOCK_ALIEXPRESS_PRODUCTS = {
    "ali_001": {
        "product_id": "ali_001",
        "title": "Wireless Bluetooth Headphones",
        "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life",
        "price": 25.99,
        "original_price": 39.99,
        "image_url": "https://via.placeholder.com/300?text=Wireless+Headphones",
        "images": [
            "https://via.placeholder.com/300?text=Wireless+Headphones+1",
            "https://via.placeholder.com/300?text=Wireless+Headphones+2"
        ],
        "delivery_days": 14,
        "rating": 4.5,
        "reviews": 342,
        "category": "electronics",
        "sku": "ALI-BT-HP-001",
        "stock": 100,
        "weight": 0.25,
        "dimensions": "20x18x8cm",
        "material": "Plastic + Metal"
    },
    "ali_002": {
        "product_id": "ali_002",
        "title": "USB-C Fast Charging Cable",
        "description": "Durable 2m USB-C charging cable with fast charging support (100W)",
        "price": 8.99,
        "original_price": 14.99,
        "image_url": "https://via.placeholder.com/300?text=USB-C+Cable",
        "images": [
            "https://via.placeholder.com/300?text=USB-C+Cable+1",
            "https://via.placeholder.com/300?text=USB-C+Cable+2"
        ],
        "delivery_days": 7,
        "rating": 4.7,
        "reviews": 1250,
        "category": "electronics",
        "sku": "ALI-USBC-001",
        "stock": 500,
        "weight": 0.05,
        "dimensions": "2m",
        "material": "Copper + Nylon"
    },
    "ali_003": {
        "product_id": "ali_003",
        "title": "Phone Protective Case",
        "description": "Shockproof phone case with raised bezels for iPhone and Android",
        "price": 5.99,
        "original_price": 9.99,
        "image_url": "https://via.placeholder.com/300?text=Phone+Case",
        "images": [
            "https://via.placeholder.com/300?text=Phone+Case+1",
            "https://via.placeholder.com/300?text=Phone+Case+2"
        ],
        "delivery_days": 10,
        "rating": 4.3,
        "reviews": 2100,
        "category": "accessories",
        "sku": "ALI-CASE-001",
        "stock": 1000,
        "weight": 0.08,
        "dimensions": "15x7x1cm",
        "material": "TPU + PC"
    },
    "ali_004": {
        "product_id": "ali_004",
        "title": "LED Desk Lamp",
        "description": "Adjustable brightness LED desk lamp with USB charging",
        "price": 12.99,
        "original_price": 21.99,
        "image_url": "https://via.placeholder.com/300?text=LED+Lamp",
        "images": [
            "https://via.placeholder.com/300?text=LED+Lamp+1",
            "https://via.placeholder.com/300?text=LED+Lamp+2"
        ],
        "delivery_days": 14,
        "rating": 4.6,
        "reviews": 567,
        "category": "home",
        "sku": "ALI-LAMP-001",
        "stock": 200,
        "weight": 0.3,
        "dimensions": "30x10x5cm",
        "material": "Plastic + Metal"
    },
    "ali_005": {
        "product_id": "ali_005",
        "title": "Portable Phone Stand",
        "description": "Adjustable phone stand compatible with all smartphones",
        "price": 4.99,
        "original_price": 8.99,
        "image_url": "https://via.placeholder.com/300?text=Phone+Stand",
        "images": [
            "https://via.placeholder.com/300?text=Phone+Stand+1"
        ],
        "delivery_days": 7,
        "rating": 4.4,
        "reviews": 3200,
        "category": "accessories",
        "sku": "ALI-STAND-001",
        "stock": 800,
        "weight": 0.1,
        "dimensions": "10x8x12cm",
        "material": "Metal + Silicone"
    },
    "ali_006": {
        "product_id": "ali_006",
        "title": "Smart Watch",
        "description": "Fitness tracker with heart rate monitor and sleep tracking",
        "price": 35.99,
        "original_price": 59.99,
        "image_url": "https://via.placeholder.com/300?text=Smart+Watch",
        "images": [
            "https://via.placeholder.com/300?text=Smart+Watch+1",
            "https://via.placeholder.com/300?text=Smart+Watch+2"
        ],
        "delivery_days": 14,
        "rating": 4.2,
        "reviews": 890,
        "category": "electronics",
        "sku": "ALI-WATCH-001",
        "stock": 150,
        "weight": 0.05,
        "dimensions": "4x4cm",
        "material": "Silicone + Glass"
    },
    "ali_007": {
        "product_id": "ali_007",
        "title": "Wireless Power Bank",
        "description": "10000mAh wireless charging power bank",
        "price": 18.99,
        "original_price": 29.99,
        "image_url": "https://via.placeholder.com/300?text=Power+Bank",
        "images": [
            "https://via.placeholder.com/300?text=Power+Bank+1",
            "https://via.placeholder.com/300?text=Power+Bank+2"
        ],
        "delivery_days": 10,
        "rating": 4.5,
        "reviews": 1450,
        "category": "electronics",
        "sku": "ALI-PB-001",
        "stock": 300,
        "weight": 0.22,
        "dimensions": "8x8x2cm",
        "material": "Plastic + Metal"
    },
    "ali_008": {
        "product_id": "ali_008",
        "title": "Keyboard and Mouse Combo",
        "description": "Wireless keyboard and mouse set with USB receiver",
        "price": 19.99,
        "original_price": 34.99,
        "image_url": "https://via.placeholder.com/300?text=Keyboard+Mouse",
        "images": [
            "https://via.placeholder.com/300?text=Keyboard+Mouse+1",
            "https://via.placeholder.com/300?text=Keyboard+Mouse+2"
        ],
        "delivery_days": 14,
        "rating": 4.4,
        "reviews": 789,
        "category": "electronics",
        "sku": "ALI-KM-001",
        "stock": 250,
        "weight": 0.4,
        "dimensions": "45x12x2cm",
        "material": "Plastic"
    },
    "ali_009": {
        "product_id": "ali_009",
        "title": "HDMI Cable 2M",
        "description": "High-speed HDMI 2.0 cable for 4K resolution",
        "price": 6.99,
        "original_price": 12.99,
        "image_url": "https://via.placeholder.com/300?text=HDMI+Cable",
        "images": [
            "https://via.placeholder.com/300?text=HDMI+Cable+1"
        ],
        "delivery_days": 7,
        "rating": 4.6,
        "reviews": 2300,
        "category": "electronics",
        "sku": "ALI-HDMI-001",
        "stock": 600,
        "weight": 0.08,
        "dimensions": "2m",
        "material": "Gold-plated"
    },
    "ali_010": {
        "product_id": "ali_010",
        "title": "Screen Protector Pack",
        "description": "Pack of 3 tempered glass screen protectors for smartphones",
        "price": 4.49,
        "original_price": 7.99,
        "image_url": "https://via.placeholder.com/300?text=Screen+Protector",
        "images": [
            "https://via.placeholder.com/300?text=Screen+Protector+1"
        ],
        "delivery_days": 7,
        "rating": 4.5,
        "reviews": 4500,
        "category": "accessories",
        "sku": "ALI-SP-001",
        "stock": 1500,
        "weight": 0.05,
        "dimensions": "Pack of 3",
        "material": "Tempered Glass"
    }
}


async def search_aliexpress(query: str) -> List[Dict]:
    """
    Search for products on AliExpress (MOCK IMPLEMENTATION).
    
    This returns mock data for development. In production, replace with real API integration.
    
    Args:
        query: Search query string (case-insensitive)
        
    Returns:
        List of product dictionaries matching the query
    """
    logger.info(f"[MOCK] Searching AliExpress for: {query}")
    
    query_lower = query.lower()
    results = []
    
    # Simple search: match query in title or category
    for product_id, product in MOCK_ALIEXPRESS_PRODUCTS.items():
        title_match = query_lower in product["title"].lower()
        description_match = query_lower in product["description"].lower()
        category_match = query_lower in product["category"].lower()
        
        if title_match or description_match or category_match:
            results.append({
                "product_id": product["product_id"],
                "title": product["title"],
                "description": product["description"],
                "price": product["price"],
                "original_price": product["original_price"],
                "image_url": product["image_url"],
                "delivery_days": product["delivery_days"],
                "rating": product["rating"],
                "reviews": product.get("reviews", 0),
                "category": product["category"]
            })
    
    # Return top 5 results or all if less than 5
    logger.info(f"[MOCK] Found {len(results)} products matching '{query}'")
    return results[:5]


async def get_product_details(source_product_id: str) -> Optional[Dict]:
    """
    Get detailed product information from AliExpress (MOCK IMPLEMENTATION).
    
    Args:
        source_product_id: AliExpress product ID
        
    Returns:
        Complete product dictionary or None if not found
    """
    logger.info(f"[MOCK] Fetching product details for: {source_product_id}")
    
    product = MOCK_ALIEXPRESS_PRODUCTS.get(source_product_id)
    if not product:
        logger.warning(f"[MOCK] Product {source_product_id} not found in mock database")
        return None
    
    logger.info(f"[MOCK] ✓ Found product: {product['title']}")
    return product


async def import_product(
    source_product_id: str,
    merchant_id: str,
    margin_percentage: float,
    source_platform: str = "AliExpress"
) -> Dict:
    """
    Import a product from AliExpress/Alibaba to the merchant's store (MOCK IMPLEMENTATION).
    
    This function:
    1. Fetches product details from mock data
    2. Calculates the selling price with merchant's margin
    3. Creates the product in the database
    4. Links it to the merchant
    
    Args:
        source_product_id: Product ID on AliExpress/Alibaba
        merchant_id: Merchant's user ID
        margin_percentage: Profit margin to add (e.g., 20 = 20%)
        source_platform: "AliExpress" or "Alibaba"
        
    Returns:
        Imported product dictionary with MongoDB _id
        
    Raises:
        ValueError: If source product not found
    """
    from app.core.database import get_database
    from datetime import datetime
    
    logger.info(f"[MOCK] Importing product {source_product_id} for merchant {merchant_id}")
    
    # Get product details from mock data
    source_product = MOCK_ALIEXPRESS_PRODUCTS.get(source_product_id)
    if not source_product:
        logger.error(f"[MOCK] Product {source_product_id} not found")
        raise ValueError(f"Product {source_product_id} not found in AliExpress catalog")
    
    # Calculate selling price with margin
    cost_price = source_product["original_price"]
    selling_price = cost_price * (1 + margin_percentage / 100)
    
    db = get_database()
    
    product_data = {
        "title": source_product["title"],
        "description": source_product["description"],
        "price": round(selling_price, 2),
        "original_price": cost_price,
        "images": source_product.get("images", [source_product["image_url"]]),
        "stock": source_product.get("stock", 0),
        "category": source_product.get("category", "imported"),
        "merchant_id": merchant_id,
        "is_imported": True,
        "source_platform": source_platform,
        "source_product_id": source_product_id,
        "delivery_days": source_product.get("delivery_days", 14),
        "age_restricted": False,
        "sku": source_product.get("sku"),
        "size": None,
        "color": None,
        "weight": source_product.get("weight"),
        "dimensions": source_product.get("dimensions"),
        "material": source_product.get("material"),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.products.insert_one(product_data)
    product_data["_id"] = result.inserted_id
    
    logger.info(f"[MOCK] ✓ Product imported successfully: {product_data['_id']}")
    return product_data


async def sync_product(product_id: str) -> Dict:
    """
    Synchronize product price and stock from AliExpress/Alibaba (MOCK IMPLEMENTATION).
    
    This function updates the local product with the latest data from the source platform.
    Should be called periodically or when a merchant manually requests a sync.
    
    Args:
        product_id: Local product ID to sync
        
    Returns:
        Updated product dictionary with sync status
    """
    from app.core.database import get_database
    from bson import ObjectId
    from datetime import datetime
    
    logger.info(f"[MOCK] Syncing product {product_id}")
    
    db = get_database()
    
    try:
        product = await db.products.find_one({"_id": ObjectId(product_id)})
    except Exception:
        return {"error": "Invalid product ID"}
    
    if not product:
        return {"error": "Product not found"}
    
    if not product.get("is_imported"):
        return {"error": "Product is not imported"}
    
    # In mock mode, just update the timestamp
    await db.products.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": {"updated_at": datetime.utcnow()}}
    )
    
    logger.info(f"[MOCK] ✓ Product {product_id} synced successfully")
    
    return {
        "product_id": product_id,
        "status": "synced",
        "message": "Mock product synced (no real API call)",
        "synced_at": datetime.utcnow().isoformat()
    }
