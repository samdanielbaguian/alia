# Merchant Dashboard Endpoints Documentation

This document describes the new REST API endpoints for the merchant dashboard.

## Authentication

All endpoints require merchant authentication via JWT Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

The authenticated user must have the role `merchant`.

## Endpoints

### 1. GET `/api/merchants/me/orders/stats`

Get order statistics time series for dashboard charts.

**Query Parameters:**
- `from` (optional): Start date in YYYY-MM-DD format. Defaults to 30 days ago.
- `to` (optional): End date in YYYY-MM-DD format. Defaults to today.

**Response:**
```json
{
  "period": {
    "from": "2026-01-01",
    "to": "2026-01-31"
  },
  "stats": [
    {
      "date": "2026-01-01",
      "orders_count": 5,
      "total_amount": 125000,
      "orders_pending": 1,
      "orders_confirmed": 2,
      "orders_shipped": 1,
      "orders_delivered": 1,
      "orders_cancelled": 0
    }
  ],
  "summary": {
    "total_orders": 133,
    "total_sales": 4590000,
    "avg_order_value": 34511.28
  }
}
```

**Use Case:** Display daily sales and orders charts in the merchant dashboard.

---

### 2. GET `/api/merchants/me/bestsellers`

Get bestselling products and categories for a specified period.

**Query Parameters:**
- `from` (optional): Start date in YYYY-MM-DD format. Defaults to first day of current month.
- `to` (optional): End date in YYYY-MM-DD format. Defaults to today.
- `limit` (optional): Number of top items to return. Default: 10, Max: 50.

**Response:**
```json
{
  "period": {
    "from": "2026-01-01",
    "to": "2026-01-31"
  },
  "top_products": [
    {
      "product_id": "prod123",
      "title": "Smartphone XYZ",
      "quantity_sold": 45,
      "revenue": 2250000,
      "orders_count": 42,
      "image_url": "https://example.com/image.jpg"
    }
  ],
  "top_categories": [
    {
      "category": "Electronics",
      "quantity_sold": 120,
      "revenue": 5400000,
      "products_count": 15
    }
  ]
}
```

**Use Case:** Display top-selling products and categories in the merchant dashboard.

---

### 3. GET `/api/merchants/me/alerts`

Get real-time alerts for the merchant.

**Query Parameters:** None

**Response:**
```json
{
  "alerts": [
    {
      "type": "pending_orders",
      "severity": "warning",
      "title": "Pending Orders",
      "message": "You have 8 orders pending confirmation",
      "count": 8,
      "action_url": "/api/merchants/me/orders?status=pending",
      "created_at": "2026-01-03T10:30:00"
    },
    {
      "type": "low_stock",
      "severity": "critical",
      "title": "Low Stock Alert",
      "message": "3 products are running low on stock",
      "count": 3,
      "action_url": "/api/products?low_stock=true",
      "created_at": "2026-01-03T10:30:00"
    }
  ],
  "total": 2
}
```

**Alert Types:**
- `pending_orders`: Orders awaiting confirmation
- `low_stock`: Products with stock <= 5
- `out_of_stock`: Products with stock = 0
- `high_refunds`: More than 5 refunds in the last 7 days
- `old_pending_orders`: Orders pending for more than 3 days

**Severity Levels:**
- `info`: Informational
- `warning`: Needs attention
- `critical`: Requires immediate action

**Use Case:** Display alert notifications in the merchant dashboard header or sidebar.

---

### 4. GET `/api/merchants/me/recent-activity`

Get recent activity for the merchant.

**Query Parameters:**
- `limit` (optional): Number of activities to return. Default: 20, Max: 100.
- `type` (optional): Filter by activity type (`order`, `refund`, `status_change`).

**Response:**
```json
{
  "activities": [
    {
      "type": "order",
      "title": "New Order Received",
      "description": "Order from customer John",
      "timestamp": "2026-01-03T09:45:00",
      "reference_id": "order123",
      "amount": 45000,
      "status": "pending"
    },
    {
      "type": "refund",
      "title": "Refund Processed",
      "description": "Refund for order #120",
      "timestamp": "2026-01-03T08:30:00",
      "reference_id": "ref_abc123",
      "amount": 32000,
      "status": "completed"
    }
  ],
  "total": 2
}
```

**Activity Types:**
- `order`: New order received
- `refund`: Refund processed

**Use Case:** Display recent activity feed in the merchant dashboard.

---

### 5. POST `/api/merchants/me/exports/orders`

Export orders to CSV format for a specified period.

**Request Body:**
```json
{
  "from": "2026-01-01",
  "to": "2026-01-31",
  "status": "delivered",
  "format": "csv"
}
```

**Request Fields:**
- `from` (optional): Start date in YYYY-MM-DD format. Defaults to first day of current month.
- `to` (optional): End date in YYYY-MM-DD format. Defaults to today.
- `status` (optional): Filter by order status.
- `format`: Export format. Currently only `csv` is supported.

**Response:**
```json
{
  "filename": "orders_2026-01-01_2026-01-31.csv",
  "content": "Order ID,Date,Customer ID,Total Amount,Status,Payment Method,Products Count\n...",
  "rows_count": 133
}
```

**CSV Format:**
The CSV includes the following columns:
- Order ID
- Date (YYYY-MM-DD HH:MM:SS)
- Customer ID
- Total Amount
- Status
- Payment Method
- Products Count

**Use Case:** Allow merchants to export order data for accounting or analysis purposes.

---

## Error Responses

All endpoints return standard HTTP error responses:

**404 Not Found:**
```json
{
  "detail": "Merchant profile not found"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden:**
```json
{
  "detail": "Only merchants can access this endpoint"
}
```

## Integration Notes

### Frontend Integration
1. All endpoints use the `/api` prefix
2. Date filters use ISO 8601 format (YYYY-MM-DD)
3. All monetary amounts are in XOF (West African CFA franc)
4. Timestamps are in UTC

### Recommended Polling Intervals
- **Alerts**: Poll every 30-60 seconds for real-time updates
- **Recent Activity**: Poll every 1-2 minutes
- **Stats & Bestsellers**: Poll every 5-10 minutes or on page load
- **Exports**: On-demand only (user initiated)

### Performance Considerations
- Stats endpoint aggregates data by day, so larger date ranges may take longer
- Bestsellers endpoint performs multiple database lookups for product details
- Exports endpoint can return large CSV files for merchants with many orders

## Testing

Unit tests are available in `tests/test_merchant_new_endpoints.py`.

To run the tests:
```bash
cd backend
python -m pytest tests/test_merchant_new_endpoints.py -v
```

## Future Enhancements

Potential improvements for future versions:
1. Add pagination to recent activity endpoint
2. Support additional export formats (Excel, JSON)
3. Add real-time WebSocket updates for alerts
4. Add filtering by product or customer in stats endpoint
5. Add ability to mark alerts as read/dismissed
6. Add comparative analytics (current period vs previous period)
