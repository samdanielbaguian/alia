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
        - Ending in 0000: Auto-success after delay
        - Ending in 9999: Auto-failure
        - Other: Pending (requires manual confirmation)
        
        Args:
            amount: Payment amount in XOF
            phone_number: Customer's phone number
            order_id: Order identifier
            payment_id: Payment identifier
            
        Returns:
            Simulated payment initiation response
        """
        logger.info(f"[SIMULATION] Initiating payment for order {order_id}")
        
        # Generate mock transaction ID
        transaction_id = f"SIM_{secrets.token_hex(8).upper()}"
        
        # Determine behavior based on phone number
        simulation_config = PAYMENT_CONFIG["simulation"]
        auto_success = phone_number.endswith(simulation_config["auto_success_pattern"])
        auto_failure = phone_number.endswith(simulation_config["auto_failure_pattern"])
        
        if auto_failure:
            logger.info(f"[SIMULATION] Auto-failure pattern detected for {phone_number}")
            return {
                "success": False,
                "transaction_id": transaction_id,
                "status": "failed",
                "message": "Simulation: Payment failed (test pattern 9999)",
                "error_code": "INSUFFICIENT_FUNDS"
            }
        
        # Get correct USSD code for provider
        ussd_code = get_ussd_code(provider)

        status = "pending"
        message = f"Veuillez composer {ussd_code} pour confirmer le paiement de {amount:.0f} FCFA"
        
        if auto_success:
            logger.info(f"[SIMULATION] Auto-success pattern detected for {phone_number}")
            message = f"Simulation: Payment will auto-complete in {simulation_config['auto_process_delay_seconds']} seconds (Provider: {provider.upper()})"
            
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
