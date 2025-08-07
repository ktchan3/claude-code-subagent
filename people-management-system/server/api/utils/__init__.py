"""
API utilities package.

This package contains utility functions for the API layer including
formatters, validators, security utilities, and other shared functionality.
"""

from .formatters import (
    format_person_response,
    format_person_summary,
    format_person_with_employment,
    format_employment_response,
    format_employment_summary,
    format_department_response,
    format_position_response,
    format_date_for_api,
    format_bulk_operation_response,
    format_error_response,
    format_health_check_response,
    sanitize_search_term
)
from .security import (
    InputSanitizer,
    RequestValidator,
    SecurityError,
    create_security_headers,
    log_security_event,
    sanitize_person_data
)
from .cache import (
    InMemoryCache,
    get_cache,
    cache_result,
    cache_department_list,
    cache_position_list,
    cache_person_search,
    cache_statistics,
    CacheInvalidator,
    get_cache_health
)

__all__ = [
    # Formatters
    "format_person_response",
    "format_person_summary", 
    "format_person_with_employment",
    "format_employment_response",
    "format_employment_summary",
    "format_department_response",
    "format_position_response",
    "format_date_for_api",
    "format_bulk_operation_response",
    "format_error_response",
    "format_health_check_response",
    "sanitize_search_term",
    # Security utilities
    "InputSanitizer",
    "RequestValidator",
    "SecurityError",
    "create_security_headers",
    "log_security_event",
    "sanitize_person_data",
    # Cache utilities
    "InMemoryCache",
    "get_cache",
    "cache_result",
    "cache_department_list",
    "cache_position_list",
    "cache_person_search",
    "cache_statistics",
    "CacheInvalidator",
    "get_cache_health"
]