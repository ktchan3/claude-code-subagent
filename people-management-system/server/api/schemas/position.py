"""
Pydantic schemas for Position-related API endpoints.

This module contains request and response schemas for all Position
operations including CRUD and relationships with departments and employees.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import Field, field_validator

from .common import BaseSchema, TimestampSchema, get_uuid_field, get_name_field, get_optional_text_field


class PositionBase(BaseSchema):
    """Base position schema with common fields."""
    
    title: str = get_name_field("Position title", 150, example="Software Engineer")
    description: Optional[str] = get_optional_text_field(
        "Position description",
        example="Responsible for developing and maintaining software applications"
    )


class PositionCreate(PositionBase):
    """Schema for creating a new position."""
    
    department_id: UUID = get_uuid_field(description="Department ID this position belongs to")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate position title."""
        if v:
            return v.strip()
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Software Engineer",
                "description": "Responsible for developing and maintaining software applications using modern technologies",
                "department_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }


class PositionUpdate(BaseSchema):
    """Schema for updating a position."""
    
    title: Optional[str] = Field(
        None,
        min_length=1,
        max_length=150,
        description="Position title"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Position description"
    )
    department_id: Optional[UUID] = Field(None, description="Department ID to move position to")
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate position title."""
        if v:
            return v.strip()
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Senior Software Engineer",
                "description": "Updated description for senior-level responsibilities"
            }
        }


class PositionResponse(PositionBase, TimestampSchema):
    """Schema for position response."""
    
    id: UUID = get_uuid_field(description="Position's unique identifier")
    department_id: UUID = get_uuid_field(description="Department ID this position belongs to")
    department_name: str = Field(..., description="Department name")
    employee_count: int = Field(..., ge=0, description="Number of active employees in this position")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "456e7890-e12b-34d5-a678-426614174111",
                "title": "Software Engineer",
                "description": "Responsible for developing and maintaining software applications",
                "department_id": "123e4567-e89b-12d3-a456-426614174000",
                "department_name": "Engineering",
                "employee_count": 3,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class PositionSummary(BaseSchema):
    """Schema for position summary (minimal info)."""
    
    id: UUID = get_uuid_field(description="Position's unique identifier")
    title: str = Field(..., description="Position title")
    department_name: str = Field(..., description="Department name")
    employee_count: int = Field(..., ge=0, description="Number of active employees")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "456e7890-e12b-34d5-a678-426614174111",
                "title": "Software Engineer",
                "department_name": "Engineering",
                "employee_count": 3
            }
        }


class PositionWithEmployees(PositionResponse):
    """Schema for position with employee details."""
    
    employees: List[dict] = Field(default_factory=list, description="List of employees in this position")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "456e7890-e12b-34d5-a678-426614174111",
                "title": "Software Engineer",
                "description": "Responsible for developing and maintaining software applications",
                "department_id": "123e4567-e89b-12d3-a456-426614174000",
                "department_name": "Engineering",
                "employee_count": 2,
                "employees": [
                    {
                        "id": "111e1111-e11b-11d1-a111-426614174111",
                        "full_name": "John Doe",
                        "email": "john.doe@example.com",
                        "start_date": "2023-01-15",
                        "salary": 85000.00,
                        "is_active": True
                    },
                    {
                        "id": "222e2222-e22b-22d2-a222-426614174222",
                        "full_name": "Jane Smith",
                        "email": "jane.smith@example.com",
                        "start_date": "2022-06-01",
                        "salary": 90000.00,
                        "is_active": True
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class PositionWithHistory(PositionResponse):
    """Schema for position with employment history."""
    
    current_employees: List[dict] = Field(default_factory=list, description="Current active employees")
    past_employees: List[dict] = Field(default_factory=list, description="Past employees")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "456e7890-e12b-34d5-a678-426614174111",
                "title": "Software Engineer",
                "description": "Responsible for developing and maintaining software applications",
                "department_id": "123e4567-e89b-12d3-a456-426614174000",
                "department_name": "Engineering",
                "employee_count": 2,
                "current_employees": [
                    {
                        "id": "111e1111-e11b-11d1-a111-426614174111",
                        "full_name": "John Doe",
                        "start_date": "2023-01-15",
                        "salary": 85000.00
                    }
                ],
                "past_employees": [
                    {
                        "id": "333e3333-e33b-33d3-a333-426614174333",
                        "full_name": "Bob Wilson",
                        "start_date": "2022-01-01",
                        "end_date": "2022-12-31",
                        "salary": 75000.00
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class PositionStatistics(BaseSchema):
    """Schema for position statistics."""
    
    id: UUID = get_uuid_field(description="Position's unique identifier")
    title: str = Field(..., description="Position title")
    department_name: str = Field(..., description="Department name")
    total_employees: int = Field(..., ge=0, description="Total number of employees (current and past)")
    active_employees: int = Field(..., ge=0, description="Number of currently active employees")
    average_salary: Optional[float] = Field(None, ge=0, description="Average salary of active employees")
    salary_range: Optional[dict] = Field(None, description="Salary range (min/max) of active employees")
    average_tenure_months: Optional[float] = Field(None, ge=0, description="Average employee tenure in months")
    turnover_rate: Optional[float] = Field(None, ge=0, le=100, description="Employee turnover rate percentage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "456e7890-e12b-34d5-a678-426614174111",
                "title": "Software Engineer",
                "department_name": "Engineering",
                "total_employees": 8,
                "active_employees": 5,
                "average_salary": 87500.00,
                "salary_range": {
                    "min": 75000.00,
                    "max": 95000.00
                },
                "average_tenure_months": 14.2,
                "turnover_rate": 12.5
            }
        }


class PositionSearch(BaseSchema):
    """Schema for position search parameters."""
    
    title: Optional[str] = Field(None, description="Search by position title")
    department: Optional[str] = Field(None, description="Filter by department name")
    department_id: Optional[UUID] = Field(None, description="Filter by department ID")
    has_employees: Optional[bool] = Field(None, description="Filter positions with/without active employees")
    min_employees: Optional[int] = Field(None, ge=0, description="Minimum number of active employees")
    max_employees: Optional[int] = Field(None, ge=0, description="Maximum number of active employees")
    min_salary: Optional[float] = Field(None, ge=0, description="Minimum average salary")
    max_salary: Optional[float] = Field(None, ge=0, description="Maximum average salary")
    
    @field_validator('max_employees')
    @classmethod
    def validate_employee_range(cls, v, info):
        """Validate that max_employees is greater than min_employees."""
        if v is not None and hasattr(info.data, 'min_employees') and info.data.min_employees is not None:
            if v < info.data.min_employees:
                raise ValueError('max_employees must be greater than or equal to min_employees')
        return v
    
    @field_validator('max_salary')
    @classmethod
    def validate_salary_range(cls, v, info):
        """Validate that max_salary is greater than min_salary."""
        if v is not None and hasattr(info.data, 'min_salary') and info.data.min_salary is not None:
            if v < info.data.min_salary:
                raise ValueError('max_salary must be greater than or equal to min_salary')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "engineer",
                "department": "Engineering",
                "has_employees": True,
                "min_salary": 80000.00
            }
        }


class PositionBulkCreate(BaseSchema):
    """Schema for bulk position creation."""
    
    positions: List[PositionCreate] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of positions to create"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "positions": [
                    {
                        "title": "Software Engineer",
                        "description": "Develop and maintain software applications",
                        "department_id": "123e4567-e89b-12d3-a456-426614174000"
                    },
                    {
                        "title": "Senior Software Engineer",
                        "description": "Lead software development projects",
                        "department_id": "123e4567-e89b-12d3-a456-426614174000"
                    }
                ]
            }
        }


class PositionBulkUpdate(BaseSchema):
    """Schema for bulk position updates."""
    
    updates: List[dict] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of position updates with ID and fields to update"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "updates": [
                    {
                        "id": "456e7890-e12b-34d5-a678-426614174111",
                        "title": "Senior Software Engineer",
                        "description": "Updated description for senior role"
                    },
                    {
                        "id": "789e0123-e45b-67d8-a901-426614174222",
                        "description": "Updated manager role description"
                    }
                ]
            }
        }


class PositionTransfer(BaseSchema):
    """Schema for transferring position to another department."""
    
    new_department_id: UUID = get_uuid_field(description="ID of department to transfer position to")
    transfer_employees: bool = Field(
        True,
        description="Whether to keep employees in the position during transfer"
    )
    effective_date: Optional[str] = Field(
        None,
        description="Effective date for the transfer (YYYY-MM-DD format)"
    )
    
    @field_validator('effective_date')
    @classmethod
    def validate_effective_date(cls, v):
        """Validate effective date format."""
        if v:
            try:
                from datetime import datetime
                datetime.fromisoformat(v)
            except ValueError:
                raise ValueError('Invalid date format. Use YYYY-MM-DD format.')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_department_id": "987fcdeb-51a2-43d1-9c45-123456789abc",
                "transfer_employees": True,
                "effective_date": "2024-02-01"
            }
        }


class PositionClone(BaseSchema):
    """Schema for cloning a position."""
    
    new_title: str = get_name_field("New position title", 150)
    new_department_id: Optional[UUID] = Field(
        None,
        description="Department ID for the new position (if different from original)"
    )
    copy_description: bool = Field(True, description="Whether to copy the description")
    
    @field_validator('new_title')
    @classmethod
    def validate_title(cls, v):
        """Validate new position title."""
        if v:
            return v.strip()
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_title": "Junior Software Engineer",
                "new_department_id": "123e4567-e89b-12d3-a456-426614174000",
                "copy_description": True
            }
        }