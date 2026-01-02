# Alia API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication

All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## Endpoints Overview

### Health & Info
- `GET /health` - Health check
- `GET /` - API information

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user (protected)

### Products
- `GET /api/products` - List products with filters
- `GET /api/products/search` - Search products
- `GET /api/products/{id}` - Get product details
- `POST /api/products` - Create product (merchant only)
- `PUT /api/products/{id}` - Update product (merchant only)
- `DELETE /api/products/{id}` - Delete product (merchant only)

### Orders
- `POST /api/orders` - Create order (protected)
- `GET /api/orders` - List user orders (protected)
- `GET /api/orders/{id}` - Get order details (protected)

### Merchants
- `GET /api/merchants/{id}` - Get merchant profile
- `PUT /api/merchants/{id}` - Update merchant profile (merchant only)
- `GET /api/merchants/{id}/dashboard` - Get dashboard analytics (merchant only)
- `GET /api/merchants/me/dashboard-overview` - Get dashboard overview with period filter (merchant only)
- `GET /api/merchants/me/orders` - Get merchant orders with pagination (merchant only)

### AliExpress Integration
- `POST /api/aliexpress/search` - Search AliExpress products (merchant only)
- `POST /api/aliexpress/import` - Import product from AliExpress (merchant only)
- `GET /api/aliexpress/sync/{product_id}` - Sync product (merchant only)

### Buy Box
- `GET /api/buybox/{product_title}` - Get Buy Box winner

---

## Detailed Endpoint Documentation

### POST /api/auth/register

Register a new user (merchant or buyer).

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "strongpassword123",
  "role": "merchant",
  "age": 30,
  "preferences": ["electronics", "fashion"],
  "shop_name": "My Store"
}
```

**Note:** `shop_name` is required for merchants.

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### POST /api/auth/login

Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "strongpassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### GET /api/auth/me

Get current authenticated user information.

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
  "id": "user123",
  "email": "user@example.com",
  "role": "merchant",
  "age": 30,
  "preferences": ["electronics"],
  "good_rate": 85.5,
  "location": {
    "lat": 14.6937,
    "lng": -17.4441
  },
  "created_at": "2024-01-01T00:00:00"
}
```

---

### GET /api/products

Get list of products with optional filters.

**Query Parameters:**
- `category` (optional) - Filter by category
- `price_min` (optional) - Minimum price
- `price_max` (optional) - Maximum price
- `age_restricted` (optional) - Filter by age restriction (true/false)
- `skip` (optional, default: 0) - Pagination offset
- `limit` (optional, default: 50, max: 100) - Items per page

**Example:**
```
GET /api/products?category=electronics&price_min=100&price_max=500&limit=20
```

**Response:**
```json
[
  {
    "id": "prod123",
    "title": "Smartphone XYZ",
    "description": "High-end smartphone",
    "price": 299.99,
    "original_price": 250.00,
    "images": ["https://example.com/image.jpg"],
    "stock": 50,
    "category": "electronics",
    "merchant_id": "merchant123",
    "is_imported": false,
    "delivery_days": 3,
    "age_restricted": false,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

---

### GET /api/products/search

Search products by title, description, or category.

**Query Parameters:**
- `q` (required) - Search query
- `category` (optional) - Filter by category
- `skip` (optional, default: 0) - Pagination offset
- `limit` (optional, default: 50, max: 100) - Items per page

**Example:**
```
GET /api/products/search?q=smartphone&category=electronics
```

---

### POST /api/products

Create a new product (merchants only).

**Headers:**
```
Authorization: Bearer <merchant_token>
```

**Request Body:**
```json
{
  "title": "Smartphone XYZ",
  "description": "High-end smartphone",
  "price": 299.99,
  "images": ["https://example.com/image.jpg"],
  "stock": 50,
  "category": "electronics",
  "delivery_days": 3,
  "age_restricted": false,
  "location": {
    "lat": 14.6937,
    "lng": -17.4441
  }
}
```

---

### POST /api/orders

Create a new order.

**Headers:**
```
Authorization: Bearer <token>
```

**Request Body:**
```json
{
  "products": [
    {
      "product_id": "prod123",
      "quantity": 2
    }
  ],
  "payment_method": "orange_money"
}
```

**Payment Methods:**
- `orange_money`
- `moov_money`
- `wave`
- `stripe`

**Response:**
```json
{
  "id": "order123",
  "user_id": "user123",
  "merchant_id": "merchant123",
  "products": [
    {
      "product_id": "prod123",
      "quantity": 2,
      "price": 299.99,
      "title": "Smartphone XYZ"
    }
  ],
  "total_amount": 599.98,
  "status": "pending",
  "payment_method": "orange_money",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

---

### GET /api/merchants/{merchant_id}/dashboard

Get merchant dashboard with analytics (merchant only, own dashboard).

**Headers:**
```
Authorization: Bearer <merchant_token>
```

**Response:**
```json
{
  "merchant_id": "merchant123",
  "shop_name": "Tech Store",
  "total_sales": 15000.0,
  "rating": 92.5,
  "products_count": 45,
  "orders_count": 120,
  "revenue": 15000.0,
  "top_products": [
    {
      "product_id": "prod123",
      "title": "Smartphone XYZ",
      "quantity_sold": 50,
      "revenue": 14999.50
    }
  ],
  "demand_zones": []
}
```

---

### GET /api/merchants/me/dashboard-overview

Get merchant dashboard overview with activity summary for a given period (merchant only).

**Headers:**
```
Authorization: Bearer <merchant_token>
```

**Query Parameters:**
- `from` (optional): Start date in YYYY-MM-DD format (default: first day of current month)
- `to` (optional): End date in YYYY-MM-DD format (default: last day of current month)

**Example Request:**
```bash
GET /api/merchants/me/dashboard-overview?from=2026-01-01&to=2026-01-31
```

**Response:**
```json
{
  "total_sales": 4590000,
  "orders_count": 133,
  "orders_pending": 11,
  "orders_shipped": 72,
  "orders_canceled": 10,
  "orders_refunded": 5,
  "refunds_total": 86000,
  "new_customers": 23,
  "products_in_stock": 78,
  "low_stock": 5,
  "period": {
    "from": "2026-01-01",
    "to": "2026-01-31"
  }
}
```

**Response Fields:**
- `total_sales`: Total sales amount in XOF from completed payments
- `orders_count`: Total number of orders in the period
- `orders_pending`: Number of orders with pending status
- `orders_shipped`: Number of orders with shipped status
- `orders_canceled`: Number of orders with canceled status
- `orders_refunded`: Number of orders with refunded status
- `refunds_total`: Total refund amount in XOF
- `new_customers`: Number of customers who made their first order in this period
- `products_in_stock`: Number of products currently in stock (stock > 0)
- `low_stock`: Number of products with low stock (0 < stock <= 5)
- `period`: The date range for which the data is calculated

---

### POST /api/aliexpress/import

Import a product from AliExpress/Alibaba (merchant only).

**Headers:**
```
Authorization: Bearer <merchant_token>
```

**Request Body:**
```json
{
  "source_product_id": "12345678",
  "source_platform": "AliExpress",
  "margin_percentage": 25.0,
  "stock": 100
}
```

**Response:**
```json
{
  "product": {
    "id": "prod123",
    "title": "Imported Product",
    "price": 62.50,
    "original_price": 50.00,
    "is_imported": true,
    "source_platform": "AliExpress",
    ...
  },
  "duplicate_warning": {
    "found": true,
    "count": 2,
    "similar_products": [
      {
        "product_id": "prod456",
        "title": "Similar Local Product",
        "similarity_score": 78.5
      }
    ]
  }
}
```

---

### GET /api/buybox/{product_title}

Get the Buy Box winner for a product.

**Query Parameters:**
- `user_lat` (optional) - User's latitude
- `user_lng` (optional) - User's longitude

**Example:**
```
GET /api/buybox/smartphone?user_lat=14.6937&user_lng=-17.4441
```

**Response:**
```json
{
  "winner": {
    "product_id": "prod123",
    "merchant_id": "merchant123",
    "title": "Smartphone XYZ",
    "price": 299.99,
    "stock": 50,
    "delivery_days": 3,
    "good_rate": 92.5,
    "distance_km": 5.2,
    "scores": {
      "stock": 50.0,
      "distance": 94.8,
      "rating": 92.5,
      "total": 85.3
    }
  },
  "all_offers": [...],
  "total_merchants": 5
}
```

**Buy Box Algorithm:**
The Buy Box winner is determined by a weighted score:
- Stock availability: 40%
- Geographic distance: 35%
- Merchant rating: 25%

---

## Error Responses

All endpoints may return error responses in the following format:

**400 Bad Request:**
```json
{
  "detail": "Invalid input data"
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

**404 Not Found:**
```json
{
  "detail": "Product not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## Interactive Documentation

Once the server is running, you can access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive API documentation where you can test endpoints directly.
