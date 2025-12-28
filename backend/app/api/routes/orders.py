from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.schemas.order import OrderCreate, OrderResponse, OrderProductResponse
from app.services.payment_service import process_payment

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order: OrderCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create a new order.
    
    This will:
    1. Validate products and calculate total
    2. Process payment
    3. Create the order in database
    4. For imported products, TODO: send order to AliExpress
    """
    user_id = str(current_user["_id"])
    
    # Validate products and calculate total
    order_products = []
    total_amount = 0.0
    merchant_id = None
    
    for item in order.products:
        # Get product details
        try:
            product = await db.products.find_one({"_id": ObjectId(item.product_id)})
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid product ID: {item.product_id}"
            )
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product not found: {item.product_id}"
            )
        
        # Check stock
        if product["stock"] < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product: {product['title']}"
            )
        
        # Set merchant_id (all products should be from same merchant)
        if merchant_id is None:
            merchant_id = product["merchant_id"]
        elif merchant_id != product["merchant_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All products must be from the same merchant"
            )
        
        # Calculate subtotal
        subtotal = product["price"] * item.quantity
        total_amount += subtotal
        
        order_products.append({
            "product_id": str(product["_id"]),
            "quantity": item.quantity,
            "price": product["price"],
            "title": product["title"]
        })
    
    # Process payment
    payment_result = await process_payment(
        amount=total_amount,
        method=order.payment_method,
        details={"user_id": user_id}
    )
    
    if payment_result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment failed: {payment_result.get('message')}"
        )
    
    # Create order
    order_data = {
        "user_id": user_id,
        "merchant_id": merchant_id,
        "products": order_products,
        "total_amount": total_amount,
        "status": "pending",
        "payment_method": order.payment_method,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.orders.insert_one(order_data)
    order_data["_id"] = result.inserted_id
    
    # Update product stock
    for item in order.products:
        await db.products.update_one(
            {"_id": ObjectId(item.product_id)},
            {"$inc": {"stock": -item.quantity}}
        )
    
    # Update merchant total_sales
    await db.merchants.update_one(
        {"user_id": merchant_id},
        {"$inc": {"total_sales": total_amount}}
    )
    
    # TODO: For imported products, send order to AliExpress
    
    return OrderResponse(
        id=str(order_data["_id"]),
        user_id=order_data["user_id"],
        merchant_id=order_data["merchant_id"],
        products=[
            OrderProductResponse(
                product_id=p["product_id"],
                quantity=p["quantity"],
                price=p["price"],
                title=p["title"]
            )
            for p in order_data["products"]
        ],
        total_amount=order_data["total_amount"],
        status=order_data["status"],
        payment_method=order_data["payment_method"],
        created_at=order_data["created_at"],
        updated_at=order_data["updated_at"]
    )


@router.get("", response_model=List[OrderResponse])
async def get_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all orders for the current user.
    """
    user_id = str(current_user["_id"])
    
    orders = await db.orders.find({"user_id": user_id}).skip(skip).limit(limit).to_list(length=limit)
    
    return [
        OrderResponse(
            id=str(order["_id"]),
            user_id=order["user_id"],
            merchant_id=order["merchant_id"],
            products=[
                OrderProductResponse(
                    product_id=p["product_id"],
                    quantity=p["quantity"],
                    price=p["price"],
                    title=p["title"]
                )
                for p in order["products"]
            ],
            total_amount=order["total_amount"],
            status=order["status"],
            payment_method=order["payment_method"],
            created_at=order["created_at"],
            updated_at=order.get("updated_at", order["created_at"])
        )
        for order in orders
    ]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get a specific order by ID.
    """
    user_id = str(current_user["_id"])
    
    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if user owns the order or is the merchant
    if order["user_id"] != user_id and order["merchant_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own orders"
        )
    
    return OrderResponse(
        id=str(order["_id"]),
        user_id=order["user_id"],
        merchant_id=order["merchant_id"],
        products=[
            OrderProductResponse(
                product_id=p["product_id"],
                quantity=p["quantity"],
                price=p["price"],
                title=p["title"]
            )
            for p in order["products"]
        ],
        total_amount=order["total_amount"],
        status=order["status"],
        payment_method=order["payment_method"],
        created_at=order["created_at"],
        updated_at=order.get("updated_at", order["created_at"])
    )
