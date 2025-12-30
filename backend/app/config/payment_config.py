"""
Payment system configuration for mobile money providers.

Supports three operating modes:
- SIMULATION: Mock payments for local development (no real API calls)
- SANDBOX: Test with provider sandbox APIs (for development/staging)
- PRODUCTION: Real transactions with live APIs
"""

import os
from typing import Dict, Any


# Payment operating mode
PAYMENT_MODE = os.getenv("PAYMENT_MODE", "SIMULATION")  # SIMULATION | SANDBOX | PRODUCTION

# Payment configuration
PAYMENT_CONFIG: Dict[str, Any] = {
    "mode": PAYMENT_MODE,
    
    # Orange Money Configuration
    "orange_money": {
        "sandbox_url": "https://api.orange.com/orange-money-webpay/dev/v1",
        "production_url": "https://api.orange.com/orange-money-webpay/v1",
        "client_id": os.getenv("ORANGE_CLIENT_ID", ""),
        "client_secret": os.getenv("ORANGE_CLIENT_SECRET", ""),
        "merchant_key": os.getenv("ORANGE_MERCHANT_KEY", ""),
        "api_version": "v1"
    },
    
    # MTN Mobile Money Configuration
    "mtn_money": {
        "sandbox_url": "https://sandbox.momodeveloper.mtn.com",
        "production_url": "https://proxy.momoapi.mtn.com",
        "subscription_key": os.getenv("MTN_SUBSCRIPTION_KEY", ""),
        "api_user": os.getenv("MTN_API_USER", ""),
        "api_key": os.getenv("MTN_API_KEY", ""),
        "callback_url": os.getenv("MTN_CALLBACK_URL", ""),
        "target_environment": "sandbox" if PAYMENT_MODE == "SANDBOX" else "production"
    },
    
    # Moov Money Configuration
    "moov_money": {
        "sandbox_url": "https://sandbox.moov-africa.com/api/v1",
        "production_url": "https://api.moov-africa.com/v1",
        "api_key": os.getenv("MOOV_API_KEY", ""),
        "api_secret": os.getenv("MOOV_API_SECRET", ""),
        "merchant_id": os.getenv("MOOV_MERCHANT_ID", "")
    },
    
    # Fee Configuration (in percentage)
    "fees": {
        "platform_commission_percent": float(os.getenv("PLATFORM_COMMISSION_PERCENT", "2.5")),
        "orange_gateway_fee_percent": float(os.getenv("ORANGE_GATEWAY_FEE_PERCENT", "1.5")),
        "mtn_gateway_fee_percent": float(os.getenv("MTN_GATEWAY_FEE_PERCENT", "1.8")),
        "moov_gateway_fee_percent": float(os.getenv("MOOV_GATEWAY_FEE_PERCENT", "2.0"))
    },
    
    # Payment Settings
    "timeout_minutes": int(os.getenv("PAYMENT_TIMEOUT_MINUTES", "10")),
    "max_retry_attempts": int(os.getenv("PAYMENT_MAX_RETRIES", "3")),
    "currency": "XOF",  # West African CFA franc
    
    # Webhook Configuration
    "webhook_secret": os.getenv("PAYMENT_WEBHOOK_SECRET", "change-this-in-production"),
    
    # Simulation Settings (for SIMULATION mode only)
    "simulation": {
        "auto_success_pattern": "0000",  # Phone numbers ending in 0000 auto-succeed
        "auto_failure_pattern": "9999",  # Phone numbers ending in 9999 auto-fail
        "auto_process_delay_seconds": 5  # Delay before auto-processing
    }
}


def get_provider_config(provider: str) -> Dict[str, Any]:
    """
    Get configuration for a specific payment provider.
    
    Args:
        provider: Provider name ("orange_money", "mtn_money", "moov_money")
        
    Returns:
        Provider configuration dictionary
    """
    return PAYMENT_CONFIG.get(provider, {})


def get_provider_url(provider: str) -> str:
    """
    Get the appropriate API URL for a provider based on the current mode.
    
    Args:
        provider: Provider name
        
    Returns:
        API URL for the provider
    """
    config = get_provider_config(provider)
    if PAYMENT_MODE == "PRODUCTION":
        return config.get("production_url", "")
    else:
        return config.get("sandbox_url", "")


def calculate_fees(amount: float, provider: str) -> Dict[str, float]:
    """
    Calculate platform and gateway fees for a payment.
    
    Args:
        amount: Payment amount in XOF
        provider: Payment provider
        
    Returns:
        Dictionary with fee breakdown
    """
    fees_config = PAYMENT_CONFIG["fees"]
    
    # Platform commission
    platform_fee = amount * (fees_config["platform_commission_percent"] / 100)
    
    # Gateway fee based on provider
    gateway_fee_percent = fees_config.get(f"{provider}_gateway_fee_percent", 2.0)
    gateway_fee = amount * (gateway_fee_percent / 100)
    
    # Merchant payout
    merchant_payout = amount - platform_fee - gateway_fee
    
    return {
        "gross_amount": amount,
        "platform_fee": round(platform_fee, 2),
        "payment_gateway_fee": round(gateway_fee, 2),
        "merchant_payout": round(merchant_payout, 2)
    }
