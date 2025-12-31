"""
Payment API routes for mobile money payments.

Handles payment initiation, status checking, webhooks, cancellation, and refunds.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

from app.api.deps import get_db, get_current_user
from app.schemas.payment import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentStatusResponse,
    PaymentHistoryResponse,
    CancelPaymentResponse,
    RefundRequest,
    RefundResponse,
    WebhookResponse,
    SimulatePaymentResponse
)
from app.services.payment_service import PaymentService
from app.config.payment_config import PAYMENT_MODE

router = APIRouter()
payment_service = PaymentService()


@router.post("/initiate", response_model=PaymentInitiateResponse, status_code=status.HTTP_201_CREATED)
async def initiate_payment(
    request: PaymentInitiateRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Initiate a mobile money payment for an order.
    
    The phone number must be a valid Ivorian mobile money number (+225XXXXXXXXXX).
    The system will automatically detect the provider (Orange Money, MTN Money, or Moov Money)
    based on the phone number prefix.
    
    **Validations:**
    - Order must exist and belong to the authenticated user
    - Order status must be "pending"
    - Phone number must be valid Ivorian format
    - Phone number must match a supported provider
    
    **Returns:**
    - Payment ID for tracking
    - Transaction ID from the provider
    - USSD code to complete payment (e.g., *144# for Orange Money)
    - Expiration time (10 minutes)
    """
    user_id = str(current_user["_id"])
    
    # Get order
    try:
        order = await db.orders.find_one({"_id": ObjectId(request.order_id)})
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
    
    # Check order belongs to user
    if order["user_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only pay for your own orders"
        )
    
    # Check order status
    if order["status"] != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pay for order with status: {order['status']}"
        )
    
    # Initiate payment
    result = await payment_service.initiate_payment(
        order_id=request.order_id,
        phone_number=request.phone_number,
        user_id=user_id,
        merchant_id=order["merchant_id"],
        amount=order["total_amount"],
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Payment initiation failed")
        )
    
    return PaymentInitiateResponse(
        payment_id=result["payment_id"],
        status=result["status"],
        amount=result["amount"],
        currency=result["currency"],
        provider=result["provider"],
        transaction_id=result.get("transaction_id"),
        message=result["message"],
        ussd_code=result["ussd_code"],
        expires_at=result["expires_at"]
    )


@router.get("/{payment_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    payment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get payment status by payment ID.
    
    This endpoint can be used to poll the payment status.
    It will also query the payment provider's API to get the latest status
    for pending/processing payments.
    
    **Authorization:**
    - User must be the payment owner or the merchant
    
    **Returns:**
    - Current payment status
    - Transaction details
    - Timestamps
    - Failure reason (if failed)
    """
    user_id = str(current_user["_id"])
    
    result = await payment_service.check_payment_status(
        payment_id=payment_id,
        user_id=user_id,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Payment not found")
        )
    
    return PaymentStatusResponse(**result)


@router.get("", response_model=PaymentHistoryResponse)
async def get_payment_history(
    status_filter: Optional[str] = Query(None, alias="status"),
    provider: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get payment history for the current user.
    
    **Filters:**
    - `status`: Filter by payment status (pending, completed, failed, etc.)
    - `provider`: Filter by provider (orange_money, mtn_money, moov_money)
    - `limit`: Max results per page (default: 20, max: 100)
    - `offset`: Skip results for pagination
    
    **Returns:**
    - List of payments
    - Total count
    - Pagination info
    """
    user_id = str(current_user["_id"])
    
    result = await payment_service.get_payment_history(
        user_id=user_id,
        db=db,
        status=status_filter,
        provider=provider,
        limit=limit,
        offset=offset
    )
    
    return PaymentHistoryResponse(**result)


@router.post("/webhook/{provider}", response_model=WebhookResponse)
async def payment_webhook(
    provider: str,
    payload: dict,
    x_signature: Optional[str] = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Webhook endpoint for payment providers to send payment confirmations.
    
    This endpoint receives notifications from Orange Money, MTN Money, and Moov Money
    when a payment status changes.
    
    **Security:**
    - Signature verification is required
    - HTTPS only in production
    
    **Actions:**
    - Updates payment status
    - Updates order status to "confirmed" if payment successful
    - Logs webhook payload for debugging
    """
    signature = x_signature or payload.get("signature", "")
    
    result = await payment_service.process_webhook(
        provider=provider,
        payload=payload,
        signature=signature,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Webhook processing failed")
        )
    
    return WebhookResponse(**result)


@router.post("/{payment_id}/cancel", response_model=CancelPaymentResponse)
async def cancel_payment(
    payment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Cancel a pending or processing payment.
    
    **Authorization:**
    - Only the customer who initiated the payment can cancel it
    
    **Conditions:**
    - Payment status must be "pending" or "processing"
    - Cannot cancel completed, failed, or already cancelled payments
    
    **Returns:**
    - Cancellation confirmation
    - Updated payment status
    """
    user_id = str(current_user["_id"])
    
    result = await payment_service.cancel_payment(
        payment_id=payment_id,
        user_id=user_id,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Payment cancellation failed")
        )
    
    return CancelPaymentResponse(**result)


@router.post("/{payment_id}/refund", response_model=RefundResponse)
async def refund_payment(
    payment_id: str,
    request: RefundRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Initiate a refund for a completed payment.
    
    **Authorization:**
    - Only the merchant of the order can initiate refunds
    
    **Conditions:**
    - Payment must be "completed"
    - Can request partial or full refund
    
    **Note:**
    This endpoint is currently a placeholder. Full refund implementation
    requires integration with provider refund APIs.
    
    **Returns:**
    - Refund ID for tracking
    - Refund status
    """
    user_id = str(current_user["_id"])
    
    # Get payment
    payment = await db.payments.find_one({"payment_id": payment_id})
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check authorization (must be merchant)
    if payment["merchant_id"] != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the merchant can refund payments"
        )
    
    # Check payment status
    if payment["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refund completed payments"
        )
    
    # TODO: Implement actual refund logic with provider APIs
    # For now, return placeholder response
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refund functionality is not yet implemented. Please contact support."
    )


# Admin endpoints for testing in SIMULATION mode

@router.post("/admin/{payment_id}/simulate-success", response_model=SimulatePaymentResponse)
async def simulate_payment_success(
    payment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Simulate successful payment completion (SIMULATION mode only).
    
    This endpoint is for testing purposes only and only works in SIMULATION mode.
    
    **Use case:**
    - Testing payment flows without real mobile money
    - Automated testing
    - Development
    
    **Note:** In production, this endpoint will return an error.
    """
    if PAYMENT_MODE != "SIMULATION":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in SIMULATION mode"
        )
    
    result = await payment_service.simulate_payment(
        payment_id=payment_id,
        success=True,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Simulation failed")
        )
    
    return SimulatePaymentResponse(**result)


@router.post("/admin/{payment_id}/simulate-failure", response_model=SimulatePaymentResponse)
async def simulate_payment_failure(
    payment_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Simulate payment failure (SIMULATION mode only).
    
    This endpoint is for testing purposes only and only works in SIMULATION mode.
    
    **Use case:**
    - Testing error handling
    - Testing failure recovery
    - Automated testing
    
    **Note:** In production, this endpoint will return an error.
    """
    if PAYMENT_MODE != "SIMULATION":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available in SIMULATION mode"
        )
    
    result = await payment_service.simulate_payment(
        payment_id=payment_id,
        success=False,
        db=db
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Simulation failed")
        )
    
    return SimulatePaymentResponse(**result)
