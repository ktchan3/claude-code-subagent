"""
Custom exceptions for the People Management System API.

This module defines custom exceptions that provide meaningful error messages
and appropriate HTTP status codes for various error conditions.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class PeopleManagementException(Exception):
    """Base exception class for the People Management System."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(PeopleManagementException):
    """Raised when input validation fails."""
    pass


class NotFoundError(PeopleManagementException):
    """Raised when a requested resource is not found."""
    pass


class DuplicateError(PeopleManagementException):
    """Raised when attempting to create a duplicate resource."""
    pass


class BusinessLogicError(PeopleManagementException):
    """Raised when business logic constraints are violated."""
    pass


class DatabaseError(PeopleManagementException):
    """Raised when database operations fail."""
    pass


class AuthenticationError(PeopleManagementException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(PeopleManagementException):
    """Raised when authorization fails."""
    pass


# HTTP Exception classes that inherit from FastAPI's HTTPException
class HTTPNotFoundError(HTTPException):
    """HTTP 404 Not Found exception."""
    
    def __init__(self, detail: str = "Resource not found", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            headers=headers
        )


class HTTPBadRequestError(HTTPException):
    """HTTP 400 Bad Request exception."""
    
    def __init__(self, detail: str = "Bad request", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            headers=headers
        )


class HTTPConflictError(HTTPException):
    """HTTP 409 Conflict exception."""
    
    def __init__(self, detail: str = "Resource conflict", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            headers=headers
        )


class HTTPUnprocessableEntityError(HTTPException):
    """HTTP 422 Unprocessable Entity exception."""
    
    def __init__(self, detail: str = "Unprocessable entity", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            headers=headers
        )


class HTTPInternalServerError(HTTPException):
    """HTTP 500 Internal Server Error exception."""
    
    def __init__(self, detail: str = "Internal server error", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            headers=headers
        )


class HTTPUnauthorizedError(HTTPException):
    """HTTP 401 Unauthorized exception."""
    
    def __init__(self, detail: str = "Unauthorized", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers=headers or {"WWW-Authenticate": "Bearer"}
        )


class HTTPForbiddenError(HTTPException):
    """HTTP 403 Forbidden exception."""
    
    def __init__(self, detail: str = "Forbidden", headers: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers=headers
        )


# Specific domain exceptions
class PersonNotFoundError(HTTPNotFoundError):
    """Raised when a person is not found."""
    
    def __init__(self, person_id: str):
        super().__init__(f"Person with ID '{person_id}' not found")


class DepartmentNotFoundError(HTTPNotFoundError):
    """Raised when a department is not found."""
    
    def __init__(self, department_id: str):
        super().__init__(f"Department with ID '{department_id}' not found")


class PositionNotFoundError(HTTPNotFoundError):
    """Raised when a position is not found."""
    
    def __init__(self, position_id: str):
        super().__init__(f"Position with ID '{position_id}' not found")


class EmploymentNotFoundError(HTTPNotFoundError):
    """Raised when an employment record is not found."""
    
    def __init__(self, employment_id: str):
        super().__init__(f"Employment record with ID '{employment_id}' not found")


class EmailAlreadyExistsError(HTTPConflictError):
    """Raised when attempting to create a person with an existing email."""
    
    def __init__(self, email: str):
        super().__init__(f"A person with email '{email}' already exists")


class DepartmentNameExistsError(HTTPConflictError):
    """Raised when attempting to create a department with an existing name."""
    
    def __init__(self, name: str):
        super().__init__(f"A department with name '{name}' already exists")


class PositionExistsError(HTTPConflictError):
    """Raised when attempting to create a position that already exists in a department."""
    
    def __init__(self, title: str, department_name: str):
        super().__init__(f"Position '{title}' already exists in department '{department_name}'")


class ActiveEmploymentExistsError(HTTPConflictError):
    """Raised when attempting to create employment for someone who is already employed."""
    
    def __init__(self, person_name: str):
        super().__init__(f"Person '{person_name}' already has an active employment")


class InvalidEmploymentPeriodError(HTTPBadRequestError):
    """Raised when employment dates are invalid."""
    
    def __init__(self, message: str = "Invalid employment period"):
        super().__init__(message)


class CannotDeleteDepartmentError(HTTPConflictError):
    """Raised when attempting to delete a department with active positions."""
    
    def __init__(self, department_name: str, position_count: int):
        super().__init__(
            f"Cannot delete department '{department_name}' because it has {position_count} active position(s)"
        )


class CannotDeletePositionError(HTTPConflictError):
    """Raised when attempting to delete a position with active employees."""
    
    def __init__(self, position_title: str, employee_count: int):
        super().__init__(
            f"Cannot delete position '{position_title}' because it has {employee_count} active employee(s)"
        )


class CannotTerminateEmploymentError(HTTPBadRequestError):
    """Raised when attempting to terminate an already inactive employment."""
    
    def __init__(self, employment_id: str):
        super().__init__(f"Employment record '{employment_id}' is already terminated")


class InvalidSalaryError(HTTPBadRequestError):
    """Raised when salary value is invalid."""
    
    def __init__(self, message: str = "Invalid salary value"):
        super().__init__(message)


class InvalidDateError(HTTPBadRequestError):
    """Raised when date values are invalid."""
    
    def __init__(self, message: str = "Invalid date value"):
        super().__init__(message)


class DatabaseConnectionError(HTTPInternalServerError):
    """Raised when database connection fails."""
    
    def __init__(self):
        super().__init__("Database connection failed")


class DatabaseTransactionError(HTTPInternalServerError):
    """Raised when database transaction fails."""
    
    def __init__(self, message: str = "Database transaction failed"):
        super().__init__(message)


def create_http_exception_from_domain_exception(exc: PeopleManagementException) -> HTTPException:
    """
    Convert domain exceptions to HTTP exceptions.
    
    Args:
        exc: Domain exception instance
        
    Returns:
        Appropriate HTTP exception
    """
    if isinstance(exc, NotFoundError):
        return HTTPNotFoundError(exc.message)
    elif isinstance(exc, DuplicateError):
        return HTTPConflictError(exc.message)
    elif isinstance(exc, ValidationError):
        return HTTPBadRequestError(exc.message)
    elif isinstance(exc, BusinessLogicError):
        return HTTPUnprocessableEntityError(exc.message)
    elif isinstance(exc, DatabaseError):
        return HTTPInternalServerError(exc.message)
    elif isinstance(exc, AuthenticationError):
        return HTTPUnauthorizedError(exc.message)
    elif isinstance(exc, AuthorizationError):
        return HTTPForbiddenError(exc.message)
    else:
        # Default to internal server error for unknown exceptions
        return HTTPInternalServerError(f"An unexpected error occurred: {exc.message}")


def format_validation_error(errors: list) -> dict:
    """
    Format validation errors for API responses.
    
    Args:
        errors: List of validation errors
        
    Returns:
        Formatted error response
    """
    formatted_errors = []
    
    for error in errors:
        formatted_error = {
            "field": ".".join(str(loc) for loc in error.get("loc", [])),
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "validation_error"),
            "input": error.get("input")
        }
        formatted_errors.append(formatted_error)
    
    return {
        "detail": "Validation failed",
        "errors": formatted_errors
    }


def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        error_code: Optional error code
        details: Optional additional details
        
    Returns:
        Standardized error response
    """
    response = {
        "error": True,
        "message": message
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return response