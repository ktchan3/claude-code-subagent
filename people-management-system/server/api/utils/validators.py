"""
Shared validation utilities for Pydantic schemas.

This module contains reusable validation functions that can be shared
across different Pydantic models to eliminate code duplication.
"""

import re
from datetime import date, datetime
from typing import Any, Optional
from pydantic import field_validator


class PersonValidatorMixin:
    """
    Mixin class providing common validation methods for Person schemas.
    
    This mixin contains all the shared validation logic that was previously
    duplicated between PersonBase and PersonUpdate classes.
    """

    @field_validator('date_of_birth')
    @classmethod
    def validate_birth_date(cls, v: Any) -> Optional[date]:
        """Validate and parse date of birth from dd-mm-yyyy format."""
        if not v:
            return None
        
        try:
            # Parse dd-mm-yyyy format
            parsed_date = datetime.strptime(v, '%d-%m-%Y').date()
            
            # Check if date is in the future
            if parsed_date > date.today():
                raise ValueError('Date of birth cannot be in the future')
                
            return parsed_date
        except ValueError as e:
            if 'Date of birth cannot be in the future' in str(e):
                raise e
            # Try ISO format as fallback
            try:
                parsed_date = datetime.fromisoformat(v).date()
                if parsed_date > date.today():
                    raise ValueError('Date of birth cannot be in the future')
                return parsed_date
            except ValueError:
                raise ValueError('Date must be in dd-mm-yyyy format (e.g., 15-01-1990)')

    @field_validator('phone', 'mobile', 'emergency_contact_phone')
    @classmethod
    def validate_phone(cls, v: Any) -> Optional[str]:
        """Basic phone number validation."""
        if v:
            # Remove all non-digit characters for validation
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) < 10 or len(digits) > 15:
                raise ValueError('Phone number must contain 10-15 digits')
        return v

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Any) -> Optional[str]:
        """Validate status field."""
        if v:
            valid_statuses = ["Active", "Inactive", "Pending", "Archived"]
            if v not in valid_statuses:
                raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v

    @field_validator('gender')
    @classmethod 
    def validate_gender(cls, v: Any) -> Optional[str]:
        """Validate gender field."""
        if v:
            valid_genders = ["Male", "Female", "Other", "Prefer not to say"]
            if v not in valid_genders:
                raise ValueError(f'Gender must be one of: {", ".join(valid_genders)}')
        return v

    @field_validator('marital_status')
    @classmethod
    def validate_marital_status(cls, v: Any) -> Optional[str]:
        """Validate marital status field."""
        if v:
            valid_statuses = ["Single", "Married", "Divorced", "Widowed", "Separated"]
            if v not in valid_statuses:
                raise ValueError(f'Marital status must be one of: {", ".join(valid_statuses)}')
        return v

    @field_validator('title', 'suffix')
    @classmethod
    def validate_title_suffix_empty_to_none(cls, v: Any) -> Optional[str]:
        """Convert empty strings to None for title and suffix."""
        if v is not None and v.strip() == '':
            return None
        return v.strip() if v else v

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: Any) -> Optional[str]:
        """Additional email validation."""
        if v:
            return v.lower().strip()
        return v


# Standalone validation functions for use outside of Pydantic models
def validate_date_format(date_str: str, format_str: str = '%d-%m-%Y') -> date:
    """
    Validate and parse date string.
    
    Args:
        date_str: Date string to validate
        format_str: Expected date format
        
    Returns:
        Parsed date object
        
    Raises:
        ValueError: If date format is invalid or date is in the future
    """
    if not date_str:
        raise ValueError("Date string cannot be empty")
    
    try:
        parsed_date = datetime.strptime(date_str, format_str).date()
        
        # Check if date is in the future for birth dates
        if parsed_date > date.today():
            raise ValueError('Date cannot be in the future')
            
        return parsed_date
    except ValueError as e:
        if 'Date cannot be in the future' in str(e):
            raise e
        raise ValueError(f'Date must be in {format_str} format')


def validate_phone_format(phone: str) -> str:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        Validated phone number
        
    Raises:
        ValueError: If phone format is invalid
    """
    if not phone:
        return phone
    
    # Remove all non-digit characters for validation
    digits = ''.join(filter(str.isdigit, phone))
    if len(digits) < 10 or len(digits) > 15:
        raise ValueError('Phone number must contain 10-15 digits')
    
    return phone


def validate_status_value(status: str, valid_statuses: list) -> str:
    """
    Validate status against list of valid values.
    
    Args:
        status: Status value to validate
        valid_statuses: List of valid status values
        
    Returns:
        Validated status
        
    Raises:
        ValueError: If status is not in valid list
    """
    if not status:
        return status
    
    if status not in valid_statuses:
        raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
    
    return status


def validate_email_format_standalone(email: str) -> str:
    """
    Validate email format using regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        Validated and normalized email
        
    Raises:
        ValueError: If email format is invalid
    """
    if not email:
        return email
    
    # Basic email regex pattern
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    email = email.lower().strip()
    
    if not email_pattern.match(email):
        raise ValueError('Invalid email format')
    
    return email


def normalize_string_field(value: Optional[str]) -> Optional[str]:
    """
    Normalize string field by trimming whitespace and converting empty strings to None.
    
    Args:
        value: String value to normalize
        
    Returns:
        Normalized string or None
    """
    if value is not None:
        value = value.strip()
        if value == '':
            return None
    return value


# Constants for validation
VALID_STATUSES = ["Active", "Inactive", "Pending", "Archived"]
VALID_GENDERS = ["Male", "Female", "Other", "Prefer not to say"]
VALID_MARITAL_STATUSES = ["Single", "Married", "Divorced", "Widowed", "Separated"]

# Phone validation constants
MIN_PHONE_DIGITS = 10
MAX_PHONE_DIGITS = 15

# Date format constants
DATE_FORMAT_DD_MM_YYYY = '%d-%m-%Y'
DATE_FORMAT_ISO = '%Y-%m-%d'