"""
Tests for order service business logic.
"""
import pytest
from app.services.order_service import OrderService


class TestStatusTransitions:
    """Test status transition validation."""
    
    def test_valid_pending_to_confirmed(self):
        """Test valid transition from pending to confirmed."""
        is_valid, error = OrderService.validate_status_transition("pending", "confirmed")
        assert is_valid is True
        assert error is None
    
    def test_valid_pending_to_cancelled(self):
        """Test valid transition from pending to cancelled."""
        is_valid, error = OrderService.validate_status_transition("pending", "cancelled")
        assert is_valid is True
        assert error is None
    
    def test_valid_confirmed_to_shipped(self):
        """Test valid transition from confirmed to shipped."""
        is_valid, error = OrderService.validate_status_transition("confirmed", "shipped")
        assert is_valid is True
        assert error is None
    
    def test_valid_confirmed_to_cancelled(self):
        """Test valid transition from confirmed to cancelled."""
        is_valid, error = OrderService.validate_status_transition("confirmed", "cancelled")
        assert is_valid is True
        assert error is None
    
    def test_valid_shipped_to_delivered(self):
        """Test valid transition from shipped to delivered."""
        is_valid, error = OrderService.validate_status_transition("shipped", "delivered")
        assert is_valid is True
        assert error is None
    
    def test_invalid_pending_to_shipped(self):
        """Test invalid transition from pending to shipped (must go through confirmed)."""
        is_valid, error = OrderService.validate_status_transition("pending", "shipped")
        assert is_valid is False
        assert "Cannot transition" in error
    
    def test_invalid_pending_to_delivered(self):
        """Test invalid transition from pending to delivered."""
        is_valid, error = OrderService.validate_status_transition("pending", "delivered")
        assert is_valid is False
        assert "Cannot transition" in error
    
    def test_invalid_confirmed_to_delivered(self):
        """Test invalid transition from confirmed to delivered (must go through shipped)."""
        is_valid, error = OrderService.validate_status_transition("confirmed", "delivered")
        assert is_valid is False
        assert "Cannot transition" in error
    
    def test_invalid_shipped_to_cancelled(self):
        """Test invalid transition from shipped to cancelled."""
        is_valid, error = OrderService.validate_status_transition("shipped", "cancelled")
        assert is_valid is False
        assert "Cannot transition" in error
    
    def test_invalid_delivered_to_any(self):
        """Test that delivered is a final state."""
        is_valid, error = OrderService.validate_status_transition("delivered", "cancelled")
        assert is_valid is False
        assert "final state" in error
    
    def test_invalid_cancelled_to_any(self):
        """Test that cancelled is a final state."""
        is_valid, error = OrderService.validate_status_transition("cancelled", "confirmed")
        assert is_valid is False
        assert "final state" in error


class TestGetValidNextStatuses:
    """Test getting valid next statuses."""
    
    def test_buyer_pending_order(self):
        """Test valid next statuses for buyer with pending order."""
        statuses = OrderService.get_valid_next_statuses("pending", "buyer")
        assert statuses == ["cancelled"]
    
    def test_buyer_confirmed_order(self):
        """Test buyer cannot transition confirmed orders."""
        statuses = OrderService.get_valid_next_statuses("confirmed", "buyer")
        assert statuses == []
    
    def test_merchant_pending_order(self):
        """Test valid next statuses for merchant with pending order."""
        statuses = OrderService.get_valid_next_statuses("pending", "merchant")
        assert set(statuses) == {"confirmed", "cancelled"}
    
    def test_merchant_confirmed_order(self):
        """Test valid next statuses for merchant with confirmed order."""
        statuses = OrderService.get_valid_next_statuses("confirmed", "merchant")
        assert set(statuses) == {"shipped", "cancelled"}
    
    def test_merchant_shipped_order(self):
        """Test valid next statuses for merchant with shipped order."""
        statuses = OrderService.get_valid_next_statuses("shipped", "merchant")
        assert statuses == ["delivered"]
    
    def test_merchant_delivered_order(self):
        """Test no valid next statuses for delivered order."""
        statuses = OrderService.get_valid_next_statuses("delivered", "merchant")
        assert statuses == []
    
    def test_merchant_cancelled_order(self):
        """Test no valid next statuses for cancelled order."""
        statuses = OrderService.get_valid_next_statuses("cancelled", "merchant")
        assert statuses == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
