# Delivery App Setup

## Run Backend

```bash
cd delivery-backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

Backend runs on: http://localhost:8001
API Docs: http://localhost:8001/docs

## Run Frontend

```bash
cd delivery-dashboard
npm install
npm run dev
```

Frontend runs on: http://localhost:3001

## Environment Variables

Create `.env` file in `delivery-backend/`:
```
DATABASE_URL=postgresql://user:password@localhost/delivery_db
DEBUG=True
```

## API Endpoints

### Shipments
- `POST /api/shipments/` - Create shipment
- `GET /api/shipments/` - Get all shipments
- `GET /api/shipments/{id}` - Get shipment by ID
- `GET /api/shipments/tracking/{tracking_number}` - Track shipment
- `PUT /api/shipments/{id}` - Update shipment
- `DELETE /api/shipments/{id}` - Delete shipment

### Deliveries
- `POST /api/deliveries/` - Create delivery
- `GET /api/deliveries/` - Get all deliveries
- `GET /api/deliveries/{id}` - Get delivery by ID
- `PUT /api/deliveries/{id}` - Update delivery
- `DELETE /api/deliveries/{id}` - Delete delivery

### Drivers
- `POST /api/drivers/` - Create driver
- `GET /api/drivers/` - Get all drivers
- `GET /api/drivers/{id}` - Get driver by ID
- `PUT /api/drivers/{id}` - Update driver
- `DELETE /api/drivers/{id}` - Delete driver

### Tracking
- `GET /api/tracking/{tracking_number}` - Track shipment
- `GET /api/tracking/delivery/{delivery_id}/progress` - Get delivery progress

## Features

### Phase 1 (Current)
- Basic CRUD operations for shipments, drivers, and deliveries
- Mock database (in-memory)
- REST API with FastAPI
- Next.js dashboard UI

### Phase 2 (Upcoming)
- PostgreSQL database integration
- Real-time tracking with WebSockets
- Driver location tracking (GPS)
- Delivery notifications
- Analytics and reporting

### Phase 3 (Future)
- Mobile app for drivers
- Customer tracking portal
- Payment integration
- Advanced route optimization
- Machine learning for delivery predictions
