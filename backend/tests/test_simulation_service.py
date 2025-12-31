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


class TestSimulationServiceMagicNumbers:
    """Test magic number automation for payment simulation."""
    
    @pytest.mark.asyncio
    async def test_magic_number_auto_success(self):
        """Test that magic number +2250777123456 triggers auto-success."""
        result = await SimulationService.initiate_payment(
            amount=50000.0,
            phone_number="+2250777123456",
            order_id="test_order_magic_success",
            payment_id="test_payment_magic_success",
            provider="orange_money"
        )
        
        assert result["success"] is True
        assert result["status"] == "pending"
        assert result["auto_success"] is True
        assert "auto-complete" in result["message"].lower()
        assert result["provider"] == "orange_money"
        assert result["simulation_mode"] is True
    
    @pytest.mark.asyncio
    async def test_magic_number_auto_failure(self):
        """Test that magic number +2250777123458 triggers auto-failure."""
        result = await SimulationService.initiate_payment(
            amount=50000.0,
            phone_number="+2250777123458",
            order_id="test_order_magic_fail",
            payment_id="test_payment_magic_fail",
            provider="mtn_money"
        )
        
        assert result["success"] is True
        assert result["status"] == "pending"
        assert result.get("auto_failure") is True
        assert "auto-fail" in result["message"].lower()
        assert result["provider"] == "mtn_money"
        assert result["simulation_mode"] is True
    
    @pytest.mark.asyncio
    async def test_magic_number_pending(self):
        """Test that magic number +2250777123457 stays pending."""
        result = await SimulationService.initiate_payment(
            amount=50000.0,
            phone_number="+2250777123457",
            order_id="test_order_magic_pending",
            payment_id="test_payment_magic_pending",
            provider="moov_money"
        )
        
        assert result["success"] is True
        assert result["status"] == "pending"
        assert result.get("auto_success") is False
        # auto_failure field is not present when False, so check it's not True
        assert result.get("auto_failure") is not True
        assert "veuillez composer" in result["message"].lower()
        assert result["provider"] == "moov_money"
    
    @pytest.mark.asyncio
    async def test_non_magic_number_normal_behavior(self):
        """Test that non-magic numbers behave normally."""
        # Use a number that doesn't end in 0000 or 9999
        result = await SimulationService.initiate_payment(
            amount=50000.0,
            phone_number="+2250707888888",
            order_id="test_order_normal",
            payment_id="test_payment_normal",
            provider="orange_money"
        )
        
        assert result["success"] is True
        assert result["status"] == "pending"
        # Should not auto-success (doesn't match magic number or 0000 pattern)
        assert result.get("auto_success") is False
        # Should not auto-fail (doesn't match magic number or 9999 pattern)
        assert result.get("auto_failure") is not True
        assert "veuillez composer" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_old_pattern_still_works_0000(self):
        """Test that old pattern (ending in 0000) still works for auto-success."""
        result = await SimulationService.initiate_payment(
            amount=1000.0,
            phone_number="+2250707000000",  # Ends in 0000
            order_id="test_order_old_success",
            payment_id="test_payment_old_success",
            provider="orange_money"
        )
        
        assert result["success"] is True
        assert result["auto_success"] is True
        assert "auto-complete" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_old_pattern_still_works_9999(self):
        """Test that old pattern (ending in 9999) still works for auto-failure."""
        result = await SimulationService.initiate_payment(
            amount=1000.0,
            phone_number="+2250707999999",  # Ends in 9999
            order_id="test_order_old_fail",
            payment_id="test_payment_old_fail",
            provider="orange_money"
        )
        
        assert result["success"] is True
        assert result["status"] == "pending"
        assert result.get("auto_failure") is True
        assert "auto-fail" in result["message"].lower()

