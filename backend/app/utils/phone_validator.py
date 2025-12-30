"""
Phone number validation and provider detection for Côte d'Ivoire mobile money.

Ivorian phone numbers format: +225 XX XX XX XX XX (12 digits total)
"""

import re
from typing import Tuple, Optional


def validate_ivorian_phone(phone_number: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate and clean Ivorian phone number.
    
    Args:
        phone_number: Phone number to validate
        
    Returns:
        Tuple of (is_valid, cleaned_number, error_message)
    """
    # Remove all spaces, hyphens, and parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone_number)
    
    # Check if it starts with +225 or 225
    if cleaned.startswith('+225'):
        cleaned = cleaned[1:]  # Remove the +
    elif not cleaned.startswith('225'):
        return False, None, "Phone number must start with +225 or 225"
    
    # Should now be 225XXXXXXXXXX (13 digits total: 225 + 10 digit number)
    if len(cleaned) != 13:
        return False, None, f"Invalid phone number length. Expected 13 digits (225 + 10), got {len(cleaned)}"
    
    # Check if all characters are digits
    if not cleaned.isdigit():
        return False, None, "Phone number must contain only digits"
    
    # Extract the prefix (first 5 digits after 225)
    prefix = cleaned[3:7]  # Get XXXX from 225XXXX
    
    # Validate prefix is within Ivorian mobile ranges
    valid_prefixes = [
        # Orange Money prefixes
        '0707', '0505', '0104', '0105', '0106', '0107', '0108', '0109',
        '0140', '0141', '0142', '0143', '0144', '0145', '0146', '0147', '0148', '0149',
        '0150', '0151', '0152', '0153', '0154', '0155', '0156', '0157', '0158', '0159',
        # MTN prefixes
        '0504', '0544', '0545', '0546', '0554', '0555', '0556', '0557',
        '0640', '0641', '0642', '0643', '0644', '0645', '0646', '0647', '0648', '0649',
        '0650', '0651', '0652', '0653', '0654', '0655', '0656', '0657', '0658', '0659',
        # Moov Money prefixes
        '0100', '0101', '0102', '0103',
        '0201', '0202', '0203', '0204', '0205',
        '0301', '0302', '0303', '0304', '0305'
    ]
    
    # For validation, we accept any 01-09 prefix as they can vary
    first_two = cleaned[3:5]
    if not first_two.startswith('0') or not first_two[1].isdigit():
        return False, None, "Invalid Ivorian mobile number prefix"
    
    # Return with + prefix
    return True, '+' + cleaned, None


def detect_provider(phone_number: str) -> Optional[str]:
    """
    Detect mobile money provider from Ivorian phone number.
    
    Phone number prefixes in Côte d'Ivoire:
    - Orange: +225 07XX, +225 05XX (some), +225 01XX (some), +225 014X, +225 015X
    - MTN: +225 04XX, +225 05XX (some), +225 06XX, +225 054X, +225 055X, +225 064X, +225 065X
    - Moov: +225 01XX, +225 02XX, +225 03XX
    
    Args:
        phone_number: Valid Ivorian phone number (with or without +)
        
    Returns:
        Provider name: "orange_money", "mtn_money", "moov_money" or None
    """
    # Clean and validate
    is_valid, cleaned, error = validate_ivorian_phone(phone_number)
    if not is_valid or not cleaned:
        return None
    
    # Remove + and country code to get 10-digit number
    number = cleaned[4:]  # Remove +225
    
    # Get first 4 digits for prefix matching
    prefix_4 = number[:4]
    prefix_2 = number[:2]
    
    # Orange Money detection
    orange_prefixes = ['0707', '0505', '0104', '0105', '0106', '0107', '0108', '0109',
                       '0140', '0141', '0142', '0143', '0144', '0145', '0146', '0147', '0148', '0149',
                       '0150', '0151', '0152', '0153', '0154', '0155', '0156', '0157', '0158', '0159']
    if prefix_4 in orange_prefixes or prefix_2 == '07':
        return "orange_money"
    
    # MTN Mobile Money detection
    mtn_prefixes = ['0504', '0544', '0545', '0546', '0554', '0555', '0556', '0557',
                    '0640', '0641', '0642', '0643', '0644', '0645', '0646', '0647', '0648', '0649',
                    '0650', '0651', '0652', '0653', '0654', '0655', '0656', '0657', '0658', '0659']
    if prefix_4 in mtn_prefixes or prefix_2 in ['04', '05', '06']:
        # Check if it's not Orange 05XX
        if prefix_2 == '05' and prefix_4 not in orange_prefixes:
            return "mtn_money"
        if prefix_2 in ['04', '06']:
            return "mtn_money"
    
    # Moov Money detection
    moov_prefixes = ['0100', '0101', '0102', '0103',
                     '0201', '0202', '0203', '0204', '0205',
                     '0301', '0302', '0303', '0304', '0305']
    if prefix_4 in moov_prefixes or prefix_2 in ['01', '02', '03']:
        # Make sure it's not Orange 01XX
        if prefix_2 == '01' and prefix_4 not in orange_prefixes:
            return "moov_money"
        if prefix_2 in ['02', '03']:
            return "moov_money"
    
    # Default to None if cannot determine
    return None


def format_phone_display(phone_number: str) -> str:
    """
    Format phone number for display.
    
    Args:
        phone_number: Phone number to format
        
    Returns:
        Formatted phone number (e.g., "+225 07 12 34 56 78")
    """
    is_valid, cleaned, _ = validate_ivorian_phone(phone_number)
    if not is_valid or not cleaned:
        return phone_number
    
    # Remove + for formatting
    number = cleaned[1:]  # Remove +
    
    # Format as +225 XX XX XX XX XX
    return f"+{number[:3]} {number[3:5]} {number[5:7]} {number[7:9]} {number[9:11]} {number[11:13]}"


def get_ussd_code(provider: str) -> str:
    """
    Get USSD code for payment confirmation for each provider.
    
    Args:
        provider: Provider name
        
    Returns:
        USSD code string
    """
    ussd_codes = {
        "orange_money": "*144#",
        "mtn_money": "*133#",
        "moov_money": "*155#"
    }
    return ussd_codes.get(provider, "*144#")
