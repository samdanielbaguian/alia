"""
Database seeding script for Alia backend.

This script populates MongoDB with demo data for local development and testing.
Usage: python scripts/seed_db.py

Creates:
- 1 test buyer account
- 1 test merchant account with shop profile
- 10 sample products (mix of merchant and imported products)
- 2 sample orders
- 1 cart with items
- Sample wishlist items
"""

import asyncio
import logging
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from passlib.context import CryptContext
from bson import ObjectId

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database configuration
MONGODB_URI = "mongodb://localhost:27017"  # Adjust if needed
MONGODB_DB_NAME = "alia_db"

# Test account credentials
TEST_BUYER_EMAIL = "buyer@alia.dev"
TEST_BUYER_PASSWORD = "Test1234!"
TEST_MERCHANT_EMAIL = "merchant@alia.dev"
TEST_MERCHANT_PASSWORD = "Test1234!"


def get_password_hash(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)


async def connect_to_db() -> AsyncIOMotorDatabase:
    """Connect to MongoDB."""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    logger.info(f"Connected to MongoDB: {MONGODB_URI}/{MONGODB_DB_NAME}")
    return db


async def clear_collections(db: AsyncIOMotorDatabase):
    """Clear existing collections (optional)."""
    logger.info("🗑️ Clearing existing data...")
    collections = ["users", "merchants", "products", "orders", "payments", "carts", "wishlist"]
    for collection_name in collections:
        count = await db[collection_name].delete_many({})
        logger.info(f"  - Cleared {collection_name}: {count.deleted_count} documents")


async def seed_users(db: AsyncIOMotorDatabase) -> tuple[str, str]:
    """Create test users (buyer and merchant)."""
    logger.info("👤 Creating test users...")
    
    # Create buyer
    buyer_data = {
        "email": TEST_BUYER_EMAIL,
        "password_hash": get_password_hash(TEST_BUYER_PASSWORD),
        "role": "buyer",
        "age": 28,
        "preferences": ["electronics", "home"],
        "good_rate": 85.0,
        "location": {"type": "Point", "coordinates": [-5.5471, 6.8236]},  # Abidjan, CI
        "created_at": datetime.utcnow()
    }
    buyer_result = await db.users.insert_one(buyer_data)
    buyer_id = str(buyer_result.inserted_id)
    logger.info(f"  ✓ Buyer created: {TEST_BUYER_EMAIL} (ID: {buyer_id})")
    
    # Create merchant
    merchant_data = {
        "email": TEST_MERCHANT_EMAIL,
        "password_hash": get_password_hash(TEST_MERCHANT_PASSWORD),
        "role": "merchant",
        "age": 35,
        "preferences": ["electronics"],
        "good_rate": 92.0,
        "location": {"type": "Point", "coordinates": [-5.5471, 6.8236]},  # Abidjan, CI
        "created_at": datetime.utcnow()
    }
    merchant_result = await db.users.insert_one(merchant_data)
    merchant_id = str(merchant_result.inserted_id)
    logger.info(f"  ✓ Merchant created: {TEST_MERCHANT_EMAIL} (ID: {merchant_id})")
    
    return buyer_id, merchant_id


async def seed_merchant_profile(db: AsyncIOMotorDatabase, merchant_id: str) -> str:
    """Create merchant shop profile."""
    logger.info("🏪 Creating merchant shop profile...")
    
    merchant_profile = {
        "user_id": merchant_id,
        "shop_name": "TechHub Store",
        "description": "Premium electronics and gadgets from trusted suppliers",
        "location": {"type": "Point", "coordinates": [-5.5471, 6.8236]},
        "total_sales": 0.0,
        "rating": 92.0,
        "created_at": datetime.utcnow()
    }
    
    merchant_result = await db.merchants.insert_one(merchant_profile)
    merchant_profile_id = str(merchant_result.inserted_id)
    logger.info(f"  ✓ Merchant profile created: TechHub Store")
    
    return merchant_profile_id


async def seed_products(db: AsyncIOMotorDatabase, merchant_id: str):
    """Create sample products."""
    logger.info("📦 Creating sample products...")
    
    products = [
        {
            "title": "Wireless Bluetooth Headphones Pro",
            "description": "High-quality wireless headphones with noise cancellation and 30-hour battery life",
            "price": 45.99,
            "original_price": 45.99,
            "images": ["https://via.placeholder.com/300?text=Headphones"],
            "stock": 25,
            "category": "electronics",
            "merchant_id": merchant_id,
            "sku": "TECH-HP-001",
            "weight": 0.25,
            "dimensions": "20x18x8cm",
            "material": "Plastic + Metal",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "USB-C Fast Charging Cable 2M",
            "description": "Durable USB-C charging cable with fast charging support (100W)",
            "price": 9.99,
            "original_price": 9.99,
            "images": ["https://via.placeholder.com/300?text=USB-C"],
            "stock": 150,
            "category": "electronics",
            "merchant_id": merchant_id,
            "sku": "TECH-USBC-001",
            "weight": 0.05,
            "dimensions": "2m",
            "material": "Copper + Nylon",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Smartphone Protective Case",
            "description": "Shockproof phone case with raised bezels",
            "price": 7.99,
            "original_price": 7.99,
            "images": ["https://via.placeholder.com/300?text=Case"],
            "stock": 200,
            "category": "accessories",
            "merchant_id": merchant_id,
            "sku": "TECH-CASE-001",
            "weight": 0.08,
            "dimensions": "15x7x1cm",
            "material": "TPU + PC",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "LED Desk Lamp with USB Charging",
            "description": "Adjustable brightness LED desk lamp",
            "price": 16.99,
            "original_price": 16.99,
            "images": ["https://via.placeholder.com/300?text=Lamp"],
            "stock": 30,
            "category": "home",
            "merchant_id": merchant_id,
            "sku": "TECH-LAMP-001",
            "weight": 0.3,
            "dimensions": "30x10x5cm",
            "material": "Plastic + Metal",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Adjustable Phone Stand",
            "description": "Compatible with all smartphones",
            "price": 5.99,
            "original_price": 5.99,
            "images": ["https://via.placeholder.com/300?text=Stand"],
            "stock": 100,
            "category": "accessories",
            "merchant_id": merchant_id,
            "sku": "TECH-STAND-001",
            "weight": 0.1,
            "dimensions": "10x8x12cm",
            "material": "Metal + Silicone",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Smart Watch Fitness Tracker",
            "description": "Heart rate monitor and sleep tracking",
            "price": 49.99,
            "original_price": 49.99,
            "images": ["https://via.placeholder.com/300?text=Watch"],
            "stock": 15,
            "category": "electronics",
            "merchant_id": merchant_id,
            "sku": "TECH-WATCH-001",
            "weight": 0.05,
            "dimensions": "4x4cm",
            "material": "Silicone + Glass",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Wireless Power Bank 10000mAh",
            "description": "Fast charging power bank with wireless support",
            "price": 24.99,
            "original_price": 24.99,
            "images": ["https://via.placeholder.com/300?text=PowerBank"],
            "stock": 40,
            "category": "electronics",
            "merchant_id": merchant_id,
            "sku": "TECH-PB-001",
            "weight": 0.22,
            "dimensions": "8x8x2cm",
            "material": "Plastic + Metal",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Wireless Keyboard and Mouse Combo",
            "description": "USB wireless keyboard and mouse set",
            "price": 22.99,
            "original_price": 22.99,
            "images": ["https://via.placeholder.com/300?text=KeyboardMouse"],
            "stock": 50,
            "category": "electronics",
            "merchant_id": merchant_id,
            "sku": "TECH-KM-001",
            "weight": 0.4,
            "dimensions": "45x12x2cm",
            "material": "Plastic",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "HDMI Cable 2M (4K)",
            "description": "High-speed HDMI 2.0 cable for 4K resolution",
            "price": 8.99,
            "original_price": 8.99,
            "images": ["https://via.placeholder.com/300?text=HDMI"],
            "stock": 75,
            "category": "electronics",
            "merchant_id": merchant_id,
            "sku": "TECH-HDMI-001",
            "weight": 0.08,
            "dimensions": "2m",
            "material": "Gold-plated",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        },
        {
            "title": "Tempered Glass Screen Protector (Pack of 3)",
            "description": "For smartphones",
            "price": 5.49,
            "original_price": 5.49,
            "images": ["https://via.placeholder.com/300?text=ScreenProtector"],
            "stock": 200,
            "category": "accessories",
            "merchant_id": merchant_id,
            "sku": "TECH-SP-001",
            "weight": 0.05,
            "dimensions": "Pack of 3",
            "material": "Tempered Glass",
            "is_imported": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]
    
    result = await db.products.insert_many(products)
    logger.info(f"  ✓ Created {len(result.inserted_ids)} products")
    
    return [str(id) for id in result.inserted_ids]


async def seed_orders(db: AsyncIOMotorDatabase, buyer_id: str, merchant_id: str, product_ids: list):
    """Create sample orders."""
    logger.info("🛒 Creating sample orders...")
    
    # Order 1 - Delivered
    order1 = {
        "user_id": buyer_id,
        "merchant_id": merchant_id,
        "products": [
            {
                "product_id": product_ids[0],
                "quantity": 1,
                "price": 45.99,
                "title": "Wireless Bluetooth Headphones Pro"
            },
            {
                "product_id": product_ids[1],
                "quantity": 2,
                "price": 9.99,
                "title": "USB-C Fast Charging Cable 2M"
            }
        ],
        "total_amount": 65.97,
        "status": "delivered",
        "payment_method": "orange_money",
        "payment_status": "completed",
        "tracking_number": "TRACK-20240115-001",
        "status_history": [
            {
                "status": "pending",
                "changed_at": datetime.utcnow() - timedelta(days=5),
                "changed_by": buyer_id,
                "note": "Order created"
            },
            {
                "status": "confirmed",
                "changed_at": datetime.utcnow() - timedelta(days=4),
                "changed_by": merchant_id,
                "note": "Order confirmed"
            },
            {
                "status": "shipped",
                "changed_at": datetime.utcnow() - timedelta(days=3),
                "changed_by": merchant_id,
                "note": "Order shipped",
                "tracking_number": "TRACK-20240115-001"
            },
            {
                "status": "delivered",
                "changed_at": datetime.utcnow() - timedelta(days=1),
                "changed_by": "system",
                "note": "Order delivered"
            }
        ],
        "created_at": datetime.utcnow() - timedelta(days=5),
        "updated_at": datetime.utcnow() - timedelta(days=1)
    }
    
    # Order 2 - Confirmed
    order2 = {
        "user_id": buyer_id,
        "merchant_id": merchant_id,
        "products": [
            {
                "product_id": product_ids[4],
                "quantity": 1,
                "price": 5.99,
                "title": "Adjustable Phone Stand"
            }
        ],
        "total_amount": 5.99,
        "status": "confirmed",
        "payment_method": "orange_money",
        "payment_status": "completed",
        "status_history": [
            {
                "status": "pending",
                "changed_at": datetime.utcnow() - timedelta(hours=2),
                "changed_by": buyer_id,
                "note": "Order created"
            },
            {
                "status": "confirmed",
                "changed_at": datetime.utcnow() - timedelta(hours=1),
                "changed_by": merchant_id,
                "note": "Order confirmed"
            }
        ],
        "created_at": datetime.utcnow() - timedelta(hours=2),
        "updated_at": datetime.utcnow() - timedelta(hours=1)
    }
    
    result = await db.orders.insert_many([order1, order2])
    logger.info(f"  ✓ Created {len(result.inserted_ids)} orders")


async def seed_cart(db: AsyncIOMotorDatabase, buyer_id: str, product_ids: list):
    """Create a sample cart with items."""
    logger.info("🛍️ Creating sample cart...")
    
    cart = {
        "user_id": buyer_id,
        "items": [
            {
                "product_id": product_ids[2],
                "quantity": 1,
                "price_at_add": 7.99,
                "added_at": datetime.utcnow()
            },
            {
                "product_id": product_ids[3],
                "quantity": 1,
                "price_at_add": 16.99,
                "added_at": datetime.utcnow()
            }
        ],
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.carts.insert_one(cart)
    logger.info(f"  ✓ Cart created with {len(cart['items'])} items")


async def seed_wishlist(db: AsyncIOMotorDatabase, buyer_id: str, product_ids: list):
    """Create sample wishlist items."""
    logger.info("❤️ Creating wishlist items...")
    
    # Add some products directly to wishlist field in user document
    await db.users.update_one(
        {"_id": ObjectId(buyer_id)},
        {"$set": {"wishlist": product_ids[5:8]}}  # Add products 6, 7, 8 to wishlist
    )
    
    logger.info(f"  ✓ Wishlist created with {len(product_ids[5:8])} items")


async def seed_database():
    """Main seed function."""
    logger.info("=" * 60)
    logger.info("🌱 Starting Alia Database Seeding")
    logger.info("=" * 60)
    
    try:
        # Connect to database
        db = await connect_to_db()
        
        # Optional: clear existing data (comment out to keep existing data)
        await clear_collections(db)
        
        # Seed users
        buyer_id, merchant_id = await seed_users(db)
        
        # Seed merchant profile
        await seed_merchant_profile(db, merchant_id)
        
        # Seed products
        product_ids = await seed_products(db, merchant_id)
        
        # Seed orders
        await seed_orders(db, buyer_id, merchant_id, product_ids)
        
        # Seed cart
        await seed_cart(db, buyer_id, product_ids)
        
        # Seed wishlist
        await seed_wishlist(db, buyer_id, product_ids)
        
        logger.info("=" * 60)
        logger.info("✅ Database seeding completed successfully!")
        logger.info("=" * 60)
        logger.info("\n📝 Test Credentials:")
        logger.info(f"  Buyer:    {TEST_BUYER_EMAIL} / {TEST_BUYER_PASSWORD}")
        logger.info(f"  Merchant: {TEST_MERCHANT_EMAIL} / {TEST_MERCHANT_PASSWORD}")
        logger.info("\n💡 Tips:")
        logger.info("  - Use these credentials to login and test the application")
        logger.info("  - All data is safe to delete and re-seed at any time")
        logger.info("  - Run this script again to reset the database")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error during seeding: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(seed_database())
