"""
Middleware package for the People Management System API.

This package contains all middleware components including security,
logging, rate limiting, and other cross-cutting concerns.
"""

from .security_middleware import SecurityMiddleware

# The setup_middleware function and other middleware classes
# are in server.api.middleware module and should be imported
# directly from there when needed

__all__ = ['SecurityMiddleware']