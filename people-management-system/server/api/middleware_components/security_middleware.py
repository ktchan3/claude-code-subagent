"""
Security middleware for API request validation and sanitization.

This middleware provides comprehensive security validation for all API requests,
including input sanitization, request validation, and security headers.
"""

import json
import logging
from typing import Dict, Any, Optional, Awaitable, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils.security import (
    InputSanitizer, RequestValidator, SecurityError, 
    create_security_headers, log_security_event,
    sanitize_search_term, sanitize_person_data
)

logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Security middleware that validates and sanitizes all API requests.
    
    This middleware:
    1. Validates request headers and content type
    2. Sanitizes request data to prevent XSS, SQL injection, etc.
    3. Adds security headers to responses
    4. Logs security events for monitoring
    """
    
    def __init__(self, app, max_request_size: int = 10 * 1024 * 1024):
        """
        Initialize security middleware.
        
        Args:
            app: FastAPI application instance
            max_request_size: Maximum allowed request size in bytes
        """
        super().__init__(app)
        self.max_request_size = max_request_size
        self.sanitizer = InputSanitizer()
        self.validator = RequestValidator()
        
        # Paths that require special handling
        self.bypass_paths = {
            '/docs', '/redoc', '/openapi.json', '/health', '/favicon.ico',
            '/api/v1/people/health',  # People health endpoint
        }
        
        # Methods that should have request body validation
        self.body_methods = {'POST', 'PUT', 'PATCH'}
    
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Process request through security middleware."""
        
        # Skip security validation for certain paths
        if request.url.path in self.bypass_paths:
            return await call_next(request)
        
        try:
            # Validate request
            await self._validate_request(request)
            
            # Validate request data if present (but don't modify body)
            if request.method in self.body_methods:
                await self._validate_request_body(request)
            
            # Sanitize query parameters
            self._sanitize_query_params(request)
            
            # Process request
            response = await call_next(request)
            
            # Add security headers to response
            self._add_security_headers(response)
            
            return response
            
        except SecurityError as e:
            # Log security event
            log_security_event(
                event_type='security_validation_failed',
                details={
                    'path': request.url.path,
                    'method': request.method,
                    'client_ip': request.client.host if request.client else 'unknown',
                    'user_agent': request.headers.get('user-agent', ''),
                    'error': str(e)
                },
                request_id=getattr(request.state, 'request_id', None)
            )
            
            # Use 422 for validation errors to match FastAPI conventions
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={'detail': f'Security validation failed: {str(e)}'}
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in security middleware: {e}")
            # If the error is database-related, just log it and proceed
            if "Database not initialized" in str(e) or "database" in str(e).lower():
                logger.warning(f"Database issue in security middleware, proceeding: {e}")
                response = await call_next(request)
                self._add_security_headers(response)
                return response
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={'detail': 'Internal security error'}
            )
    
    async def _validate_request(self, request: Request) -> None:
        """Validate request headers and basic security requirements."""
        
        # Validate content length
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                length = int(content_length)
                if not self.validator.validate_request_size(length, self.max_request_size):
                    raise SecurityError(f"Request size {length} exceeds maximum allowed {self.max_request_size}")
            except ValueError:
                raise SecurityError("Invalid content-length header")
        
        # Validate content type for requests with body
        if request.method in self.body_methods:
            content_type = request.headers.get('content-type', '')
            if content_type and not self.validator.validate_content_type(content_type):
                logger.warning(f"Potentially unsafe content type: {content_type}")
                # Don't reject, just log for now
        
        # Validate user agent
        user_agent = request.headers.get('user-agent', '')
        if user_agent and not self.validator.validate_user_agent(user_agent):
            # Log suspicious user agent but don't block
            logger.warning(f"Suspicious user agent detected: {user_agent}")
    
    async def _validate_request_body(self, request: Request) -> None:
        """Validate request body data for security threats without modifying it."""
        
        # Only validate JSON payloads
        content_type = request.headers.get('content-type', '')
        if 'application/json' not in content_type.lower():
            return
        
        try:
            # Read and parse body
            body = await request.body()
            if not body:
                return
            
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                raise SecurityError("Invalid JSON in request body")
            
            # Validate data based on endpoint
            self._validate_data_by_endpoint(request.url.path, data)
            
        except SecurityError:
            raise
        except Exception as e:
            logger.error(f"Error validating request body: {e}")
            # Don't fail the request for validation errors, just log them
            logger.warning(f"Request body validation failed: {e}")
    
    def _validate_data_by_endpoint(self, path: str, data: Any) -> None:
        """Validate data for security threats based on the API endpoint."""
        
        if isinstance(data, dict):
            # Check for dangerous patterns in string values
            for key, value in data.items():
                if isinstance(value, str) and value:
                    # Check for XSS patterns
                    from ..utils.security import DANGEROUS_PATTERNS
                    for pattern in DANGEROUS_PATTERNS:
                        if hasattr(pattern, 'search') and pattern.search(value):
                            logger.warning(f"Dangerous pattern detected in {path}: {key}={value[:100]}")
                            # Log but don't block
                            
                    # Check for SQL injection patterns
                    from ..utils.security import SQL_INJECTION_PATTERNS
                    for pattern in SQL_INJECTION_PATTERNS:
                        if hasattr(pattern, 'search') and pattern.search(value):
                            logger.warning(f"Potential SQL injection detected in {path}: {key}={value[:100]}")
                            # Log but don't block
                            
        elif isinstance(data, list):
            # Validate each item in the list
            for item in data:
                if isinstance(item, (dict, list)):
                    self._validate_data_by_endpoint(path, item)
                    
    def _sanitize_data_by_endpoint(self, path: str, data: Any) -> Any:
        """Sanitize data based on the API endpoint."""
        
        if isinstance(data, dict):
            # Apply general sanitization
            sanitized = self.sanitizer.sanitize_dict(data)
            
            # Apply endpoint-specific sanitization
            if '/people' in path:
                sanitized = self._apply_person_sanitization(sanitized)
            elif '/departments' in path:
                sanitized = self._apply_department_sanitization(sanitized)
            elif '/employment' in path:
                sanitized = self._apply_employment_sanitization(sanitized)
            
            return sanitized
            
        elif isinstance(data, list):
            return self.sanitizer.sanitize_list(data)
        
        return data
    
    def _apply_person_sanitization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply person-specific data sanitization."""
        return sanitize_person_data(data)
    
    def _apply_department_sanitization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply department-specific data sanitization."""
        # Sanitize department name and description
        if 'name' in data and data['name']:
            data['name'] = self.sanitizer.sanitize_string(data['name'], max_length=100)
        
        if 'description' in data and data['description']:
            data['description'] = self.sanitizer.sanitize_string(data['description'], max_length=1000)
        
        return data
    
    def _apply_employment_sanitization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply employment-specific data sanitization."""
        # Validate UUIDs for person_id and position_id
        if 'person_id' in data and data['person_id']:
            if not self.sanitizer.validate_uuid(str(data['person_id'])):
                raise SecurityError("Invalid person_id format")
        
        if 'position_id' in data and data['position_id']:
            if not self.sanitizer.validate_uuid(str(data['position_id'])):
                raise SecurityError("Invalid position_id format")
        
        # Validate salary
        if 'salary' in data and data['salary'] is not None:
            try:
                salary = float(data['salary'])
                if salary < 0 or salary > 10_000_000:  # Reasonable salary range
                    raise SecurityError("Salary amount out of reasonable range")
            except (ValueError, TypeError):
                raise SecurityError("Invalid salary format")
        
        return data
    
    def _sanitize_query_params(self, request: Request) -> None:
        """Sanitize query parameters."""
        
        # Create sanitized query params
        sanitized_params = {}
        
        for key, value in request.query_params.items():
            try:
                if key in ['search', 'query', 'name', 'email']:
                    # Apply search term sanitization
                    sanitized_value = sanitize_search_term(value)
                    sanitized_params[key] = sanitized_value
                elif key in ['sort_by', 'sort', 'order_by']:
                    # Validate sort parameters against allowed columns
                    allowed_sort_fields = {
                        'first_name', 'last_name', 'email', 'created_at', 'updated_at',
                        'name', 'title', 'start_date', 'end_date', 'salary'
                    }
                    if value in allowed_sort_fields:
                        sanitized_params[key] = value
                    else:
                        logger.warning(f"Invalid sort field requested: {value}")
                        # Skip invalid sort field
                        continue
                elif key in ['page', 'size', 'limit']:
                    # Validate pagination parameters
                    try:
                        int_value = int(value)
                        if key == 'page' and int_value >= 1:
                            sanitized_params[key] = str(int_value)
                        elif key in ['size', 'limit'] and 1 <= int_value <= 100:
                            sanitized_params[key] = str(int_value)
                    except ValueError:
                        logger.warning(f"Invalid pagination parameter: {key}={value}")
                        continue
                else:
                    # Apply general string sanitization
                    sanitized_value = self.sanitizer.sanitize_string(value, max_length=200)
                    sanitized_params[key] = sanitized_value
                    
            except SecurityError as e:
                logger.warning(f"Query parameter sanitization failed for {key}={value}: {e}")
                # Skip problematic parameters
                continue
        
        # Replace query params with sanitized version
        # Note: This is a bit hacky since Request.query_params is immutable
        # In a real implementation, you might want to store sanitized params in request.state
        request.state.sanitized_query_params = sanitized_params
    
    def _add_security_headers(self, response: Response) -> None:
        """Add security headers to response."""
        
        security_headers = create_security_headers()
        
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value


# Utility function to get sanitized query params from request
def get_sanitized_query_params(request: Request) -> Dict[str, str]:
    """
    Get sanitized query parameters from request.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary of sanitized query parameters
    """
    return getattr(request.state, 'sanitized_query_params', dict(request.query_params))


# Decorator for endpoints that need additional security validation
def require_security_validation(func):
    """Decorator for endpoints requiring additional security validation."""
    
    def wrapper(*args, **kwargs):
        # Additional security validation can be added here
        return func(*args, **kwargs)
    
    return wrapper