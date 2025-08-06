#!/usr/bin/env python3
"""
Test the exact error case from the original problem.
"""

import re

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


def main():
    """Test the exact corrupted API key that caused the original error."""
    
    # Recreate the exact key from the error message
    corrupted_key = "Ultrathink error and fix and test it, use context7, use subagent.\n-When i add new person.\n    -email address not allow me to entry '.'."
    
    print("Testing the exact corrupted API key that caused 'Illegal header value' error:")
    print("-" * 80)
    print(f"Key length: {len(corrupted_key)}")
    print(f"Key preview: {repr(corrupted_key[:100])}...")
    print(f"Contains newlines (\\n): {corrupted_key.count(chr(10))} occurrences")
    print(f"Contains spaces: {corrupted_key.count(' ')} occurrences")
    print(f"Contains special chars: {bool(set(corrupted_key) - set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.'))}")
    print()
    
    # Test our validation
    is_valid = validate_api_key(corrupted_key)
    
    if is_valid:
        print("❌ CRITICAL ERROR: Our validation accepts this corrupted key!")
        print("This means the 'Illegal header value' error could still occur.")
        print()
        print("The key should be rejected because it contains:")
        if '\n' in corrupted_key:
            print("  - Newline characters (\\n)")
        if ' ' in corrupted_key:
            print("  - Space characters")
        if ',' in corrupted_key:
            print("  - Comma characters")
        if '.' in corrupted_key and corrupted_key != corrupted_key.replace('.', ''):
            print("  - Multiple dots (some may be valid, but this pattern isn't)")
        
        return False
    else:
        print("✅ SUCCESS: Our validation correctly rejects this corrupted key!")
        print("The 'Illegal header value' error should no longer occur.")
        print()
        
        # Show why it was rejected
        print("Key rejected because it contains:")
        reasons = []
        if '\n' in corrupted_key:
            reasons.append(f"  - {corrupted_key.count(chr(10))} newline character(s)")
        if '\r' in corrupted_key:
            reasons.append(f"  - {corrupted_key.count(chr(13))} carriage return character(s)")
        if ' ' in corrupted_key:
            reasons.append(f"  - {corrupted_key.count(' ')} space character(s)")
        if any(ord(char) < 32 for char in corrupted_key if char not in '\t\n\r'):
            reasons.append("  - Other control characters")
        if not re.match(r'^[a-zA-Z0-9\-_\.]+$', corrupted_key.strip()):
            reasons.append("  - Invalid characters for API key format")
        
        for reason in reasons:
            print(reason)
        
        return True


if __name__ == "__main__":
    success = main()
    print()
    if success:
        print("🎉 The fix is working! The original error case is now prevented.")
    else:
        print("⚠️  The fix needs more work.")
    
    exit(0 if success else 1)