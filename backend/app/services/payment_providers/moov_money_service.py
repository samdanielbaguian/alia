"""
Moov Money API service for Côte d'Ivoire.

Documentation: https://www.moov-africa.ci/ (Contact Moov for API docs)
"""

import requests
import secrets
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hmac
import hashlib

from app.config.payment_config import get_provider_config, get_provider_url, PAYMENT_MODE

logger = logging.getLogger(__name__)


class MoovMoneyService:
    """Moov Money payment service."""
    
    def __init__(self):
        self.config = get_provider_config("moov_money")
        self.base_url = get_provider_url("moov_money")
        self.api_key = self.config.get("api_key")
        self.api_secret = self.config.get("api_secret")
        self.merchant_id = self.config.get("merchant_id")
    
    async def initiate_payment(
        self,
        amount: float,
        phone_number: str,
        order_id: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """
        Initiate Moov Money payment.
        
        Args:
            amount: Payment amount in XOF
            phone_number: Customer's Moov Money number
            order_id: Order identifier
            payment_id: Payment identifier
            
        Returns:
            Payment initiation response
        """
        if PAYMENT_MODE == "SIMULATION":
            logger.warning("Moov Money called in SIMULATION mode - this shouldn't happen")
            return {"success": False, "message": "Use simulation service in SIMULATION mode"}
        
        logger.info(f"Initiating Moov Money payment for order {order_id}")
        
        try:
            # Moov Money API endpoint for payment
            payment_url = f"{self.base_url}/payments/init"
            
            # Clean phone number (remove +225)
            cleaned_phone = phone_number.replace("+225", "").replace(" ", "")
            
            # Generate transaction reference
            transaction_ref = f"MOOV_{secrets.token_hex(8).upper()}"
            
            # Prepare request payload
            payload = {
                "merchant_id": self.merchant_id,
                "amount": int(amount),
                "currency": "XOF",
                "reference": transaction_ref,
                "order_id": order_id,
                "customer_phone": cleaned_phone,
                "callback_url": f"https://alia.com/api/payments/webhook/moov_money",
                "description": f"Payment for Alia order {order_id}"
            }
            
            # Create signature for request
            signature = self._create_signature(payload)
            
            response = requests.post(
                payment_url,
                headers={
                    "X-API-Key": self.api_key,
                    "X-Signature": signature,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Moov Money payment initiated: {data.get('transaction_id')}")
            
            return {
                "success": True,
                "transaction_id": data.get("transaction_id", transaction_ref),
                "status": "pending",
                "message": f"Veuillez composer *155# pour confirmer le paiement de {amount:.0f} FCFA",
                "ussd_code": "*155#"
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Moov Money payment initiation failed: {str(e)}")
            return {
                "success": False,
                "status": "failed",
                "message": f"Failed to initiate Moov Money payment: {str(e)}",
                "error_code": "API_ERROR"
            }
    
    async def check_payment_status(
        self,
        transaction_id: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """
        Check Moov Money payment status.
        
        Args:
            transaction_id: Moov Money transaction ID
            payment_id: Internal payment ID
            
        Returns:
            Payment status information
        """
        if PAYMENT_MODE == "SIMULATION":
            return {"success": False, "message": "Use simulation service in SIMULATION mode"}
        
        logger.info(f"Checking Moov Money payment status: {transaction_id}")
        
        try:
            status_url = f"{self.base_url}/payments/{transaction_id}/status"
            
            response = requests.get(
                status_url,
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Map Moov Money status to our status
            moov_status = data.get("status", "").lower()
            status_map = {
                "success": "completed",
                "completed": "completed",
                "pending": "pending",
                "failed": "failed",
                "cancelled": "cancelled"
            }
            status = status_map.get(moov_status, "pending")
            
            return {
                "success": True,
                "status": status,
                "message": data.get("message", ""),
                "transaction_id": transaction_id
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check Moov Money payment status: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to check payment status: {str(e)}"
            }
    
    def _create_signature(self, payload: Dict[str, Any]) -> str:
        """
        Create signature for Moov Money API request.
        
        Args:
            payload: Request payload
            
        Returns:
            HMAC signature
        """
        import json
        payload_string = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            self.api_secret.encode(),
            payload_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_webhook_signature(
        self,
        signature: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Verify Moov Money webhook signature.
        
        Args:
            signature: Signature from webhook header
            payload: Webhook payload
            
        Returns:
            True if signature is valid
        """
        try:
            expected_signature = self._create_signature(payload)
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying Moov Money webhook signature: {str(e)}")
            return False
