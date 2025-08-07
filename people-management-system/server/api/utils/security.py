"""
Security utilities for input validation and sanitization.

This module provides comprehensive security utilities including input sanitization,
validation helpers, and security-related functions for the API layer.
"""

import re
import html
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, unquote
from datetime import datetime

logger = logging.getLogger(__name__)

# Security constants
MAX_STRING_LENGTH = 10000
MAX_TEXT_LENGTH = 50000
MAX_LIST_LENGTH = 1000
ALLOWED_MIME_TYPES = ['application/json', 'text/plain']

# Regex patterns for validation
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9._+%-]*[a-zA-Z0-9])*@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])*\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^[\+]?[1-9]?[\d\s\-\(\)\.]{7,15}$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._\-]+$')

# Dangerous patterns to detect potential security threats
DANGEROUS_PATTERNS = [
    re.compile(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', re.IGNORECASE),  # XSS
    re.compile(r'javascript:', re.IGNORECASE),  # JavaScript injection
    re.compile(r'data:text/html', re.IGNORECASE),  # Data URI XSS
    re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
    re.compile(r'expression\s*\(', re.IGNORECASE),  # CSS expression
    re.compile(r'url\s*\(', re.IGNORECASE),  # CSS URL
    re.compile(r'@import', re.IGNORECASE),  # CSS import
    re.compile(r'vbscript:', re.IGNORECASE),  # VBScript
    re.compile(r'file://', re.IGNORECASE),  # File protocol
    re.compile(r'ftp://', re.IGNORECASE),  # FTP protocol
]

# SQL injection patterns
SQL_INJECTION_PATTERNS = [
    re.compile(r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b', re.IGNORECASE),
    re.compile(r'[\'";]', re.IGNORECASE),  # Quote characters
    re.compile(r'--', re.IGNORECASE),  # SQL comments
    re.compile(r'/\*.*\*/', re.IGNORECASE),  # SQL block comments
    re.compile(r'\bor\b.*=.*=', re.IGNORECASE),  # OR injection patterns
    re.compile(r'\band\b.*=.*=', re.IGNORECASE),  # AND injection patterns
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS = [
    re.compile(r'\.\./', re.IGNORECASE),
    re.compile(r'\.\.\\', re.IGNORECASE),
    re.compile(r'%2e%2e%2f', re.IGNORECASE),
    re.compile(r'%2e%2e%5c', re.IGNORECASE),
    re.compile(r'%252e%252e%252f', re.IGNORECASE),
]

# Command injection patterns
COMMAND_INJECTION_PATTERNS = [
    re.compile(r'[;&|`]', re.IGNORECASE),  # Command separators and pipes
    re.compile(r'\$\(', re.IGNORECASE),   # Command substitution
    re.compile(r'&&', re.IGNORECASE),     # Logical AND
    re.compile(r'\|\|', re.IGNORECASE),   # Logical OR
    re.compile(r'<\(', re.IGNORECASE),    # Process substitution
    re.compile(r'>\(', re.IGNORECASE),    # Process substitution
]


class SecurityError(Exception):
    """Exception raised for security-related errors."""
    pass


class InputSanitizer:
    """
    Comprehensive input sanitization and validation utilities.
    
    Provides methods to sanitize and validate various types of input
    to prevent security vulnerabilities like XSS, SQL injection, etc.
    """
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = MAX_STRING_LENGTH, allow_html: bool = False) -> str:
        """
        Sanitize a string input to prevent XSS and other attacks.
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML (escaped)
            
        Returns:
            Sanitized string
            
        Raises:
            SecurityError: If input contains dangerous content when allow_html=True
        """
        if not isinstance(input_str, str):
            input_str = str(input_str)
        
        # Check length
        if len(input_str) > max_length:
            raise SecurityError(f"Input exceeds maximum length of {max_length} characters")
        
        # Check for dangerous patterns - these should always raise SecurityError
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(input_str):
                logger.warning(f"Dangerous pattern detected in input: {pattern.pattern}")
                raise SecurityError("Input contains potentially dangerous content")
        
        # Check for SQL injection patterns - these should always raise SecurityError  
        for pattern in SQL_INJECTION_PATTERNS:
            if pattern.search(input_str):
                logger.warning(f"SQL injection pattern detected in input: {pattern.pattern}")
                raise SecurityError("Input contains potentially dangerous content")
        
        # Check for path traversal patterns - these should always raise SecurityError
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if pattern.search(input_str):
                logger.warning(f"Path traversal pattern detected in input: {pattern.pattern}")
                raise SecurityError("Input contains potentially dangerous content")
        
        # HTML escape if not allowing HTML
        if not allow_html:
            input_str = html.escape(input_str, quote=True)
        
        # Remove null bytes and control characters (except \t, \n, \r)
        input_str = ''.join(char for char in input_str if ord(char) >= 32 or char in '\t\n\r')
        
        # Normalize excessive whitespace (but preserve single tabs, newlines, carriage returns)
        input_str = re.sub(r'[ ]{2,}', ' ', input_str)  # Multiple spaces become single space
        input_str = re.sub(r'\t{2,}', '\t', input_str)  # Multiple tabs become single tab
        
        # Trim only leading and trailing spaces (preserve \t\n\r at the ends if they were there)
        input_str = input_str.strip(' ')
        
        return input_str
    
    @staticmethod
    def _sanitize_string_for_list(input_str: str, max_length: int = MAX_STRING_LENGTH) -> str:
        """
        Sanitize a string for use in lists - removes dangerous patterns and escapes HTML.
        Unlike sanitize_string, this method never raises SecurityError but sanitizes content.
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string with dangerous patterns removed and HTML escaped
        """
        if not isinstance(input_str, str):
            input_str = str(input_str)
        
        # Truncate if too long instead of raising error
        if len(input_str) > max_length:
            input_str = input_str[:max_length]
        
        # For some dangerous patterns, we need to be selective
        # Only remove javascript: completely, let HTML escaping handle the rest
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(input_str):
                if 'javascript:' in pattern.pattern:
                    input_str = pattern.sub('', input_str)  # Remove javascript: completely
        
        # Remove SQL injection patterns
        for pattern in SQL_INJECTION_PATTERNS:
            if pattern.search(input_str):
                # Remove SQL injection patterns
                if r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b' in pattern.pattern:
                    input_str = pattern.sub('', input_str)  # Remove SQL keywords completely
                elif pattern.pattern == r'[\'";]':
                    input_str = pattern.sub('', input_str)  # Remove quotes
                elif pattern.pattern == r'--':
                    input_str = pattern.sub('', input_str)  # Remove comments
                else:
                    input_str = pattern.sub('', input_str)
        
        # Remove path traversal patterns
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if pattern.search(input_str):
                input_str = pattern.sub('', input_str)
        
        # Always HTML escape (equivalent to allow_html=False)
        input_str = html.escape(input_str, quote=True)
        
        # Remove null bytes and control characters (except \t, \n, \r)
        input_str = ''.join(char for char in input_str if ord(char) >= 32 or char in '\t\n\r')
        
        # Normalize excessive whitespace (but preserve single tabs, newlines, carriage returns)
        input_str = re.sub(r'[ ]{2,}', ' ', input_str)  # Multiple spaces become single space
        input_str = re.sub(r'\t{2,}', '\t', input_str)  # Multiple tabs become single tab
        
        # Clean up extra spaces that might result from removals
        input_str = re.sub(r'\s+', ' ', input_str)
        
        # Trim only leading and trailing spaces (preserve \t\n\r at the ends if they were there)
        input_str = input_str.strip(' ')
        
        return input_str
    
    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """
        Sanitize search query to prevent SQL injection and other attacks.
        
        Args:
            query: Search query string
            
        Returns:
            Sanitized search query (empty string if dangerous patterns found)
        """
        if not query:
            return ""
        
        # Check for SQL injection patterns - raise SecurityError if found
        for pattern in SQL_INJECTION_PATTERNS:
            if pattern.search(query):
                logger.warning(f"Potential SQL injection detected in search query: {query}")
                raise SecurityError("Search query contains potentially dangerous SQL patterns")
        
        # Check for path traversal patterns - raise SecurityError if found
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if pattern.search(query):
                logger.warning(f"Path traversal pattern detected in search query: {query}")
                raise SecurityError("Search query contains path traversal patterns")
        
        # Check for XSS and dangerous patterns - return empty if found
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(query):
                logger.warning(f"Dangerous pattern detected in search query: {query}")
                raise SecurityError("Search query contains dangerous patterns")
        
        # Check for command injection patterns - raise SecurityError if found
        for pattern in COMMAND_INJECTION_PATTERNS:
            if pattern.search(query):
                logger.warning(f"Command injection pattern detected in search query: {query}")
                raise SecurityError("Search query contains command injection patterns")
        
        # Limit length
        if len(query) > 200:
            query = query[:200]
        
        # Remove dangerous characters but preserve wildcards for search
        query = re.sub(r'[^\w\s\-@.%*]', '', query)
        
        # Normalize whitespace
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitize and validate email address.
        
        Args:
            email: Email address to sanitize
            
        Returns:
            Sanitized email address
            
        Raises:
            SecurityError: If email format is invalid or contains dangerous content
        """
        if not email or not email.strip():
            raise SecurityError("Email cannot be empty")
        
        email = email.lower().strip()
        
        # Check for dangerous patterns first (before format validation)
        for pattern in DANGEROUS_PATTERNS:
            if pattern.search(email):
                raise SecurityError("Email contains potentially dangerous content")
        
        # Check for consecutive dots
        if '..' in email:
            raise SecurityError("Invalid email format")
        
        # Basic format validation
        if not EMAIL_PATTERN.match(email):
            raise SecurityError("Invalid email format")
        
        # Check length
        if len(email) > 254:  # RFC 5321 limit
            raise SecurityError("Email address too long")
        
        return email
    
    @staticmethod
    def sanitize_phone(phone: str) -> str:
        """
        Sanitize phone number.
        
        Args:
            phone: Phone number to sanitize
            
        Returns:
            Sanitized phone number
            
        Raises:
            SecurityError: If phone format is invalid
        """
        if not phone:
            return ""
        
        phone = phone.strip()
        
        # Basic format validation
        if not PHONE_PATTERN.match(phone):
            raise SecurityError("Invalid phone number format")
        
        # Remove excessive characters and normalize (remove dots for consistency)
        phone = re.sub(r'[^\d\+\-\s\(\)]', '', phone)
        
        return phone
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal and other attacks.
        
        Args:
            filename: Filename to sanitize
            
        Returns:
            Sanitized filename
            
        Raises:
            SecurityError: If filename contains dangerous patterns
        """
        if not filename:
            return ""
        
        # Check for path traversal
        for pattern in PATH_TRAVERSAL_PATTERNS:
            if pattern.search(filename):
                raise SecurityError("Filename contains path traversal patterns")
        
        # Remove path separators
        filename = filename.replace('/', '_').replace('\\', '_')
        
        # Allow only safe characters
        if not SAFE_FILENAME_PATTERN.match(filename):
            # Replace unsafe characters with underscores
            filename = re.sub(r'[^a-zA-Z0-9._\-]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename
    
    @staticmethod
    def validate_uuid(uuid_str: str) -> bool:
        """
        Validate UUID format.
        
        Args:
            uuid_str: UUID string to validate
            
        Returns:
            True if valid UUID format, False otherwise
        """
        return bool(UUID_PATTERN.match(uuid_str))
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values.
        
        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized dictionary
            
        Raises:
            SecurityError: If data structure is too complex
        """
        if max_depth <= 0:
            raise SecurityError("Data structure too deeply nested")
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            if isinstance(key, str):
                sanitized_key = InputSanitizer._sanitize_string_for_list(key, max_length=100)
            else:
                sanitized_key = str(key)
            
            # Sanitize value based on type
            if isinstance(value, str):
                # Use safe sanitization that escapes rather than raises errors
                sanitized[sanitized_key] = InputSanitizer._sanitize_string_for_list(value)
            elif isinstance(value, dict):
                sanitized[sanitized_key] = InputSanitizer.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[sanitized_key] = InputSanitizer.sanitize_list(value, max_depth - 1)
            elif isinstance(value, (int, float, bool, type(None))):
                sanitized[sanitized_key] = value
            elif isinstance(value, datetime):
                sanitized[sanitized_key] = value
            else:
                # Convert unknown types to string and sanitize
                sanitized[sanitized_key] = InputSanitizer._sanitize_string_for_list(str(value))
        
        return sanitized
    
    @staticmethod
    def sanitize_list(data: List[Any], max_depth: int = 10) -> List[Any]:
        """
        Recursively sanitize list values.
        
        Args:
            data: List to sanitize
            max_depth: Maximum recursion depth
            
        Returns:
            Sanitized list
            
        Raises:
            SecurityError: If data structure is too complex
        """
        if max_depth <= 0:
            raise SecurityError("Data structure too deeply nested")
        
        if len(data) > MAX_LIST_LENGTH:
            raise SecurityError(f"List exceeds maximum length of {MAX_LIST_LENGTH} items")
        
        sanitized = []
        
        for item in data:
            if isinstance(item, str):
                # For lists, we want to sanitize strings with HTML escaping (no allow_html)
                # but we need to handle dangerous patterns differently - escape instead of raise error
                sanitized.append(InputSanitizer._sanitize_string_for_list(item))
            elif isinstance(item, dict):
                sanitized.append(InputSanitizer.sanitize_dict(item, max_depth - 1))
            elif isinstance(item, list):
                sanitized.append(InputSanitizer.sanitize_list(item, max_depth - 1))
            elif isinstance(item, (int, float, bool, type(None))):
                sanitized.append(item)
            elif isinstance(item, datetime):
                sanitized.append(item)
            else:
                sanitized.append(InputSanitizer._sanitize_string_for_list(str(item)))
        
        return sanitized


class RequestValidator:
    """
    Request validation utilities for API endpoints.
    
    Provides methods to validate request structure, headers, and content
    to ensure security and data integrity.
    """
    
    @staticmethod
    def validate_content_type(content_type: str) -> bool:
        """
        Validate content type against allowed types.
        
        Args:
            content_type: Content type to validate
            
        Returns:
            True if content type is allowed, False otherwise
        """
        if not content_type:
            return False
        
        # Extract main content type (ignore charset, etc.)
        main_type = content_type.split(';')[0].strip().lower()
        
        return main_type in ALLOWED_MIME_TYPES
    
    @staticmethod
    def validate_user_agent(user_agent: str) -> bool:
        """
        Validate user agent string for suspicious patterns.
        
        Args:
            user_agent: User agent string to validate
            
        Returns:
            True if user agent appears legitimate, False otherwise
        """
        if not user_agent:
            return False
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'sqlmap',
            r'nikto',
            r'nmap',
            r'masscan',
            r'dirb',
            r'gobuster',
            r'wfuzz',
            r'burp',
        ]
        
        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent_lower):
                logger.warning(f"Suspicious user agent detected: {user_agent}")
                return False
        
        return True
    
    @staticmethod
    def validate_request_size(content_length: int, max_size: int = 10 * 1024 * 1024) -> bool:
        """
        Validate request content length.
        
        Args:
            content_length: Content length in bytes
            max_size: Maximum allowed size in bytes (default 10MB)
            
        Returns:
            True if size is within limits, False otherwise
        """
        return 0 <= content_length <= max_size


def create_security_headers() -> Dict[str, str]:
    """
    Create security headers for API responses.
    
    Returns:
        Dictionary of security headers
    """
    return {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'none'; frame-ancestors 'none'",
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }


def log_security_event(event_type: str, details: Dict[str, Any], request_id: str = None) -> None:
    """
    Log security-related events for monitoring and alerting.
    
    Args:
        event_type: Type of security event
        details: Event details
        request_id: Associated request ID if available
    """
    log_data = {
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        'details': details
    }
    
    if request_id:
        log_data['request_id'] = request_id
    
    logger.warning(f"Security event [{event_type}]: {log_data}")


# Utility functions for common sanitization tasks
def sanitize_search_term(search_term: Optional[str]) -> str:
    """
    Sanitize search term to prevent SQL injection and other attacks.
    
    This is a convenience function that uses the InputSanitizer.sanitize_search_query
    method to sanitize search terms. It handles None/empty inputs safely.
    
    Args:
        search_term: Search term to sanitize (can be None or empty)
        
    Returns:
        Sanitized search term (empty string if input was None/empty)
    """
    if not search_term:
        return ""
    
    try:
        return InputSanitizer.sanitize_search_query(str(search_term))
    except SecurityError as e:
        logger.warning(f"Search term sanitization failed: {e}")
        # Return empty string if sanitization fails to prevent potential attacks
        return ""


def sanitize_person_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize person-specific data with appropriate rules.
    
    Args:
        data: Person data dictionary
        
    Returns:
        Sanitized person data
    """
    sanitizer = InputSanitizer()
    sanitized = {}
    
    # Email fields
    email_fields = ['email']
    for field in email_fields:
        if field in data and data[field]:
            try:
                sanitized[field] = sanitizer.sanitize_email(data[field])
            except SecurityError as e:
                logger.warning(f"Email sanitization failed for field {field}: {e}")
                sanitized[field] = None
    
    # Phone fields
    phone_fields = ['phone', 'mobile', 'emergency_contact_phone']
    for field in phone_fields:
        if field in data and data[field]:
            try:
                sanitized[field] = sanitizer.sanitize_phone(data[field])
            except SecurityError as e:
                logger.warning(f"Phone sanitization failed for field {field}: {e}")
                sanitized[field] = None
    
    # String fields - use safe sanitization that escapes rather than raises errors
    string_fields = ['first_name', 'last_name', 'title', 'suffix', 'gender', 'marital_status',
                     'address', 'city', 'state', 'zip_code', 'country', 'emergency_contact_name', 'status']
    for field in string_fields:
        if field in data and data[field]:
            sanitized[field] = sanitizer._sanitize_string_for_list(data[field], max_length=200)
    
    # Text fields - use safe sanitization that escapes rather than raises errors
    text_fields = ['notes']
    for field in text_fields:
        if field in data and data[field]:
            sanitized[field] = sanitizer._sanitize_string_for_list(data[field], max_length=MAX_TEXT_LENGTH)
    
    # List fields
    list_fields = ['tags']
    for field in list_fields:
        if field in data and data[field]:
            if isinstance(data[field], list):
                sanitized[field] = sanitizer.sanitize_list(data[field])
            else:
                logger.warning(f"Expected list for field {field}, got {type(data[field])}")
                sanitized[field] = []
    
    # Date fields (should be handled by Pydantic validation)
    date_fields = ['date_of_birth']
    for field in date_fields:
        if field in data:
            sanitized[field] = data[field]  # Let Pydantic handle date validation
    
    return sanitized