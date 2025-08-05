"""
Common Pydantic schemas for the People Management System API.

This module contains base schemas and common response models used
across different API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID
from pydantic import BaseModel, Field

# Generic type for paginated responses
T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        orm_mode = True
        use_enum_values = True
        validate_assignment = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class TimestampSchema(BaseSchema):
    """Schema for models with timestamps."""
    
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    
    page: int = Field(..., ge=1, description="Current page number")
    size: int = Field(..., ge=1, description="Page size")
    total: int = Field(..., ge=0, description="Total number of items")
    pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    
    items: List[T] = Field(..., description="List of items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class SuccessResponse(BaseModel):
    """Generic success response."""
    
    success: bool = Field(True, description="Success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")


class ErrorResponse(BaseModel):
    """Generic error response."""
    
    error: bool = Field(True, description="Error status")
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")


class ValidationErrorDetail(BaseModel):
    """Validation error detail."""
    
    field: str = Field(..., description="Field name that failed validation")
    message: str = Field(..., description="Validation error message")
    type: str = Field(..., description="Validation error type")
    input: Optional[Any] = Field(None, description="Invalid input value")


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    
    error: bool = Field(True, description="Error status")
    message: str = Field("Validation failed", description="Error message")
    errors: List[ValidationErrorDetail] = Field(..., description="List of validation errors")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="API version")
    database_connected: bool = Field(..., description="Database connection status")
    uptime_seconds: float = Field(..., description="Uptime in seconds")


class DatabaseHealthResponse(BaseModel):
    """Database health check response."""
    
    database_connected: bool = Field(..., description="Database connection status")
    tables_exist: bool = Field(..., description="Whether required tables exist")
    can_read: bool = Field(..., description="Whether database can be read from")
    can_write: bool = Field(..., description="Whether database can be written to")
    errors: List[str] = Field(default_factory=list, description="List of health check errors")


class StatisticsResponse(BaseModel):
    """Statistics response."""
    
    total_people: int = Field(..., ge=0, description="Total number of people")
    active_employees: int = Field(..., ge=0, description="Number of active employees")
    total_departments: int = Field(..., ge=0, description="Total number of departments")
    total_positions: int = Field(..., ge=0, description="Total number of positions")
    average_salary: Optional[float] = Field(None, ge=0, description="Average salary")
    employment_statistics: Dict[str, Any] = Field(..., description="Employment statistics")


class SearchResponse(BaseModel, Generic[T]):
    """Generic search response."""
    
    query: Optional[str] = Field(None, description="Search query")
    results: List[T] = Field(..., description="Search results")
    total_results: int = Field(..., ge=0, description="Total number of results")
    search_time_ms: float = Field(..., ge=0, description="Search time in milliseconds")


class BulkOperationResponse(BaseModel):
    """Bulk operation response."""
    
    success_count: int = Field(..., ge=0, description="Number of successful operations")
    error_count: int = Field(..., ge=0, description="Number of failed operations")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="List of errors")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional operation details")


class FileUploadResponse(BaseModel):
    """File upload response."""
    
    filename: str = Field(..., description="Uploaded filename")
    size: int = Field(..., ge=0, description="File size in bytes")
    content_type: str = Field(..., description="File content type")
    upload_timestamp: datetime = Field(..., description="Upload timestamp")
    url: Optional[str] = Field(None, description="File access URL")


# Request/Response helpers
def create_success_response(message: str, data: Optional[Dict[str, Any]] = None) -> SuccessResponse:
    """Create a success response."""
    return SuccessResponse(message=message, data=data)


def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """Create an error response."""
    return ErrorResponse(
        message=message,
        error_code=error_code,
        details=details
    )


def create_paginated_response(
    items: List[T],
    page: int,
    size: int,
    total: int
) -> PaginatedResponse[T]:
    """Create a paginated response."""
    pages = (total + size - 1) // size  # Ceiling division
    
    meta = PaginationMeta(
        page=page,
        size=size,
        total=total,
        pages=pages,
        has_next=page < pages,
        has_prev=page > 1
    )
    
    return PaginatedResponse(items=items, meta=meta)


# Common field validators and examples
def get_uuid_field(**kwargs) -> UUID:
    """Get a UUID field with common configuration."""
    return Field(
        ...,
        description=kwargs.get('description', 'Unique identifier'),
        example=kwargs.get('example', '123e4567-e89b-12d3-a456-426614174000')
    )


def get_name_field(description: str, max_length: int = 100, **kwargs) -> str:
    """Get a name field with common validation."""
    return Field(
        ...,
        min_length=1,
        max_length=max_length,
        description=description,
        **kwargs
    )


def get_email_field(**kwargs) -> str:
    """Get an email field with common validation."""
    return Field(
        ...,
        max_length=254,
        regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        description='Valid email address',
        example='john.doe@example.com',
        **kwargs
    )


def get_optional_text_field(description: str, max_length: int = 1000, **kwargs) -> Optional[str]:
    """Get an optional text field with common validation."""
    return Field(
        None,
        max_length=max_length,
        description=description,
        **kwargs
    )