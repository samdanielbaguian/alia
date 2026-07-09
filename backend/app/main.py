from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api.routes import auth, products, merchants, orders, aliexpress, buybox, cart, payments, uploads, customers
from app.api.routes import admin_orders, admin_users, admin_products, admin_merchants

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Alia - Marketplace for merchants with AliExpress integration and intelligent Buy Box",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount uploads static directory
uploads_dir = Path(__file__).resolve().parents[2] / 'uploads'
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount('/uploads', StaticFiles(directory=str(uploads_dir)), name='uploads')

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting up Alia backend...")
    await connect_to_mongo()
    logger.info("Alia backend started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown."""
    logger.info("Shutting down Alia backend...")
    await close_mongo_connection()
    logger.info("Alia backend shut down successfully")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "alia-backend",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "description": "Alia Backend API",
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_PREFIX}/auth", tags=["Authentication"])
app.include_router(products.router, prefix=f"{settings.API_V1_PREFIX}/products", tags=["Products"])
app.include_router(merchants.router, prefix=f"{settings.API_V1_PREFIX}/merchants", tags=["Merchants"])
app.include_router(customers.router, prefix=f"{settings.API_V1_PREFIX}/customers", tags=["Customers"])
app.include_router(orders.router, prefix=f"{settings.API_V1_PREFIX}/orders", tags=["Orders"])
app.include_router(payments.router, prefix=f"{settings.API_V1_PREFIX}/payments", tags=["Payments"])
app.include_router(aliexpress.router, prefix=f"{settings.API_V1_PREFIX}/aliexpress", tags=["AliExpress"])
app.include_router(buybox.router, prefix=f"{settings.API_V1_PREFIX}/buybox", tags=["Buy Box"])
app.include_router(cart.router, prefix=f"{settings.API_V1_PREFIX}/cart", tags=["Cart"])
app.include_router(uploads.router, prefix=f"{settings.API_V1_PREFIX}/uploads", tags=["Uploads"])

# Admin routes
app.include_router(admin_orders.router, prefix=f"{settings.API_V1_PREFIX}/admin/orders", tags=["Admin - Orders"])
app.include_router(admin_users.router, prefix=f"{settings.API_V1_PREFIX}/admin/users", tags=["Admin - Users"])
app.include_router(admin_products.router, prefix=f"{settings.API_V1_PREFIX}/admin/products", tags=["Admin - Products"])
app.include_router(admin_merchants.router, prefix=f"{settings.API_V1_PREFIX}/admin/merchants", tags=["Admin - Merchants"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
