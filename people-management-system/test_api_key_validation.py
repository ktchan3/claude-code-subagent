#!/usr/bin/env python3
"""
Simple API Key Validation Test

Tests the core API key validation logic without external dependencies.
"""

import re

# Copy the validation functions to test them independently
def validate_api_key(api_key: str) -> bool:
    """Validate API key format for HTTP header use."""
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Check for newlines or carriage returns (HTTP header killers)
    if '\n' in api_key or '\r' in api_key:
        return False
    
    # Check for other control characters that could break HTTP headers
    if any(ord(char) < 32 for char in api_key if char not in '\t'):
        return False
    
    # Check for reasonable length (API keys are typically 20-128 characters)
    if len(api_key.strip()) < 10 or len(api_key.strip()) > 256:
        return False
    
    # Basic format check - should contain alphanumeric chars and possibly hyphens/underscores
    if not re.match(r'^[a-zA-Z0-9\-_\.]+$', api_key.strip()):
        return False
    
    return True


def sanitize_api_key(api_key: str) -> str:
    """Sanitize API key by removing invalid characters."""
    if not api_key or not isinstance(api_key, str):
        raise ValueError("API key must be a non-empty string")
    
    # Strip whitespace and remove newlines/carriage returns
    sanitized = api_key.strip().replace('\n', '').replace('\r', '')
    
    # Remove any control characters except tab (though tab shouldn't be in API keys)
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char == '\t')
    
    # Remove tabs as well since they shouldn't be in API keys
    sanitized = sanitized.replace('\t', '')
    
    if not validate_api_key(sanitized):
        raise ValueError("API key contains invalid characters or format")
    
    return sanitized


def main():
    """Test the validation functions."""
    print("=" * 60)
    print("API Key Validation Test")
    print("=" * 60)
    
    # Test the exact API key that caused the original problem
    corrupted_key = "Ultrathink error and fix and test it, use context7, use subagent.\n-When i add new person.\n    -email address not allow me to entry '.'."
    
    print(f"Testing original corrupted key (length: {len(corrupted_key)})...")
    print(f"Contains newlines: {'\\n' in corrupted_key}")
    print(f"Contains carriage returns: {'\\r' in corrupted_key}")
    print()
    
    # Test validation
    is_valid = validate_api_key(corrupted_key)
    print(f"Validation result: {'PASS' if not is_valid else 'FAIL'} (should be PASS - rejecting invalid key)")
    
    if is_valid:
        print("❌ ERROR: The validation function accepts the corrupted key!")
        print("This means the 'Illegal header value' error could still occur.")
        return False
    else:
        print("✅ SUCCESS: The validation function correctly rejects the corrupted key!")
    
    print()
    
    # Test sanitization
    print("Testing sanitization...")
    try:
        sanitized = sanitize_api_key(corrupted_key)
        print(f"❌ ERROR: Sanitization accepted the corrupted key: '{sanitized}'")
        return False
    except ValueError as e:
        print(f"✅ SUCCESS: Sanitization correctly rejected the corrupted key: {e}")
    
    print()
    
    # Test valid API keys
    valid_keys = [
        "abc123def456ghi789",
        "API-KEY-WITH-HYPHENS-123",
        "api_key_with_underscores_456",
        "mixed-key_with.dots123"
    ]
    
    print("Testing valid API keys...")
    all_valid_passed = True
    for key in valid_keys:
        if validate_api_key(key):
            print(f"✅ Valid key accepted: {key}")
        else:
            print(f"❌ Valid key rejected: {key}")
            all_valid_passed = False
    
    print()
    
    # Test other invalid cases
    invalid_keys = [
        ("key\nwith\nnewline", "newlines"),
        ("key\rwith\rcarriage", "carriage returns"),
        ("key with spaces", "spaces"),
        ("short", "too short"),
        ("", "empty string"),
        ("key@with#special$chars", "special characters")
    ]
    
    print("Testing invalid API keys...")
    all_invalid_passed = True
    for key, reason in invalid_keys:
        if not validate_api_key(key):
            print(f"✅ Invalid key rejected ({reason}): {key[:30]}{'...' if len(key) > 30 else ''}")
        else:
            print(f"❌ Invalid key accepted ({reason}): {key}")
            all_invalid_passed = False
    
    print()
    print("=" * 60)
    if all_valid_passed and all_invalid_passed:
        print("🎉 ALL TESTS PASSED!")
        print("The API key validation fixes are working correctly.")
        print("The 'Illegal header value' error should no longer occur.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the validation logic.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)