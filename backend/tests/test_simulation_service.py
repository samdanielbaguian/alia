"""
Tests for SimulationService provider handling.
"""

import pytest
from app.services.payment_providers.simulation_service import SimulationService


class TestSimulationServiceProviderHandling:
    """Test that SimulationService properly handles different providers."""
    
    @pytest.mark.asyncio
    async def test_orange_money_provider(self):
        """Test that Orange Money provider returns correct USSD code."""
        result = await SimulationService.initiate_payment(
            amount=1000.0,
            phone_number="+2250707123456",
            order_id="test_order_1",
            payment_id="test_payment_1",
            provider="orange_money"
        )
        
        assert result["success"] is True
        assert result["provider"] == "orange_money"
        assert result["ussd_code"] == "*144#"
        assert "*144#" in result["message"]
    
    @pytest.mark.asyncio
    async def test_mtn_money_provider(self):
        """Test that MTN Money provider returns correct USSD code."""
        result = await SimulationService.initiate_payment(
            amount=1000.0,
            phone_number="+2250504123456",
            order_id="test_order_2",
            payment_id="test_payment_2",
            provider="mtn_money"
        )
        
        assert result["success"] is True
        assert result["provider"] == "mtn_money"
        assert result["ussd_code"] == "*133#"
        assert "*133#" in result["message"]
    
    @pytest.mark.asyncio
    async def test_moov_money_provider(self):
        """Test that Moov Money provider returns correct USSD code."""
        result = await SimulationService.initiate_payment(
            amount=1000.0,
            phone_number="+2250101123456",
            order_id="test_order_3",
            payment_id="test_payment_3",
            provider="moov_money"
        )
        
        assert result["success"] is True
        assert result["provider"] == "moov_money"
        assert result["ussd_code"] == "*155#"
        assert "*155#" in result["message"]
    
    @pytest.mark.asyncio
    async def test_default_provider(self):
        """Test that default provider (Orange Money) is used when not specified."""
        result = await SimulationService.initiate_payment(
            amount=1000.0,
            phone_number="+2250707123456",
            order_id="test_order_4",
            payment_id="test_payment_4"
            # No provider specified
        )
        
        assert result["success"] is True
        assert result["provider"] == "orange_money"
        assert result["ussd_code"] == "*144#"
    
    @pytest.mark.asyncio
    async def test_auto_success_includes_provider(self):
        """Test that auto-success message includes provider name."""
        result = await SimulationService.initiate_payment(
            amount=1000.0,
            phone_number="+2250504120000",  # Ends in 0000 for auto-success
            order_id="test_order_5",
            payment_id="test_payment_5",
            provider="mtn_money"
        )
        
        assert result["success"] is True
        assert result["auto_success"] is True
        assert result["provider"] == "mtn_money"
        assert "MTN_MONEY" in result["message"]
