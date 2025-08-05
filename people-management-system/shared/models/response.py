"""
Shared API response models using Pydantic.

These models standardize API responses between client and server.
"""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

# Type variable for generic response data
T = TypeVar('T')


class APIResponse(BaseModel, Generic[T]):
    """Generic API response model."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Optional[T] = Field(None, description="Response data")
    errors: Optional[list[str]] = Field(None, description="List of error messages")


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")


class ValidationErrorResponse(BaseModel):
    """Response model for validation errors."""
    
    success: bool = Field(False, description="Always false for error responses")
    message: str = Field("Validation error", description="Error message")
    errors: list[ErrorDetail] = Field(..., description="List of validation errors")


class PaginationInfo(BaseModel):
    """Pagination information for list responses."""
    
    page: int = Field(1, ge=1, description="Current page number")
    size: int = Field(10, ge=1, le=100, description="Number of items per page")
    total: int = Field(0, ge=0, description="Total number of items")
    total_pages: int = Field(0, ge=0, description="Total number of pages")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field("Success", description="Response message")
    data: list[T] = Field(default_factory=list, description="List of items")
    pagination: PaginationInfo = Field(..., description="Pagination information")