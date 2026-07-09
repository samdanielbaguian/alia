from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routes
from app.api.routes import shipments, deliveries, drivers, tracking, shipping

# Initialize FastAPI app
app = FastAPI(
    title="Delivery Management API",
    description="API for shipment management, delivery tracking, and logistics",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(shipments.router, prefix="/api/shipments", tags=["Shipments"])
app.include_router(deliveries.router, prefix="/api/deliveries", tags=["Deliveries"])
app.include_router(drivers.router, prefix="/api/drivers", tags=["Drivers"])
app.include_router(tracking.router, prefix="/api/tracking", tags=["Tracking"])
app.include_router(shipping.router, prefix="/api/shipping", tags=["Shipping Algorithm"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "service": "delivery-management"})

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "Delivery Management API",
        "version": "1.0.0",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
