"""
FastAPI dependencies for the People Management System API.

This module provides common dependencies for database sessions, pagination,
authentication, and other shared functionality used across API endpoints.
"""

from typing import Optional, Generator, Tuple
from fastapi import Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from ..database.db import get_db
from ..core.config import get_settings, Settings
from ..core.exceptions import HTTPBadRequestError


def get_database_session() -> Generator[Session, None, None]:
    """
    Get database session dependency.
    
    This dependency provides a database session that is automatically
    closed after the request is processed.
    
    Yields:
        Database session
    """
    yield from get_db()


def get_app_settings() -> Settings:
    """
    Get application settings dependency.
    
    Returns:
        Application settings instance
    """
    return get_settings()


class PaginationParams:
    """
    Pagination parameters for list endpoints.
    
    Provides standardized pagination with configurable page size limits.
    """
    
    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number (starts from 1)"),
        size: int = Query(20, ge=1, le=100, description="Page size (1-100)"),
        settings: Settings = Depends(get_app_settings)
    ):
        # Validate page size against settings
        if size > settings.max_page_size:
            raise HTTPBadRequestError(f"Page size cannot exceed {settings.max_page_size}")
        
        self.page = page
        self.size = size
        self.offset = (page - 1) * size
        self.limit = size
    
    def get_offset_limit(self) -> Tuple[int, int]:
        """
        Get offset and limit for database queries.
        
        Returns:
            Tuple of (offset, limit)
        """
        return self.offset, self.limit


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    size: int = Query(20, ge=1, le=100, description="Page size (1-100)"),
    settings: Settings = Depends(get_app_settings)
) -> PaginationParams:
    """
    Get pagination parameters dependency.
    
    Args:
        page: Page number (starts from 1)
        size: Page size (1-100)
        settings: Application settings
        
    Returns:
        Pagination parameters instance
        
    Raises:
        HTTPException: If page size exceeds maximum allowed
    """
    return PaginationParams(page, size, settings)


class SearchParams:
    """
    Search parameters for filtering endpoints.
    
    Provides standardized search functionality with query string support.
    """
    
    def __init__(
        self,
        q: Optional[str] = Query(None, min_length=1, max_length=100, description="Search query"),
        sort_by: Optional[str] = Query(None, description="Field to sort by"),
        sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order (asc or desc)")
    ):
        self.query = q.strip() if q else None
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        self.is_descending = sort_order.lower() == "desc"


def get_search_params(
    q: Optional[str] = Query(None, min_length=1, max_length=100, description="Search query"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order (asc or desc)")
) -> SearchParams:
    """
    Get search parameters dependency.
    
    Args:
        q: Search query string
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)
        
    Returns:
        Search parameters instance
    """
    return SearchParams(q, sort_by, sort_order)


def validate_uuid_format(uuid_str: str) -> str:
    """
    Validate UUID format dependency.
    
    Args:
        uuid_str: UUID string to validate
        
    Returns:
        Validated UUID string
        
    Raises:
        HTTPException: If UUID format is invalid
    """
    import uuid
    
    try:
        # Try to parse as UUID to validate format
        uuid.UUID(uuid_str)
        return uuid_str
    except ValueError:
        raise HTTPBadRequestError(f"Invalid UUID format: {uuid_str}")


def get_person_id(person_id: str) -> str:
    """
    Validate and get person ID dependency.
    
    Args:
        person_id: Person ID to validate
        
    Returns:
        Validated person ID
    """
    return validate_uuid_format(person_id)


def get_department_id(department_id: str) -> str:
    """
    Validate and get department ID dependency.
    
    Args:
        department_id: Department ID to validate
        
    Returns:
        Validated department ID
    """
    return validate_uuid_format(department_id)


def get_position_id(position_id: str) -> str:
    """
    Validate and get position ID dependency.
    
    Args:
        position_id: Position ID to validate
        
    Returns:
        Validated position ID
    """
    return validate_uuid_format(position_id)


def get_employment_id(employment_id: str) -> str:
    """
    Validate and get employment ID dependency.
    
    Args:
        employment_id: Employment ID to validate
        
    Returns:
        Validated employment ID
    """
    return validate_uuid_format(employment_id)


class DateRangeParams:
    """
    Date range parameters for filtering by date ranges.
    """
    
    def __init__(
        self,
        start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
    ):
        from datetime import datetime
        
        self.start_date = None
        self.end_date = None
        
        if start_date:
            try:
                self.start_date = datetime.fromisoformat(start_date).date()
            except ValueError:
                raise HTTPBadRequestError(f"Invalid start date format: {start_date}. Use YYYY-MM-DD format.")
        
        if end_date:
            try:
                self.end_date = datetime.fromisoformat(end_date).date()
            except ValueError:
                raise HTTPBadRequestError(f"Invalid end date format: {end_date}. Use YYYY-MM-DD format.")
        
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise HTTPBadRequestError("Start date cannot be after end date")


def get_date_range_params(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")
) -> DateRangeParams:
    """
    Get date range parameters dependency.
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        Date range parameters instance
    """
    return DateRangeParams(start_date, end_date)


def get_active_filter(
    active: Optional[bool] = Query(None, description="Filter by active status")
) -> Optional[bool]:
    """
    Get active status filter dependency.
    
    Args:
        active: Optional active status filter
        
    Returns:
        Active status filter
    """
    return active


def validate_email_format(email: str) -> str:
    """
    Validate email format dependency.
    
    Args:
        email: Email address to validate
        
    Returns:
        Validated email address
        
    Raises:
        HTTPException: If email format is invalid
    """
    import re
    
    # Basic email validation regex
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise HTTPBadRequestError(f"Invalid email format: {email}")
    
    return email.lower().strip()


def validate_phone_format(phone: Optional[str]) -> Optional[str]:
    """
    Validate phone number format dependency.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Validated phone number
        
    Raises:
        HTTPException: If phone format is invalid
    """
    if not phone:
        return None
    
    # Remove all non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone))
    
    # Check if we have a reasonable number of digits
    if len(digits_only) < 10 or len(digits_only) > 15:
        raise HTTPBadRequestError(f"Invalid phone number format: {phone}")
    
    return phone.strip()


def validate_salary_amount(salary: Optional[float]) -> Optional[float]:
    """
    Validate salary amount dependency.
    
    Args:
        salary: Salary amount to validate
        
    Returns:
        Validated salary amount
        
    Raises:
        HTTPException: If salary is invalid
    """
    if salary is None:
        return None
    
    if salary < 0:
        raise HTTPBadRequestError("Salary cannot be negative")
    
    if salary > 10_000_000:  # 10 million cap
        raise HTTPBadRequestError("Salary amount is unreasonably high")
    
    return round(salary, 2)


class CommonQueryParams:
    """
    Common query parameters that combine pagination, search, and filtering.
    """
    
    def __init__(
        self,
        pagination: PaginationParams = Depends(get_pagination_params),
        search: SearchParams = Depends(get_search_params),
        date_range: DateRangeParams = Depends(get_date_range_params),
        active: Optional[bool] = Depends(get_active_filter)
    ):
        self.pagination = pagination
        self.search = search
        self.date_range = date_range
        self.active = active


def get_common_query_params(
    pagination: PaginationParams = Depends(get_pagination_params),
    search: SearchParams = Depends(get_search_params),
    date_range: DateRangeParams = Depends(get_date_range_params),
    active: Optional[bool] = Depends(get_active_filter)
) -> CommonQueryParams:
    """
    Get common query parameters dependency.
    
    This combines pagination, search, and filtering parameters
    for use in list endpoints.
    
    Returns:
        Common query parameters instance
    """
    return CommonQueryParams(pagination, search, date_range, active)


# Health check dependency
def check_database_health(db: Session = Depends(get_database_session)) -> bool:
    """
    Check database health dependency.
    
    Args:
        db: Database session
        
    Returns:
        True if database is healthy
        
    Raises:
        HTTPException: If database is unhealthy
    """
    try:
        # Simple query to check database connectivity
        db.execute("SELECT 1")
        return True
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database health check failed: {str(e)}"
        )


# Request size limit dependency
def validate_request_size(
    content_length: Optional[str] = None,
    settings: Settings = Depends(get_app_settings)
):
    """
    Validate request size dependency.
    
    Args:
        content_length: Content-Length header value
        settings: Application settings
        
    Raises:
        HTTPException: If request size exceeds limit
    """
    if content_length:
        try:
            size = int(content_length)
            if size > settings.max_file_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Request size {size} exceeds maximum allowed size {settings.max_file_size}"
                )
        except ValueError:
            # Invalid Content-Length header, let it through
            pass