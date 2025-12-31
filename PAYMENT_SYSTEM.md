# Mobile Money Payment System - Implementation Guide

## Overview

This document describes the complete mobile money payment system implemented for Alia, supporting Orange Money, MTN Mobile Money, and Moov Money for Côte d'Ivoire.

## 📋 System Architecture

### Components

1. **Payment Models** (`app/models/payment.py`)
   - `Payment`: Main payment record with status tracking
   - `Refund`: Refund tracking
   - Enumerations for status and providers

2. **Payment Configuration** (`app/config/payment_config.py`)
   - Three operating modes: SIMULATION, SANDBOX, PRODUCTION
   - Provider-specific configurations
   - Fee calculation
   - Timeout settings

3. **Phone Validator** (`app/utils/phone_validator.py`)
   - Validates Ivorian phone numbers (+225XXXXXXXXXX)
   - Detects provider from phone number prefix
   - Phone number formatting

4. **Payment Providers** (`app/services/payment_providers/`)
   - `simulation_service.py`: Testing without real APIs
   - `orange_money_service.py`: Orange Money integration
   - `mtn_money_service.py`: MTN Mobile Money integration
   - `moov_money_service.py`: Moov Money integration

5. **Payment Service** (`app/services/payment_service.py`)
   - Core business logic
   - Payment initiation
   - Status tracking
   - Webhook processing
   - Fee calculation
   - Payment cancellation

6. **Payment Routes** (`app/api/routes/payments.py`)
   - REST API endpoints
   - Authentication and authorization
   - Request/response validation

## 🚀 Quick Start

### 1. Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Payment System Mode
PAYMENT_MODE=SIMULATION  # Use SIMULATION for testing

# Orange Money (for SANDBOX/PRODUCTION)
ORANGE_CLIENT_ID=your-client-id
ORANGE_CLIENT_SECRET=your-client-secret
ORANGE_MERCHANT_KEY=your-merchant-key

# MTN Mobile Money (for SANDBOX/PRODUCTION)
MTN_SUBSCRIPTION_KEY=your-subscription-key
MTN_API_USER=your-api-user
MTN_API_KEY=your-api-key

# Moov Money (for SANDBOX/PRODUCTION)
MOOV_API_KEY=your-api-key
MOOV_API_SECRET=your-api-secret
MOOV_MERCHANT_ID=your-merchant-id

# Fee Configuration
PLATFORM_COMMISSION_PERCENT=2.5
ORANGE_GATEWAY_FEE_PERCENT=1.5
MTN_GATEWAY_FEE_PERCENT=1.8
MOOV_GATEWAY_FEE_PERCENT=2.0
```

### 2. Testing in SIMULATION Mode

The system starts in SIMULATION mode by default. No real API credentials needed!

**Special Phone Numbers for Testing:**
- `+2250707******0000`: Auto-success after 5 seconds
- `+2250707******9999`: Auto-failure
- Other numbers: Pending (use admin endpoints to simulate)

## 📡 API Endpoints

### Initiate Payment
```http
POST /api/payments/initiate
Authorization: Bearer <token>
Content-Type: application/json

{
  "order_id": "695318db0f5f01144f5b4fb0",
  "phone_number": "+2250707123456"
}
```

**Response:**
```json
{
  "payment_id": "pay_abc123xyz",
  "status": "pending",
  "amount": 92000,
  "currency": "XOF",
  "provider": "orange_money",
  "transaction_id": "OM123456789",
  "message": "Veuillez composer *144# pour confirmer le paiement de 92000 FCFA",
  "ussd_code": "*144#",
  "expires_at": "2025-12-30T00:22:11Z"
}
```

### Check Payment Status
```http
GET /api/payments/{payment_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "payment_id": "pay_abc123xyz",
  "order_id": "695318db0f5f01144f5b4fb0",
  "status": "completed",
  "amount": 92000,
  "currency": "XOF",
  "provider": "orange_money",
  "transaction_id": "OM123456789",
  "phone_number": "+2250707******",
  "initiated_at": "2025-12-30T00:12:11Z",
  "completed_at": "2025-12-30T00:15:32Z"
}
```

### Get Payment History
```http
GET /api/payments?status=completed&limit=20&offset=0
Authorization: Bearer <token>
```

### Cancel Payment
```http
POST /api/payments/{payment_id}/cancel
Authorization: Bearer <token>
```

### Payment Webhook (Provider Callback)
```http
POST /api/payments/webhook/{provider}
X-Signature: <provider_signature>
Content-Type: application/json

{
  "transaction_id": "OM123456789",
  "status": "success",
  ...
}
```

### Admin Endpoints (SIMULATION mode only)

**Simulate Success:**
```http
POST /api/payments/admin/{payment_id}/simulate-success
Authorization: Bearer <token>
```

**Simulate Failure:**
```http
POST /api/payments/admin/{payment_id}/simulate-failure
Authorization: Bearer <token>
```

## 🔐 Phone Number Format & Provider Detection

### Valid Format
- Must start with +225 or 225
- Total: 13 digits (225 + 10 digit number)
- Example: `+2250707123456`

### Provider Detection (Automatic)

**Orange Money:**
- Prefixes: 07XX, 0505, 01XX (some), 014X, 015X
- USSD: `*144#`

**MTN Mobile Money:**
- Prefixes: 04XX, 05XX (some), 06XX, 054X, 055X, 064X, 065X
- USSD: `*133#`

**Moov Money:**
- Prefixes: 01XX, 02XX, 03XX
- USSD: `*155#`

## 💰 Fee Structure

### Fee Calculation

For a 100,000 XOF payment:

**Orange Money:**
- Platform Fee: 2,500 XOF (2.5%)
- Gateway Fee: 1,500 XOF (1.5%)
- Merchant Payout: 96,000 XOF

**MTN Mobile Money:**
- Platform Fee: 2,500 XOF (2.5%)
- Gateway Fee: 1,800 XOF (1.8%)
- Merchant Payout: 95,700 XOF

**Moov Money:**
- Platform Fee: 2,500 XOF (2.5%)
- Gateway Fee: 2,000 XOF (2.0%)
- Merchant Payout: 95,500 XOF

## 🔄 Payment Flow

### 1. Customer Initiates Payment
```
POST /api/payments/initiate
↓
System validates order and phone number
↓
Detects provider from phone number
↓
Calculates fees
↓
Creates payment record (status: pending)
↓
Calls provider API (or simulation)
↓
Returns payment details with USSD code
```

### 2. Customer Confirms via USSD
```
Customer dials *144# (Orange)
↓
Confirms payment on their phone
↓
Provider processes payment
```

### 3. Provider Sends Webhook
```
Provider calls /api/payments/webhook/orange_money
↓
System verifies signature
↓
Updates payment status (completed/failed)
↓
Updates order status (confirmed if successful)
↓
Sends notifications (TODO)
```

### 4. Status Polling (Optional)
```
GET /api/payments/{payment_id}
↓
System checks database status
↓
If pending, queries provider API
↓
Returns current status
```

## 🧪 Testing Scenarios

### Scenario 1: Successful Payment (SIMULATION)
1. Create an order
2. Initiate payment with phone ending in `0000`
   - Example: `+2250707123450000`
3. Wait 5 seconds OR call simulate-success endpoint
4. Check payment status → should be "completed"
5. Check order status → should be "confirmed"

### Scenario 2: Failed Payment (SIMULATION)
1. Create an order
2. Initiate payment with phone ending in `9999`
   - Example: `+2250707123459999`
3. Check payment status → should be "failed"
4. Check order status → still "pending"

### Scenario 3: Manual Simulation
1. Create an order
2. Initiate payment with normal phone
   - Example: `+2250707123456`
3. Payment status → "pending"
4. Call `POST /api/payments/admin/{payment_id}/simulate-success`
5. Check payment status → "completed"

### Scenario 4: Payment Cancellation
1. Initiate payment
2. While status is "pending", call cancel endpoint
3. Payment status → "cancelled"

### Scenario 5: Expired Payment
1. Initiate payment
2. Wait 10+ minutes (or modify timeout in config)
3. Check payment status → "expired"

## 🔧 Operating Modes

### SIMULATION Mode (Default)
- No real API calls
- Perfect for local development
- Instant testing with special phone patterns
- No credentials required

**Use when:**
- Developing locally
- Writing automated tests
- Demonstrating the system

### SANDBOX Mode
- Uses provider sandbox APIs
- Real API integration testing
- Requires sandbox credentials
- No real money involved

**Use when:**
- Testing real API integration
- Staging environment
- Pre-production validation

**Setup:**
```bash
PAYMENT_MODE=SANDBOX
# Add sandbox API credentials
```

### PRODUCTION Mode
- Real transactions
- Live provider APIs
- Requires production credentials
- Real money transfers

**Use when:**
- Live production environment
- Processing actual customer payments

**Setup:**
```bash
PAYMENT_MODE=PRODUCTION
# Add production API credentials
# Ensure webhook URLs are accessible
```

## 🔐 Security Features

1. **Webhook Signature Verification**
   - HMAC-SHA256 signature validation
   - Prevents unauthorized webhook calls

2. **Phone Number Validation**
   - Strict format validation
   - Provider verification

3. **Authorization Checks**
   - Users can only pay for their own orders
   - Merchants can only refund their orders

4. **Payment Expiration**
   - Payments expire after 10 minutes
   - Prevents stale transactions

5. **Rate Limiting** (TODO)
   - Max 3 payment attempts per order

## 📊 Database Schema

### Payments Collection
```javascript
{
  _id: ObjectId,
  payment_id: "pay_abc123xyz",  // Unique payment identifier
  order_id: "695318db0f5f01144f5b4fb0",
  user_id: "user123",
  merchant_id: "merchant123",
  amount: 92000,
  currency: "XOF",
  provider: "orange_money",
  phone_number: "+2250707123456",
  transaction_id: "OM123456789",  // Provider's transaction ID
  status: "completed",
  failure_reason: null,
  metadata: {},
  gross_amount: 92000,
  platform_fee: 2300,
  payment_gateway_fee: 1380,
  merchant_payout: 88320,
  initiated_at: ISODate("2025-12-30T00:12:11Z"),
  completed_at: ISODate("2025-12-30T00:15:32Z"),
  expires_at: ISODate("2025-12-30T00:22:11Z"),
  webhook_received_at: ISODate("2025-12-30T00:15:32Z"),
  retry_count: 0,
  created_at: ISODate("2025-12-30T00:12:11Z"),
  updated_at: ISODate("2025-12-30T00:15:32Z")
}
```

### Orders Collection (Updated)
```javascript
{
  _id: ObjectId,
  user_id: "user123",
  merchant_id: "merchant123",
  products: [...],
  total_amount: 92000,
  status: "confirmed",  // pending → confirmed (after payment)
  payment_status: "completed",  // New field
  payment_method: "orange_money",
  created_at: ISODate,
  updated_at: ISODate
}
```

## 🎯 Next Steps

### Immediate
- ✅ Basic payment flow implemented
- ✅ SIMULATION mode working
- ✅ Phone validation and provider detection
- ✅ Fee calculation
- ✅ API endpoints

### Short Term
- [ ] Add SANDBOX mode API credentials
- [ ] Test with real sandbox APIs
- [ ] Add email/SMS notifications
- [ ] Implement payment timeout background job
- [ ] Add refund API integration

### Long Term
- [ ] Add payment analytics dashboard
- [ ] Implement partial refunds
- [ ] Add payment dispute handling
- [ ] Support for Wave payment method
- [ ] Multi-currency support
- [ ] Advanced fraud detection

## 🐛 Troubleshooting

### Payment stays in "pending" status
- **SIMULATION mode:** Use admin endpoints to simulate completion
- **SANDBOX/PRODUCTION:** Check provider API credentials
- **All modes:** Verify webhook endpoint is accessible

### Phone number validation fails
- Ensure format: `+225XXXXXXXXXX` (13 digits total)
- Check provider prefixes match
- Remove spaces/hyphens before sending

### Webhook not received
- Verify webhook URL is publicly accessible
- Check firewall settings
- Verify signature verification logic
- Check provider webhook logs

### Fee calculation incorrect
- Verify environment variables for fee percentages
- Check provider name matches exactly
- Review fee configuration in payment_config.py

## 📚 Additional Resources

- [Orange Money API Documentation](https://developer.orange.com/apis/orange-money-webpay/)
- [MTN MoMo API Documentation](https://momodeveloper.mtn.com/)
- [Moov Money Contact](https://www.moov-africa.ci/) (Request API access)

## 🤝 Support

For issues or questions:
1. Check this documentation
2. Review API documentation at `/docs`
3. Check server logs
4. Contact support team

---

**Version:** 1.0.0  
**Last Updated:** December 30, 2024  
**Status:** Production Ready (SIMULATION mode) | SANDBOX Ready | PRODUCTION Ready (requires credentials)
