"""
Tests for security utilities and sanitization functions.

This module tests the InputSanitizer class, sanitization functions,
SQL injection prevention, XSS prevention, and other security measures.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

from server.api.utils.security import (
    InputSanitizer, SecurityError, RequestValidator,
    sanitize_search_term, sanitize_person_data,
    create_security_headers, log_security_event
)


class TestInputSanitizer:
    """Tests for the InputSanitizer class."""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        sanitizer = InputSanitizer()
        
        # Normal string should pass through
        result = sanitizer.sanitize_string("Hello World")
        assert result == "Hello World"
        
        # String with extra whitespace should be normalized
        result = sanitizer.sanitize_string("  Hello   World  ")
        assert result == "Hello World"
    
    def test_sanitize_string_html_escaping(self):
        """Test HTML escaping in string sanitization."""
        sanitizer = InputSanitizer()
        
        # Regular HTML should be escaped by default (using non-dangerous tags)
        result = sanitizer.sanitize_string("<b>bold text</b> & <i>italic</i>")
        assert "&lt;b&gt;bold text&lt;/b&gt;" in result
        assert "&amp;" in result
        assert "&lt;i&gt;italic&lt;/i&gt;" in result
        
        # With allow_html=True, HTML should not be escaped for non-dangerous content
        result_html = sanitizer.sanitize_string("<b>bold text</b>", allow_html=True)
        assert "<b>bold text</b>" == result_html
        
        # But dangerous patterns should still be blocked even with allow_html=True
        with pytest.raises(SecurityError):
            sanitizer.sanitize_string("<script>alert('xss')</script>", allow_html=True)
    
    def test_sanitize_string_length_limit(self):
        """Test string length limits."""
        sanitizer = InputSanitizer()
        
        # String within limit should pass
        result = sanitizer.sanitize_string("A" * 100, max_length=200)
        assert len(result) == 100
        
        # String exceeding limit should raise error
        with pytest.raises(SecurityError, match="exceeds maximum length"):
            sanitizer.sanitize_string("A" * 1000, max_length=500)
    
    def test_sanitize_string_dangerous_patterns(self):
        """Test detection of dangerous patterns."""
        sanitizer = InputSanitizer()
        
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "<img onload='alert(1)'>",
            "expression(alert('xss'))",
            "url(javascript:alert('xss'))",
            "@import 'evil.css'",
            "vbscript:msgbox('xss')",
            "file://etc/passwd",
            "ftp://malicious.com/evil.exe"
        ]
        
        for dangerous_input in dangerous_inputs:
            with pytest.raises(SecurityError, match="potentially dangerous content"):
                sanitizer.sanitize_string(dangerous_input)
    
    def test_sanitize_string_control_characters(self):
        """Test removal of control characters."""
        sanitizer = InputSanitizer()
        
        # Control characters should be removed (except \t, \n, \r)
        input_with_control = "Hello\x00\x01\x02World\t\n\r"
        result = sanitizer.sanitize_string(input_with_control)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
        assert "\t" in result
        assert "\n" in result
        assert "\r" in result
    
    def test_sanitize_search_query_basic(self):
        """Test basic search query sanitization."""
        sanitizer = InputSanitizer()
        
        # Normal search query should pass
        result = sanitizer.sanitize_search_query("john doe")
        assert result == "john doe"
        
        # Query with wildcards should be preserved
        result = sanitizer.sanitize_search_query("john*")
        assert result == "john*"
        
        # Email-like queries should work
        result = sanitizer.sanitize_search_query("john@example.com")
        assert result == "john@example.com"
    
    def test_sanitize_search_query_sql_injection(self):
        """Test SQL injection pattern detection in search queries."""
        sanitizer = InputSanitizer()
        
        sql_injection_patterns = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "UNION SELECT * FROM passwords",
            "INSERT INTO users VALUES",
            "UPDATE users SET password",
            "DELETE FROM users WHERE",
            "CREATE TABLE malicious",
            "ALTER TABLE users",
            "EXEC xp_cmdshell",
            "' AND 1=1 --",
            "/* comment */ SELECT"
        ]
        
        for injection_pattern in sql_injection_patterns:
            with pytest.raises(SecurityError, match="potentially dangerous SQL patterns"):
                sanitizer.sanitize_search_query(injection_pattern)
    
    def test_sanitize_search_query_path_traversal(self):
        """Test path traversal pattern detection in search queries."""
        sanitizer = InputSanitizer()
        
        path_traversal_patterns = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2f",
            "%2e%2e%5c%2e%2e%5c%2e%2e%5c",
            "%252e%252e%252f"
        ]
        
        for traversal_pattern in path_traversal_patterns:
            with pytest.raises(SecurityError, match="path traversal patterns"):
                sanitizer.sanitize_search_query(traversal_pattern)
    
    def test_sanitize_search_query_length_limit(self):
        """Test search query length limits."""
        sanitizer = InputSanitizer()
        
        # Long query should be truncated
        long_query = "A" * 300
        result = sanitizer.sanitize_search_query(long_query)
        assert len(result) == 200
    
    def test_sanitize_search_query_character_filtering(self):
        """Test character filtering in search queries."""
        sanitizer = InputSanitizer()
        
        # Dangerous characters should be removed, safe ones preserved
        query_with_mixed_chars = "john<script>doe@example.com*"
        result = sanitizer.sanitize_search_query(query_with_mixed_chars)
        
        assert "john" in result
        assert "doe" in result
        assert "@example.com" in result
        assert "*" in result
        assert "<script>" not in result
    
    def test_sanitize_email_valid(self):
        """Test email sanitization with valid emails."""
        sanitizer = InputSanitizer()
        
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@456.com"
        ]
        
        for email in valid_emails:
            result = sanitizer.sanitize_email(email)
            assert result == email.lower().strip()
    
    def test_sanitize_email_invalid(self):
        """Test email sanitization with invalid emails."""
        sanitizer = InputSanitizer()
        
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            ""
        ]
        
        for email in invalid_emails:
            if email:  # Empty string has different handling
                with pytest.raises(SecurityError, match="Invalid email format"):
                    sanitizer.sanitize_email(email)
            else:  # Empty string should raise SecurityError
                with pytest.raises(SecurityError, match="Email cannot be empty"):
                    sanitizer.sanitize_email(email)
    
    def test_sanitize_email_too_long(self):
        """Test email length validation."""
        sanitizer = InputSanitizer()
        
        # Email longer than 254 characters should fail
        long_email = "a" * 250 + "@test.com"  # 259 characters total
        with pytest.raises(SecurityError, match="Email address too long"):
            sanitizer.sanitize_email(long_email)
    
    def test_sanitize_email_dangerous_content(self):
        """Test email sanitization with dangerous content."""
        sanitizer = InputSanitizer()
        
        # Email with dangerous patterns should fail
        with pytest.raises(SecurityError, match="potentially dangerous content"):
            sanitizer.sanitize_email("test@example.com<script>alert('xss')</script>")
    
    def test_sanitize_phone_valid(self):
        """Test phone number sanitization with valid numbers."""
        sanitizer = InputSanitizer()
        
        valid_phones = [
            "+1-555-123-4567",
            "555.123.4567",
            "(555) 123-4567",
            "15551234567",
            "+44 20 7946 0958"
        ]
        
        for phone in valid_phones:
            result = sanitizer.sanitize_phone(phone)
            assert result is not None
            # Result should contain only allowed characters
            assert all(c in "0123456789+-() " for c in result)
    
    def test_sanitize_phone_invalid(self):
        """Test phone number sanitization with invalid numbers."""
        sanitizer = InputSanitizer()
        
        invalid_phones = [
            "123",  # Too short
            "abc",  # No digits
            "555-CALL-NOW",  # Letters
            "",  # Empty
            "1234567890123456789"  # Too long
        ]
        
        for phone in invalid_phones:
            if phone:  # Empty string has different handling
                with pytest.raises(SecurityError, match="Invalid phone number format"):
                    sanitizer.sanitize_phone(phone)
            else:
                result = sanitizer.sanitize_phone(phone)
                assert result == ""
    
    def test_sanitize_filename_valid(self):
        """Test filename sanitization with valid filenames."""
        sanitizer = InputSanitizer()
        
        valid_filenames = [
            "document.pdf",
            "my_file.txt",
            "report-2024.xlsx",
            "IMG_001.jpg"
        ]
        
        for filename in valid_filenames:
            result = sanitizer.sanitize_filename(filename)
            assert result == filename
    
    def test_sanitize_filename_path_traversal(self):
        """Test filename sanitization with path traversal attempts."""
        sanitizer = InputSanitizer()
        
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32.exe",
            "%2e%2e%2fetc%2fpasswd",
            "normal_file/../../../etc/passwd"
        ]
        
        for filename in malicious_filenames:
            with pytest.raises(SecurityError, match="path traversal patterns"):
                sanitizer.sanitize_filename(filename)
    
    def test_sanitize_filename_unsafe_characters(self):
        """Test filename sanitization with unsafe characters."""
        sanitizer = InputSanitizer()
        
        # Filename with unsafe characters should be cleaned
        unsafe_filename = "my<script>file|name?.exe"
        result = sanitizer.sanitize_filename(unsafe_filename)
        
        assert "<script>" not in result
        assert "|" not in result
        assert "?" not in result
        # Unsafe characters should be replaced with underscores
        assert "_" in result
    
    def test_sanitize_filename_too_long(self):
        """Test filename length limits."""
        sanitizer = InputSanitizer()
        
        # Very long filename should be truncated
        long_filename = "A" * 300 + ".txt"
        result = sanitizer.sanitize_filename(long_filename)
        assert len(result) <= 255
    
    def test_validate_uuid_valid(self):
        """Test UUID validation with valid UUIDs."""
        sanitizer = InputSanitizer()
        
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "00000000-0000-0000-0000-000000000000",
            "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"
        ]
        
        for uuid_str in valid_uuids:
            assert sanitizer.validate_uuid(uuid_str) is True
            assert sanitizer.validate_uuid(uuid_str.lower()) is True
    
    def test_validate_uuid_invalid(self):
        """Test UUID validation with invalid UUIDs."""
        sanitizer = InputSanitizer()
        
        invalid_uuids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456",  # Too short
            "123e4567-e89b-12d3-a456-426614174000-extra",  # Too long
            "123e4567_e89b_12d3_a456_426614174000",  # Wrong separators
            ""
        ]
        
        for uuid_str in invalid_uuids:
            assert sanitizer.validate_uuid(uuid_str) is False
    
    def test_sanitize_dict_basic(self):
        """Test dictionary sanitization."""
        sanitizer = InputSanitizer()
        
        test_dict = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "active": True,
            "notes": None
        }
        
        result = sanitizer.sanitize_dict(test_dict)
        
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"
        assert result["age"] == 30
        assert result["active"] is True
        assert result["notes"] is None
    
    def test_sanitize_dict_nested(self):
        """Test nested dictionary sanitization."""
        sanitizer = InputSanitizer()
        
        test_dict = {
            "user": {
                "name": "John Doe",
                "profile": {
                    "bio": "Software developer"
                }
            }
        }
        
        result = sanitizer.sanitize_dict(test_dict)
        
        assert result["user"]["name"] == "John Doe"
        assert result["user"]["profile"]["bio"] == "Software developer"
    
    def test_sanitize_dict_max_depth(self):
        """Test dictionary sanitization depth limits."""
        sanitizer = InputSanitizer()
        
        # Create deeply nested dict
        deep_dict = {"level1": {"level2": {"level3": {"level4": {"level5": {}}}}}}
        
        # Should fail with default max_depth
        with pytest.raises(SecurityError, match="too deeply nested"):
            sanitizer.sanitize_dict(deep_dict, max_depth=3)
    
    def test_sanitize_list_basic(self):
        """Test list sanitization."""
        sanitizer = InputSanitizer()
        
        test_list = ["item1", "item2", 123, True, None]
        result = sanitizer.sanitize_list(test_list)
        
        assert result[0] == "item1"
        assert result[1] == "item2"
        assert result[2] == 123
        assert result[3] is True
        assert result[4] is None
    
    def test_sanitize_list_max_length(self):
        """Test list length limits."""
        sanitizer = InputSanitizer()
        
        # List exceeding max length should fail
        long_list = ["item"] * 1001
        with pytest.raises(SecurityError, match="exceeds maximum length"):
            sanitizer.sanitize_list(long_list)
    
    def test_sanitize_list_with_dangerous_content(self):
        """Test list sanitization with dangerous content."""
        sanitizer = InputSanitizer()
        
        dangerous_list = [
            "safe_item",
            "<script>alert('xss')</script>",
            "normal_item"
        ]
        
        result = sanitizer.sanitize_list(dangerous_list)
        
        assert result[0] == "safe_item"
        assert "&lt;script&gt;" in result[1]  # Should be escaped
        assert result[2] == "normal_item"


class TestRequestValidator:
    """Tests for the RequestValidator class."""
    
    def test_validate_content_type_valid(self):
        """Test content type validation with valid types."""
        validator = RequestValidator()
        
        valid_types = [
            "application/json",
            "text/plain",
            "application/json; charset=utf-8"
        ]
        
        for content_type in valid_types:
            assert validator.validate_content_type(content_type) is True
    
    def test_validate_content_type_invalid(self):
        """Test content type validation with invalid types."""
        validator = RequestValidator()
        
        invalid_types = [
            "text/html",
            "application/xml",
            "image/jpeg",
            "",
            None
        ]
        
        for content_type in invalid_types:
            assert validator.validate_content_type(content_type) is False
    
    def test_validate_user_agent_legitimate(self):
        """Test user agent validation with legitimate agents."""
        validator = RequestValidator()
        
        legitimate_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Chrome/91.0.4472.124 Safari/537.36",
            "PostmanRuntime/7.28.4",
            "curl/7.68.0",
            "Python-urllib/3.8"
        ]
        
        for user_agent in legitimate_agents:
            assert validator.validate_user_agent(user_agent) is True
    
    def test_validate_user_agent_suspicious(self):
        """Test user agent validation with suspicious agents."""
        validator = RequestValidator()
        
        suspicious_agents = [
            "sqlmap/1.4.7",
            "nikto/2.1.6",
            "nmap scripting engine",
            "Burp Suite",
            "gobuster/3.1.0"
        ]
        
        for user_agent in suspicious_agents:
            assert validator.validate_user_agent(user_agent) is False
    
    def test_validate_request_size_valid(self):
        """Test request size validation with valid sizes."""
        validator = RequestValidator()
        
        valid_sizes = [0, 1024, 1024*1024, 5*1024*1024]  # 0B, 1KB, 1MB, 5MB
        
        for size in valid_sizes:
            assert validator.validate_request_size(size) is True
    
    def test_validate_request_size_invalid(self):
        """Test request size validation with invalid sizes."""
        validator = RequestValidator()
        
        invalid_sizes = [
            -1,  # Negative size
            11*1024*1024,  # 11MB (exceeds default 10MB limit)
            100*1024*1024  # 100MB
        ]
        
        for size in invalid_sizes:
            assert validator.validate_request_size(size) is False
    
    def test_validate_request_size_custom_limit(self):
        """Test request size validation with custom limits."""
        validator = RequestValidator()
        
        # 1MB limit
        assert validator.validate_request_size(512*1024, max_size=1024*1024) is True
        assert validator.validate_request_size(2*1024*1024, max_size=1024*1024) is False


class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_sanitize_search_term_basic(self):
        """Test the sanitize_search_term utility function."""
        # Normal search term should pass
        result = sanitize_search_term("john doe")
        assert result == "john doe"
        
        # None should return empty string
        result = sanitize_search_term(None)
        assert result == ""
        
        # Empty string should return empty string
        result = sanitize_search_term("")
        assert result == ""
    
    def test_sanitize_search_term_dangerous_input(self):
        """Test sanitize_search_term with dangerous input."""
        # Should return empty string for dangerous input instead of raising exception
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd"
        ]
        
        for dangerous_input in dangerous_inputs:
            result = sanitize_search_term(dangerous_input)
            assert result == ""
    
    def test_sanitize_person_data_basic(self):
        """Test person data sanitization."""
        person_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "JOHN.DOE@EXAMPLE.COM",
            "phone": "+1-555-123-4567",
            "notes": "Software developer",
            "tags": ["Developer", "Full-time"]
        }
        
        result = sanitize_person_data(person_data)
        
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe" 
        assert result["email"] == "john.doe@example.com"  # Should be lowercased
        assert result["phone"] == "+1-555-123-4567"
        assert result["notes"] == "Software developer"
        assert result["tags"] == ["Developer", "Full-time"]
    
    def test_sanitize_person_data_invalid_email(self):
        """Test person data sanitization with invalid email."""
        person_data = {
            "email": "invalid-email-format"
        }
        
        result = sanitize_person_data(person_data)
        
        # Invalid email should be set to None
        assert result["email"] is None
    
    def test_sanitize_person_data_invalid_phone(self):
        """Test person data sanitization with invalid phone."""
        person_data = {
            "phone": "123",  # Too short
            "mobile": "abc-def-ghij"  # Invalid format
        }
        
        result = sanitize_person_data(person_data)
        
        # Invalid phones should be set to None
        assert result["phone"] is None
        assert result["mobile"] is None
    
    def test_sanitize_person_data_dangerous_content(self):
        """Test person data sanitization with dangerous content."""
        person_data = {
            "first_name": "<script>alert('xss')</script>",
            "notes": "javascript:alert('malicious')",
            "address": "../../../etc/passwd"
        }
        
        result = sanitize_person_data(person_data)
        
        # Dangerous content should be escaped/sanitized
        assert "<script>" not in result["first_name"]
        assert "javascript:" not in result["notes"]
        assert "../" not in result["address"]
    
    def test_create_security_headers(self):
        """Test security headers creation."""
        headers = create_security_headers()
        
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options', 
            'X-XSS-Protection',
            'Referrer-Policy',
            'Content-Security-Policy',
            'Cache-Control',
            'Pragma',
            'Expires'
        ]
        
        for header in expected_headers:
            assert header in headers
            assert headers[header] is not None
    
    def test_log_security_event(self, caplog):
        """Test security event logging."""
        event_type = "XSS_ATTEMPT"
        details = {"ip": "192.168.1.1", "input": "<script>alert('xss')</script>"}
        request_id = "req-123"
        
        log_security_event(event_type, details, request_id)
        
        # Check that the event was logged
        assert len(caplog.records) == 1
        log_record = caplog.records[0]
        assert "Security event [XSS_ATTEMPT]" in log_record.message
        assert "req-123" in log_record.message


class TestSecurityIntegration:
    """Integration tests for security components."""
    
    def test_full_person_sanitization_workflow(self):
        """Test complete person data sanitization workflow."""
        raw_person_data = {
            "first_name": "  John  ",
            "last_name": "Doe<script>alert('xss')</script>",
            "email": "JOHN.DOE@EXAMPLE.COM  ",
            "phone": "+1-555-123-4567",
            "mobile": "555.987.6543",
            "notes": "Software developer\x00\x01with\x02control\x03chars",
            "tags": ["Developer", "Full-time", "<script>evil</script>"],
            "address": "123 Main St",
            "city": "New York  ",
            "emergency_contact_phone": "(555) 111-2222"
        }
        
        sanitized = sanitize_person_data(raw_person_data)
        
        # Check that data is properly sanitized
        assert sanitized["first_name"] == "John"
        assert "&lt;script&gt;" in sanitized["last_name"]
        assert sanitized["email"] == "john.doe@example.com"
        assert sanitized["phone"] == "+1-555-123-4567"
        assert sanitized["city"] == "New York"
        assert "\x00" not in sanitized["notes"]
        assert "\x01" not in sanitized["notes"]
        assert len(sanitized["tags"]) == 3
        assert "&lt;script&gt;" in sanitized["tags"][2]
    
    def test_search_query_security_bypass_attempts(self):
        """Test various attempts to bypass search query security."""
        bypass_attempts = [
            # SQL injection variations
            "admin'/**/OR/**/'1'='1",
            "admin'; WAITFOR DELAY '00:00:05'--",
            "admin' UNION SELECT NULL,version(),NULL--",
            
            # XSS variations
            "<svg onload=alert(1)>",
            "javascript&#58;alert(1)",
            "<iframe src=javascript:alert(1)>",
            
            # Path traversal variations
            "....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2fwindows%2fsystem32",
            
            # Command injection
            "; cat /etc/passwd;",
            "| nc -l 4444",
            "&& rm -rf /"
        ]
        
        for attempt in bypass_attempts:
            result = sanitize_search_term(attempt)
            # All bypass attempts should result in empty string
            assert result == "", f"Failed to sanitize: {attempt}"
    
    def test_nested_malicious_content(self):
        """Test sanitization of deeply nested malicious content."""
        sanitizer = InputSanitizer()
        
        nested_malicious = {
            "level1": {
                "level2": {
                    "malicious_script": "<script>alert('deep xss')</script>",
                    "sql_injection": "'; DROP TABLE users; --",
                    "list_with_evil": [
                        "safe_item",
                        "<img onerror=alert(1) src=x>",
                        {"nested_evil": "javascript:alert('nested')"}
                    ]
                }
            }
        }
        
        result = sanitizer.sanitize_dict(nested_malicious)
        
        # Check that all malicious content was sanitized at all levels
        level2 = result["level1"]["level2"]
        assert "&lt;script&gt;" in level2["malicious_script"]
        assert "DROP" not in level2["sql_injection"]  # Should be removed
        assert "&lt;img" in level2["list_with_evil"][1]
        assert "javascript:" not in str(level2["list_with_evil"][2]["nested_evil"])
    
    @pytest.mark.parametrize("email_input,expected_valid", [
        ("test@example.com", True),
        ("TEST@EXAMPLE.COM", True),  # Should be normalized
        ("user+tag@domain.co.uk", True),
        ("invalid-email", False),
        ("@example.com", False),
        ("test@", False),
        ("", False),
        ("test@example.com<script>", False),  # With XSS
    ])
    def test_email_sanitization_edge_cases(self, email_input, expected_valid):
        """Test email sanitization edge cases."""
        if expected_valid and "<script>" not in email_input:
            result = InputSanitizer.sanitize_email(email_input)
            assert result == email_input.lower().strip()
        else:
            with pytest.raises(SecurityError):
                InputSanitizer.sanitize_email(email_input)
    
    @pytest.mark.parametrize("phone_input,expected_valid", [
        ("+1-555-123-4567", True),
        ("(555) 123-4567", True),
        ("555.123.4567", True),
        ("15551234567", True),
        ("123", False),  # Too short
        ("555-CALL-NOW", False),  # Contains letters
        ("", False),
        ("+1-555-123-4567<script>", False),  # With XSS
    ])
    def test_phone_sanitization_edge_cases(self, phone_input, expected_valid):
        """Test phone sanitization edge cases."""
        if expected_valid and "<script>" not in phone_input:
            result = InputSanitizer.sanitize_phone(phone_input)
            assert result is not None
        else:
            if phone_input:  # Non-empty invalid phone
                with pytest.raises(SecurityError):
                    InputSanitizer.sanitize_phone(phone_input)
            else:  # Empty phone
                result = InputSanitizer.sanitize_phone(phone_input)
                assert result == ""