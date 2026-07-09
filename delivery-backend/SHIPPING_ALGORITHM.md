# Shipping Algorithm Implementation Documentation

## Overview

The shipping algorithm has been successfully integrated into the delivery backend. It calculates delivery prices, times, methods, and commissions based on weight, distance, location, and delivery ratings.

## Algorithm Components

### 1. Zone Validation
Checks if delivery address is in allowed West African zones:
- Burkina Faso
- Mali
- Niger
- Ivory Coast
- Togo
- Benin
- Ghana

### 2. Primary Algorithm (Distances ≤ 60km)
**Scenario A:** Same city, ≤ 1kg, ≤ 30km
- Price: 2,000 CFA
- Time: 1-3 days

**Scenario B:** Regional, 30km < distance ≤ 60km
- Price: 3,500 CFA
- Time: 1-3 days

### 3. Secondary Algorithm (Distances > 60km)
**Scenario A:** Different city or ≤ 1kg
- Price: 5,000 CFA
- Time: 2-4 days

**Scenario B:** Medium weight (1-2kg)
- Price: 5,000 CFA
- Time: 2-4 days
- Method: Car

### 4. Third Algorithm (Distances 100-800km)
**Scenario A:** Light weight (≤ 5kg)
- Price: 7,000 CFA
- Time: 3-7 days
- Method: Car

**Scenario B:** Heavy weight (> 5kg)
- Price: 10,000 CFA
- Time: 5-10 days
- Method: Truck

### 5. Delivery Method Selection
Based on rating and weight:
- Rating ≥ 4.5 and weight ≤ 1kg: Motorbike or Bicycle
- Rating ≥ 4.5 and weight > 1kg: Car

### 6. Commission Calculation
Commission = (Delivery Price × 25) / 100

## API Endpoints

### Calculate Shipping Quote
```
POST /api/shipping/calculate-quote
```

**Request Body:**
```json
{
  "article_weight": 2.5,
  "delivery_address": "Burkina Faso",
  "delivery_city": "Ouagadougou",
  "stock_city": "Bobo-Dioulasso",
  "distance": 100,
  "delivery_rating": 4.7
}
```

**Response:**
```json
{
  "delivery_price": 7000,
  "delivery_time": [3, 7],
  "delivery_method": "Car",
  "commission": 1750,
  "zone_allowed": true,
  "details": "THIRD ALGORITHM: Very long distance delivery (100-800km, <= 5kg)"
}
```

### Get Allowed Zones
```
GET /api/shipping/allowed-zones
```

### Validate Address
```
POST /api/shipping/validate-address
Query: address=Burkina Faso
```

## Integration Points

### Backend Files Created/Modified:
1. `app/schemas/shipping.py` - Request/Response models
2. `app/services/shipping_algorithm.py` - Algorithm implementation
3. `app/api/routes/shipping.py` - API endpoints
4. `app/main.py` - Router registration
5. `tests/test_shipping_algorithm.py` - Comprehensive tests

## Testing

Run tests:
```bash
pytest tests/test_shipping_algorithm.py -v
```

Tests cover:
- Zone validation
- Primary algorithm (local and regional)
- Secondary algorithm (long distance)
- Third algorithm (very long distance)
- Delivery method selection
- Commission calculations
- All edge cases

## Usage Example

```python
from app.schemas.shipping import ShippingQuoteRequest
from app.services.shipping_algorithm import ShippingAlgorithm

# Create request
request = ShippingQuoteRequest(
    article_weight=2.0,
    delivery_address="Mali",
    delivery_city="Bamako",
    stock_city="Kayes",
    distance=150,
    delivery_rating=4.5
)

# Calculate quote
quote = ShippingAlgorithm.calculate_shipping_quote(request)

print(f"Price: {quote.delivery_price} CFA")
print(f"Time: {quote.delivery_time[0]}-{quote.delivery_time[1]} days")
print(f"Method: {quote.delivery_method}")
print(f"Commission: {quote.commission} CFA")
```

## Future Enhancements

- [ ] Database storage of shipping quotes
- [ ] Promotional pricing rules
- [ ] Peak/off-peak pricing variations
- [ ] VIP customer discounts
- [ ] Bulk shipment pricing
- [ ] Real-time rate updates
- [ ] Integration with payment system
