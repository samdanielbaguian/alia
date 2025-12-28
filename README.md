# Alia - Marketplace Backend

Alia is a comprehensive e-commerce marketplace platform designed for merchants in West Africa. It features AliExpress/Alibaba integration, intelligent Buy Box algorithm, and support for local payment methods.

## 🚀 Features

### Core Features
- **User Authentication**: JWT-based authentication with bcrypt password hashing
- **Role-Based Access**: Support for merchants and buyers with different permissions
- **Product Management**: Full CRUD operations for products with categories, images, and stock management
- **Order Processing**: Complete order workflow with payment integration
- **Merchant Dashboard**: Analytics including sales, revenue, and top products

### Advanced Features
- **AliExpress/Alibaba Integration**: Import products with customizable margins (structure ready, TODO: API integration)
- **Duplicate Detection**: AI-powered similarity detection to prevent importing existing local products
- **Buy Box Algorithm**: Intelligent algorithm that selects the best merchant based on:
  - Stock availability (40%)
  - Geographic proximity (35%)
  - Merchant rating (25%)
- **Geolocation**: Haversine formula for accurate distance calculations
- **Payment Gateways**: Support for Orange Money, Moov Money, Wave, and Stripe (structure ready)

## 📋 Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for containerized deployment)
- MongoDB 7.0 or higher (or use Docker)

## 🛠️ Installation

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/samdanielbaguian/alia.git
cd alia
```

2. **Create virtual environment**
```bash
cd backend
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
# Edit .env with your configuration
```

5. **Configure MongoDB**
   - Option 1: Install MongoDB locally
   - Option 2: Use MongoDB Atlas (cloud)
   - Option 3: Use Docker (see Docker setup below)

6. **Run the application**
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

7. **Access the API**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Setup (Recommended)

1. **Build and run with Docker Compose**
```bash
docker-compose up -d
```

2. **View logs**
```bash
docker-compose logs -f backend
```

3. **Stop services**
```bash
docker-compose down
```

## 🔐 Environment Variables

Create a `.env` file in the `backend` directory with the following variables:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=alia_db

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AliExpress API (TODO: Get real API keys)
ALIEXPRESS_API_KEY=your-aliexpress-api-key
ALIEXPRESS_API_SECRET=your-aliexpress-api-secret

# Alibaba API (TODO)
ALIBABA_API_KEY=your-alibaba-api-key

# Payment Providers (TODO)
ORANGE_MONEY_API_KEY=your-orange-money-key
MOOV_MONEY_API_KEY=your-moov-money-key
WAVE_API_KEY=your-wave-key
STRIPE_API_KEY=your-stripe-key

# Application Settings
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
API_V1_PREFIX=/api
PROJECT_NAME=Alia
```

## 📚 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user (merchant or buyer)
- `POST /api/auth/login` - Login with email and password
- `GET /api/auth/me` - Get current user information

### Products
- `GET /api/products` - List products with filters
- `GET /api/products/search?q={query}` - Search products
- `GET /api/products/{id}` - Get product details
- `POST /api/products` - Create product (merchants only)
- `PUT /api/products/{id}` - Update product (merchants only)
- `DELETE /api/products/{id}` - Delete product (merchants only)

### Orders
- `POST /api/orders` - Create new order
- `GET /api/orders` - Get user's orders
- `GET /api/orders/{id}` - Get order details

### Merchants
- `GET /api/merchants/{id}` - Get merchant profile
- `PUT /api/merchants/{id}` - Update merchant profile
- `GET /api/merchants/{id}/dashboard` - Get merchant analytics dashboard

### AliExpress Integration
- `POST /api/aliexpress/search` - Search products on AliExpress
- `POST /api/aliexpress/import` - Import product with duplicate detection
- `GET /api/aliexpress/sync/{product_id}` - Sync product from AliExpress

### Buy Box
- `GET /api/buybox/{product_title}?user_lat={lat}&user_lng={lng}` - Get Buy Box winner

## 🧪 Testing

Run tests with pytest:

```bash
cd backend
pytest
```

Run with coverage:

```bash
pytest --cov=app --cov-report=html
```

## 🏗️ Project Structure

```
alia/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── core/
│   │   │   ├── config.py        # Configuration management
│   │   │   ├── database.py      # MongoDB connection
│   │   │   └── security.py      # JWT and password hashing
│   │   ├── models/              # MongoDB models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── api/
│   │   │   ├── deps.py          # API dependencies
│   │   │   └── routes/          # API route handlers
│   │   ├── services/            # Business logic
│   │   └── utils/               # Utility functions
│   ├── tests/                   # Test files
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Environment variables template
│   └── Dockerfile              # Docker configuration
├── docker-compose.yml          # Docker Compose configuration
├── .gitignore
└── README.md
```

## 🔑 API Keys Setup

### MongoDB Atlas (Free Tier)
1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free account
3. Create a new cluster
4. Get your connection string
5. Update `MONGODB_URI` in `.env`

### AliExpress API (TODO)
1. Register at https://portals.aliexpress.com/
2. Create an application
3. Get App Key and App Secret
4. Update `.env` with credentials

### Payment Providers

**Orange Money**
- Documentation: https://developer.orange.com/apis/orange-money-webpay/

**Wave**
- Documentation: https://developer.wave.com/

**Stripe**
- Sign up: https://stripe.com/
- Get API keys from dashboard

## 🚀 Deployment

### Deploy to Railway

1. Install Railway CLI
```bash
npm i -g @railway/cli
```

2. Login and deploy
```bash
railway login
railway init
railway up
```

### Deploy to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set environment variables
4. Deploy!

### Deploy to AWS

Use AWS Elastic Beanstalk or ECS with the provided Dockerfile.

## 🗺️ Roadmap

### Phase 1: Core Features ✅
- [x] User authentication and authorization
- [x] Product CRUD operations
- [x] Order management
- [x] Merchant dashboard

### Phase 2: Advanced Features ✅
- [x] Buy Box algorithm
- [x] Duplicate product detection
- [x] Geolocation services
- [x] Payment service structure

### Phase 3: Integrations (TODO)
- [ ] Implement real AliExpress API
- [ ] Implement Alibaba API
- [ ] Integrate Orange Money
- [ ] Integrate Moov Money
- [ ] Integrate Wave
- [ ] Integrate Stripe

### Phase 4: Enhancements (TODO)
- [ ] Product recommendations using ML
- [ ] Advanced search with Elasticsearch
- [ ] Real-time notifications (WebSocket)
- [ ] Admin panel
- [ ] Multi-language support
- [ ] Mobile apps (React Native)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- Samuel Daniel Baguian - Initial work

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- MongoDB for the flexible database
- All contributors and users of Alia

## 📞 Support

For support, email support@alia.com or join our Slack channel.
