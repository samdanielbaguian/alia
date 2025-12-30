"""
Orange Money API service for Côte d'Ivoire.

Documentation: https://developer.orange.com/apis/orange-money-webpay/
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


class OrangeMoneyService:
    """Orange Money payment service."""
    
    def __init__(self):
        self.config = get_provider_config("orange_money")
        self.base_url = get_provider_url("orange_money")
        self.client_id = self.config.get("client_id")
        self.client_secret = self.config.get("client_secret")
        self.merchant_key = self.config.get("merchant_key")
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _get_access_token(self) -> str:
        """
        Get OAuth 2.0 access token for Orange Money API.
        
        Returns:
            Access token
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token
        
        # Request new token
        token_url = f"{self.base_url}/oauth/token"
        
        try:
            response = requests.post(
                token_url,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Authorization": f"Basic {self._encode_credentials()}"
                },
                data={
                    "grant_type": "client_credentials"
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            
            # Set expiration with 5-minute buffer
            from datetime import timedelta
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)
            
            logger.info("Successfully obtained Orange Money access token")
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Orange Money access token: {str(e)}")
            raise Exception(f"Orange Money authentication failed: {str(e)}")
    
    def _encode_credentials(self) -> str:
        """Encode client credentials for Basic Auth."""
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        return base64.b64encode(credentials.encode()).decode()
    
    async def initiate_payment(
        self,
        amount: float,
        phone_number: str,
        order_id: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """
        Initiate Orange Money payment.
        
        Args:
            amount: Payment amount in XOF
            phone_number: Customer's Orange Money number
            order_id: Order identifier
            payment_id: Payment identifier
            
        Returns:
            Payment initiation response
        """
        if PAYMENT_MODE == "SIMULATION":
            logger.warning("Orange Money called in SIMULATION mode - this shouldn't happen")
            return {"success": False, "message": "Use simulation service in SIMULATION mode"}
        
        logger.info(f"Initiating Orange Money payment for order {order_id}")
        
        try:
            access_token = await self._get_access_token()
            
            # Orange Money API endpoint for payment
            payment_url = f"{self.base_url}/webpayment/v1/transactionRequest"
            
            # Clean phone number (remove +225)
            cleaned_phone = phone_number.replace("+225", "").replace(" ", "")
            
            # Prepare request payload
            payload = {
                "merchant_key": self.merchant_key,
                "currency": "XOF",
                "order_id": order_id,
                "amount": int(amount),  # Orange Money expects integer
                "return_url": f"https://alia.com/payments/{payment_id}/callback",
                "cancel_url": f"https://alia.com/payments/{payment_id}/cancel",
                "notif_url": f"https://alia.com/api/payments/webhook/orange_money",
                "lang": "fr",
                "reference": payment_id,
                "customer_phone": cleaned_phone
            }
            
            response = requests.post(
                payment_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            logger.info(f"Orange Money payment initiated: {data.get('payment_token')}")
            
            return {
                "success": True,
                "transaction_id": data.get("payment_token"),
                "status": "pending",
                "message": f"Veuillez composer *144# pour confirmer le paiement de {amount:.0f} FCFA",
                "payment_url": data.get("payment_url"),
                "pay_token": data.get("pay_token")
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Orange Money payment initiation failed: {str(e)}")
            return {
                "success": False,
                "status": "failed",
                "message": f"Failed to initiate Orange Money payment: {str(e)}",
                "error_code": "API_ERROR"
            }
    
    async def check_payment_status(
        self,
        transaction_id: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """
        Check Orange Money payment status.
        
        Args:
            transaction_id: Orange Money transaction ID
            payment_id: Internal payment ID
            
        Returns:
            Payment status information
        """
        if PAYMENT_MODE == "SIMULATION":
            return {"success": False, "message": "Use simulation service in SIMULATION mode"}
        
        logger.info(f"Checking Orange Money payment status: {transaction_id}")
        
        try:
            access_token = await self._get_access_token()
            
            status_url = f"{self.base_url}/webpayment/v1/transactionStatus"
            
            response = requests.post(
                status_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "merchant_key": self.merchant_key,
                    "pay_token": transaction_id
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Map Orange Money status to our status
            om_status = data.get("status", "").lower()
            status_map = {
                "success": "completed",
                "pending": "pending",
                "failed": "failed",
                "cancelled": "cancelled"
            }
            status = status_map.get(om_status, "pending")
            
            return {
                "success": True,
                "status": status,
                "message": data.get("message", ""),
                "transaction_id": transaction_id
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check Orange Money payment status: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to check payment status: {str(e)}"
            }
    
    def verify_webhook_signature(
        self,
        signature: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Verify Orange Money webhook signature.
        
        Args:
            signature: Signature from webhook header
            payload: Webhook payload
            
        Returns:
            True if signature is valid
        """
        try:
            # Orange Money uses HMAC-SHA256 for webhook signatures
            secret = self.config.get("webhook_secret", self.merchant_key)
            
            # Create signature from payload
            import json
            payload_string = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            expected_signature = hmac.new(
                secret.encode(),
                payload_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying Orange Money webhook signature: {str(e)}")
            return False
