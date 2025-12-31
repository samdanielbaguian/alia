"""
Tests for refund functionality.

This test suite validates the refund service methods and ensures:
- Merchants can refund completed payments
- Non-merchants cannot refund payments
- Refund validations work correctly
- Refund records are created in database
- Payment and order status updates work correctly
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from app.services.payment_service import PaymentService
from app.models.refund import RefundStatus


class TestRefundService:
    """Test refund service functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_refund_simulation_mode(self):
        """Test successful refund in SIMULATION mode."""
        payment_service = PaymentService()
        
        # Mock database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        mock_db.orders = MagicMock()
        mock_db.refunds = MagicMock()
        
        # Mock payment data
        mock_payment = {
            "payment_id": "pay_test123",
            "order_id": "order_test123",
            "user_id": "user123",
            "merchant_id": "merchant123",
            "amount": 46000,
            "currency": "XOF",
            "provider": "orange_money",
            "status": "completed",
            "transaction_id": "OM_TRANS_123"
        }
        
        mock_db.payments.find_one = AsyncMock(return_value=mock_payment)
        mock_db.refunds.find_one = AsyncMock(return_value=None)  # No existing refund
        mock_db.refunds.insert_one = AsyncMock(return_value=MagicMock())
        mock_db.refunds.update_one = AsyncMock(return_value=MagicMock())
        mock_db.payments.update_one = AsyncMock(return_value=MagicMock())
        mock_db.orders.update_one = AsyncMock(return_value=MagicMock())
        
        # Mock PAYMENT_MODE to be SIMULATION
        with patch('app.services.payment_service.PAYMENT_MODE', 'SIMULATION'):
            result = await payment_service.refund_payment(
                payment_id="pay_test123",
                amount=46000,
                reason="Customer requested refund",
                note="Product was defective",
                merchant_id="merchant123",
                db=mock_db
            )
        
        # Verify result
        assert result["success"] is True
        assert result["message"] == "Refund processed successfully"
        assert "refund_id" in result
        assert result["refund_id"].startswith("ref_")
        assert result["payment_id"] == "pay_test123"
        assert result["amount"] == 46000
        assert result["status"] == "refunded"
        assert "refunded_at" in result
        
        # Verify database calls
        mock_db.refunds.insert_one.assert_called_once()
        mock_db.refunds.update_one.assert_called()
        mock_db.payments.update_one.assert_called_once()
        mock_db.orders.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_refund_unauthorized_user(self):
        """Test that non-merchants cannot refund payments."""
        payment_service = PaymentService()
        
        # Mock database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        
        # Mock payment data
        mock_payment = {
            "payment_id": "pay_test123",
            "merchant_id": "merchant123",
            "status": "completed"
        }
        
        mock_db.payments.find_one = AsyncMock(return_value=mock_payment)
        
        # Try to refund with different user
        result = await payment_service.refund_payment(
            payment_id="pay_test123",
            amount=46000,
            reason="Customer requested refund",
            note=None,
            merchant_id="different_merchant",
            db=mock_db
        )
        
        # Verify rejection
        assert result["success"] is False
        assert "Only the merchant can refund payments" in result["message"]
    
    @pytest.mark.asyncio
    async def test_refund_non_completed_payment(self):
        """Test that only completed payments can be refunded."""
        payment_service = PaymentService()
        
        # Mock database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        
        # Mock pending payment
        mock_payment = {
            "payment_id": "pay_test123",
            "merchant_id": "merchant123",
            "status": "pending",
            "amount": 46000
        }
        
        mock_db.payments.find_one = AsyncMock(return_value=mock_payment)
        
        result = await payment_service.refund_payment(
            payment_id="pay_test123",
            amount=46000,
            reason="Test refund",
            note=None,
            merchant_id="merchant123",
            db=mock_db
        )
        
        # Verify rejection
        assert result["success"] is False
        assert "Can only refund completed payments" in result["message"]
    
    @pytest.mark.asyncio
    async def test_refund_amount_exceeds_payment(self):
        """Test that refund amount cannot exceed payment amount."""
        payment_service = PaymentService()
        
        # Mock database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        
        # Mock payment
        mock_payment = {
            "payment_id": "pay_test123",
            "merchant_id": "merchant123",
            "status": "completed",
            "amount": 46000
        }
        
        mock_db.payments.find_one = AsyncMock(return_value=mock_payment)
        
        result = await payment_service.refund_payment(
            payment_id="pay_test123",
            amount=50000,  # More than payment amount
            reason="Test refund",
            note=None,
            merchant_id="merchant123",
            db=mock_db
        )
        
        # Verify rejection
        assert result["success"] is False
        assert "exceeds payment amount" in result["message"]
    
    @pytest.mark.asyncio
    async def test_refund_duplicate_prevention(self):
        """Test that duplicate refunds are prevented."""
        payment_service = PaymentService()
        
        # Mock database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        mock_db.refunds = MagicMock()
        
        # Mock payment
        mock_payment = {
            "payment_id": "pay_test123",
            "merchant_id": "merchant123",
            "status": "completed",
            "amount": 46000
        }
        
        # Mock existing refund
        mock_existing_refund = {
            "refund_id": "ref_existing123",
            "payment_id": "pay_test123",
            "status": "completed"
        }
        
        mock_db.payments.find_one = AsyncMock(return_value=mock_payment)
        mock_db.refunds.find_one = AsyncMock(return_value=mock_existing_refund)
        
        result = await payment_service.refund_payment(
            payment_id="pay_test123",
            amount=46000,
            reason="Test refund",
            note=None,
            merchant_id="merchant123",
            db=mock_db
        )
        
        # Verify rejection
        assert result["success"] is False
        assert "already exists" in result["message"]
        assert result["refund_id"] == "ref_existing123"
    
    @pytest.mark.asyncio
    async def test_refund_payment_not_found(self):
        """Test refund when payment doesn't exist."""
        payment_service = PaymentService()
        
        # Mock database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        
        mock_db.payments.find_one = AsyncMock(return_value=None)
        
        result = await payment_service.refund_payment(
            payment_id="nonexistent_payment",
            amount=46000,
            reason="Test refund",
            note=None,
            merchant_id="merchant123",
            db=mock_db
        )
        
        # Verify rejection
        assert result["success"] is False
        assert "Payment not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_refund_with_none_amount_defaults_to_full(self):
        """Test that None amount defaults to full refund."""
        payment_service = PaymentService()
        
        # Mock database
        mock_db = MagicMock()
        mock_db.payments = MagicMock()
        mock_db.orders = MagicMock()
        mock_db.refunds = MagicMock()
        
        # Mock payment data
        mock_payment = {
            "payment_id": "pay_test123",
            "order_id": "order_test123",
            "user_id": "user123",
            "merchant_id": "merchant123",
            "amount": 46000,
            "currency": "XOF",
            "provider": "orange_money",
            "status": "completed",
            "transaction_id": "OM_TRANS_123"
        }
        
        mock_db.payments.find_one = AsyncMock(return_value=mock_payment)
        mock_db.refunds.find_one = AsyncMock(return_value=None)
        mock_db.refunds.insert_one = AsyncMock(return_value=MagicMock())
        mock_db.refunds.update_one = AsyncMock(return_value=MagicMock())
        mock_db.payments.update_one = AsyncMock(return_value=MagicMock())
        mock_db.orders.update_one = AsyncMock(return_value=MagicMock())
        
        # Mock PAYMENT_MODE to be SIMULATION
        with patch('app.services.payment_service.PAYMENT_MODE', 'SIMULATION'):
            result = await payment_service.refund_payment(
                payment_id="pay_test123",
                amount=None,  # None should default to full amount
                reason="Full refund requested",
                note=None,
                merchant_id="merchant123",
                db=mock_db
            )
        
        # Verify result - should refund full amount
        assert result["success"] is True
        assert result["amount"] == 46000  # Full payment amount
