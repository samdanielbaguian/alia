"""
Script to remove temporary admin users and test orders from MongoDB.
Run this after testing is complete.

Usage:
    python scripts/cleanup_test_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


async def cleanup_test_data():
    """Remove test users and orders from MongoDB."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    print("🧹 Cleaning up test data from MongoDB...")
    print(f"Database: {settings.MONGODB_DB_NAME}")
    print("-" * 50)
    
    # Delete test users
    test_user_ids = [
        "admin-test-1",
        "admin-test-2",
        "test-admin",
        "test-merchant-1",
        "test-buyer-1"
    ]
    
    print("\n📋 Removing test users...")
    for user_id in test_user_ids:
        result = await db.users.delete_one({"_id": user_id})
        if result.deleted_count > 0:
            print(f"  ✓ Deleted user: {user_id}")
    
    # Delete users by email pattern (test emails)
    email_patterns = ["test@", "admin@test", "@example.com"]
    for pattern in email_patterns:
        result = await db.users.delete_many({"email": {"$regex": pattern, "$options": "i"}})
        if result.deleted_count > 0:
            print(f"  ✓ Deleted {result.deleted_count} user(s) with email pattern: {pattern}")
    
    # Delete test orders
    print("\n📦 Removing test orders...")
    test_order_ids = [
        "order-test-1",
        "order-test-2",
        "test-order-1"
    ]
    
    for order_id in test_order_ids:
        result = await db.orders.delete_one({"_id": order_id})
        if result.deleted_count > 0:
            print(f"  ✓ Deleted order: {order_id}")
    
    # Delete orders with test flag
    result = await db.orders.delete_many({"is_test": True})
    if result.deleted_count > 0:
        print(f"  ✓ Deleted {result.deleted_count} test order(s) with is_test flag")
    
    # Delete test merchants
    print("\n🏪 Removing test merchants...")
    result = await db.merchants.delete_many({
        "$or": [
            {"shop_name": {"$regex": "test", "$options": "i"}},
            {"user_id": {"$in": test_user_ids}}
        ]
    })
    if result.deleted_count > 0:
        print(f"  ✓ Deleted {result.deleted_count} test merchant(s)")
    
    # Verify deletions
    print("\n✅ Verifying cleanup...")
    users_count = await db.users.count_documents({"email": {"$regex": "test", "$options": "i"}})
    orders_count = await db.orders.count_documents({"is_test": True})
    
    print(f"  Remaining test users: {users_count}")
    print(f"  Remaining test orders: {orders_count}")
    
    if users_count == 0 and orders_count == 0:
        print("\n🎉 Cleanup completed successfully!")
    else:
        print("\n⚠️  Some test data may remain. Manual review recommended.")
    
    # Close connection
    client.close()


if __name__ == "__main__":
    asyncio.run(cleanup_test_data())
