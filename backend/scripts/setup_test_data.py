"""
Script to create test admin user and test orders for smoke testing.
Run this to set up data for testing the admin approval UI.

Usage:
    python scripts/setup_test_data.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from bson import ObjectId

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import get_password_hash


async def setup_test_data():
    """Create test admin user and test orders."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    print("🚀 Setting up test data for admin approval testing...")
    print(f"Database: {settings.MONGODB_DB_NAME}")
    print("-" * 50)
    
    # Create test admin user
    print("\n👤 Creating test admin user...")
    admin_password = "admin123"  # Default password for testing
    admin_user = {
        "_id": "admin-test-" + str(ObjectId()),
        "email": "admin@alia.test",
        "password_hash": get_password_hash(admin_password),
        "role": "admin",
        "age": 30,
        "preferences": [],
        "good_rate": 100.0,
        "created_at": datetime.utcnow(),
        "is_test": True
    }
    
    # Check if admin already exists
    existing = await db.users.find_one({"email": admin_user["email"]})
    if existing:
        print(f"  ⚠️  Admin user already exists: {admin_user['email']}")
        admin_user["_id"] = str(existing["_id"])
    else:
        await db.users.insert_one(admin_user)
        print(f"  ✓ Created admin user:")
        print(f"    Email: {admin_user['email']}")
        print(f"    Password: {admin_password}")
        print(f"    ID: {admin_user['_id']}")
    
    # Create test merchant user
    print("\n🏪 Creating test merchant user...")
    merchant_password = "merchant123"
    merchant_user = {
        "_id": "merchant-test-" + str(ObjectId()),
        "email": "merchant@alia.test",
        "password_hash": get_password_hash(merchant_password),
        "role": "merchant",
        "age": 35,
        "preferences": ["electronics"],
        "good_rate": 85.0,
        "created_at": datetime.utcnow(),
        "is_test": True
    }
    
    existing_merchant = await db.users.find_one({"email": merchant_user["email"]})
    if existing_merchant:
        print(f"  ⚠️  Merchant user already exists: {merchant_user['email']}")
        merchant_user["_id"] = str(existing_merchant["_id"])
    else:
        await db.users.insert_one(merchant_user)
        print(f"  ✓ Created merchant user: {merchant_user['email']}")
        
        # Create merchant profile
        merchant_profile = {
            "user_id": merchant_user["_id"],
            "shop_name": "Test Electronics Store",
            "description": "Test store for admin approval testing",
            "total_sales": 0.0,
            "rating": 85.0,
            "created_at": datetime.utcnow(),
            "is_test": True
        }
        await db.merchants.insert_one(merchant_profile)
        print(f"    ✓ Created merchant profile: {merchant_profile['shop_name']}")
    
    # Create test buyer user
    print("\n🛒 Creating test buyer user...")
    buyer_password = "buyer123"
    buyer_user = {
        "_id": "buyer-test-" + str(ObjectId()),
        "email": "buyer@alia.test",
        "password_hash": get_password_hash(buyer_password),
        "role": "buyer",
        "age": 28,
        "preferences": ["electronics", "fashion"],
        "good_rate": 95.0,
        "created_at": datetime.utcnow(),
        "is_test": True
    }
    
    existing_buyer = await db.users.find_one({"email": buyer_user["email"]})
    if existing_buyer:
        print(f"  ⚠️  Buyer user already exists: {buyer_user['email']}")
        buyer_user["_id"] = str(existing_buyer["_id"])
    else:
        await db.users.insert_one(buyer_user)
        print(f"  ✓ Created buyer user: {buyer_user['email']}")
    
    # Create test orders pending approval
    print("\n📦 Creating test orders...")
    
    test_orders = [
        {
            "_id": ObjectId(),
            "user_id": buyer_user["_id"],
            "merchant_id": merchant_user["_id"],
            "items": [
                {
                    "product_id": "test-product-1",
                    "product_name": "Test Wireless Headphones",
                    "quantity": 2,
                    "price": 59.99
                }
            ],
            "total": 119.98,
            "status": "pending",
            "payment_approved": False,
            "shipping_approved": False,
            "shipping_address": {
                "street": "123 Test St",
                "city": "Test City",
                "country": "Test Country",
                "postal_code": "12345"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status_history": [
                {
                    "status": "pending",
                    "changed_at": datetime.utcnow(),
                    "note": "Order created and awaiting admin payment approval"
                }
            ],
            "is_test": True
        },
        {
            "_id": ObjectId(),
            "user_id": buyer_user["_id"],
            "merchant_id": merchant_user["_id"],
            "items": [
                {
                    "product_id": "test-product-2",
                    "product_name": "Test Smart Watch",
                    "quantity": 1,
                    "price": 199.99
                }
            ],
            "total": 199.99,
            "status": "confirmed",
            "payment_approved": True,
            "payment_approved_at": datetime.utcnow(),
            "shipping_approved": False,
            "shipping_address": {
                "street": "456 Test Ave",
                "city": "Test City",
                "country": "Test Country",
                "postal_code": "67890"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status_history": [
                {
                    "status": "pending",
                    "changed_at": datetime.utcnow(),
                    "note": "Order created"
                },
                {
                    "status": "confirmed",
                    "changed_at": datetime.utcnow(),
                    "note": "Payment approved automatically for testing"
                }
            ],
            "is_test": True
        },
        {
            "_id": ObjectId(),
            "user_id": buyer_user["_id"],
            "merchant_id": merchant_user["_id"],
            "items": [
                {
                    "product_id": "test-product-3",
                    "product_name": "Test Laptop",
                    "quantity": 1,
                    "price": 899.99
                }
            ],
            "total": 899.99,
            "status": "payment_pending",
            "payment_approved": False,
            "shipping_approved": False,
            "shipping_address": {
                "street": "789 Test Blvd",
                "city": "Test City",
                "country": "Test Country",
                "postal_code": "11111"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status_history": [
                {
                    "status": "payment_pending",
                    "changed_at": datetime.utcnow(),
                    "note": "Awaiting payment approval"
                }
            ],
            "is_test": True
        }
    ]
    
    for i, order in enumerate(test_orders, 1):
        await db.orders.insert_one(order)
        print(f"  ✓ Created test order {i}:")
        print(f"    ID: {order['_id']}")
        print(f"    Status: {order['status']}")
        print(f"    Total: ${order['total']:.2f}")
        print(f"    Payment Approved: {order['payment_approved']}")
        print(f"    Shipping Approved: {order['shipping_approved']}")
    
    print("\n" + "=" * 50)
    print("✅ Test data setup completed!")
    print("\n📝 Test Credentials:")
    print("-" * 50)
    print(f"Admin:    {admin_user['email']} / {admin_password}")
    print(f"Merchant: {merchant_user['email']} / {merchant_password}")
    print(f"Buyer:    {buyer_user['email']} / {buyer_password}")
    print("\n🧪 Next Steps:")
    print("1. Login to dashboard with admin credentials")
    print("2. Navigate to /dashboard/admin/orders")
    print("3. Test approve/reject payment and shipping")
    print("4. Run cleanup script when done: python scripts/cleanup_test_data.py")
    
    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(setup_test_data())
