# Admin Management Scripts

This directory contains scripts for managing test data and verifying the admin order approval functionality.

## Prerequisites

Ensure MongoDB is running and the backend environment is configured:

```bash
# Make sure MongoDB connection string is set in .env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=alia
```

## Scripts Overview

### 1. Setup Test Data
Creates test admin user, merchant, buyer, and sample orders for testing.

```bash
cd backend
python scripts/setup_test_data.py
```

**Output:**
- Admin user: `admin@alia.test` / `admin123`
- Merchant user: `merchant@alia.test` / `merchant123`
- Buyer user: `buyer@alia.test` / `buyer123`
- 3 test orders with different statuses

### 2. Smoke Test Admin Approval
Runs automated tests to verify admin approval functionality.

```bash
cd backend
python scripts/smoke_test_admin.py
```

**Tests:**
- ✓ Admin user verification
- ✓ List pending orders
- ✓ Approve payment
- ✓ Approve shipping
- ✓ Reject payment with reason
- ✓ Database state verification

### 3. Cleanup Test Data
Removes all test users and orders created during testing.

```bash
cd backend
python scripts/cleanup_test_data.py
```

**Removes:**
- Test users (admin-test-*, merchant-test-*, buyer-test-*)
- Test orders (flagged with `is_test: true`)
- Test merchant profiles
- All data with test email patterns

## Complete Testing Workflow

### Step 1: Setup
```bash
# Start MongoDB (if not already running)
# Windows:
# mongod --dbpath C:\data\db

# Install dependencies
cd backend
pip install -r requirements.txt

# Create test data
python scripts/setup_test_data.py
```

### Step 2: Start Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

### Step 3: Start Frontend
```bash
cd alia-dashboard
npm install
npm run dev
```

### Step 4: Manual UI Testing

1. **Login as Admin**
   - Navigate to: http://localhost:3000
   - Email: `admin@alia.test`
   - Password: `admin123`

2. **Access Admin Panel**
   - Look for "Admin" section in sidebar
   - Click "Order Approvals"
   - URL: http://localhost:3000/dashboard/admin/orders

3. **Test Payment Approval**
   - Find order with status "pending" or "payment_pending"
   - Click "Approve Payment" button
   - Verify success message appears
   - Check status badge changes to "confirmed"

4. **Test Payment Rejection**
   - Find another pending order
   - Click "Reject Payment" button
   - Enter rejection reason in modal
   - Click "Confirm Reject"
   - Verify status changes to "payment_rejected"

5. **Test Shipping Approval**
   - Find order with status "confirmed"
   - Click "Approve Shipping" button
   - Verify success message
   - Check status changes to "shipped"

6. **Test Shipping Rejection**
   - Find order ready for shipping
   - Click "Reject Shipping"
   - Enter reason and confirm
   - Verify status changes to "shipping_rejected"

### Step 5: Automated Verification
```bash
cd backend
python scripts/smoke_test_admin.py
```

### Step 6: Cleanup
```bash
cd backend
python scripts/cleanup_test_data.py
```

## API Endpoints Used

### List Pending Orders
```
GET /api/v1/admin/orders
Authorization: Bearer <admin_token>

Response:
{
  "orders": [
    {
      "_id": "...",
      "status": "pending",
      "payment_approved": false,
      "shipping_approved": false,
      "total": 119.98,
      ...
    }
  ]
}
```

### Approve Payment
```
POST /api/v1/admin/orders/{order_id}/approve-payment
Authorization: Bearer <admin_token>

Response:
{
  "ok": true,
  "order_id": "..."
}
```

### Reject Payment
```
POST /api/v1/admin/orders/{order_id}/reject-payment
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "reason": "Suspicious transaction"
}

Response:
{
  "ok": true,
  "order_id": "..."
}
```

### Approve Shipping
```
POST /api/v1/admin/orders/{order_id}/approve-shipping
Authorization: Bearer <admin_token>

Response:
{
  "ok": true,
  "order_id": "..."
}
```

### Reject Shipping
```
POST /api/v1/admin/orders/{order_id}/reject-shipping
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "reason": "Address verification failed"
}

Response:
{
  "ok": true,
  "order_id": "..."
}
```

## Troubleshooting

### Issue: "Admin user not found"
**Solution:** Run `python scripts/setup_test_data.py` first

### Issue: "Access denied. Admin only"
**Solution:** 
1. Verify user role is "admin" in database
2. Check localStorage for user object with correct role
3. Re-login to fetch updated user profile

### Issue: "No pending orders"
**Solution:** Create test orders using setup script or manually via API

### Issue: Scripts can't connect to MongoDB
**Solution:**
1. Check MongoDB is running: `mongosh` or `mongo`
2. Verify MONGODB_URL in backend/.env
3. Ensure firewall allows connections

### Issue: Token authentication fails
**Solution:**
1. Check JWT_SECRET is set in backend/.env
2. Verify token is stored in localStorage as "access_token"
3. Check token expiration (default: 7 days)

## Database Schema

### Users Collection
```javascript
{
  "_id": "admin-test-...",
  "email": "admin@alia.test",
  "password_hash": "...",
  "role": "admin",  // "admin" | "merchant" | "buyer"
  "age": 30,
  "preferences": [],
  "good_rate": 100.0,
  "created_at": ISODate("..."),
  "is_test": true  // Flag for cleanup
}
```

### Orders Collection
```javascript
{
  "_id": ObjectId("..."),
  "user_id": "buyer-id",
  "merchant_id": "merchant-id",
  "items": [...],
  "total": 119.98,
  "status": "pending",
  "payment_approved": false,
  "payment_approved_by": "admin-id",  // Set after approval
  "payment_approved_at": ISODate("..."),
  "payment_rejection_reason": "...",  // Set if rejected
  "shipping_approved": false,
  "shipping_approved_by": "admin-id",
  "shipping_approved_at": ISODate("..."),
  "shipping_rejection_reason": "...",
  "created_at": ISODate("..."),
  "updated_at": ISODate("..."),
  "status_history": [...],
  "is_test": true
}
```

## Security Notes

- Test admin credentials should **NEVER** be used in production
- Change default passwords before deploying
- Implement proper admin user management with invitation system
- Add 2FA for admin accounts in production
- Audit all admin actions with proper logging
- Implement IP whitelisting for admin panel access

## Future Enhancements

- [ ] Email notifications for approval/rejection
- [ ] Bulk approve/reject operations
- [ ] Advanced filtering and search
- [ ] Export orders to CSV/Excel
- [ ] Admin activity audit log
- [ ] Real-time notifications via WebSocket
- [ ] Role-based permissions (super admin, moderator, etc.)
