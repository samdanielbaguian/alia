"""
Tests for payment configuration.
"""

import pytest
from app.config.payment_config import (
    PAYMENT_CONFIG,
    get_provider_config,
    get_provider_url,
    calculate_fees
)


class TestPaymentConfig:
    """Test payment configuration."""
    
    def test_payment_mode_exists(self):
        """Test payment mode is configured."""
        assert "mode" in PAYMENT_CONFIG
        assert PAYMENT_CONFIG["mode"] in ["SIMULATION", "SANDBOX", "PRODUCTION"]
    
    def test_providers_configured(self):
        """Test all providers are configured."""
        assert "orange_money" in PAYMENT_CONFIG
        assert "mtn_money" in PAYMENT_CONFIG
        assert "moov_money" in PAYMENT_CONFIG
    
    def test_fees_configured(self):
        """Test fee configuration exists."""
        assert "fees" in PAYMENT_CONFIG
        assert "platform_commission_percent" in PAYMENT_CONFIG["fees"]
        assert "orange_gateway_fee_percent" in PAYMENT_CONFIG["fees"]
        assert "mtn_gateway_fee_percent" in PAYMENT_CONFIG["fees"]
        assert "moov_gateway_fee_percent" in PAYMENT_CONFIG["fees"]
    
    def test_timeout_configured(self):
        """Test timeout is configured."""
        assert "timeout_minutes" in PAYMENT_CONFIG
        assert PAYMENT_CONFIG["timeout_minutes"] > 0
    
    def test_simulation_settings(self):
        """Test simulation settings exist."""
        assert "simulation" in PAYMENT_CONFIG
        assert "auto_success_pattern" in PAYMENT_CONFIG["simulation"]
        assert "auto_failure_pattern" in PAYMENT_CONFIG["simulation"]


class TestProviderConfig:
    """Test provider configuration retrieval."""
    
    def test_get_orange_config(self):
        """Test getting Orange Money config."""
        config = get_provider_config("orange_money")
        assert config is not None
        assert "sandbox_url" in config
        assert "production_url" in config
    
    def test_get_mtn_config(self):
        """Test getting MTN Money config."""
        config = get_provider_config("mtn_money")
        assert config is not None
        assert "sandbox_url" in config
        assert "production_url" in config
    
    def test_get_moov_config(self):
        """Test getting Moov Money config."""
        config = get_provider_config("moov_money")
        assert config is not None
        assert "sandbox_url" in config
        assert "production_url" in config
    
    def test_get_invalid_provider_config(self):
        """Test getting config for invalid provider."""
        config = get_provider_config("invalid_provider")
        assert config == {}


class TestProviderURL:
    """Test provider URL retrieval."""
    
    def test_get_provider_url_orange(self):
        """Test getting Orange Money URL."""
        url = get_provider_url("orange_money")
        assert url is not None
        assert len(url) > 0
    
    def test_get_provider_url_mtn(self):
        """Test getting MTN Money URL."""
        url = get_provider_url("mtn_money")
        assert url is not None
        assert len(url) > 0
    
    def test_get_provider_url_moov(self):
        """Test getting Moov Money URL."""
        url = get_provider_url("moov_money")
        assert url is not None
        assert len(url) > 0


class TestFeeCalculation:
    """Test fee calculation."""
    
    def test_calculate_fees_orange(self):
        """Test fee calculation for Orange Money."""
        amount = 100000  # 100,000 XOF
        fees = calculate_fees(amount, "orange_money")
        
        assert "gross_amount" in fees
        assert "platform_fee" in fees
        assert "payment_gateway_fee" in fees
        assert "merchant_payout" in fees
        
        assert fees["gross_amount"] == amount
        assert fees["platform_fee"] > 0
        assert fees["payment_gateway_fee"] > 0
        assert fees["merchant_payout"] > 0
        
        # Verify total adds up
        total = fees["platform_fee"] + fees["payment_gateway_fee"] + fees["merchant_payout"]
        assert abs(total - amount) < 1  # Allow for rounding
    
    def test_calculate_fees_mtn(self):
        """Test fee calculation for MTN Money."""
        amount = 50000  # 50,000 XOF
        fees = calculate_fees(amount, "mtn_money")
        
        assert fees["gross_amount"] == amount
        assert fees["platform_fee"] > 0
        assert fees["payment_gateway_fee"] > 0
        assert fees["merchant_payout"] > 0
    
    def test_calculate_fees_moov(self):
        """Test fee calculation for Moov Money."""
        amount = 75000  # 75,000 XOF
        fees = calculate_fees(amount, "moov_money")
        
        assert fees["gross_amount"] == amount
        assert fees["platform_fee"] > 0
        assert fees["payment_gateway_fee"] > 0
        assert fees["merchant_payout"] > 0
    
    def test_fee_calculation_small_amount(self):
        """Test fee calculation for small amount."""
        amount = 1000  # 1,000 XOF
        fees = calculate_fees(amount, "orange_money")
        
        assert fees["gross_amount"] == amount
        assert fees["merchant_payout"] < amount
    
    def test_fee_calculation_large_amount(self):
        """Test fee calculation for large amount."""
        amount = 1000000  # 1,000,000 XOF
        fees = calculate_fees(amount, "orange_money")
        
        assert fees["gross_amount"] == amount
        assert fees["platform_fee"] > 20000  # 2.5% of 1M is 25K
        assert fees["merchant_payout"] < amount
