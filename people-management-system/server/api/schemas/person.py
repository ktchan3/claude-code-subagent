"""
Pydantic schemas for Person-related API endpoints.

This module contains request and response schemas for all Person
operations including CRUD and search functionality.
"""

from datetime import date, datetime
from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, EmailStr

from .common import BaseSchema, TimestampSchema, get_uuid_field, get_name_field, get_optional_text_field
from ..utils.validators import PersonValidatorMixin


class PersonBase(BaseSchema, PersonValidatorMixin):
    """Base person schema with common fields."""
    
    first_name: str = get_name_field("Person's first name", example="John")
    last_name: str = get_name_field("Person's last name", example="Doe")
    title: Optional[str] = Field(
        None,
        max_length=20,
        description="Person's title (Mr., Ms., Dr., etc.)",
        example="Mr."
    )
    suffix: Optional[str] = Field(
        None,
        max_length=20,
        description="Person's suffix (Jr., Sr., III, etc.)",
        example="Jr."
    )
    email: EmailStr = Field(..., description="Person's email address", example="john.doe@example.com")
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Person's phone number",
        example="+1-555-123-4567"
    )
    mobile: Optional[str] = Field(
        None,
        max_length=20,
        description="Person's mobile number",
        example="+1-555-987-6543"
    )
    date_of_birth: Optional[str] = Field(
        None,
        description="Person's date of birth in dd-mm-yyyy format",
        example="15-01-1990"
    )
    gender: Optional[str] = Field(
        None,
        max_length=50,
        description="Person's gender",
        example="Male"
    )
    marital_status: Optional[str] = Field(
        None,
        max_length=50,
        description="Person's marital status",
        example="Single"
    )
    address: Optional[str] = get_optional_text_field("Street address", 255, example="123 Main St")
    city: Optional[str] = Field(
        None,
        max_length=100,
        description="City",
        example="New York"
    )
    state: Optional[str] = Field(
        None,
        max_length=50,
        description="State or province",
        example="NY"
    )
    zip_code: Optional[str] = Field(
        None,
        max_length=20,
        description="ZIP or postal code",
        example="10001"
    )
    country: Optional[str] = Field(
        "United States",
        max_length=100,
        description="Country",
        example="United States"
    )
    emergency_contact_name: Optional[str] = Field(
        None,
        max_length=200,
        description="Emergency contact name",
        example="Jane Doe"
    )
    emergency_contact_phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Emergency contact phone",
        example="+1-555-111-2222"
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes",
        example="Important client"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Tags for categorization",
        example=["VIP", "Client"]
    )
    status: Optional[str] = Field(
        "Active",
        max_length=20,
        description="Person's status",
        example="Active"
    )
    
    # Validation methods are now inherited from PersonValidatorMixin


class PersonCreate(PersonBase):
    """Schema for creating a new person."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "date_of_birth": "1990-01-15",
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "country": "United States"
            }
        }


class PersonUpdate(BaseSchema, PersonValidatorMixin):
    """Schema for updating a person."""
    
    first_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Person's first name"
    )
    last_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Person's last name"
    )
    title: Optional[str] = Field(None, max_length=20, description="Person's title")
    suffix: Optional[str] = Field(None, max_length=20, description="Person's suffix")
    email: Optional[EmailStr] = Field(None, description="Person's email address")
    phone: Optional[str] = Field(None, max_length=20, description="Person's phone number")
    mobile: Optional[str] = Field(None, max_length=20, description="Person's mobile number")
    date_of_birth: Optional[str] = Field(None, description="Person's date of birth in dd-mm-yyyy format")
    gender: Optional[str] = Field(None, max_length=50, description="Person's gender")
    marital_status: Optional[str] = Field(None, max_length=50, description="Person's marital status")
    address: Optional[str] = Field(None, max_length=255, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State or province")
    zip_code: Optional[str] = Field(None, max_length=20, description="ZIP or postal code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    emergency_contact_name: Optional[str] = Field(None, max_length=200, description="Emergency contact name")
    emergency_contact_phone: Optional[str] = Field(None, max_length=20, description="Emergency contact phone")
    notes: Optional[str] = Field(None, description="Additional notes")
    tags: Optional[List[str]] = Field(None, description="Tags for categorization")
    status: Optional[str] = Field(None, max_length=20, description="Person's status")
    
    # Validation methods are now inherited from PersonValidatorMixin
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Jane",
                "email": "jane.doe@example.com",
                "phone": "+1-555-987-6543"
            }
        }


class PersonResponse(PersonBase, TimestampSchema):
    """Schema for person response."""
    
    id: UUID = get_uuid_field(description="Person's unique identifier")
    full_name: str = Field(..., description="Person's full name")
    age: Optional[int] = Field(None, ge=0, le=150, description="Person's age in years")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-555-123-4567",
                "date_of_birth": "1990-01-15",
                "age": 34,
                "address": "123 Main St",
                "city": "New York",
                "state": "NY",
                "zip_code": "10001",
                "country": "United States",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class PersonSummary(BaseSchema):
    """Schema for person summary (minimal info)."""
    
    id: UUID = get_uuid_field(description="Person's unique identifier")
    full_name: str = Field(..., description="Person's full name")
    email: EmailStr = Field(..., description="Person's email address")
    current_position: Optional[str] = Field(None, description="Current position title")
    current_department: Optional[str] = Field(None, description="Current department name")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "full_name": "John Doe",
                "email": "john.doe@example.com",
                "current_position": "Software Engineer",
                "current_department": "Engineering"
            }
        }


class PersonWithEmployment(PersonResponse):
    """Schema for person with employment details."""
    
    current_employment: Optional[dict] = Field(None, description="Current employment details")
    employment_history: List[dict] = Field(default_factory=list, description="Employment history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "email": "john.doe@example.com",
                "current_employment": {
                    "position": "Software Engineer",
                    "department": "Engineering",
                    "start_date": "2023-01-15",
                    "salary": 85000.00
                },
                "employment_history": [
                    {
                        "position": "Junior Developer",
                        "department": "Engineering",
                        "start_date": "2022-01-15",
                        "end_date": "2022-12-31",
                        "salary": 70000.00
                    }
                ]
            }
        }


class PersonSearch(BaseSchema):
    """Schema for person search parameters."""
    
    name: Optional[str] = Field(None, description="Search by name (first or last)")
    email: Optional[str] = Field(None, description="Search by email")
    department: Optional[str] = Field(None, description="Filter by department")
    position: Optional[str] = Field(None, description="Filter by position")
    active_only: Optional[bool] = Field(True, description="Show only active employees")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "john",
                "department": "Engineering",
                "active_only": True
            }
        }


class PersonBulkCreate(BaseSchema):
    """Schema for bulk person creation."""
    
    people: List[dict] = Field(..., min_length=1, max_length=100, description="List of people to create")
    
    class Config:
        json_schema_extra = {
            "example": {
                "people": [
                    {
                        "first_name": "John",
                        "last_name": "Doe",
                        "email": "john.doe@example.com"
                    },
                    {
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "email": "jane.smith@example.com"
                    }
                ]
            }
        }


class PersonBulkUpdate(BaseSchema):
    """Schema for bulk person updates."""
    
    updates: List[dict] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of person updates with ID and fields to update"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "updates": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "first_name": "Jonathan",
                        "phone": "+1-555-999-8888"
                    },
                    {
                        "id": "987fcdeb-51a2-43d1-9c45-123456789abc",
                        "email": "jane.doe@newcompany.com"
                    }
                ]
            }
        }


class PersonAddressUpdate(BaseSchema):
    """Schema for updating only address information."""
    
    address: Optional[str] = Field(None, max_length=255, description="Street address")
    city: Optional[str] = Field(None, max_length=100, description="City")
    state: Optional[str] = Field(None, max_length=50, description="State or province")
    zip_code: Optional[str] = Field(None, max_length=20, description="ZIP or postal code")
    country: Optional[str] = Field(None, max_length=100, description="Country")
    
    class Config:
        json_schema_extra = {
            "example": {
                "address": "456 Oak Ave",
                "city": "San Francisco",
                "state": "CA",
                "zip_code": "94102"
            }
        }


class PersonContactUpdate(BaseSchema):
    """Schema for updating only contact information."""
    
    email: Optional[EmailStr] = Field(None, description="Person's email address")
    phone: Optional[str] = Field(None, max_length=20, description="Person's phone number")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Any) -> Optional[str]:
        """Basic phone number validation."""
        if v:
            # Remove all non-digit characters for validation
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) < 10 or len(digits) > 15:
                raise ValueError('Phone number must contain 10-15 digits')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john.doe@newcompany.com",
                "phone": "+1-555-111-2222"
            }
        }