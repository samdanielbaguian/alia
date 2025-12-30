"""
Tests for phone number validation and provider detection.
"""

import pytest
from app.utils.phone_validator import (
    validate_ivorian_phone,
    detect_provider,
    format_phone_display,
    get_ussd_code
)


class TestPhoneValidation:
    """Test phone number validation."""
    
    def test_valid_phone_with_plus(self):
        """Test valid phone number with + prefix."""
        is_valid, cleaned, error = validate_ivorian_phone("+2250707123456")
        assert is_valid is True
        assert cleaned == "+2250707123456"
        assert error is None
    
    def test_valid_phone_without_plus(self):
        """Test valid phone number without + prefix."""
        is_valid, cleaned, error = validate_ivorian_phone("2250707123456")
        assert is_valid is True
        assert cleaned == "+2250707123456"
        assert error is None
    
    def test_valid_phone_with_spaces(self):
        """Test valid phone number with spaces."""
        is_valid, cleaned, error = validate_ivorian_phone("+225 07 07 12 34 56")
        assert is_valid is True
        assert cleaned == "+2250707123456"
        assert error is None
    
    def test_invalid_phone_wrong_country_code(self):
        """Test phone number with wrong country code."""
        is_valid, cleaned, error = validate_ivorian_phone("+2330707123456")
        assert is_valid is False
        assert error is not None
    
    def test_invalid_phone_too_short(self):
        """Test phone number that's too short."""
        is_valid, cleaned, error = validate_ivorian_phone("+225070712")
        assert is_valid is False
        assert error is not None
    
    def test_invalid_phone_too_long(self):
        """Test phone number that's too long."""
        is_valid, cleaned, error = validate_ivorian_phone("+22507071234567890")
        assert is_valid is False
        assert error is not None
    
    def test_invalid_phone_non_numeric(self):
        """Test phone number with non-numeric characters."""
        is_valid, cleaned, error = validate_ivorian_phone("+225070712abcd")
        assert is_valid is False
        assert error is not None


class TestProviderDetection:
    """Test mobile money provider detection."""
    
    def test_detect_orange_money(self):
        """Test Orange Money number detection."""
        # Orange prefix 07
        provider = detect_provider("+2250707123456")
        assert provider == "orange_money"
        
        # Orange prefix 0505
        provider = detect_provider("+2250505123456")
        assert provider == "orange_money"
    
    def test_detect_mtn_money(self):
        """Test MTN Money number detection."""
        # MTN prefix 05 (not Orange)
        provider = detect_provider("+2250544123456")
        assert provider == "mtn_money"
        
        # MTN prefix 06
        provider = detect_provider("+2250640123456")
        assert provider == "mtn_money"
    
    def test_detect_moov_money(self):
        """Test Moov Money number detection."""
        # Moov prefix 01
        provider = detect_provider("+2250100123456")
        assert provider == "moov_money"
        
        # Moov prefix 02
        provider = detect_provider("+2250201123456")
        assert provider == "moov_money"
        
        # Moov prefix 03
        provider = detect_provider("+2250301123456")
        assert provider == "moov_money"
    
    def test_detect_provider_invalid_phone(self):
        """Test provider detection with invalid phone."""
        provider = detect_provider("+233123456789")
        assert provider is None


class TestPhoneFormatting:
    """Test phone number formatting."""
    
    def test_format_phone_display(self):
        """Test phone number display formatting."""
        formatted = format_phone_display("+2250707123456")
        assert formatted == "+225 07 07 12 34 56"
    
    def test_format_invalid_phone(self):
        """Test formatting invalid phone returns original."""
        original = "+233123"
        formatted = format_phone_display(original)
        assert formatted == original


class TestUSSDCodes:
    """Test USSD code retrieval."""
    
    def test_orange_ussd_code(self):
        """Test Orange Money USSD code."""
        code = get_ussd_code("orange_money")
        assert code == "*144#"
    
    def test_mtn_ussd_code(self):
        """Test MTN Money USSD code."""
        code = get_ussd_code("mtn_money")
        assert code == "*133#"
    
    def test_moov_ussd_code(self):
        """Test Moov Money USSD code."""
        code = get_ussd_code("moov_money")
        assert code == "*155#"
    
    def test_default_ussd_code(self):
        """Test default USSD code for unknown provider."""
        code = get_ussd_code("unknown_provider")
        assert code == "*144#"  # Default to Orange
