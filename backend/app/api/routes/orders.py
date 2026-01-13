from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.schemas.order import (
    OrderCreate, OrderResponse, OrderProductResponse,
    StatusUpdateRequest, ShipOrderRequest, CancelOrderRequest,
    ConfirmOrderRequest, DeliverOrderRequest, OrderHistoryResponse,
    StatusHistoryResponse
)
from app.schemas.cart import OrderFromCartRequest
from app.services.payment_service import process_payment
from app.services.cart_service import CartService
from app.services.order_service import OrderService

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
            "title": product["title"],
            "size": product.get("size"),
            "color": product.get("color"),
            "sku": product.get("sku"),
            "weight": product.get("weight"),
            "dimensions": product.get("dimensions"),
            "material": product.get("material")
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
        "updated_at": datetime.utcnow(),
        "status_history": [
            {
                "status": "pending",
                "changed_at": datetime.utcnow(),
                "changed_by": "system",
                "note": "Order created"
            }
        ]
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
                title=p["title"],
                size=p.get("size"),
                color=p.get("color"),
                sku=p.get("sku"),
                weight=p.get("weight"),
                dimensions=p.get("dimensions"),
                material=p.get("material")
            )
            for p in order_data["products"]
        ],
        total_amount=order_data["total_amount"],
        status=order_data["status"],
        payment_method=order_data["payment_method"],
        created_at=order_data["created_at"],
        updated_at=order_data["updated_at"]
    )


@router.get("", response_model=dict)
async def get_orders(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by order status"),
    skip: int = Query(0, ge=0, alias="offset"),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get orders based on user role:
    - Customers (buyers): See orders they placed (filter by user_id)
    - Merchants: See orders they received (filter by merchant_id)
    - Admins: See all orders (if role exists in future)
    """
    user_id = str(current_user["_id"])
    user_role = current_user.get("role")
    
    # Determine filter based on role
    filter_query = {}
    
    if user_role == "buyer":
        filter_query = {"user_id": user_id}
    elif user_role == "merchant":
        # Get merchant profile to find merchant_id
        merchant = await OrderService.get_merchant_by_user_id(user_id, db)
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Merchant profile not found"
            )
        filter_query = {"merchant_id": merchant["user_id"]}
    elif user_role == "admin":
        filter_query = {}  # See all orders
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role"
        )
    
    # Add status filter if provided
    if status_filter:
        filter_query["status"] = status_filter
    
    # Query with pagination
    orders = await db.orders.find(filter_query).skip(skip).limit(limit).to_list(length=limit)
    total = await db.orders.count_documents(filter_query)
    
    return {
        "orders": [
            OrderResponse(
                id=str(order["_id"]),
                user_id=order["user_id"],
                merchant_id=order["merchant_id"],
                products=[
                    OrderProductResponse(
                        product_id=p["product_id"],
                        quantity=p["quantity"],
                        price=p["price"],
                        title=p["title"],
                        size=p.get("size"),
                        color=p.get("color"),
                        sku=p.get("sku"),
                        weight=p.get("weight"),
                        dimensions=p.get("dimensions"),
                        material=p.get("material")
                    )
                    for p in order["products"]
                ],
                total_amount=order["total_amount"],
                status=order["status"],
                payment_method=order["payment_method"],
                created_at=order["created_at"],
                updated_at=order.get("updated_at", order["created_at"]),
                status_history=[
                    StatusHistoryResponse(**h) for h in order.get("status_history", [])
                ] if order.get("status_history") else None,
                cancelled_by=order.get("cancelled_by"),
                cancellation_reason=order.get("cancellation_reason"),
                tracking_number=order.get("tracking_number"),
                shipped_at=order.get("shipped_at"),
                delivered_at=order.get("delivered_at")
            )
            for order in orders
        ],
        "total": total,
        "limit": limit,
        "offset": skip
    }


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
    user_role = current_user.get("role")
    
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
    
    # Verify access using service
    has_access = await OrderService.verify_order_access(order, user_id, user_role, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this order"
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
                title=p["title"],
                size=p.get("size"),
                color=p.get("color"),
                sku=p.get("sku"),
                weight=p.get("weight"),
                dimensions=p.get("dimensions"),
                material=p.get("material")
            )
            for p in order["products"]
        ],
        total_amount=order["total_amount"],
        status=order["status"],
        payment_method=order["payment_method"],
        created_at=order["created_at"],
        updated_at=order.get("updated_at", order["created_at"]),
        status_history=[
            StatusHistoryResponse(**h) for h in order.get("status_history", [])
        ] if order.get("status_history") else None,
        cancelled_by=order.get("cancelled_by"),
        cancellation_reason=order.get("cancellation_reason"),
        tracking_number=order.get("tracking_number"),
        shipped_at=order.get("shipped_at"),
        delivered_at=order.get("delivered_at")
    )


@router.post("/from-cart", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order_from_cart(
    request: OrderFromCartRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Create an order from the current user's cart.
    
    This will:
    1. Validate all cart items are available
    2. Process payment
    3. Create the order
    4. Clear the cart
    """
    user_id = str(current_user["_id"])
    
    # Validate cart and get order products
    order_products = await CartService.validate_cart_for_order(user_id, db)
    
    # Calculate total and get merchant_id
    total_amount = sum(p["price"] * p["quantity"] for p in order_products)
    merchant_id = order_products[0]["merchant_id"]
    
    # Process payment
    payment_result = await process_payment(
        amount=total_amount,
        method=request.payment_method,
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
        "payment_method": request.payment_method,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "status_history": [
            {
                "status": "pending",
                "changed_at": datetime.utcnow(),
                "changed_by": "system",
                "note": "Order created from cart"
            }
        ]
    }
    
    result = await db.orders.insert_one(order_data)
    order_data["_id"] = result.inserted_id
    
    # Update product stock
    for product in order_products:
        await db.products.update_one(
            {"_id": ObjectId(product["product_id"])},
            {"$inc": {"stock": -product["quantity"]}}
        )
    
    # Update merchant total_sales
    await db.merchants.update_one(
        {"user_id": merchant_id},
        {"$inc": {"total_sales": total_amount}}
    )
    
    # Clear cart
    await CartService.clear_cart(user_id, db)
    
    return OrderResponse(
        id=str(order_data["_id"]),
        user_id=order_data["user_id"],
        merchant_id=order_data["merchant_id"],
        products=[
            OrderProductResponse(
                product_id=p["product_id"],
                quantity=p["quantity"],
                price=p["price"],
                title=p["title"],
                size=p.get("size"),
                color=p.get("color"),
                sku=p.get("sku"),
                weight=p.get("weight"),
                dimensions=p.get("dimensions"),
                material=p.get("material")
            )
            for p in order_data["products"]
        ],
        total_amount=order_data["total_amount"],
        status=order_data["status"],
        payment_method=order_data["payment_method"],
        created_at=order_data["created_at"],
        updated_at=order_data["updated_at"]
    )


# ===== ORDER MANAGEMENT ENDPOINTS =====

@router.patch("/{order_id}/status")
async def update_order_status(
    order_id: str,
    request: StatusUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Update order status with validation.
    
    Valid transitions:
    - pending → confirmed (merchant only)
    - pending → cancelled (customer or merchant)
    - confirmed → shipped (merchant only)
    - confirmed → cancelled (merchant only)
    - shipped → delivered (merchant only)
    """
    user_id = str(current_user["_id"])
    user_role = current_user.get("role")
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status=request.status,
        user_id=user_id,
        user_role=user_role,
        db=db,
        note=request.note,
        tracking_number=request.tracking_number
    )
    
    return result


@router.post("/{order_id}/confirm")
async def confirm_order(
    order_id: str,
    request: ConfirmOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Confirm an order (shortcut for merchants).
    
    Only the merchant who received the order can confirm.
    Order must be in 'pending' status.
    """
    user_id = str(current_user["_id"])
    user_role = current_user.get("role")
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status="confirmed",
        user_id=user_id,
        user_role=user_role,
        db=db,
        note=request.note or "Order confirmed"
    )
    
    return {
        "message": "Order confirmed",
        "order_id": order_id,
        "status": "confirmed"
    }


@router.post("/{order_id}/ship")
async def ship_order(
    order_id: str,
    request: ShipOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Mark order as shipped (shortcut for merchants).
    
    Only the merchant who received the order can ship.
    Order must be in 'confirmed' status.
    Tracking number is required.
    """
    user_id = str(current_user["_id"])
    user_role = current_user.get("role")
    
    note = request.note or f"Shipped via {request.carrier}" if request.carrier else "Order shipped"
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status="shipped",
        user_id=user_id,
        user_role=user_role,
        db=db,
        note=note,
        tracking_number=request.tracking_number
    )
    
    # Get updated order to return shipped_at
    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    return {
        "message": "Order marked as shipped",
        "order_id": order_id,
        "status": "shipped",
        "tracking_number": request.tracking_number,
        "shipped_at": order.get("shipped_at")
    }


@router.post("/{order_id}/deliver")
async def deliver_order(
    order_id: str,
    request: DeliverOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Mark order as delivered (shortcut for merchants).
    
    Only the merchant who received the order can mark as delivered.
    Order must be in 'shipped' status.
    """
    user_id = str(current_user["_id"])
    user_role = current_user.get("role")
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status="delivered",
        user_id=user_id,
        user_role=user_role,
        db=db,
        note=request.note or "Order delivered"
    )
    
    # Get updated order to return delivered_at
    try:
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid order ID"
        )
    
    return {
        "message": "Order marked as delivered",
        "order_id": order_id,
        "status": "delivered",
        "delivered_at": order.get("delivered_at")
    }


@router.post("/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    request: CancelOrderRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Cancel an order.
    
    Authorization:
    - Customer can cancel if status is 'pending'
    - Merchant can cancel if status is 'pending' or 'confirmed'
    - Cannot cancel if status is 'shipped' or 'delivered'
    
    Actions:
    - Sets status to 'cancelled'
    - Records who cancelled and reason
    - Restores product stock
    - TODO: Initiates refund if payment completed
    - TODO: Sends notification to both parties
    """
    user_id = str(current_user["_id"])
    user_role = current_user.get("role")
    
    # Determine cancelled_by
    cancelled_by = "customer" if user_role == "buyer" else "merchant"
    
    # Build cancellation note
    note = f"Cancelled: {request.reason}"
    if request.details:
        note += f". {request.details}"
    
    result = await OrderService.update_order_status(
        order_id=order_id,
        new_status="cancelled",
        user_id=user_id,
        user_role=user_role,
        db=db,
        note=note,
        cancelled_by=cancelled_by,
        cancellation_reason=request.reason
    )
    
    return {
        "message": "Order cancelled successfully",
        "order_id": order_id,
        "status": "cancelled",
        "cancelled_by": cancelled_by,
        "reason": request.reason
    }


@router.get("/{order_id}/history", response_model=OrderHistoryResponse)
async def get_order_history(
    order_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get order status history.
    
    Authorization: Customer who placed order or merchant who received it.
    """
    user_id = str(current_user["_id"])
    user_role = current_user.get("role")
    
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
    
    # Verify access
    has_access = await OrderService.verify_order_access(order, user_id, user_role, db)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this order"
        )
    
    return OrderHistoryResponse(
        order_id=order_id,
        current_status=order["status"],
        history=[
            StatusHistoryResponse(**h) for h in order.get("status_history", [])
        ]
    )
