"""
Centralized response formatters for consistent API responses.

This module provides standardized formatting functions for all database models
to ensure consistent date formatting, field handling, and response structure
across all API endpoints.
"""

from typing import Dict, Any, Optional, List
from datetime import date

from ...database.models import Person, Department, Position, Employment


def format_date_for_api(date_obj: Optional[date]) -> Optional[str]:
    """
    Format date objects to DD-MM-YYYY string format for API responses.
    
    Args:
        date_obj: Date object to format, can be None
        
    Returns:
        Formatted date string in DD-MM-YYYY format or None
    """
    if not date_obj:
        return None
    return date_obj.strftime('%d-%m-%Y')


def format_person_response(person: Person) -> Dict[str, Any]:
    """
    Convert a Person database object to properly formatted response data.
    
    This function ensures consistent response formatting across all endpoints
    and handles the conversion of complex fields like dates and tags.
    
    Args:
        person: Person database model instance
        
    Returns:
        Dictionary with properly formatted person data
    """
    return {
        "id": person.id,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "title": person.title,
        "suffix": person.suffix,
        "email": person.email,
        "phone": person.phone,
        "mobile": person.mobile,
        "date_of_birth": format_date_for_api(person.date_of_birth),
        "gender": person.gender,
        "marital_status": person.marital_status,
        "address": person.address,
        "city": person.city,
        "state": person.state,
        "zip_code": person.zip_code,
        "country": person.country,
        "emergency_contact_name": person.emergency_contact_name,
        "emergency_contact_phone": person.emergency_contact_phone,
        "notes": person.notes,
        "tags": person.tags_list,  # Use the property that converts JSON to list
        "status": person.status,
        "full_name": person.full_name,
        "age": person.age,
        "created_at": person.created_at,
        "updated_at": person.updated_at
    }


def format_person_summary(person: Person, include_employment: bool = True) -> Dict[str, Any]:
    """
    Format person data for summary responses (lists, search results).
    
    Args:
        person: Person database model instance
        include_employment: Whether to include current employment info
        
    Returns:
        Dictionary with summary person data
    """
    data = {
        "id": person.id,
        "full_name": person.full_name,
        "email": person.email,
    }
    
    if include_employment:
        current_employment = person.current_employment
        data.update({
            "current_position": current_employment.position.title if current_employment else None,
            "current_department": current_employment.position.department.name if current_employment else None
        })
    
    return data


def format_employment_response(employment: Employment) -> Dict[str, Any]:
    """
    Format employment data for API responses.
    
    Args:
        employment: Employment database model instance
        
    Returns:
        Dictionary with properly formatted employment data
    """
    return {
        "id": employment.id,
        "position": employment.position.title,
        "department": employment.position.department.name,
        "start_date": format_date_for_api(employment.start_date),
        "end_date": format_date_for_api(employment.end_date),
        "is_active": employment.is_active,
        "salary": float(employment.salary) if employment.salary else None,
        "duration_days": employment.duration_days,
        "duration_years": employment.duration_years
    }


def format_employment_summary(employment: Employment) -> Dict[str, Any]:
    """
    Format employment data for summary responses (without person details).
    
    Args:
        employment: Employment database model instance
        
    Returns:
        Dictionary with summary employment data
    """
    return {
        "id": employment.id,
        "position": employment.position.title,
        "department": employment.position.department.name,
        "start_date": format_date_for_api(employment.start_date),
        "end_date": format_date_for_api(employment.end_date),
        "salary": float(employment.salary) if employment.salary else None
    }


def format_person_with_employment(person: Person) -> Dict[str, Any]:
    """
    Format person data with employment details for comprehensive responses.
    
    Args:
        person: Person database model instance
        
    Returns:
        Dictionary with person data and employment history
    """
    # Get base person data
    person_data = format_person_response(person)
    
    # Add current employment
    current_employment = person.current_employment
    current_emp_data = None
    if current_employment:
        current_emp_data = format_employment_summary(current_employment)
    
    # Add employment history (past employments)
    employment_history = [
        format_employment_summary(emp)
        for emp in person.employments if not emp.is_active
    ]
    
    # Add employment data to person data
    person_data.update({
        "current_employment": current_emp_data,
        "employment_history": employment_history
    })
    
    return person_data


def format_department_response(department: Department) -> Dict[str, Any]:
    """
    Format department data for API responses.
    
    Args:
        department: Department database model instance
        
    Returns:
        Dictionary with properly formatted department data
    """
    return {
        "id": department.id,
        "name": department.name,
        "description": department.description,
        "position_count": department.position_count,
        "active_employment_count": department.active_employment_count,
        "created_at": department.created_at,
        "updated_at": department.updated_at
    }


def format_position_response(position: Position) -> Dict[str, Any]:
    """
    Format position data for API responses.
    
    Args:
        position: Position database model instance
        
    Returns:
        Dictionary with properly formatted position data
    """
    return {
        "id": position.id,
        "title": position.title,
        "description": position.description,
        "department_id": position.department_id,
        "department_name": position.department.name if position.department else None,
        "employee_count": position.employee_count,
        "created_at": position.created_at,
        "updated_at": position.updated_at
    }


def format_bulk_operation_response(
    created_items: List[Dict[str, Any]], 
    errors: List[Dict[str, Any]],
    operation_name: str = "operation"
) -> Dict[str, Any]:
    """
    Format bulk operation responses for consistency.
    
    Args:
        created_items: List of successfully created items
        errors: List of errors encountered
        operation_name: Name of the operation for logging
        
    Returns:
        Dictionary with bulk operation results
    """
    return {
        "created_count": len(created_items),
        "error_count": len(errors),
        "created_items": created_items,
        "errors": errors,
        "message": f"Bulk {operation_name} completed: {len(created_items)} successful, {len(errors)} errors"
    }


def sanitize_search_term(search_term: str) -> str:
    """
    Sanitize search terms to prevent injection attacks and ensure consistency.
    
    Args:
        search_term: Raw search term from user input
        
    Returns:
        Sanitized search term safe for database queries
    """
    if not search_term:
        return ""
    
    # Remove leading/trailing whitespace
    sanitized = search_term.strip()
    
    # Escape special SQL characters while preserving wildcards
    # Note: SQLAlchemy's ilike() handles SQL injection prevention,
    # but we still sanitize for consistency and additional safety
    sanitized = sanitized.replace('\\', '\\\\')  # Escape backslashes first
    sanitized = sanitized.replace('_', '\\_')     # Escape underscore wildcards
    sanitized = sanitized.replace('[', '\\[')     # Escape bracket wildcards
    
    # Limit length to prevent excessive database load
    if len(sanitized) > 100:
        sanitized = sanitized[:100]
    
    return sanitized


def format_error_response(error_message: str, error_code: str = None) -> Dict[str, Any]:
    """
    Format error responses for consistency.
    
    Args:
        error_message: Human-readable error message
        error_code: Optional error code for programmatic handling
        
    Returns:
        Dictionary with standardized error format
    """
    response = {
        "error": error_message,
        "timestamp": date.today().isoformat()
    }
    
    if error_code:
        response["error_code"] = error_code
    
    return response


def format_health_check_response(
    service_name: str,
    status: str = "healthy",
    additional_data: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Format health check responses for consistency.
    
    Args:
        service_name: Name of the service being checked
        status: Health status ("healthy", "unhealthy", "degraded")
        additional_data: Additional health check data
        
    Returns:
        Dictionary with standardized health check format
    """
    response = {
        "service_name": service_name,
        "status": status,
        "timestamp": date.today().isoformat()
    }
    
    if additional_data:
        response["additional_data"] = additional_data
    
    return response