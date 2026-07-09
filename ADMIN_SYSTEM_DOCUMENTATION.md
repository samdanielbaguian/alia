# Admin Management System - Implementation Guide

## Overview
This document describes the comprehensive admin management system implemented for the Alia marketplace platform. Admins now have complete control over users, products, merchants, and orders.

## Features Implemented

### 1. User Management (`/dashboard/admin/users`)

**Capabilities:**
- List all users with filtering by role (admin/merchant/buyer)
- Search users by email
- View detailed user profiles with statistics
- Suspend/unsuspend user accounts
- Ban/unban users
- Reset user passwords
- View user activity logs

**Endpoints Used:**
- `GET /api/v1/admin/users` - List users with filters
- `GET /api/v1/admin/users/{user_id}` - Get user details
- `PUT /api/v1/admin/users/{user_id}/suspend` - Suspend/unsuspend user
- `PUT /api/v1/admin/users/{user_id}/ban` - Ban/unban user
- `POST /api/v1/admin/users/{user_id}/reset-password` - Reset password
- `GET /api/v1/admin/users/{user_id}/activity` - View activity logs
- `DELETE /api/v1/admin/users/{user_id}` - Delete user (soft delete)

**UI Components:**
- `alia-dashboard/app/dashboard/admin/users/page.js` - User list with filters
- `alia-dashboard/app/dashboard/admin/users/[id]/page.js` - User detail page

**Features:**
- Status badges (Active/Suspended/Banned)
- Role-based color coding
- Action buttons with loading states
- Confirmation dialogs for destructive actions
- Admin users cannot suspend/ban other admins
- Activity timeline with timestamp and admin tracking

---

### 2. Product Management (`/dashboard/admin/products`)

**Capabilities:**
- List all products with status filtering (all/pending/approved/rejected)
- Search products by name or merchant
- View product statistics (total, pending, approved, rejected)
- Approve/reject individual products
- Bulk approve multiple products
- Bulk delete multiple products
- View rejection reasons

**Endpoints Used:**
- `GET /api/v1/admin/products` - List all products
- `GET /api/v1/admin/products/pending` - List pending products
- `PUT /api/v1/admin/products/{product_id}/approve` - Approve/reject product
- `POST /api/v1/admin/products/bulk-approve` - Bulk approve products
- `POST /api/v1/admin/products/bulk-delete` - Bulk delete products
- `DELETE /api/v1/admin/products/{product_id}` - Delete single product
- `GET /api/v1/admin/products/stats` - Get product statistics

**UI Components:**
- `alia-dashboard/app/dashboard/admin/products/page.js` - Product moderation interface

**Features:**
- Checkbox selection for bulk operations
- Statistics dashboard showing pending/approved/rejected counts
- Status badges with color coding
- Merchant information display
- Inline rejection reason display
- Approve/Reject buttons with confirmation
- Select all/deselect all functionality

---

### 3. Merchant Management (`/dashboard/admin/merchants`)

**Capabilities:**
- List all merchants with status filtering (all/pending/verified/suspended)
- Search merchants by name or email
- View merchant statistics (products, sales, orders)
- Verify/reject merchant applications
- Suspend/unsuspend merchant accounts
- Set custom commission rates per merchant
- View total platform revenue

**Endpoints Used:**
- `GET /api/v1/admin/merchants` - List all merchants
- `GET /api/v1/admin/merchants/pending` - List pending merchants
- `PUT /api/v1/admin/merchants/{merchant_id}/verify` - Verify/reject merchant
- `PUT /api/v1/admin/merchants/{merchant_id}/suspend` - Suspend/unsuspend merchant
- `PUT /api/v1/admin/merchants/{merchant_id}/commission` - Set commission rate
- `GET /api/v1/admin/merchants/stats` - Get merchant statistics

**UI Components:**
- `alia-dashboard/app/dashboard/admin/merchants/page.js` - Merchant verification interface

**Features:**
- Statistics showing total products, sales, and orders per merchant
- Commission rate display and editor
- Verify/Reject workflow for new merchants
- Suspend functionality (cascades to merchant's products)
- Revenue aggregation and display
- Status badges (Pending/Verified/Suspended)
- Inline reason display for suspensions/rejections

---

### 4. Order Approvals (`/dashboard/admin/orders`)

**Existing Functionality Enhanced:**
- List pending orders requiring approval
- Approve/reject payment approvals
- Approve/reject shipping approvals
- View order details and merchant information
- Modal-based approval workflow

**Endpoints Used:**
- `GET /api/v1/admin/orders` - List pending orders
- `POST /api/v1/admin/orders/{order_id}/approve-payment` - Approve payment
- `POST /api/v1/admin/orders/{order_id}/reject-payment` - Reject payment
- `POST /api/v1/admin/orders/{order_id}/approve-shipping` - Approve shipping
- `POST /api/v1/admin/orders/{order_id}/reject-shipping` - Reject shipping

---

### 5. Admin Overview Dashboard (`/dashboard/admin`)

**Features:**
- Platform-wide statistics display
- Product count with pending/approved breakdown
- Merchant count with pending/suspended status
- Total revenue from all sales
- "Needs Review" counter (pending products + merchants)
- Quick action cards linking to each admin section
- Real-time stats loading with error handling

**UI Components:**
- `alia-dashboard/app/dashboard/admin/page.js` - Admin overview dashboard

---

## Navigation Updates

### Sidebar Changes (`alia-dashboard/layout/Sidebar.js`)

Added new admin menu items:
- 🔒 Admin Overview
- 📦 Order Approvals
- 👥 User Management (NEW)
- 📦 Product Approval (NEW)
- 🏪 Merchant Verification (NEW)

Icons imported:
- `SupervisorAccount` for users
- `Category` for products
- `Business` for merchants

The admin section only appears when the user is logged in as an admin.

---

## API Client Updates

### AdminApi.js Expansion (`alia-dashboard/utils/AdminApi.js`)

**Organized into 4 sections:**

#### ORDER MANAGEMENT
- `listPendingOrders()`
- `approvePayment(orderId, reason)`
- `rejectPayment(orderId, reason)`
- `approveShipping(orderId, reason)`
- `rejectShipping(orderId, reason)`
- `getOrder(orderId)`

#### USER MANAGEMENT (NEW)
- `listUsers(params)` - Filter by role, search
- `getUser(userId)` - Get details with stats
- `updateUser(userId, data)` - Update user data
- `suspendUser(userId, isSuspended, reason)` - Suspend/unsuspend
- `banUser(userId, isBanned, reason)` - Ban/unban
- `resetUserPassword(userId, newPassword)` - Force password reset
- `deleteUser(userId)` - Soft delete user
- `getUserActivity(userId)` - Get activity logs

#### PRODUCT MANAGEMENT (NEW)
- `listProducts(params)` - List with filters
- `listPendingProducts()` - Pending approval only
- `approveProduct(productId, isApproved, reason)` - Approve/reject
- `updateProduct(productId, data)` - Update product
- `deleteProduct(productId)` - Soft delete
- `bulkApproveProducts(productIds)` - Bulk approve
- `bulkDeleteProducts(productIds)` - Bulk delete
- `getProductsStats()` - Get statistics

#### MERCHANT MANAGEMENT (NEW)
- `listMerchants(params)` - List with filters
- `listPendingMerchants()` - Pending verification only
- `verifyMerchant(merchantId, isVerified, reason)` - Verify/reject
- `suspendMerchant(merchantId, isSuspended, reason)` - Suspend/unsuspend
- `setMerchantCommission(merchantId, commissionRate)` - Set rate
- `getMerchant(merchantId)` - Get details
- `getMerchantsStats()` - Get statistics

**Total API Functions:** ~40 functions

---

## Backend Routes Created

### 1. Admin Users Route (`backend/app/api/routes/admin_users.py`)

**8 Endpoints:**
- `GET /api/v1/admin/users`
- `GET /api/v1/admin/users/{user_id}`
- `PUT /api/v1/admin/users/{user_id}`
- `PUT /api/v1/admin/users/{user_id}/suspend`
- `PUT /api/v1/admin/users/{user_id}/ban`
- `POST /api/v1/admin/users/{user_id}/reset-password`
- `DELETE /api/v1/admin/users/{user_id}`
- `GET /api/v1/admin/users/{user_id}/activity`

**Key Features:**
- Admin-only access via `get_current_admin` dependency
- Prevents admins from deleting/suspending other admins
- Password hashing for resets
- Activity logging with admin_id and timestamps
- Aggregation pipeline for user statistics (orders, spending)
- Merchant stats include product count and total sales

### 2. Admin Products Route (`backend/app/api/routes/admin_products.py`)

**8 Endpoints:**
- `GET /api/v1/admin/products`
- `GET /api/v1/admin/products/pending`
- `PUT /api/v1/admin/products/{product_id}/approve`
- `PUT /api/v1/admin/products/{product_id}`
- `DELETE /api/v1/admin/products/{product_id}`
- `POST /api/v1/admin/products/bulk-approve`
- `POST /api/v1/admin/products/bulk-delete`
- `GET /api/v1/admin/products/stats`

**Key Features:**
- Soft-delete pattern with `is_deleted` flag
- Merchant information enrichment via user lookup
- Bulk operations use MongoDB `update_many`
- Approval status tracking with reasons
- Statistics aggregation with `_id` filtering
- Admin tracking for all modifications

### 3. Admin Merchants Route (`backend/app/api/routes/admin_merchants.py`)

**7 Endpoints:**
- `GET /api/v1/admin/merchants`
- `GET /api/v1/admin/merchants/pending`
- `PUT /api/v1/admin/merchants/{merchant_id}/verify`
- `PUT /api/v1/admin/merchants/{merchant_id}/suspend`
- `PUT /api/v1/admin/merchants/{merchant_id}/commission`
- `GET /api/v1/admin/merchants/{merchant_id}`
- `GET /api/v1/admin/merchants/stats`

**Key Features:**
- Cascading suspension deactivates all merchant products
- Commission rate validation (0-100%)
- Revenue aggregation via MongoDB pipeline
- Product, sales, and order stats per merchant
- Verification workflow tracking
- Admin action logging

### 4. Main App Registration (`backend/app/main.py`)

**Router Registrations:**
```python
app.include_router(admin_orders.router, prefix="/api/v1/admin", tags=["Admin - Orders"])
app.include_router(admin_users.router, prefix="/api/v1/admin", tags=["Admin - Users"])
app.include_router(admin_products.router, prefix="/api/v1/admin", tags=["Admin - Products"])
app.include_router(admin_merchants.router, prefix="/api/v1/admin", tags=["Admin - Merchants"])
```

All admin routes are prefixed with `/api/v1/admin` and tagged for API documentation.

---

## Security & Access Control

### Authentication Guards

**Backend:**
- All admin routes use `get_current_admin` dependency
- Validates JWT token from `Authorization: Bearer <token>` header
- Checks user role === "admin"
- Returns 403 Forbidden for non-admin users

**Frontend:**
- `useAdminCheck()` hook checks role from localStorage
- Redirects non-admin users to `/dashboard`
- Protected routes check auth before rendering
- Role stored in localStorage after login from `/auth/me` endpoint

### Authorization Rules

- Admins cannot suspend, ban, or delete other admin accounts
- All admin actions logged with admin_id and timestamp
- Soft-delete pattern preserves data integrity
- Cascading suspensions maintain platform integrity

---

## Database Schema Additions

### Users Collection Updates
```javascript
{
  is_suspended: Boolean,
  suspension_reason: String,
  suspended_at: DateTime,
  suspended_by: ObjectId,
  is_banned: Boolean,
  ban_reason: String,
  banned_at: DateTime,
  banned_by: ObjectId,
  activity_log: [
    {
      action: String,
      timestamp: DateTime,
      admin_id: ObjectId,
      reason: String
    }
  ]
}
```

### Products Collection Updates
```javascript
{
  is_approved: Boolean | null,  // null = pending
  rejection_reason: String,
  approved_at: DateTime,
  approved_by: ObjectId,
  is_deleted: Boolean
}
```

### Merchants (Users with role="merchant") Updates
```javascript
{
  is_verified: Boolean,
  rejection_reason: String,
  verified_at: DateTime,
  verified_by: ObjectId,
  commission_rate: Number,  // percentage (0-100)
  is_suspended: Boolean,
  suspension_reason: String,
  suspended_at: DateTime,
  suspended_by: ObjectId
}
```

---

## Testing

### Test Scripts Created (`backend/scripts/`)

1. **setup_test_data.py** - Creates test users and orders
2. **cleanup_test_data.py** - Removes all test data
3. **smoke_test_admin.py** - Automated approval workflow test
4. **README.md** - Complete testing documentation

**Note:** Test scripts require `pymongo` module to be installed:
```bash
pip install pymongo
```

---

## Usage Examples

### Suspending a User
```javascript
await adminApi.suspendUser("user_id_here", true, "Violating terms of service")
```

### Approving Multiple Products
```javascript
const productIds = ["prod1", "prod2", "prod3"]
await adminApi.bulkApproveProducts(productIds)
```

### Setting Merchant Commission
```javascript
await adminApi.setMerchantCommission("merchant_id", 15.5)  // 15.5%
```

### Verifying a Merchant
```javascript
await adminApi.verifyMerchant("merchant_id", true, null)  // Approve
await adminApi.verifyMerchant("merchant_id", false, "Incomplete documentation")  // Reject
```

---

## UI/UX Features

### Design Patterns
- **Status Badges:** Color-coded badges for quick status identification
- **Confirmation Dialogs:** Browser confirm() for destructive actions
- **Loading States:** Disabled buttons with loading indicators
- **Toast/Alert Notifications:** Success/error feedback after actions
- **Search & Filters:** Real-time filtering for large datasets
- **Bulk Operations:** Checkbox selection with batch actions
- **Statistics Dashboard:** Visual overview of platform metrics

### Accessibility
- Semantic HTML structure
- Keyboard navigation support
- Focus states on interactive elements
- Color contrast for readability
- Descriptive button labels

---

## Future Enhancements

### Potential Additions
1. **Export Functionality:** CSV/Excel export for users, products, merchants
2. **Advanced Filters:** Date range, multi-select filters, saved filters
3. **Audit Trail:** Complete admin action logging and reporting
4. **Email Notifications:** Notify users/merchants of admin actions
5. **Role Management:** Create custom roles with granular permissions
6. **Dashboard Analytics:** Charts and graphs for platform metrics
7. **Scheduled Reports:** Automated daily/weekly admin reports
8. **Bulk Import:** CSV import for bulk user/product creation

---

## File Structure

```
alia-dashboard/
├── app/
│   └── dashboard/
│       └── admin/
│           ├── page.js (Overview)
│           ├── orders/
│           │   └── page.js (Order approvals)
│           ├── users/
│           │   ├── page.js (User list)
│           │   └── [id]/
│           │       └── page.js (User details)
│           ├── products/
│           │   └── page.js (Product moderation)
│           └── merchants/
│               └── page.js (Merchant verification)
├── utils/
│   ├── AdminApi.js (API client - 40+ functions)
│   ├── authUtils.js (Auth helpers)
│   └── protectedRoute.js (Route guards)
└── layout/
    └── Sidebar.js (Navigation with admin section)

backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── admin_orders.py (Order approvals)
│   │       ├── admin_users.py (User management - NEW)
│   │       ├── admin_products.py (Product moderation - NEW)
│   │       └── admin_merchants.py (Merchant verification - NEW)
│   └── main.py (Router registration)
└── scripts/
    ├── setup_test_data.py
    ├── cleanup_test_data.py
    ├── smoke_test_admin.py
    └── README.md
```

---

## Deployment Checklist

- [ ] Ensure MongoDB has proper indexes on user/product/merchant collections
- [ ] Set up admin user accounts with role="admin"
- [ ] Configure JWT secret and token expiration
- [ ] Test all admin endpoints with Postman/Thunder Client
- [ ] Verify role-based access control in production
- [ ] Set up monitoring for admin actions
- [ ] Create backup strategy for user/product data
- [ ] Document admin credentials securely
- [ ] Train admin staff on platform management

---

## Support & Maintenance

### Common Issues

**Issue:** Admin not seeing admin section in sidebar
**Solution:** Ensure user has `role: "admin"` in database and localStorage.user is set correctly after login

**Issue:** API returns 403 Forbidden
**Solution:** Check JWT token in Authorization header and verify user role

**Issue:** Bulk operations failing
**Solution:** Check MongoDB write permissions and ObjectId validation

### Logs to Monitor
- Admin action logs in user activity
- Product approval/rejection logs
- Merchant verification logs
- Failed authentication attempts

---

## Contributors

**Implementation Date:** December 2024
**Backend Framework:** FastAPI (Python)
**Frontend Framework:** Next.js 13+ (React)
**Database:** MongoDB with Motor async driver

---

**End of Documentation**
