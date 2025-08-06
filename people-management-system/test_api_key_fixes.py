#!/usr/bin/env python3
"""
Test Script for API Key Corruption Fixes

This script tests all the fixes implemented to prevent API key corruption
that caused "Illegal header value" errors.

Usage:
    python test_api_key_fixes.py

This script tests:
1. API key validation functions
2. API key sanitization
3. Config service validation
4. API client validation
5. Prevention of corrupted API keys
"""

import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from client.services.config_service import (
    ConfigService, ConnectionConfig, validate_api_key, 
    sanitize_api_key, APIKeyValidationError
)
from shared.api_client import (
    PeopleManagementClient, ClientConfig, 
    validate_api_key as client_validate_api_key,
    APIKeyValidationError as ClientAPIKeyValidationError
)


class TestResults:
    """Helper class to track test results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_pass(self, test_name: str):
        self.passed += 1
        print(f"✓ {test_name}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append(f"{test_name}: {error}")
        print(f"✗ {test_name}: {error}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{total} passed")
        if self.failed > 0:
            print(f"Failed tests:")
            for error in self.errors:
                print(f"  - {error}")
        print(f"{'='*60}")
        return self.failed == 0


def test_api_key_validation():
    """Test the API key validation functions."""
    results = TestResults()
    
    print("\n1. Testing API key validation functions...")
    
    # Test valid API keys
    valid_keys = [
        "abc123def456ghi789",
        "API-KEY-WITH-HYPHENS-123",
        "api_key_with_underscores_456",
        "mixed-key_with.dots123",
        "1234567890abcdef"
    ]
    
    for key in valid_keys:
        try:
            if validate_api_key(key) and client_validate_api_key(key):
                results.add_pass(f"Valid key accepted: '{key[:20]}{'...' if len(key) > 20 else ''}'")
            else:
                results.add_fail(f"Valid key rejected", f"'{key}'")
        except Exception as e:
            results.add_fail(f"Valid key error", f"'{key}' - {e}")
    
    # Test invalid API keys (the ones that caused the original problem)
    invalid_keys = [
        "Ultrathink error and fix and test it, use context7, use subagent.\n-When i add new person.\n    -email address not allow me to entry '.'.",
        "api-key-with\nnewline",
        "api-key-with\rcarriage-return",
        "api\tkey\twith\ttabs",
        "key with spaces",
        "",
        "short",
        "a" * 300,  # Too long
        "key-with-unicode-éñ",
        "key@with#special$chars%",
    ]
    
    for key in invalid_keys:
        try:
            if not validate_api_key(key) and not client_validate_api_key(key):
                results.add_pass(f"Invalid key rejected: '{key[:30]}{'...' if len(key) > 30 else ''}'")
            else:
                results.add_fail(f"Invalid key accepted", f"'{key[:50]}'")
        except Exception as e:
            results.add_fail(f"Invalid key validation error", f"'{key[:50]}' - {e}")
    
    return results


def test_api_key_sanitization():
    """Test API key sanitization."""
    results = TestResults()
    
    print("\n2. Testing API key sanitization...")
    
    # Test cases that should be sanitizable
    sanitizable_cases = [
        ("api-key-123\n", "api-key-123"),
        ("api-key-456\r", "api-key-456"),
        ("  api-key-789  ", "api-key-789"),
        ("api\tkey\twith\ttabs", "apikeywithtabs"),
    ]
    
    for original, expected in sanitizable_cases:
        try:
            sanitized = sanitize_api_key(original)
            if sanitized == expected:
                results.add_pass(f"Sanitization: '{original[:20]}...' -> '{sanitized}'")
            else:
                results.add_fail(f"Sanitization incorrect", f"'{original}' -> '{sanitized}', expected '{expected}'")
        except Exception as e:
            results.add_fail(f"Sanitization error", f"'{original}' - {e}")
    
    # Test cases that should fail sanitization
    unsanitizable_cases = [
        "",
        "short",
        "key@with#special$chars%",
        "key with spaces that cannot be fixed",
    ]
    
    for key in unsanitizable_cases:
        try:
            sanitize_api_key(key)
            results.add_fail(f"Unsanitizable key accepted", f"'{key}'")
        except APIKeyValidationError:
            results.add_pass(f"Unsanitizable key rejected: '{key[:30]}...'")
        except Exception as e:
            results.add_fail(f"Unexpected sanitization error", f"'{key}' - {e}")
    
    return results


def test_config_service_validation():
    """Test config service API key validation."""
    results = TestResults()
    
    print("\n3. Testing config service validation...")
    
    # Create a temporary config directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the config directories to use our temp directory
        with patch('client.services.config_service.user_config_dir', return_value=temp_dir):
            with patch('client.services.config_service.user_data_dir', return_value=temp_dir):
                try:
                    config_service = ConfigService()
                    config_service.initialize()
                    
                    # Test setting a valid API key
                    try:
                        config_service.set_api_key("http://localhost:8000", "valid-api-key-123")
                        results.add_pass("Config service accepts valid API key")
                    except Exception as e:
                        results.add_fail("Config service rejects valid API key", str(e))
                    
                    # Test setting an invalid API key with newlines
                    try:
                        config_service.set_api_key("http://localhost:8000", "invalid-key\nwith-newline")
                        results.add_fail("Config service accepts invalid API key", "Should have rejected key with newline")
                    except (ValueError, APIKeyValidationError):
                        results.add_pass("Config service rejects invalid API key with newline")
                    except Exception as e:
                        results.add_fail("Config service validation error", str(e))
                    
                    # Test the clear corrupted keys function
                    try:
                        cleared = config_service.clear_corrupted_api_keys()
                        results.add_pass(f"Corrupted key cleanup completed (cleared {cleared})")
                    except Exception as e:
                        results.add_fail("Corrupted key cleanup failed", str(e))
                        
                except Exception as e:
                    results.add_fail("Config service initialization failed", str(e))
    
    return results


def test_api_client_validation():
    """Test API client validation."""
    results = TestResults()
    
    print("\n4. Testing API client validation...")
    
    # Test valid API key
    try:
        config = ClientConfig(
            base_url="http://localhost:8000",
            api_key="valid-api-key-123"
        )
        client = PeopleManagementClient(config)
        client.close()  # Clean up
        results.add_pass("API client accepts valid API key")
    except Exception as e:
        results.add_fail("API client rejects valid API key", str(e))
    
    # Test invalid API key with newline (the original problem)
    try:
        config = ClientConfig(
            base_url="http://localhost:8000",
            api_key="Ultrathink error and fix and test it, use context7, use subagent.\n-When i add new person.\n    -email address not allow me to entry '.'."
        )
        client = PeopleManagementClient(config)
        client.close()
        results.add_fail("API client accepts corrupted API key", "Should have rejected key with newlines")
    except ClientAPIKeyValidationError:
        results.add_pass("API client rejects corrupted API key with newlines")
    except Exception as e:
        results.add_fail("API client validation error", str(e))
    
    # Test invalid API key with carriage return
    try:
        config = ClientConfig(
            base_url="http://localhost:8000",
            api_key="invalid-key\rwith-carriage-return"
        )
        client = PeopleManagementClient(config)
        client.close()
        results.add_fail("API client accepts invalid API key", "Should have rejected key with carriage return")
    except ClientAPIKeyValidationError:
        results.add_pass("API client rejects API key with carriage return")
    except Exception as e:
        results.add_fail("API client validation error", str(e))
    
    return results


def test_original_error_prevention():
    """Test that the original error case is now prevented."""
    results = TestResults()
    
    print("\n5. Testing prevention of original error case...")
    
    # The exact API key value that caused the original error
    corrupted_key = "Ultrathink error and fix and test it, use context7, use subagent.\n-When i add new person.\n    -email address not allow me to entry '.'."
    
    # Test validation functions
    if not validate_api_key(corrupted_key):
        results.add_pass("Validation function rejects original corrupted key")
    else:
        results.add_fail("Validation function accepts original corrupted key", "Should reject")
    
    # Test sanitization
    try:
        sanitize_api_key(corrupted_key)
        results.add_fail("Sanitization accepts original corrupted key", "Should fail to sanitize")
    except APIKeyValidationError:
        results.add_pass("Sanitization rejects original corrupted key")
    except Exception as e:
        results.add_fail("Sanitization error", str(e))
    
    # Test API client
    try:
        config = ClientConfig(base_url="http://localhost:8000", api_key=corrupted_key)
        client = PeopleManagementClient(config)
        client.close()
        results.add_fail("API client accepts original corrupted key", "Should reject")
    except ClientAPIKeyValidationError:
        results.add_pass("API client rejects original corrupted key")
    except Exception as e:
        results.add_fail("API client error", str(e))
    
    return results


def main():
    """Run all tests."""
    print("=" * 60)
    print("People Management System - API Key Fix Test Suite")
    print("=" * 60)
    
    all_results = []
    
    # Run all test suites
    all_results.append(test_api_key_validation())
    all_results.append(test_api_key_sanitization())
    all_results.append(test_config_service_validation())
    all_results.append(test_api_client_validation())
    all_results.append(test_original_error_prevention())
    
    # Calculate overall results
    total_passed = sum(r.passed for r in all_results)
    total_failed = sum(r.failed for r in all_results)
    total_tests = total_passed + total_failed
    
    print(f"\n{'='*60}")
    print(f"OVERALL TEST RESULTS")
    print(f"{'='*60}")
    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    
    if total_failed > 0:
        print(f"\nFAILED TESTS:")
        for results in all_results:
            for error in results.errors:
                print(f"  - {error}")
    
    if total_failed == 0:
        print(f"\n🎉 ALL TESTS PASSED! The API key corruption fixes are working correctly.")
        print(f"The 'Illegal header value' error should no longer occur.")
    else:
        print(f"\n⚠️  {total_failed} test(s) failed. Please review the fixes.")
    
    print(f"{'='*60}")
    
    return total_failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)