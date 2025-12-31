"""
Simulation service for testing payments without real API calls.

This service is used in SIMULATION mode for local development and testing.
It simulates payment responses based on phone number patterns.
"""

import asyncio
import secrets
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from app.config.payment_config import PAYMENT_CONFIG
from app.utils.phone_validator import get_ussd_code

logger = logging.getLogger(__name__)


# Magic phone numbers for automated simulation
MAGIC_NUMBERS = {
    "+2250777123456": "SUCCESS",   # Auto-complete after delay
    "+2250777123457": "PENDING",   # Stay pending (manual webhook required)
    "+2250777123458": "FAILED"     # Auto-fail after delay
}


class SimulationService:
    """Payment simulation service for testing."""
    
    @staticmethod
    async def initiate_payment(
        amount: float,
        phone_number: str,
        order_id: str,
        payment_id: str,
        provider: str = "orange_money"
    ) -> Dict[str, Any]:
        """
        Simulate payment initiation.
        
        Phone number patterns:
        - Magic numbers (specific behavior):
          - +2250777123456: Auto-success after delay
          - +2250777123457: Stay pending (manual webhook required)
          - +2250777123458: Auto-fail after delay
        - Ending in 0000: Auto-success after delay (old pattern)
        - Ending in 9999: Auto-failure (old pattern)
        - Other: Pending (requires manual confirmation)
        
        Args:
            amount: Payment amount in XOF
            phone_number: Customer's phone number
            order_id: Order identifier
            payment_id: Payment identifier
            provider: Payment provider (orange_money, mtn_money, moov_money)
            
        Returns:
            Simulated payment initiation response
        """
        logger.info(f"[SIMULATION] Initiating payment for order {order_id}")
        
        # Generate mock transaction ID
        transaction_id = f"SIM_{secrets.token_hex(8).upper()}"
        
        # Determine behavior based on phone number (magic numbers)
        magic_behavior = MAGIC_NUMBERS.get(phone_number, "PENDING")
        
        simulation_config = PAYMENT_CONFIG["simulation"]
        auto_success = magic_behavior == "SUCCESS"
        auto_failure = magic_behavior == "FAILED"
        
        # Fallback to old pattern matching if not a magic number
        if magic_behavior == "PENDING":
            auto_success = phone_number.endswith(simulation_config["auto_success_pattern"])
            auto_failure = phone_number.endswith(simulation_config["auto_failure_pattern"])
        
        if auto_failure:
            logger.info(f"[SIMULATION] Auto-failure pattern detected for {phone_number}")
            # Schedule automatic failure after delay
            delay = 3
            asyncio.create_task(
                SimulationService._auto_fail_payment(
                    payment_id=payment_id,
                    transaction_id=transaction_id,
                    provider=provider,
                    delay_seconds=delay
                )
            )
            return {
                "success": True,
                "transaction_id": transaction_id,
                "status": "pending",
                "message": f"Simulation: Payment will auto-fail in {delay} seconds (magic number)",
                "ussd_code": get_ussd_code(provider),
                "provider": provider,
                "simulation_mode": True,
                "auto_failure": True
            }
        
        # Get correct USSD code for provider
        ussd_code = get_ussd_code(provider)

        status = "pending"
        message = f"Veuillez composer {ussd_code} pour confirmer le paiement de {amount:.0f} FCFA"
        
        if auto_success:
            logger.info(f"[SIMULATION] Auto-success pattern detected for {phone_number}")
            message = f"Simulation: Payment will auto-complete in {simulation_config['auto_process_delay_seconds']} seconds (Provider: {provider.upper()})"
            
            # Schedule automatic success after delay
            asyncio.create_task(
                SimulationService._auto_complete_payment(
                    payment_id=payment_id,
                    transaction_id=transaction_id,
                    provider=provider,
                    delay_seconds=simulation_config['auto_process_delay_seconds']
                )
            )
            
        return {
            "success": True,
            "transaction_id": transaction_id,
            "status": status,
            "message": message,
            "ussd_code": ussd_code,
            "provider": provider,
            "simulation_mode": True,
            "auto_success": auto_success
        }
    
    @staticmethod
    async def check_payment_status(transaction_id: str, payment_id: str) -> Dict[str, Any]:
        """
        Check simulated payment status.
        
        Args:
            transaction_id: Provider's transaction ID
            payment_id: Internal payment ID
            
        Returns:
            Payment status information
        """
        logger.info(f"[SIMULATION] Checking payment status for transaction {transaction_id}")
        
        # In simulation, we return pending status
        # Actual status updates happen via simulate_success/failure endpoints
        return {
            "success": True,
            "status": "pending",
            "message": "Payment pending confirmation",
            "simulation_mode": True
        }
    
    @staticmethod
    async def simulate_success(payment_id: str) -> Dict[str, Any]:
        """
        Simulate successful payment completion.
        
        Args:
            payment_id: Payment identifier
            
        Returns:
            Success confirmation
        """
        logger.info(f"[SIMULATION] Simulating payment success for {payment_id}")
        
        return {
            "success": True,
            "status": "completed",
            "message": "Payment completed successfully (simulated)",
            "completed_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    async def simulate_failure(payment_id: str, reason: str = "User cancelled") -> Dict[str, Any]:
        """
        Simulate failed payment.
        
        Args:
            payment_id: Payment identifier
            reason: Failure reason
            
        Returns:
            Failure confirmation
        """
        logger.info(f"[SIMULATION] Simulating payment failure for {payment_id}: {reason}")
        
        return {
            "success": True,
            "status": "failed",
            "message": f"Payment failed (simulated): {reason}",
            "failure_reason": reason
        }
    
    @staticmethod
    async def auto_complete_payment(
        payment_id: str,
        delay_seconds: int = None
    ) -> None:
        """
        Auto-complete a payment after delay (for auto-success pattern).
        
        Args:
            payment_id: Payment identifier
            delay_seconds: Delay before completion
        """
        if delay_seconds is None:
            delay_seconds = PAYMENT_CONFIG["simulation"]["auto_process_delay_seconds"]
        
        logger.info(f"[SIMULATION] Will auto-complete payment {payment_id} in {delay_seconds}s")
        
        # This would trigger an async task in production
        # For now, we just log it
        await asyncio.sleep(delay_seconds)
        logger.info(f"[SIMULATION] Auto-completed payment {payment_id}")
    
    @staticmethod
    async def _auto_complete_payment(
        payment_id: str,
        transaction_id: str,
        provider: str,
        delay_seconds: int = 5
    ):
        """
        Automatically complete payment after delay (simulation only).
        
        This simulates the provider webhook callback for successful payment.
        
        Args:
            payment_id: Payment identifier
            transaction_id: Simulated transaction ID
            provider: Payment provider
            delay_seconds: Delay before auto-completion
        """
        logger.info(f"[SIMULATION] Scheduling auto-complete for payment {payment_id} in {delay_seconds}s")
        
        await asyncio.sleep(delay_seconds)
        
        try:
            # Import here to avoid circular dependencies
            from app.core.database import get_database
            
            db = get_database()
            
            # Update payment status to completed
            result = await db.payments.update_one(
                {"payment_id": payment_id},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.utcnow(),
                        "webhook_received_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "metadata.auto_completed": True,
                        "metadata.simulation_auto_trigger": True
                    }
                }
            )
            
            if result.modified_count == 0:
                logger.warning(f"[SIMULATION] Failed to auto-complete payment {payment_id}")
                return
            
            # Get payment details to update order
            payment = await db.payments.find_one({"payment_id": payment_id})
            
            if payment:
                # Update associated order status
                await db.orders.update_one(
                    {"_id": payment["order_id"]},
                    {
                        "$set": {
                            "status": "confirmed",
                            "payment_status": "completed",
                            "updated_at": datetime.utcnow()
                        },
                        "$push": {
                            "status_history": {
                                "status": "confirmed",
                                "changed_at": datetime.utcnow(),
                                "changed_by": "system",
                                "note": f"Payment completed automatically (simulation) - {transaction_id}"
                            }
                        }
                    }
                )
                
                logger.info(f"[SIMULATION] ✅ Auto-completed payment {payment_id} and updated order {payment['order_id']}")
            
        except Exception as e:
            logger.error(f"[SIMULATION] Error auto-completing payment {payment_id}: {str(e)}")
    
    @staticmethod
    async def _auto_fail_payment(
        payment_id: str,
        transaction_id: str,
        provider: str,
        delay_seconds: int = 3
    ):
        """
        Automatically fail payment after delay (simulation only).
        
        This simulates the provider webhook callback for failed payment.
        
        Args:
            payment_id: Payment identifier
            transaction_id: Simulated transaction ID (unused but kept for symmetry with _auto_complete_payment)
            provider: Payment provider (unused but kept for future extensibility)
            delay_seconds: Delay before auto-failure
        """
        logger.info(f"[SIMULATION] Scheduling auto-fail for payment {payment_id} in {delay_seconds}s")
        
        await asyncio.sleep(delay_seconds)
        
        try:
            # Import here to avoid circular dependencies
            from app.core.database import get_database
            
            db = get_database()
            
            # Update payment status to failed
            result = await db.payments.update_one(
                {"payment_id": payment_id},
                {
                    "$set": {
                        "status": "failed",
                        "failure_reason": "Insufficient balance (simulated failure via magic number)",
                        "webhook_received_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow(),
                        "metadata.auto_failed": True,
                        "metadata.simulation_auto_trigger": True
                    }
                }
            )
            
            if result.modified_count == 0:
                logger.warning(f"[SIMULATION] Failed to auto-fail payment {payment_id}")
                return
            
            logger.info(f"[SIMULATION] ❌ Auto-failed payment {payment_id}")
            
        except Exception as e:
            logger.error(f"[SIMULATION] Error auto-failing payment {payment_id}: {str(e)}")
    
    @staticmethod
    def verify_webhook_signature(signature: str, payload: Dict[str, Any]) -> bool:
        """
        Verify webhook signature (always returns True in simulation).
        
        Args:
            signature: Signature to verify
            payload: Webhook payload
            
        Returns:
            True (simulation always accepts)
        """
        logger.info("[SIMULATION] Webhook signature verification (auto-accept)")
        return True
