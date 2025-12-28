# Alia Backend - Quick Start Guide

This guide will help you get the Alia backend up and running in 5 minutes.

## Prerequisites

Choose **ONE** of the following options:

### Option 1: Docker (Recommended - Easiest)
- Docker installed
- Docker Compose installed

### Option 2: Local Development
- Python 3.11 or higher
- MongoDB 7.0 or higher (local installation or MongoDB Atlas)

---

## Quick Start with Docker 🐳 (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/samdanielbaguian/alia.git
cd alia
```

2. **Start the services**
```bash
docker compose up -d
```

That's it! The backend is now running at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **MongoDB**: localhost:27017

3. **Check the logs**
```bash
docker compose logs -f backend
```

4. **Stop the services**
```bash
docker compose down
```

---

## Quick Start with Local Development 💻

1. **Clone the repository**
```bash
git clone https://github.com/samdanielbaguian/alia.git
cd alia/backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
```

Edit the `.env` file and set your MongoDB URI:
```env
MONGODB_URI=mongodb://localhost:27017
# OR use MongoDB Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
JWT_SECRET_KEY=your-super-secret-key-change-this
```

5. **Run the application**
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend is now running at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs

---

## Testing the API

### 1. Health Check
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "alia-backend",
  "version": "1.0.0"
}
```

### 2. Register a Merchant
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "merchant@example.com",
    "password": "password123",
    "role": "merchant",
    "shop_name": "Tech Store",
    "age": 30,
    "preferences": ["electronics"]
  }'
```

Save the `access_token` from the response.

### 3. Create a Product (using the token)
```bash
curl -X POST http://localhost:8000/api/products \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title": "Smartphone XYZ",
    "description": "High-end smartphone",
    "price": 299.99,
    "stock": 50,
    "category": "electronics",
    "delivery_days": 3,
    "images": ["https://via.placeholder.com/300"],
    "age_restricted": false
  }'
```

### 4. Get All Products
```bash
curl http://localhost:8000/api/products
```

### 5. Search Products
```bash
curl "http://localhost:8000/api/products/search?q=smartphone"
```

---

## Using the Interactive Documentation

The easiest way to test the API is through the interactive documentation:

1. Open http://localhost:8000/docs in your browser
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

You can also authorize with your JWT token:
1. Click the "Authorize" button at the top
2. Enter `Bearer YOUR_TOKEN_HERE`
3. Click "Authorize"

---

## Next Steps

### For Merchants
1. Register as a merchant
2. Create products
3. Import products from AliExpress (structure ready, add API keys)
4. View your dashboard
5. Manage orders

### For Buyers
1. Register as a buyer
2. Browse products
3. Search for products
4. Place orders
5. View your orders

### For Developers
1. Read the full [API Documentation](API_DOCUMENTATION.md)
2. Read the [README](../README.md) for deployment instructions
3. Explore the code structure
4. Add your AliExpress/Alibaba API keys to `.env`
5. Add your payment provider API keys to `.env`

---

## Common Commands

### Docker Commands
```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f backend

# Restart backend
docker compose restart backend

# Stop all services
docker compose down

# Rebuild after code changes
docker compose up -d --build
```

### Local Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Check syntax
python -m py_compile app/main.py
```

---

## Troubleshooting

### MongoDB Connection Issues
- **Docker**: Make sure MongoDB container is running: `docker compose ps`
- **Local**: Make sure MongoDB is installed and running: `mongod --version`
- **Atlas**: Check your connection string and network access settings

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000
# Kill the process
kill -9 <PID>
```

### Module Not Found Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Docker Build Issues
```bash
# Clean up and rebuild
docker compose down -v
docker compose up -d --build
```

---

## Support

For more information:
- Full documentation: [README.md](../README.md)
- API documentation: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- Issues: https://github.com/samdanielbaguian/alia/issues

---

## What's Next?

1. **Add Real API Integrations**
   - AliExpress API credentials
   - Alibaba API credentials
   - Payment provider credentials

2. **Deploy to Production**
   - Railway: `railway init && railway up`
   - Render: Connect GitHub repo
   - AWS: Use Elastic Beanstalk or ECS

3. **Build the Frontend**
   - Next.js application
   - React Native mobile app

4. **Add More Features**
   - Email notifications
   - SMS notifications
   - Real-time updates with WebSocket
   - Admin panel
   - Analytics dashboard

Happy coding! 🚀
