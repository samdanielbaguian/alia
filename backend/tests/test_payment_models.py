"""
Tests for payment models.
"""

import pytest
from datetime import datetime, timedelta
from app.models.payment import (
    Payment,
    PaymentStatus,
    PaymentProvider,
    Refund,
    generate_payment_id
)


class TestPaymentModel:
    """Test Payment model."""
    
    def test_create_payment(self):
        """Test creating a payment instance."""
        payment = Payment(
            order_id="order123",
            user_id="user123",
            merchant_id="merchant123",
            amount=50000,
            currency="XOF",
            provider=PaymentProvider.ORANGE_MONEY,
            phone_number="+2250707123456",
            gross_amount=50000,
            platform_fee=1250,
            payment_gateway_fee=750,
            merchant_payout=48000
        )
        
        assert payment.order_id == "order123"
        assert payment.user_id == "user123"
        assert payment.merchant_id == "merchant123"
        assert payment.amount == 50000
        assert payment.currency == "XOF"
        assert payment.provider == PaymentProvider.ORANGE_MONEY
        assert payment.status == PaymentStatus.PENDING
        assert payment.phone_number == "+2250707123456"
    
    def test_payment_has_payment_id(self):
        """Test payment automatically gets a payment_id."""
        payment = Payment(
            order_id="order123",
            user_id="user123",
            merchant_id="merchant123",
            amount=50000,
            provider=PaymentProvider.ORANGE_MONEY,
            phone_number="+2250707123456",
            gross_amount=50000
        )
        
        assert payment.payment_id is not None
        assert payment.payment_id.startswith("pay_")
    
    def test_payment_has_timestamps(self):
        """Test payment has required timestamps."""
        payment = Payment(
            order_id="order123",
            user_id="user123",
            merchant_id="merchant123",
            amount=50000,
            provider=PaymentProvider.ORANGE_MONEY,
            phone_number="+2250707123456",
            gross_amount=50000
        )
        
        assert payment.initiated_at is not None
        assert payment.created_at is not None
        assert payment.updated_at is not None
        assert payment.expires_at is not None
    
    def test_payment_expiration(self):
        """Test payment expiration is set correctly."""
        payment = Payment(
            order_id="order123",
            user_id="user123",
            merchant_id="merchant123",
            amount=50000,
            provider=PaymentProvider.ORANGE_MONEY,
            phone_number="+2250707123456",
            gross_amount=50000
        )
        
        # Should expire approximately 10 minutes after initiation
        time_diff = payment.expires_at - payment.initiated_at
        assert time_diff.total_seconds() >= 595  # 9:55
        assert time_diff.total_seconds() <= 605  # 10:05
    
    def test_payment_default_status(self):
        """Test payment default status is PENDING."""
        payment = Payment(
            order_id="order123",
            user_id="user123",
            merchant_id="merchant123",
            amount=50000,
            provider=PaymentProvider.ORANGE_MONEY,
            phone_number="+2250707123456",
            gross_amount=50000
        )
        
        assert payment.status == PaymentStatus.PENDING
    
    def test_payment_metadata(self):
        """Test payment can store metadata."""
        payment = Payment(
            order_id="order123",
            user_id="user123",
            merchant_id="merchant123",
            amount=50000,
            provider=PaymentProvider.ORANGE_MONEY,
            phone_number="+2250707123456",
            gross_amount=50000,
            metadata={"mode": "SIMULATION", "test": True}
        )
        
        assert "mode" in payment.metadata
        assert payment.metadata["mode"] == "SIMULATION"
        assert payment.metadata["test"] is True


class TestPaymentProvider:
    """Test PaymentProvider enum."""
    
    def test_orange_money_provider(self):
        """Test Orange Money provider."""
        assert PaymentProvider.ORANGE_MONEY == "orange_money"
    
    def test_mtn_money_provider(self):
        """Test MTN Money provider."""
        assert PaymentProvider.MTN_MONEY == "mtn_money"
    
    def test_moov_money_provider(self):
        """Test Moov Money provider."""
        assert PaymentProvider.MOOV_MONEY == "moov_money"


class TestPaymentStatus:
    """Test PaymentStatus enum."""
    
    def test_all_statuses(self):
        """Test all payment statuses."""
        assert PaymentStatus.PENDING == "pending"
        assert PaymentStatus.PROCESSING == "processing"
        assert PaymentStatus.COMPLETED == "completed"
        assert PaymentStatus.FAILED == "failed"
        assert PaymentStatus.CANCELLED == "cancelled"
        assert PaymentStatus.REFUNDED == "refunded"
        assert PaymentStatus.EXPIRED == "expired"


class TestRefundModel:
    """Test Refund model."""
    
    def test_create_refund(self):
        """Test creating a refund instance."""
        refund = Refund(
            payment_id="pay_abc123",
            order_id="order123",
            user_id="user123",
            merchant_id="merchant123",
            amount=50000,
            currency="XOF",
            reason="Product out of stock"
        )
        
        assert refund.payment_id == "pay_abc123"
        assert refund.order_id == "order123"
        assert refund.amount == 50000
        assert refund.reason == "Product out of stock"
        assert refund.status == PaymentStatus.PROCESSING
    
    def test_refund_has_refund_id(self):
        """Test refund automatically gets a refund_id."""
        refund = Refund(
            payment_id="pay_abc123",
            order_id="order123",
            user_id="user123",
            merchant_id="merchant123",
            amount=50000,
            reason="Test"
        )
        
        assert refund.refund_id is not None
        assert refund.refund_id.startswith("ref_")
    
    def test_refund_has_timestamps(self):
        """Test refund has required timestamps."""
        refund = Refund(
            payment_id="pay_abc123",
            order_id="order123",
            user_id="user123",
            merchant_id="merchant123",
            amount=50000,
            reason="Test"
        )
        
        assert refund.requested_at is not None
        assert refund.created_at is not None
        assert refund.updated_at is not None


class TestPaymentIDGeneration:
    """Test payment ID generation."""
    
    def test_generate_payment_id(self):
        """Test payment ID generation."""
        payment_id = generate_payment_id()
        
        assert payment_id is not None
        assert payment_id.startswith("pay_")
        assert len(payment_id) > 4  # Should be longer than just "pay_"
    
    def test_payment_ids_are_unique(self):
        """Test generated payment IDs are unique."""
        id1 = generate_payment_id()
        id2 = generate_payment_id()
        
        assert id1 != id2
