"""
Pydantic schemas for Department-related API endpoints.

This module contains request and response schemas for all Department
operations including CRUD and relationships with positions.
"""

from typing import List, Optional
from uuid import UUID
from pydantic import Field, field_validator

from .common import BaseSchema, TimestampSchema, get_uuid_field, get_name_field, get_optional_text_field


class DepartmentBase(BaseSchema):
    """Base department schema with common fields."""
    
    name: str = get_name_field("Department name", example="Engineering")
    description: Optional[str] = get_optional_text_field(
        "Department description",
        example="Software development and engineering teams"
    )


class DepartmentCreate(DepartmentBase):
    """Schema for creating a new department."""
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate department name."""
        if v:
            return v.strip()
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Engineering",
                "description": "Software development and engineering teams responsible for product development"
            }
        }


class DepartmentUpdate(BaseSchema):
    """Schema for updating a department."""
    
    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Department name"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Department description"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate department name."""
        if v:
            return v.strip()
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Software Engineering",
                "description": "Updated description for the engineering department"
            }
        }


class DepartmentResponse(DepartmentBase, TimestampSchema):
    """Schema for department response."""
    
    id: UUID = get_uuid_field(description="Department's unique identifier")
    position_count: int = Field(..., ge=0, description="Number of positions in this department")
    active_employee_count: int = Field(..., ge=0, description="Number of active employees in this department")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Engineering",
                "description": "Software development and engineering teams",
                "position_count": 5,
                "active_employee_count": 12,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class DepartmentSummary(BaseSchema):
    """Schema for department summary (minimal info)."""
    
    id: UUID = get_uuid_field(description="Department's unique identifier")
    name: str = Field(..., description="Department name")
    position_count: int = Field(..., ge=0, description="Number of positions")
    active_employee_count: int = Field(..., ge=0, description="Number of active employees")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Engineering",
                "position_count": 5,
                "active_employee_count": 12
            }
        }


class DepartmentWithPositions(DepartmentResponse):
    """Schema for department with positions."""
    
    positions: List[dict] = Field(default_factory=list, description="List of positions in this department")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Engineering",
                "description": "Software development and engineering teams",
                "position_count": 3,
                "active_employee_count": 8,
                "positions": [
                    {
                        "id": "456e7890-e12b-34d5-a678-426614174111",
                        "title": "Software Engineer",
                        "employee_count": 5
                    },
                    {
                        "id": "789e0123-e45b-67d8-a901-426614174222",
                        "title": "Senior Software Engineer",
                        "employee_count": 3
                    },
                    {
                        "id": "012e3456-e78b-90d1-a234-426614174333",
                        "title": "Engineering Manager",
                        "employee_count": 1
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class DepartmentWithEmployees(DepartmentResponse):
    """Schema for department with employee details."""
    
    employees: List[dict] = Field(default_factory=list, description="List of employees in this department")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Engineering",
                "description": "Software development and engineering teams",
                "position_count": 3,
                "active_employee_count": 2,
                "employees": [
                    {
                        "id": "111e1111-e11b-11d1-a111-426614174111",
                        "full_name": "John Doe",
                        "email": "john.doe@example.com",
                        "position": "Software Engineer",
                        "start_date": "2023-01-15",
                        "salary": 85000.00
                    },
                    {
                        "id": "222e2222-e22b-22d2-a222-426614174222",
                        "full_name": "Jane Smith",
                        "email": "jane.smith@example.com",
                        "position": "Senior Software Engineer",
                        "start_date": "2022-06-01",
                        "salary": 105000.00
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class DepartmentStatistics(BaseSchema):
    """Schema for department statistics."""
    
    id: UUID = get_uuid_field(description="Department's unique identifier")
    name: str = Field(..., description="Department name")
    total_positions: int = Field(..., ge=0, description="Total number of positions")
    total_employees: int = Field(..., ge=0, description="Total number of employees (current and past)")
    active_employees: int = Field(..., ge=0, description="Number of currently active employees")
    average_salary: Optional[float] = Field(None, ge=0, description="Average salary of active employees")
    salary_range: Optional[dict] = Field(None, description="Salary range (min/max) of active employees")
    average_tenure_months: Optional[float] = Field(None, ge=0, description="Average employee tenure in months")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Engineering",
                "total_positions": 5,
                "total_employees": 15,
                "active_employees": 12,
                "average_salary": 92500.00,
                "salary_range": {
                    "min": 65000.00,
                    "max": 150000.00
                },
                "average_tenure_months": 18.5
            }
        }


class DepartmentSearch(BaseSchema):
    """Schema for department search parameters."""
    
    name: Optional[str] = Field(None, description="Search by department name")
    has_positions: Optional[bool] = Field(None, description="Filter departments with/without positions")
    has_employees: Optional[bool] = Field(None, description="Filter departments with/without active employees")
    min_employees: Optional[int] = Field(None, ge=0, description="Minimum number of active employees")
    max_employees: Optional[int] = Field(None, ge=0, description="Maximum number of active employees")
    
    @field_validator('max_employees')
    @classmethod
    def validate_employee_range(cls, v, info):
        """Validate that max_employees is greater than min_employees."""
        if v is not None and hasattr(info.data, 'min_employees') and info.data.min_employees is not None:
            if v < info.data.min_employees:
                raise ValueError('max_employees must be greater than or equal to min_employees')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "name": "eng",
                "has_employees": True,
                "min_employees": 5
            }
        }


class DepartmentBulkCreate(BaseSchema):
    """Schema for bulk department creation."""
    
    departments: List[DepartmentCreate] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of departments to create"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "departments": [
                    {
                        "name": "Engineering",
                        "description": "Software development teams"
                    },
                    {
                        "name": "Marketing",
                        "description": "Marketing and communications teams"
                    },
                    {
                        "name": "Sales",
                        "description": "Sales and business development teams"
                    }
                ]
            }
        }


class DepartmentBulkUpdate(BaseSchema):
    """Schema for bulk department updates."""
    
    updates: List[dict] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of department updates with ID and fields to update"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "updates": [
                    {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "name": "Software Engineering",
                        "description": "Updated engineering department description"
                    },
                    {
                        "id": "987fcdeb-51a2-43d1-9c45-123456789abc",
                        "description": "Updated marketing department description"
                    }
                ]
            }
        }


class DepartmentMerge(BaseSchema):
    """Schema for merging departments."""
    
    source_department_id: UUID = get_uuid_field(description="ID of department to merge from")
    target_department_id: UUID = get_uuid_field(description="ID of department to merge into")
    transfer_positions: bool = Field(True, description="Whether to transfer positions to target department")
    delete_source: bool = Field(True, description="Whether to delete source department after merge")
    
    @field_validator('target_department_id')
    @classmethod
    def validate_different_departments(cls, v, info):
        """Validate that source and target departments are different."""
        if hasattr(info.data, 'source_department_id') and v == info.data.source_department_id:
            raise ValueError('Source and target departments must be different')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "source_department_id": "123e4567-e89b-12d3-a456-426614174000",
                "target_department_id": "987fcdeb-51a2-43d1-9c45-123456789abc",
                "transfer_positions": True,
                "delete_source": True
            }
        }