"""
Payment service - Core business logic for mobile money payments.

This service handles payment initiation, status tracking, webhooks,
and integrates with various payment providers.
"""

import logging
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.models.payment import Payment, PaymentStatus, PaymentProvider, Refund
from app.models.refund import Refund as RefundModel, RefundStatus
from app.utils.phone_validator import validate_ivorian_phone, detect_provider, get_ussd_code
from app.config.payment_config import PAYMENT_CONFIG, PAYMENT_MODE, calculate_fees

# Import payment providers
from app.services.payment_providers.simulation_service import SimulationService
from app.services.payment_providers.orange_money_service import OrangeMoneyService
from app.services.payment_providers.mtn_money_service import MTNMoneyService
from app.services.payment_providers.moov_money_service import MoovMoneyService

logger = logging.getLogger(__name__)


class PaymentService:
    """Core payment service handling all payment operations."""
    
    def __init__(self):
        self.simulation_service = SimulationService()
        self.orange_service = OrangeMoneyService()
        self.mtn_service = MTNMoneyService()
        self.moov_service = MoovMoneyService()
    
    async def initiate_payment(
        self,
        order_id: str,
        phone_number: str,
        user_id: str,
        merchant_id: str,
        amount: float,
        db: AsyncIOMotorDatabase
    ) -> Dict[str, Any]:
        """
        Initiate a mobile money payment.
        
        Args:
            order_id: Order identifier
            phone_number: Customer's mobile money number
            user_id: Customer user ID
            merchant_id: Merchant user ID
            amount: Payment amount in XOF
            db: Database connection
            
        Returns:
            Payment initiation response with payment_id and transaction details
        """
        logger.info(f"Initiating payment for order {order_id}, amount {amount} XOF")
        
        # Validate phone number
        is_valid, cleaned_phone, error = validate_ivorian_phone(phone_number)
        if not is_valid:
            return {
                "success": False,
                "message": f"Invalid phone number: {error}"
            }
        
        # Detect provider from phone number
        provider = detect_provider(cleaned_phone)
        if not provider:
            return {
                "success": False,
                "message": "Could not determine payment provider from phone number"
            }
        
        logger.info(f"Detected provider: {provider}")
        
        # Check for existing pending payment for this order
        existing_payment = await db.payments.find_one({
            "order_id": order_id,
            "status": {"$in": ["pending", "processing"]}
        })
        
        if existing_payment:
            # Check if it's expired
            if existing_payment["expires_at"] > datetime.utcnow():
                return {
                    "success": False,
                    "message": "A pending payment already exists for this order",
                    "payment_id": existing_payment.get("payment_id")
                }
        
        # Calculate fees
        fee_breakdown = calculate_fees(amount, provider)
        
        # Create payment record
        payment = Payment(
            order_id=order_id,
            user_id=user_id,
            merchant_id=merchant_id,
            amount=amount,
            currency="XOF",
            provider=PaymentProvider(provider),
            phone_number=cleaned_phone,
            status=PaymentStatus.PENDING,
            gross_amount=fee_breakdown["gross_amount"],
            platform_fee=fee_breakdown["platform_fee"],
            payment_gateway_fee=fee_breakdown["payment_gateway_fee"],
            merchant_payout=fee_breakdown["merchant_payout"],
            metadata={"mode": PAYMENT_MODE}
        )
        
        # Convert to dict for MongoDB
        payment_dict = payment.model_dump(by_alias=True, exclude={"id"})
        
        # Insert payment record
        result = await db.payments.insert_one(payment_dict)
        payment_id = payment.payment_id
        
        logger.info(f"Created payment record: {payment_id}")
        
        # Call appropriate provider service
        provider_response = await self._call_provider(
            provider=provider,
            amount=amount,
            phone_number=cleaned_phone,
            order_id=order_id,
            payment_id=payment_id
        )
        
        if not provider_response.get("success", False):
            # Update payment status to failed
            await db.payments.update_one(
                {"payment_id": payment_id},
                {
                    "$set": {
                        "status": PaymentStatus.FAILED,
                        "failure_reason": provider_response.get("message", "Provider error"),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "success": False,
                "message": provider_response.get("message", "Payment initiation failed"),
                "payment_id": payment_id
            }
        
        # Update payment with transaction ID
        transaction_id = provider_response.get("transaction_id")
        await db.payments.update_one(
            {"payment_id": payment_id},
            {
                "$set": {
                    "transaction_id": transaction_id,
                    "status": PaymentStatus.PENDING if provider_response.get("status") == "pending" else PaymentStatus.PROCESSING,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Get USSD code
        ussd_code = get_ussd_code(provider)
        
        # Return success response
        return {
            "success": True,
            "payment_id": payment_id,
            "status": provider_response.get("status", "pending"),
            "amount": amount,
            "currency": "XOF",
            "provider": provider,
            "transaction_id": transaction_id,
            "message": provider_response.get("message", f"Veuillez composer {ussd_code} pour confirmer le paiement de {amount:.0f} FCFA"),
            "ussd_code": ussd_code,
            "expires_at": payment.expires_at.isoformat()
        }
    
    async def _call_provider(
        self,
        provider: str,
        amount: float,
        phone_number: str,
        order_id: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """
        Call the appropriate payment provider service.
        
        Args:
            provider: Payment provider name
            amount: Payment amount
            phone_number: Customer phone number
            order_id: Order ID
            payment_id: Payment ID
            
        Returns:
            Provider response
        """
        if PAYMENT_MODE == "SIMULATION":
            return await self.simulation_service.initiate_payment(
                amount=amount,
                phone_number=phone_number,
                order_id=order_id,
                payment_id=payment_id,
                provider=provider
            )
        
        # Call real provider APIs in SANDBOX or PRODUCTION mode
        if provider == "orange_money":
            return await self.orange_service.initiate_payment(
                amount=amount,
                phone_number=phone_number,
                order_id=order_id,
                payment_id=payment_id
            )
        elif provider == "mtn_money":
            return await self.mtn_service.initiate_payment(
                amount=amount,
                phone_number=phone_number,
                order_id=order_id,
                payment_id=payment_id
            )
        elif provider == "moov_money":
            return await self.moov_service.initiate_payment(
                amount=amount,
                phone_number=phone_number,
                order_id=order_id,
                payment_id=payment_id
            )
        else:
            return {
                "success": False,
                "message": f"Unsupported provider: {provider}"
            }
    
    async def check_payment_status(
        self,
        payment_id: str,
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> Dict[str, Any]:
        """
        Check payment status.
        
        Args:
            payment_id: Payment identifier
            user_id: User ID (for authorization)
            db: Database connection
            
        Returns:
            Payment status information
        """
        # Get payment from database
        payment = await db.payments.find_one({"payment_id": payment_id})
        
        if not payment:
            return {
                "success": False,
                "message": "Payment not found"
            }
        
        # Check authorization
        if payment["user_id"] != user_id and payment["merchant_id"] != user_id:
            return {
                "success": False,
                "message": "Unauthorized access to payment"
            }
        
        # If payment is already completed, failed, cancelled, or refunded, return current status
        if payment["status"] in [PaymentStatus.COMPLETED, PaymentStatus.FAILED, PaymentStatus.CANCELLED, PaymentStatus.REFUNDED]:
            return {
                "success": True,
                "payment_id": payment["payment_id"],
                "order_id": payment["order_id"],
                "status": payment["status"],
                "amount": payment["amount"],
                "currency": payment["currency"],
                "provider": payment["provider"],
                "transaction_id": payment.get("transaction_id"),
                "phone_number": self._mask_phone(payment.get("phone_number")),
                "initiated_at": payment["initiated_at"].isoformat(),
                "completed_at": payment.get("completed_at").isoformat() if payment.get("completed_at") else None,
                "expires_at": payment.get("expires_at").isoformat() if payment.get("expires_at") else None,
                "failure_reason": payment.get("failure_reason")
            }
        
        # Check if payment has expired
        if payment.get("expires_at") and payment["expires_at"] < datetime.utcnow():
            # Update status to expired
            await db.payments.update_one(
                {"payment_id": payment_id},
                {
                    "$set": {
                        "status": PaymentStatus.EXPIRED,
                        "failure_reason": "Payment expired",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            payment["status"] = PaymentStatus.EXPIRED
            payment["failure_reason"] = "Payment expired"
        
        # For pending/processing payments, query provider API
        elif payment["status"] in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            if payment.get("transaction_id"):
                provider_status = await self._check_provider_status(
                    provider=payment["provider"],
                    transaction_id=payment["transaction_id"],
                    payment_id=payment_id
                )
                
                if provider_status.get("success"):
                    new_status = provider_status.get("status")
                    if new_status != payment["status"]:
                        # Update status
                        update_data = {
                            "status": new_status,
                            "updated_at": datetime.utcnow()
                        }
                        
                        if new_status == PaymentStatus.COMPLETED:
                            update_data["completed_at"] = datetime.utcnow()
                        elif new_status == PaymentStatus.FAILED:
                            update_data["failure_reason"] = provider_status.get("message", "Payment failed")
                        
                        await db.payments.update_one(
                            {"payment_id": payment_id},
                            {"$set": update_data}
                        )
                        
                        payment["status"] = new_status
                        if "completed_at" in update_data:
                            payment["completed_at"] = update_data["completed_at"]
                        if "failure_reason" in update_data:
                            payment["failure_reason"] = update_data["failure_reason"]
        
        # Return current status
        return {
            "success": True,
            "payment_id": payment["payment_id"],
            "order_id": payment["order_id"],
            "status": payment["status"],
            "amount": payment["amount"],
            "currency": payment["currency"],
            "provider": payment["provider"],
            "transaction_id": payment.get("transaction_id"),
            "phone_number": self._mask_phone(payment.get("phone_number")),
            "initiated_at": payment["initiated_at"].isoformat(),
            "completed_at": payment.get("completed_at").isoformat() if payment.get("completed_at") else None,
            "expires_at": payment.get("expires_at").isoformat() if payment.get("expires_at") else None,
            "failure_reason": payment.get("failure_reason")
        }
    
    async def _check_provider_status(
        self,
        provider: str,
        transaction_id: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """Check status with payment provider."""
        if PAYMENT_MODE == "SIMULATION":
            return await self.simulation_service.check_payment_status(transaction_id, payment_id)
        
        if provider == "orange_money":
            return await self.orange_service.check_payment_status(transaction_id, payment_id)
        elif provider == "mtn_money":
            return await self.mtn_service.check_payment_status(transaction_id, payment_id)
        elif provider == "moov_money":
            return await self.moov_service.check_payment_status(transaction_id, payment_id)
        
        return {"success": False, "message": "Unsupported provider"}
    
    async def process_webhook(
        self,
        provider: str,
        payload: Dict[str, Any],
        signature: str,
        db: AsyncIOMotorDatabase
    ) -> Dict[str, Any]:
        """
        Process webhook from payment provider.
        
        Args:
            provider: Payment provider name
            payload: Webhook payload
            signature: Webhook signature for verification
            db: Database connection
            
        Returns:
            Processing result
        """
        logger.info(f"Processing webhook from {provider}")
        
        # Verify signature
        if not self._verify_webhook_signature(provider, signature, payload):
            logger.warning(f"Invalid webhook signature from {provider}")
            return {
                "success": False,
                "message": "Invalid signature"
            }
        
        # Extract payment information from payload
        # Note: Payload format varies by provider
        transaction_id = payload.get("transaction_id") or payload.get("reference_id") or payload.get("pay_token")
        status = payload.get("status", "").lower()
        
        # Find payment by transaction_id
        payment = await db.payments.find_one({"transaction_id": transaction_id})
        
        if not payment:
            logger.warning(f"Payment not found for transaction {transaction_id}")
            return {
                "success": False,
                "message": "Payment not found"
            }
        
        payment_id = payment["payment_id"]
        order_id = payment["order_id"]
        
        # Map provider status to our status
        status_map = {
            "success": PaymentStatus.COMPLETED,
            "successful": PaymentStatus.COMPLETED,
            "completed": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "cancelled": PaymentStatus.CANCELLED,
            "pending": PaymentStatus.PROCESSING
        }
        
        new_status = status_map.get(status, PaymentStatus.PROCESSING)
        
        # Update payment
        update_data = {
            "status": new_status,
            "webhook_received_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata.webhook_payload": payload
        }
        
        if new_status == PaymentStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()
            
            # Update order status
            await db.orders.update_one(
                {"_id": ObjectId(order_id)},
                {
                    "$set": {
                        "status": "confirmed",
                        "payment_status": "completed",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Payment {payment_id} completed, order {order_id} confirmed")
            
        elif new_status == PaymentStatus.FAILED:
            update_data["failure_reason"] = payload.get("message", "Payment failed")
            
            # Update order status
            await db.orders.update_one(
                {"_id": ObjectId(order_id)},
                {
                    "$set": {
                        "payment_status": "failed",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        
        await db.payments.update_one(
            {"payment_id": payment_id},
            {"$set": update_data}
        )
        
        return {
            "success": True,
            "message": "Webhook processed successfully",
            "payment_id": payment_id,
            "status": new_status
        }
    
    def _verify_webhook_signature(
        self,
        provider: str,
        signature: str,
        payload: Dict[str, Any]
    ) -> bool:
        """Verify webhook signature from provider."""
        if PAYMENT_MODE == "SIMULATION":
            return self.simulation_service.verify_webhook_signature(signature, payload)
        
        if provider == "orange_money":
            return self.orange_service.verify_webhook_signature(signature, payload)
        elif provider == "mtn_money":
            return self.mtn_service.verify_webhook_signature(signature, payload)
        elif provider == "moov_money":
            return self.moov_service.verify_webhook_signature(signature, payload)
        
        return False
    
    async def cancel_payment(
        self,
        payment_id: str,
        user_id: str,
        db: AsyncIOMotorDatabase
    ) -> Dict[str, Any]:
        """
        Cancel a pending payment.
        
        Args:
            payment_id: Payment identifier
            user_id: User ID (must be payment owner)
            db: Database connection
            
        Returns:
            Cancellation result
        """
        payment = await db.payments.find_one({"payment_id": payment_id})
        
        if not payment:
            return {"success": False, "message": "Payment not found"}
        
        # Only customer can cancel their payment
        if payment["user_id"] != user_id:
            return {"success": False, "message": "Unauthorized"}
        
        # Can only cancel pending or processing payments
        if payment["status"] not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            return {
                "success": False,
                "message": f"Cannot cancel payment with status: {payment['status']}"
            }
        
        # Update payment status
        await db.payments.update_one(
            {"payment_id": payment_id},
            {
                "$set": {
                    "status": PaymentStatus.CANCELLED,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Payment {payment_id} cancelled by user {user_id}")
        
        return {
            "success": True,
            "message": "Payment cancelled successfully",
            "payment_id": payment_id,
            "status": PaymentStatus.CANCELLED
        }
    
    async def refund_payment(
        self,
        payment_id: str,
        amount: Optional[float],
        reason: str,
        note: Optional[str],
        merchant_id: str,
        db: AsyncIOMotorDatabase
    ) -> Dict[str, Any]:
        """
        Process payment refund.
        
        Args:
            payment_id: Payment ID to refund
            amount: Refund amount (None for full refund)
            reason: Refund reason
            note: Optional note
            merchant_id: Merchant initiating refund
            db: Database instance
            
        Returns:
            Refund result with refund_id, status, and details
        """
        logger.info(f"Initiating refund for payment {payment_id} by merchant {merchant_id}")
        
        # Get payment
        payment = await db.payments.find_one({"payment_id": payment_id})
        
        if not payment:
            return {"success": False, "message": "Payment not found"}
        
        # Verify merchant ownership
        if payment["merchant_id"] != merchant_id:
            logger.warning(f"Unauthorized refund attempt by {merchant_id} for payment {payment_id}")
            return {"success": False, "message": "Only the merchant can refund payments"}
        
        # Verify payment is completed
        if payment["status"] != "completed":
            return {
                "success": False,
                "message": f"Can only refund completed payments. Current status: {payment['status']}"
            }
        
        # Default to full refund if amount not specified
        if amount is None:
            amount = payment["amount"]
        
        # Verify amount
        if amount > payment["amount"]:
            return {
                "success": False,
                "message": f"Refund amount ({amount}) exceeds payment amount ({payment['amount']})"
            }
        
        if amount <= 0:
            return {"success": False, "message": "Refund amount must be greater than 0"}
        
        # Check for existing refund
        existing_refund = await db.refunds.find_one({
            "payment_id": payment_id,
            "status": {"$in": ["pending", "processing", "completed"]}
        })
        
        if existing_refund:
            return {
                "success": False,
                "message": "A refund already exists for this payment",
                "refund_id": existing_refund.get("refund_id")
            }
        
        # Create refund record
        refund = RefundModel(
            payment_id=payment_id,
            order_id=payment["order_id"],
            user_id=payment["user_id"],
            merchant_id=merchant_id,
            initiated_by=merchant_id,
            amount=amount,
            currency="XOF",
            reason=reason,
            note=note,
            provider=payment["provider"],
            transaction_id=payment.get("transaction_id"),
            status=RefundStatus.PENDING
        )
        
        refund_dict = refund.model_dump(by_alias=True, exclude={"id"})
        await db.refunds.insert_one(refund_dict)
        
        refund_id = refund.refund_id
        
        logger.info(f"Created refund record: {refund_id} for payment {payment_id}")
        
        # Call provider refund API
        if PAYMENT_MODE == "SIMULATION":
            # Auto-approve in simulation mode
            logger.info(f"[SIMULATION] Auto-approving refund {refund_id}")
            provider_response = {
                "success": True,
                "provider_refund_id": f"SIM_REF_{secrets.token_hex(8).upper()}",
                "status": "completed",
                "message": "Refund completed successfully (simulated)"
            }
        else:
            # Call real provider API
            provider_response = await self._call_provider_refund(
                provider=payment["provider"],
                transaction_id=payment.get("transaction_id"),
                amount=amount,
                refund_id=refund_id
            )
        
        if not provider_response.get("success"):
            # Mark refund as failed
            await db.refunds.update_one(
                {"refund_id": refund_id},
                {
                    "$set": {
                        "status": RefundStatus.FAILED,
                        "failure_reason": provider_response.get("message", "Provider refund failed"),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            logger.error(f"Refund failed: {refund_id} - {provider_response.get('message')}")
            return {
                "success": False,
                "message": provider_response.get("message", "Refund failed"),
                "refund_id": refund_id
            }
        
        # Update refund status to completed
        await db.refunds.update_one(
            {"refund_id": refund_id},
            {
                "$set": {
                    "status": RefundStatus.COMPLETED,
                    "provider_refund_id": provider_response.get("provider_refund_id"),
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Update payment status to refunded
        await db.payments.update_one(
            {"payment_id": payment_id},
            {
                "$set": {
                    "status": "refunded",
                    "updated_at": datetime.utcnow(),
                    "metadata.refund_id": refund_id,
                    "metadata.refunded_amount": amount,
                    "metadata.refund_reason": reason
                }
            }
        )
        
        # Update order status to refunded
        await db.orders.update_one(
            {"_id": ObjectId(payment["order_id"])},
            {
                "$set": {
                    "status": "cancelled",
                    "payment_status": "refunded",
                    "updated_at": datetime.utcnow()
                },
                "$push": {
                    "status_history": {
                        "status": "cancelled",
                        "changed_at": datetime.utcnow(),
                        "changed_by": merchant_id,
                        "note": f"Payment refunded: {reason}"
                    }
                }
            }
        )
        
        logger.info(f"Refund completed successfully: {refund_id}")
        
        refunded_at = datetime.utcnow()
        
        return {
            "success": True,
            "message": "Refund processed successfully",
            "refund_id": refund_id,
            "payment_id": payment_id,
            "amount": amount,
            "status": "refunded",
            "refunded_at": refunded_at.isoformat()
        }

    async def _call_provider_refund(
        self,
        provider: str,
        transaction_id: str,
        amount: float,
        refund_id: str
    ) -> Dict[str, Any]:
        """
        Call provider-specific refund API.
        
        Args:
            provider: Payment provider
            transaction_id: Original transaction ID
            amount: Refund amount
            refund_id: Refund identifier
            
        Returns:
            Provider refund response
        """
        logger.info(f"Calling {provider} refund API for transaction {transaction_id}")
        
        # TODO: Implement real provider refund APIs
        # For now, return success for all providers in sandbox/production mode
        
        if provider == "orange_money":
            # TODO: Implement Orange Money refund API
            return {
                "success": True,
                "provider_refund_id": f"OM_REF_{secrets.token_hex(8).upper()}",
                "status": "completed",
                "message": "Orange Money refund completed"
            }
        elif provider == "mtn_money":
            # TODO: Implement MTN Mobile Money refund API
            return {
                "success": True,
                "provider_refund_id": f"MTN_REF_{secrets.token_hex(8).upper()}",
                "status": "completed",
                "message": "MTN Money refund completed"
            }
        elif provider == "moov_money":
            # TODO: Implement Moov Money refund API
            return {
                "success": True,
                "provider_refund_id": f"MOOV_REF_{secrets.token_hex(8).upper()}",
                "status": "completed",
                "message": "Moov Money refund completed"
            }
        else:
            return {
                "success": False,
                "message": f"Unsupported provider for refund: {provider}"
            }
    
    async def simulate_payment(
        self,
        payment_id: str,
        success: bool,
        db: AsyncIOMotorDatabase
    ) -> Dict[str, Any]:
        """
        Simulate payment success or failure (SIMULATION mode only).
        
        Args:
            payment_id: Payment identifier
            success: True for success, False for failure
            db: Database connection
            
        Returns:
            Simulation result
        """
        if PAYMENT_MODE != "SIMULATION":
            return {
                "success": False,
                "message": "Payment simulation only available in SIMULATION mode"
            }
        
        payment = await db.payments.find_one({"payment_id": payment_id})
        
        if not payment:
            return {"success": False, "message": "Payment not found"}
        
        if payment["status"] not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            return {
                "success": False,
                "message": f"Cannot simulate payment with status: {payment['status']}"
            }
        
        if success:
            # Simulate success
            await db.payments.update_one(
                {"payment_id": payment_id},
                {
                    "$set": {
                        "status": PaymentStatus.COMPLETED,
                        "completed_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Update order
            await db.orders.update_one(
                {"_id": ObjectId(payment["order_id"])},
                {
                    "$set": {
                        "status": "confirmed",
                        "payment_status": "completed",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "success": True,
                "message": "Payment simulated successfully",
                "payment_id": payment_id,
                "status": PaymentStatus.COMPLETED
            }
        else:
            # Simulate failure
            await db.payments.update_one(
                {"payment_id": payment_id},
                {
                    "$set": {
                        "status": PaymentStatus.FAILED,
                        "failure_reason": "Simulated failure",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "success": True,
                "message": "Payment failure simulated",
                "payment_id": payment_id,
                "status": PaymentStatus.FAILED
            }
    
    def _mask_phone(self, phone_number: Optional[str]) -> Optional[str]:
        """Mask phone number for privacy (show only last 4 digits)."""
        if not phone_number:
            return None
        
        # Show only last 4 digits: +225****3456
        if len(phone_number) >= 8:
            return phone_number[:4] + "*" * (len(phone_number) - 8) + phone_number[-4:]
        return phone_number
    
    async def get_payment_history(
        self,
        user_id: str,
        db: AsyncIOMotorDatabase,
        status: Optional[str] = None,
        provider: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get payment history for a user.
        
        Args:
            user_id: User ID
            db: Database connection
            status: Filter by status
            provider: Filter by provider
            limit: Max results
            offset: Skip results
            
        Returns:
            Payment history
        """
        query = {"user_id": user_id}
        
        if status:
            query["status"] = status
        if provider:
            query["provider"] = provider
        
        # Get total count
        total = await db.payments.count_documents(query)
        
        # Get payments
        payments = await db.payments.find(query).sort("created_at", -1).skip(offset).limit(limit).to_list(length=limit)
        
        payment_items = []
        for payment in payments:
            payment_items.append({
                "payment_id": payment["payment_id"],
                "order_id": payment["order_id"],
                "amount": payment["amount"],
                "status": payment["status"],
                "provider": payment["provider"],
                "created_at": payment["created_at"].isoformat(),
                "completed_at": payment.get("completed_at").isoformat() if payment.get("completed_at") else None
            })
        
        return {
            "success": True,
            "payments": payment_items,
            "total": total,
            "limit": limit,
            "offset": offset
        }


# Legacy function for backward compatibility
async def process_payment(amount: float, method: str, details: Dict) -> Dict:
    """
    Legacy payment processing function (for backward compatibility).
    
    This function is kept for compatibility with existing order creation code.
    New code should use PaymentService.initiate_payment() directly.
    """
    # For now, return pending status to allow order creation
    # The actual payment will be initiated separately via the payment API
    return {
        "status": "pending",
        "transaction_id": "PENDING",
        "message": "Payment pending - will be initiated separately",
        "amount": amount,
        "method": method
    }
