"""
Integration test for payment provider handling.

This test verifies that the payment service correctly passes the provider
parameter to the simulation service and returns the correct USSD code.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.payment_service import PaymentService
from app.models.payment import PaymentStatus


class TestPaymentServiceProviderIntegration:
    """Test payment service provider integration with simulation service."""
    
    @pytest.mark.asyncio
    async def test_payment_service_passes_provider_to_simulation(self):
        """
        Test that PaymentService correctly passes provider to SimulationService.
        """
        payment_service = PaymentService()
        
        # Mock the database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        mock_db.payments.find_one = AsyncMock(return_value=None)
        mock_db.payments.insert_one = AsyncMock(return_value=MagicMock())
        mock_db.payments.update_one = AsyncMock(return_value=MagicMock())
        
        # Mock the simulation service initiate_payment method
        with patch.object(
            payment_service.simulation_service, 
            'initiate_payment',
            new_callable=AsyncMock
        ) as mock_initiate:
            mock_initiate.return_value = {
                "success": True,
                "transaction_id": "SIM_TEST123",
                "status": "pending",
                "message": "Test message",
                "ussd_code": "*133#",
                "provider": "mtn_money",
                "simulation_mode": True,
                "auto_success": False
            }
            
            # Mock PAYMENT_MODE to be SIMULATION
            with patch('app.services.payment_service.PAYMENT_MODE', 'SIMULATION'):
                # Call initiate_payment with MTN number
                result = await payment_service.initiate_payment(
                    order_id="test_order_123",
                    phone_number="+2250504123456",  # MTN prefix
                    user_id="test_user",
                    merchant_id="test_merchant",
                    amount=1000.0,
                    db=mock_db
                )
            
            # Verify simulation service was called with provider
            mock_initiate.assert_called_once()
            call_args = mock_initiate.call_args[1]
            assert call_args['provider'] == 'mtn_money'
            assert call_args['amount'] == 1000.0
            assert call_args['phone_number'] == '+2250504123456'
            
            # Verify response includes correct USSD code
            assert result['success'] is True
            assert result['provider'] == 'mtn_money'
            assert result['ussd_code'] == '*133#'
    
    @pytest.mark.asyncio
    async def test_orange_money_provider_flow(self):
        """Test Orange Money provider flow end-to-end."""
        payment_service = PaymentService()
        
        # Mock database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        mock_db.payments.find_one = AsyncMock(return_value=None)
        mock_db.payments.insert_one = AsyncMock(return_value=MagicMock())
        mock_db.payments.update_one = AsyncMock(return_value=MagicMock())
        
        with patch('app.services.payment_service.PAYMENT_MODE', 'SIMULATION'):
            result = await payment_service.initiate_payment(
                order_id="test_order_orange",
                phone_number="+2250707123456",  # Orange prefix
                user_id="test_user",
                merchant_id="test_merchant",
                amount=5000.0,
                db=mock_db
            )
        
        assert result['success'] is True
        assert result['provider'] == 'orange_money'
        assert result['ussd_code'] == '*144#'
        assert '*144#' in result['message']
    
    @pytest.mark.asyncio
    async def test_moov_money_provider_flow(self):
        """Test Moov Money provider flow end-to-end."""
        payment_service = PaymentService()
        
        # Mock database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        mock_db.payments.find_one = AsyncMock(return_value=None)
        mock_db.payments.insert_one = AsyncMock(return_value=MagicMock())
        mock_db.payments.update_one = AsyncMock(return_value=MagicMock())
        
        with patch('app.services.payment_service.PAYMENT_MODE', 'SIMULATION'):
            result = await payment_service.initiate_payment(
                order_id="test_order_moov",
                phone_number="+2250101123456",  # Moov prefix
                user_id="test_user",
                merchant_id="test_merchant",
                amount=3000.0,
                db=mock_db
            )
        
        assert result['success'] is True
        assert result['provider'] == 'moov_money'
        assert result['ussd_code'] == '*155#'
        assert '*155#' in result['message']
