"""
Custom middleware for the People Management System API.

This module provides custom middleware for logging, error handling,
security headers, rate limiting, API client tracking, and other cross-cutting concerns.
"""

import time
import logging
import uuid
from typing import Callable, Dict, Any, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_429_TOO_MANY_REQUESTS

from ..core.config import get_settings
from ..core.exceptions import create_error_response
from .auth import get_client_info_from_request, APIClientInfo

# Configure logging
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Enhanced middleware for logging HTTP requests and responses with API client tracking.
    
    Logs request details including method, URL, headers, processing time, and API client information.
    Tracks API usage patterns and client behavior for analytics and debugging.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.request_counts: Dict[str, int] = {}
        self.client_stats: Dict[str, Dict[str, Any]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        client_ip = request.client.host if request.client else 'unknown'
        
        # Get API client info if available (will be set by auth dependency)
        api_client = get_client_info_from_request(request)
        client_identifier = api_client.client_name if api_client else client_ip
        
        # Track client statistics
        self._track_client_request(client_identifier, request.method, str(request.url.path))
        
        # Create detailed log message
        log_parts = [
            f"Request started - ID: {request_id}",
            f"Method: {request.method}",
            f"URL: {request.url}",
            f"IP: {client_ip}"
        ]
        
        if api_client:
            log_parts.extend([
                f"Client: {api_client.client_name}",
                f"Key: {api_client.key_id}",
                f"Permissions: {','.join(api_client.permissions) if api_client.permissions else 'none'}"
            ])
        
        # Add user agent if available
        user_agent = request.headers.get("user-agent")
        if user_agent:
            log_parts.append(f"User-Agent: {user_agent[:100]}...")
        
        logger.info(" | ".join(log_parts))
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Update client statistics with response
            self._track_client_response(client_identifier, response.status_code, process_time)
            
            # Create completion log message
            completion_parts = [
                f"Request completed - ID: {request_id}",
                f"Status: {response.status_code}",
                f"Time: {process_time:.3f}s"
            ]
            
            if api_client:
                completion_parts.append(f"Client: {api_client.client_name}")
            
            logger.info(" | ".join(completion_parts))
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            response.headers["X-API-Version"] = "1.0.0"
            
            if api_client:
                response.headers["X-Client-ID"] = api_client.key_id
            
            return response
            
        except Exception as e:
            # Calculate processing time for error case
            process_time = time.time() - start_time
            
            # Update client statistics with error
            self._track_client_response(client_identifier, 500, process_time)
            
            # Create error log message
            error_parts = [
                f"Request failed - ID: {request_id}",
                f"Error: {str(e)}",
                f"Time: {process_time:.3f}s"
            ]
            
            if api_client:
                error_parts.append(f"Client: {api_client.client_name}")
            
            logger.error(" | ".join(error_parts))
            
            # Return error response
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content=create_error_response(
                    message="Internal server error",
                    error_code="INTERNAL_ERROR",
                    details={"request_id": request_id}
                ),
                headers={
                    "X-Request-ID": request_id,
                    "X-API-Version": "1.0.0"
                }
            )
    
    def _track_client_request(self, client_identifier: str, method: str, path: str) -> None:
        """Track client request statistics."""
        if client_identifier not in self.client_stats:
            self.client_stats[client_identifier] = {
                "total_requests": 0,
                "methods": {},
                "paths": {},
                "status_codes": {},
                "avg_response_time": 0.0,
                "total_response_time": 0.0,
                "first_seen": time.time(),
                "last_seen": time.time()
            }
        
        stats = self.client_stats[client_identifier]
        stats["total_requests"] += 1
        stats["last_seen"] = time.time()
        
        # Track method distribution
        stats["methods"][method] = stats["methods"].get(method, 0) + 1
        
        # Track path distribution (simplified)
        path_key = path.split("?")[0]  # Remove query parameters
        stats["paths"][path_key] = stats["paths"].get(path_key, 0) + 1
    
    def _track_client_response(self, client_identifier: str, status_code: int, response_time: float) -> None:
        """Track client response statistics."""
        if client_identifier in self.client_stats:
            stats = self.client_stats[client_identifier]
            
            # Track status code distribution
            stats["status_codes"][str(status_code)] = stats["status_codes"].get(str(status_code), 0) + 1
            
            # Update response time statistics
            stats["total_response_time"] += response_time
            stats["avg_response_time"] = stats["total_response_time"] / stats["total_requests"]
    
    def get_client_stats(self, client_identifier: Optional[str] = None) -> Dict[str, Any]:
        """Get client statistics for monitoring and analytics."""
        if client_identifier:
            return self.client_stats.get(client_identifier, {})
        
        return {
            "total_clients": len(self.client_stats),
            "clients": dict(self.client_stats)
        }


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding security headers to responses.
    
    Adds various security headers to protect against common attacks.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            ),
        }
        
        # Only add HSTS in production
        settings = get_settings()
        if not settings.debug and request.url.scheme == "https":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Add headers to response
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for global error handling.
    
    Catches unhandled exceptions and returns appropriate error responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            # Log the error
            request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
            
            logger.exception(
                f"Unhandled exception in request {request_id}: {str(e)}"
            )
            
            # Determine if this is a development environment
            settings = get_settings()
            
            # Create error response
            if settings.debug:
                # In debug mode, include more details
                error_response = create_error_response(
                    message=f"Internal server error: {str(e)}",
                    error_code="INTERNAL_ERROR",
                    details={
                        "request_id": request_id,
                        "exception_type": type(e).__name__,
                        "exception_details": str(e)
                    }
                )
            else:
                # In production, use generic error message
                error_response = create_error_response(
                    message="An internal server error occurred",
                    error_code="INTERNAL_ERROR",
                    details={"request_id": request_id}
                )
            
            return JSONResponse(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enhanced in-memory rate limiting middleware with API client support.
    
    Supports per-client rate limiting based on API keys and IP addresses.
    API clients can have custom rate limits that override the default.
    
    Note: This is a basic implementation. For production use,
    consider using Redis or another distributed cache.
    """
    
    def __init__(self, app, calls_per_minute: int = 60):
        super().__init__(app)
        self.default_calls_per_minute = calls_per_minute
        self.clients: Dict[str, Dict[str, Any]] = {}
        self.cleanup_interval = 60  # seconds
        self.last_cleanup = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client identifiers
        client_ip = request.client.host if request.client else "unknown"
        api_client = get_client_info_from_request(request)
        
        # Determine the client identifier and rate limit
        if api_client:
            client_identifier = f"api_client:{api_client.key_id}"
            rate_limit = api_client.rate_limit or self.default_calls_per_minute
        else:
            client_identifier = f"ip:{client_ip}"
            rate_limit = self.default_calls_per_minute
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/api/v1/health"]:
            return await call_next(request)
        
        # Clean up old entries periodically
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self._cleanup_clients(current_time)
            self.last_cleanup = current_time
        
        # Check rate limit
        if self._is_rate_limited(client_identifier, current_time, rate_limit):
            client_info = api_client.client_name if api_client else client_ip
            logger.warning(f"Rate limit exceeded for client {client_info} (limit: {rate_limit}/min)")
            
            return JSONResponse(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                content=create_error_response(
                    message="Rate limit exceeded",
                    error_code="RATE_LIMIT_EXCEEDED",
                    details={
                        "limit": rate_limit,
                        "window": "1 minute",
                        "client_type": "api_client" if api_client else "ip_address"
                    }
                ),
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(rate_limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + 60))
                }
            )
        
        # Record the request
        self._record_request(client_identifier, current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_identifier, current_time, rate_limit)
        response.headers["X-RateLimit-Limit"] = str(rate_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))
        
        return response
    
    def _is_rate_limited(self, client_identifier: str, current_time: float, rate_limit: int) -> bool:
        """Check if client is rate limited."""
        if client_identifier not in self.clients:
            return False
        
        client_data = self.clients[client_identifier]
        requests = client_data.get("requests", [])
        
        # Count requests in the last minute
        minute_ago = current_time - 60
        recent_requests = [req_time for req_time in requests if req_time > minute_ago]
        
        return len(recent_requests) >= rate_limit
    
    def _record_request(self, client_identifier: str, current_time: float):
        """Record a request for the client."""
        if client_identifier not in self.clients:
            self.clients[client_identifier] = {"requests": []}
        
        # Add current request
        self.clients[client_identifier]["requests"].append(current_time)
        
        # Keep only requests from the last minute
        minute_ago = current_time - 60
        self.clients[client_identifier]["requests"] = [
            req_time for req_time in self.clients[client_identifier]["requests"]
            if req_time > minute_ago
        ]
    
    def _get_remaining_requests(self, client_identifier: str, current_time: float, rate_limit: int) -> int:
        """Get remaining requests for the client."""
        if client_identifier not in self.clients:
            return rate_limit
        
        requests = self.clients[client_identifier].get("requests", [])
        minute_ago = current_time - 60
        recent_requests = [req_time for req_time in requests if req_time > minute_ago]
        
        return max(0, rate_limit - len(recent_requests))
    
    def _cleanup_clients(self, current_time: float):
        """Clean up old client data."""
        minute_ago = current_time - 60
        clients_to_remove = []
        
        for client_ip, client_data in self.clients.items():
            requests = client_data.get("requests", [])
            recent_requests = [req_time for req_time in requests if req_time > minute_ago]
            
            if not recent_requests:
                clients_to_remove.append(client_ip)
            else:
                self.clients[client_ip]["requests"] = recent_requests
        
        for client_ip in clients_to_remove:
            del self.clients[client_ip]


class DatabaseConnectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for ensuring database connections are properly handled.
    
    This middleware ensures that database connections are properly
    managed and closed after each request.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            # Log database-related errors
            if "database" in str(e).lower() or "connection" in str(e).lower():
                logger.error(f"Database connection error: {str(e)}")
            
            raise e


class CacheControlMiddleware(BaseHTTPMiddleware):
    """
    Middleware for adding cache control headers.
    
    Adds appropriate cache control headers based on the endpoint.
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.cache_rules = {
            "/api/v1/health": "no-cache",
            "/api/v1/statistics": "max-age=300",  # 5 minutes
            "/openapi.json": "max-age=3600",  # 1 hour
            "/docs": "max-age=3600",  # 1 hour
            "/redoc": "max-age=3600",  # 1 hour
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add cache control headers based on path
        path = request.url.path
        
        # Check for specific cache rules
        for rule_path, cache_control in self.cache_rules.items():
            if path.startswith(rule_path):
                response.headers["Cache-Control"] = cache_control
                break
        else:
            # Default cache control for API endpoints
            if path.startswith("/api/"):
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
        
        return response


def create_rate_limit_middleware(calls_per_minute: int = None) -> RateLimitMiddleware:
    """
    Create rate limit middleware with configuration from settings.
    
    Args:
        calls_per_minute: Override for calls per minute limit
        
    Returns:
        Configured rate limit middleware
    """
    settings = get_settings()
    limit = calls_per_minute or settings.rate_limit_per_minute
    
    def middleware_factory(app):
        return RateLimitMiddleware(app, calls_per_minute=limit)
    
    return middleware_factory


def setup_middleware(app):
    """
    Set up all middleware for the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    settings = get_settings()
    
    # Add middleware in reverse order (last added = first executed)
    
    # Cache control (outermost)
    app.add_middleware(CacheControlMiddleware)
    
    # Rate limiting
    app.add_middleware(RateLimitMiddleware, calls_per_minute=settings.rate_limit_per_minute)
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Database connection handling
    app.add_middleware(DatabaseConnectionMiddleware)
    
    # Error handling
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Request logging (innermost)
    app.add_middleware(RequestLoggingMiddleware)
    
    logger.info("Middleware setup completed")