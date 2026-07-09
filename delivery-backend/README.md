# Delivery App Backend - Separate Service

This is an independent backend service for the Delivery/Shipping Management System.

## Quick Start

### 1. Setup Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Create .env file
Copy `.env.example` to `.env` and update values if needed.

### 4. Run Server
```bash
python -m uvicorn app.main:app --reload --port 8001
```

Server will be available at: `http://localhost:8001`
Interactive API docs at: `http://localhost:8001/docs`

## Project Structure

```
delivery-backend/
├── app/
│   ├── main.py           # FastAPI application entry point
│   ├── config/           # Configuration settings
│   ├── models/           # Database models (SQLAlchemy)
│   ├── schemas/          # Pydantic schemas
│   ├── api/
│   │   └── routes/       # API endpoints
│   │       ├── shipments.py
│   │       ├── deliveries.py
│   │       ├── drivers.py
│   │       └── tracking.py
│   ├── services/         # Business logic
│   └── utils/            # Helper functions
├── tests/                # Unit and integration tests
├── requirements.txt      # Python dependencies
└── .env.example          # Environment variables template
```

## API Features

### Core Entities
- **Shipments**: Track packages from origin to destination
- **Drivers**: Manage delivery personnel
- **Deliveries**: Link shipments to drivers
- **Tracking**: Real-time shipment tracking

### Current Status
- ✅ Mock in-memory database
- ✅ Full CRUD operations
- ✅ Tracking endpoints
- 🔄 Database migration (PostgreSQL coming)
- 🔄 WebSocket for real-time updates
- 🔄 Authentication/Authorization

## Testing

Run tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=app tests/
```

## Notes

- This is a **separate, independent service** from the main alia app
- Currently uses mock data in memory (no persistent database yet)
- Ready for PostgreSQL integration in Phase 2
- CORS enabled for frontend on ports 3000 and 3001
