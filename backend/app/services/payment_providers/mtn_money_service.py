"""
MTN Mobile Money API service for Côte d'Ivoire.

Documentation: https://momodeveloper.mtn.com/
"""

import requests
import secrets
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import hmac
import hashlib
import uuid

from app.config.payment_config import get_provider_config, get_provider_url, PAYMENT_MODE

logger = logging.getLogger(__name__)


class MTNMoneyService:
    """MTN Mobile Money payment service."""
    
    def __init__(self):
        self.config = get_provider_config("mtn_money")
        self.base_url = get_provider_url("mtn_money")
        self.subscription_key = self.config.get("subscription_key")
        self.api_user = self.config.get("api_user")
        self.api_key = self.config.get("api_key")
        self.target_environment = self.config.get("target_environment", "sandbox")
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
    
    async def _get_access_token(self) -> str:
        """
        Get access token for MTN MoMo API.
        
        Returns:
            Access token
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token
        
        # Request new token
        token_url = f"{self.base_url}/collection/token/"
        
        try:
            import base64
            credentials = f"{self.api_user}:{self.api_key}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            response = requests.post(
                token_url,
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Ocp-Apim-Subscription-Key": self.subscription_key,
                    "X-Target-Environment": self.target_environment
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
            
            logger.info("Successfully obtained MTN MoMo access token")
            return self._access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get MTN MoMo access token: {str(e)}")
            raise Exception(f"MTN MoMo authentication failed: {str(e)}")
    
    async def initiate_payment(
        self,
        amount: float,
        phone_number: str,
        order_id: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """
        Initiate MTN Mobile Money payment.
        
        Args:
            amount: Payment amount in XOF
            phone_number: Customer's MTN Mobile Money number
            order_id: Order identifier
            payment_id: Payment identifier
            
        Returns:
            Payment initiation response
        """
        if PAYMENT_MODE == "SIMULATION":
            logger.warning("MTN Money called in SIMULATION mode - this shouldn't happen")
            return {"success": False, "message": "Use simulation service in SIMULATION mode"}
        
        logger.info(f"Initiating MTN MoMo payment for order {order_id}")
        
        try:
            access_token = await self._get_access_token()
            
            # Generate reference ID for this transaction
            reference_id = str(uuid.uuid4())
            
            # MTN MoMo API endpoint for payment request
            payment_url = f"{self.base_url}/collection/v1_0/requesttopay"
            
            # Clean phone number (keep format with country code)
            cleaned_phone = phone_number.replace("+", "").replace(" ", "")
            
            # Prepare request payload
            payload = {
                "amount": str(int(amount)),
                "currency": "XOF",
                "externalId": order_id,
                "payer": {
                    "partyIdType": "MSISDN",
                    "partyId": cleaned_phone
                },
                "payerMessage": f"Payment for order {order_id}",
                "payeeNote": f"Alia order {order_id}"
            }
            
            response = requests.post(
                payment_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Reference-Id": reference_id,
                    "X-Target-Environment": self.target_environment,
                    "Ocp-Apim-Subscription-Key": self.subscription_key,
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30
            )
            
            # MTN returns 202 Accepted for successful initiation
            if response.status_code == 202:
                logger.info(f"MTN MoMo payment initiated: {reference_id}")
                
                return {
                    "success": True,
                    "transaction_id": reference_id,
                    "status": "pending",
                    "message": f"Veuillez composer *133# pour confirmer le paiement de {amount:.0f} FCFA"
                }
            else:
                response.raise_for_status()
                return {
                    "success": False,
                    "status": "failed",
                    "message": "Failed to initiate MTN MoMo payment",
                    "error_code": "API_ERROR"
                }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MTN MoMo payment initiation failed: {str(e)}")
            return {
                "success": False,
                "status": "failed",
                "message": f"Failed to initiate MTN MoMo payment: {str(e)}",
                "error_code": "API_ERROR"
            }
    
    async def check_payment_status(
        self,
        transaction_id: str,
        payment_id: str
    ) -> Dict[str, Any]:
        """
        Check MTN Mobile Money payment status.
        
        Args:
            transaction_id: MTN MoMo reference ID
            payment_id: Internal payment ID
            
        Returns:
            Payment status information
        """
        if PAYMENT_MODE == "SIMULATION":
            return {"success": False, "message": "Use simulation service in SIMULATION mode"}
        
        logger.info(f"Checking MTN MoMo payment status: {transaction_id}")
        
        try:
            access_token = await self._get_access_token()
            
            status_url = f"{self.base_url}/collection/v1_0/requesttopay/{transaction_id}"
            
            response = requests.get(
                status_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "X-Target-Environment": self.target_environment,
                    "Ocp-Apim-Subscription-Key": self.subscription_key
                },
                timeout=30
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Map MTN status to our status
            mtn_status = data.get("status", "").upper()
            status_map = {
                "SUCCESSFUL": "completed",
                "PENDING": "pending",
                "FAILED": "failed"
            }
            status = status_map.get(mtn_status, "pending")
            
            return {
                "success": True,
                "status": status,
                "message": data.get("reason", ""),
                "transaction_id": transaction_id
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to check MTN MoMo payment status: {str(e)}")
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
        Verify MTN MoMo webhook signature.
        
        Args:
            signature: Signature from webhook header
            payload: Webhook payload
            
        Returns:
            True if signature is valid
        """
        try:
            # MTN MoMo webhook verification
            # Note: Actual implementation depends on MTN's webhook signature method
            secret = self.config.get("webhook_secret", self.api_key)
            
            import json
            payload_string = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            expected_signature = hmac.new(
                secret.encode(),
                payload_string.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Error verifying MTN MoMo webhook signature: {str(e)}")
            return False
