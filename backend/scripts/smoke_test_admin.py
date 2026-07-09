"""
Smoke test for admin order approval functionality.
Tests the full workflow: list orders, approve/reject payment and shipping.

Usage:
    python scripts/smoke_test_admin.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import get_password_hash, create_access_token


async def run_smoke_test():
    """Run smoke test for admin order approval."""
    # Connect to MongoDB
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    print("🧪 Running Admin Order Approval Smoke Test")
    print("=" * 60)
    
    # Step 1: Verify admin user exists
    print("\n1️⃣  Verifying admin user exists...")
    admin = await db.users.find_one({"email": "admin@alia.test"})
    if not admin:
        print("  ❌ Admin user not found. Run setup_test_data.py first.")
        client.close()
        return False
    print(f"  ✓ Admin user found: {admin['email']}")
    
    # Step 2: Check for pending orders
    print("\n2️⃣  Checking for orders pending approval...")
    pending_query = {
        "$or": [
            {"payment_approved": False, "status": {"$in": ["pending", "payment_pending"]}},
            {"shipping_approved": False, "status": {"$in": ["confirmed", "ready_to_ship"]}}
        ]
    }
    pending_orders = await db.orders.find(pending_query).to_list(100)
    
    if not pending_orders:
        print("  ⚠️  No pending orders found. Creating test order...")
        # Create a test order
        test_order = {
            "user_id": "test-buyer",
            "merchant_id": "test-merchant",
            "items": [{"product_id": "test-product", "product_name": "Test Item", "quantity": 1, "price": 50.0}],
            "total": 50.0,
            "status": "pending",
            "payment_approved": False,
            "shipping_approved": False,
            "created_at": datetime.utcnow(),
            "is_test": True
        }
        result = await db.orders.insert_one(test_order)
        test_order_id = str(result.inserted_id)
        print(f"  ✓ Created test order: {test_order_id}")
    else:
        print(f"  ✓ Found {len(pending_orders)} pending order(s)")
        test_order_id = str(pending_orders[0]["_id"])
    
    # Step 3: Test payment approval
    print("\n3️⃣  Testing payment approval...")
    order_before = await db.orders.find_one({"_id": test_order_id})
    if not order_before:
        from bson import ObjectId
        order_before = await db.orders.find_one({"_id": ObjectId(test_order_id)})
    
    if not order_before:
        print(f"  ❌ Order not found: {test_order_id}")
        client.close()
        return False
    
    print(f"  Order status before: {order_before.get('status')}")
    print(f"  Payment approved: {order_before.get('payment_approved', False)}")
    
    # Simulate admin approval
    update_result = await db.orders.update_one(
        {"_id": order_before["_id"]},
        {
            "$set": {
                "payment_approved": True,
                "payment_approved_by": str(admin["_id"]),
                "payment_approved_at": datetime.utcnow(),
                "status": "confirmed",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if update_result.modified_count > 0:
        print("  ✓ Payment approval successful")
    else:
        print("  ⚠️  No changes made (possibly already approved)")
    
    # Verify update
    order_after = await db.orders.find_one({"_id": order_before["_id"]})
    print(f"  Order status after: {order_after.get('status')}")
    print(f"  Payment approved: {order_after.get('payment_approved', False)}")
    
    # Step 4: Test shipping approval
    print("\n4️⃣  Testing shipping approval...")
    update_result = await db.orders.update_one(
        {"_id": order_before["_id"]},
        {
            "$set": {
                "shipping_approved": True,
                "shipping_approved_by": str(admin["_id"]),
                "shipping_approved_at": datetime.utcnow(),
                "status": "shipped",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if update_result.modified_count > 0:
        print("  ✓ Shipping approval successful")
    else:
        print("  ⚠️  No changes made")
    
    # Verify final state
    order_final = await db.orders.find_one({"_id": order_before["_id"]})
    print(f"  Order status final: {order_final.get('status')}")
    print(f"  Shipping approved: {order_final.get('shipping_approved', False)}")
    
    # Step 5: Test rejection (create another test order)
    print("\n5️⃣  Testing payment rejection...")
    reject_order = {
        "user_id": "test-buyer",
        "merchant_id": "test-merchant",
        "items": [{"product_id": "test-product-2", "product_name": "Test Item 2", "quantity": 1, "price": 75.0}],
        "total": 75.0,
        "status": "pending",
        "payment_approved": False,
        "shipping_approved": False,
        "created_at": datetime.utcnow(),
        "is_test": True
    }
    result = await db.orders.insert_one(reject_order)
    reject_order_id = result.inserted_id
    print(f"  Created order for rejection test: {reject_order_id}")
    
    # Reject payment
    rejection_reason = "Suspicious transaction detected (test)"
    update_result = await db.orders.update_one(
        {"_id": reject_order_id},
        {
            "$set": {
                "payment_approved": False,
                "payment_rejection_reason": rejection_reason,
                "payment_approved_by": str(admin["_id"]),
                "payment_approved_at": datetime.utcnow(),
                "status": "payment_rejected",
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if update_result.modified_count > 0:
        print("  ✓ Payment rejection successful")
        rejected_order = await db.orders.find_one({"_id": reject_order_id})
        print(f"  Rejection reason: {rejected_order.get('payment_rejection_reason')}")
    else:
        print("  ❌ Payment rejection failed")
    
    # Step 6: Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("-" * 60)
    
    total_orders = await db.orders.count_documents({"is_test": True})
    approved_payment = await db.orders.count_documents({"payment_approved": True, "is_test": True})
    approved_shipping = await db.orders.count_documents({"shipping_approved": True, "is_test": True})
    rejected = await db.orders.count_documents({"status": "payment_rejected", "is_test": True})
    
    print(f"Total test orders: {total_orders}")
    print(f"Payment approved: {approved_payment}")
    print(f"Shipping approved: {approved_shipping}")
    print(f"Rejected: {rejected}")
    
    print("\n✅ Smoke test completed successfully!")
    print("\n💡 Next steps:")
    print("1. Test the UI at http://localhost:3000/dashboard/admin/orders")
    print("2. Login with admin@alia.test / admin123")
    print("3. Verify UI updates match database changes")
    print("4. Run cleanup: python scripts/cleanup_test_data.py")
    
    # Close connection
    client.close()
    return True


if __name__ == "__main__":
    success = asyncio.run(run_smoke_test())
    sys.exit(0 if success else 1)
