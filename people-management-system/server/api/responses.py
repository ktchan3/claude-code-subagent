"""
Standardized API Response Models and Utilities.

This module provides consistent response formats, error handling,
and response utilities for the People Management System API.
"""

import time
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from uuid import UUID
from pydantic import BaseModel, Field
from fastapi import status
from fastapi.responses import JSONResponse

# Type variable for generic responses
T = TypeVar('T')


class APIMetadata(BaseModel):
    """Metadata included in API responses."""
    
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    timestamp: float = Field(default_factory=time.time, description="Response timestamp")
    version: str = Field(default="1.0.0", description="API version")
    server: str = Field(default="people-management-api", description="Server identifier")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable response message")
    data: Optional[T] = Field(None, description="Response data payload")
    errors: Optional[List[str]] = Field(None, description="List of error messages")
    metadata: APIMetadata = Field(default_factory=APIMetadata, description="Response metadata")


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    code: str = Field(..., description="Error code identifier")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ValidationError(BaseModel):
    """Validation error information."""
    
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(None, description="Invalid value that was provided")


class ErrorResponse(BaseModel):
    """Standardized error response format."""
    
    success: bool = Field(False, description="Always false for error responses")
    message: str = Field(..., description="Main error message")
    error_code: str = Field(..., description="Specific error code")
    errors: Optional[List[ErrorDetail]] = Field(None, description="Detailed error list")
    validation_errors: Optional[List[ValidationError]] = Field(None, description="Validation errors")
    metadata: APIMetadata = Field(default_factory=APIMetadata, description="Response metadata")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response format."""
    
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field(default="Data retrieved successfully", description="Response message")
    data: List[T] = Field(..., description="List of items for current page")
    pagination: PaginationMeta = Field(..., description="Pagination information")
    metadata: APIMetadata = Field(default_factory=APIMetadata, description="Response metadata")


class SuccessResponse(BaseModel):
    """Simple success response format."""
    
    success: bool = Field(True, description="Always true for success responses")
    message: str = Field(..., description="Success message")
    metadata: APIMetadata = Field(default_factory=APIMetadata, description="Response metadata")


class HealthResponse(BaseModel):
    """Health check response format."""
    
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    timestamp: float = Field(default_factory=time.time, description="Health check timestamp")
    uptime_seconds: Optional[float] = Field(None, description="Server uptime in seconds")
    components: Dict[str, str] = Field(default_factory=dict, description="Component health status")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health details")


# Response factory functions

def create_success_response(
    message: str,
    data: Optional[T] = None,
    request_id: Optional[str] = None,
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Create a standardized success response."""
    
    metadata = APIMetadata()
    if request_id:
        metadata.request_id = request_id
    
    response_data = APIResponse[T](
        success=True,
        message=message,
        data=data,
        metadata=metadata
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict()
    )


def create_error_response(
    message: str,
    error_code: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    errors: Optional[List[ErrorDetail]] = None,
    validation_errors: Optional[List[ValidationError]] = None,
    request_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response."""
    
    metadata = APIMetadata()
    if request_id:
        metadata.request_id = request_id
    
    response_data = ErrorResponse(
        message=message,
        error_code=error_code,
        errors=errors,
        validation_errors=validation_errors,
        metadata=metadata
    )
    
    return JSONResponse(
        status_code=status_code,
        content=response_data.dict()
    )


def create_validation_error_response(
    message: str = "Validation failed",
    validation_errors: List[ValidationError] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a validation error response."""
    
    return create_error_response(
        message=message,
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        validation_errors=validation_errors or [],
        request_id=request_id
    )


def create_paginated_response(
    items: List[T],
    page: int,
    size: int,
    total: int,
    message: str = "Data retrieved successfully",
    request_id: Optional[str] = None
) -> PaginatedResponse[T]:
    """Create a paginated response."""
    
    total_pages = (total + size - 1) // size if total > 0 else 0
    has_next = page < total_pages
    has_previous = page > 1
    
    pagination_meta = PaginationMeta(
        page=page,
        size=size,
        total=total,
        total_pages=total_pages,
        has_next=has_next,
        has_previous=has_previous
    )
    
    metadata = APIMetadata()
    if request_id:
        metadata.request_id = request_id
    
    return PaginatedResponse[T](
        success=True,
        message=message,
        data=items,
        pagination=pagination_meta,
        metadata=metadata
    )


def create_health_response(
    status: str,
    version: str,
    uptime_seconds: Optional[float] = None,
    components: Optional[Dict[str, str]] = None,
    details: Optional[Dict[str, Any]] = None
) -> HealthResponse:
    """Create a health check response."""
    
    return HealthResponse(
        status=status,
        version=version,
        uptime_seconds=uptime_seconds,
        components=components or {},
        details=details
    )


# HTTP Exception mappers

def map_http_exception_to_error_response(
    status_code: int,
    detail: str,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Map HTTP exceptions to standardized error responses."""
    
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED", 
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = error_code_map.get(status_code, "UNKNOWN_ERROR")
    
    return create_error_response(
        message=detail,
        error_code=error_code,
        status_code=status_code,
        request_id=request_id
    )


# Domain-specific error responses

def create_not_found_response(
    resource: str,
    identifier: Union[str, UUID],
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a not found error response."""
    
    return create_error_response(
        message=f"{resource} not found",
        error_code="RESOURCE_NOT_FOUND",
        status_code=status.HTTP_404_NOT_FOUND,
        errors=[ErrorDetail(
            code="NOT_FOUND",
            message=f"{resource} with identifier '{identifier}' was not found",
            details={"resource": resource, "identifier": str(identifier)}
        )],
        request_id=request_id
    )


def create_already_exists_response(
    resource: str,
    field: str,
    value: str,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create an already exists error response."""
    
    return create_error_response(
        message=f"{resource} already exists",
        error_code="RESOURCE_ALREADY_EXISTS",
        status_code=status.HTTP_409_CONFLICT,
        errors=[ErrorDetail(
            code="ALREADY_EXISTS",
            message=f"{resource} with {field} '{value}' already exists",
            field=field,
            details={"resource": resource, "field": field, "value": value}
        )],
        request_id=request_id
    )


def create_unauthorized_response(
    message: str = "Authentication required",
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create an unauthorized error response."""
    
    return create_error_response(
        message=message,
        error_code="UNAUTHORIZED",
        status_code=status.HTTP_401_UNAUTHORIZED,
        request_id=request_id
    )


def create_forbidden_response(
    message: str = "Access forbidden",
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a forbidden error response."""
    
    return create_error_response(
        message=message,
        error_code="FORBIDDEN",
        status_code=status.HTTP_403_FORBIDDEN,
        request_id=request_id
    )


def create_rate_limit_response(
    limit: int,
    window: str = "1 minute",
    retry_after: int = 60,
    request_id: Optional[str] = None
) -> JSONResponse:
    """Create a rate limit error response."""
    
    response = create_error_response(
        message="Rate limit exceeded",
        error_code="RATE_LIMITED",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        errors=[ErrorDetail(
            code="RATE_LIMITED",
            message=f"Too many requests. Limit: {limit} per {window}",
            details={"limit": limit, "window": window, "retry_after": retry_after}
        )],
        request_id=request_id
    )
    
    # Add rate limit headers
    response.headers.update({
        "Retry-After": str(retry_after),
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int(time.time() + retry_after))
    })
    
    return response


# Utility functions for response enhancement

def add_request_id_to_response(response: JSONResponse, request_id: str) -> JSONResponse:
    """Add request ID to response headers."""
    response.headers["X-Request-ID"] = request_id
    return response


def add_api_version_to_response(response: JSONResponse, version: str) -> JSONResponse:
    """Add API version to response headers."""
    response.headers["X-API-Version"] = version
    return response


def add_processing_time_to_response(response: JSONResponse, processing_time: float) -> JSONResponse:
    """Add processing time to response headers."""
    response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
    return response


# Export all public classes and functions
__all__ = [
    # Models
    "APIResponse",
    "ErrorResponse", 
    "PaginatedResponse",
    "SuccessResponse",
    "HealthResponse",
    "ErrorDetail",
    "ValidationError",
    "PaginationMeta",
    "APIMetadata",
    
    # Factory functions
    "create_success_response",
    "create_error_response",
    "create_validation_error_response",
    "create_paginated_response",
    "create_health_response",
    
    # Specialized responses
    "create_not_found_response",
    "create_already_exists_response",
    "create_unauthorized_response",
    "create_forbidden_response",
    "create_rate_limit_response",
    
    # Utilities
    "map_http_exception_to_error_response",
    "add_request_id_to_response",
    "add_api_version_to_response",
    "add_processing_time_to_response"
]