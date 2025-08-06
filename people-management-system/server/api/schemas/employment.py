"""
Pydantic schemas for Employment-related API endpoints.

This module contains request and response schemas for all Employment
operations including creation, updates, termination, and history tracking.
"""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import Field, field_validator
from decimal import Decimal

from .common import BaseSchema, TimestampSchema, get_uuid_field


class EmploymentBase(BaseSchema):
    """Base employment schema with common fields."""
    
    start_date: date = Field(..., description="Employment start date", example="2023-01-15")
    salary: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Annual salary in USD",
        example=85000.00
    )
    
    @field_validator('start_date')
    @classmethod
    def validate_start_date(cls, v):
        """Validate start date is not in the future."""
        if v and v > date.today():
            raise ValueError('Start date cannot be in the future')
        return v
    
    @field_validator('salary')
    @classmethod
    def validate_salary(cls, v):
        """Validate salary amount."""
        if v is not None:
            if v < 0:
                raise ValueError('Salary cannot be negative')
            if v > 10_000_000:
                raise ValueError('Salary amount is unreasonably high')
        return v


class EmploymentCreate(EmploymentBase):
    """Schema for creating a new employment record."""
    
    person_id: UUID = get_uuid_field(description="ID of the person being employed")
    position_id: UUID = get_uuid_field(description="ID of the position being filled")
    
    class Config:
        schema_extra = {
            "example": {
                "person_id": "111e1111-e11b-11d1-a111-426614174111",
                "position_id": "456e7890-e12b-34d5-a678-426614174111",
                "start_date": "2023-01-15",
                "salary": 85000.00
            }
        }


class EmploymentUpdate(BaseSchema):
    """Schema for updating an employment record."""
    
    salary: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Updated annual salary in USD"
    )
    position_id: Optional[UUID] = Field(None, description="New position ID (for promotions/transfers)")
    
    @field_validator('salary')
    @classmethod
    def validate_salary(cls, v):
        """Validate salary amount."""
        if v is not None:
            if v < 0:
                raise ValueError('Salary cannot be negative')
            if v > 10_000_000:
                raise ValueError('Salary amount is unreasonably high')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "salary": 95000.00,
                "position_id": "789e0123-e45b-67d8-a901-426614174222"
            }
        }


class EmploymentTerminate(BaseSchema):
    """Schema for terminating an employment."""
    
    end_date: date = Field(..., description="Employment termination date", example="2024-01-31")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for termination",
        example="Voluntary resignation"
    )
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v):
        """Validate end date is not in the future."""
        if v and v > date.today():
            raise ValueError('End date cannot be in the future')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "end_date": "2024-01-31",
                "reason": "Voluntary resignation - accepted position at another company"
            }
        }


class EmploymentResponse(EmploymentBase, TimestampSchema):
    """Schema for employment response."""
    
    id: UUID = get_uuid_field(description="Employment record unique identifier")
    person_id: UUID = get_uuid_field(description="Person ID")
    position_id: UUID = get_uuid_field(description="Position ID")
    end_date: Optional[date] = Field(None, description="Employment end date")
    is_active: bool = Field(..., description="Whether employment is currently active")
    
    # Related entity information
    person_name: str = Field(..., description="Employee's full name")
    person_email: str = Field(..., description="Employee's email address")
    position_title: str = Field(..., description="Position title")
    department_name: str = Field(..., description="Department name")
    
    # Calculated fields
    duration_days: Optional[int] = Field(None, ge=0, description="Employment duration in days")
    duration_years: Optional[float] = Field(None, ge=0, description="Employment duration in years")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "555e5555-e55b-55d5-a555-426614174555",
                "person_id": "111e1111-e11b-11d1-a111-426614174111",
                "position_id": "456e7890-e12b-34d5-a678-426614174111",
                "person_name": "John Doe",
                "person_email": "john.doe@example.com",
                "position_title": "Software Engineer",
                "department_name": "Engineering",
                "start_date": "2023-01-15",
                "end_date": None,
                "is_active": True,
                "salary": 85000.00,
                "duration_days": 385,
                "duration_years": 1.05,
                "created_at": "2023-01-15T09:00:00Z",
                "updated_at": "2023-01-15T09:00:00Z"
            }
        }


class EmploymentSummary(BaseSchema):
    """Schema for employment summary (minimal info)."""
    
    id: UUID = get_uuid_field(description="Employment record unique identifier")
    person_name: str = Field(..., description="Employee's full name")
    position_title: str = Field(..., description="Position title")
    department_name: str = Field(..., description="Department name")
    start_date: date = Field(..., description="Employment start date")
    is_active: bool = Field(..., description="Whether employment is currently active")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "555e5555-e55b-55d5-a555-426614174555",
                "person_name": "John Doe",
                "position_title": "Software Engineer",
                "department_name": "Engineering",
                "start_date": "2023-01-15",
                "is_active": True
            }
        }


class EmploymentHistory(BaseSchema):
    """Schema for employment history of a person."""
    
    person_id: UUID = get_uuid_field(description="Person ID")
    person_name: str = Field(..., description="Employee's full name")
    total_employments: int = Field(..., ge=0, description="Total number of employment records")
    current_employment: Optional[dict] = Field(None, description="Current active employment")
    past_employments: List[dict] = Field(default_factory=list, description="Past employment records")
    total_tenure_years: float = Field(..., ge=0, description="Total tenure across all employments in years")
    
    class Config:
        schema_extra = {
            "example": {
                "person_id": "111e1111-e11b-11d1-a111-426614174111",
                "person_name": "John Doe",
                "total_employments": 3,
                "current_employment": {
                    "id": "555e5555-e55b-55d5-a555-426614174555",
                    "position_title": "Senior Software Engineer",
                    "department_name": "Engineering",
                    "start_date": "2023-06-01",
                    "salary": 95000.00,
                    "duration_years": 0.67
                },
                "past_employments": [
                    {
                        "id": "444e4444-e44b-44d4-a444-426614174444",
                        "position_title": "Software Engineer",
                        "department_name": "Engineering",
                        "start_date": "2022-01-15",
                        "end_date": "2023-05-31",
                        "salary": 75000.00,
                        "duration_years": 1.37
                    },
                    {
                        "id": "333e3333-e33b-33d3-a333-426614174333",
                        "position_title": "Junior Developer",
                        "department_name": "Engineering",
                        "start_date": "2021-06-01",
                        "end_date": "2022-01-14",
                        "salary": 60000.00,
                        "duration_years": 0.62
                    }
                ],
                "total_tenure_years": 2.66
            }
        }


class EmploymentStatistics(BaseSchema):
    """Schema for employment statistics."""
    
    total_employments: int = Field(..., ge=0, description="Total number of employment records")
    active_employments: int = Field(..., ge=0, description="Number of active employment records")
    terminated_employments: int = Field(..., ge=0, description="Number of terminated employment records")
    average_tenure_months: float = Field(..., ge=0, description="Average employment tenure in months")
    average_salary: Optional[float] = Field(None, ge=0, description="Average salary of active employments")
    salary_statistics: dict = Field(..., description="Salary statistics (min, max, median, etc.)")
    turnover_rate: float = Field(..., ge=0, le=100, description="Employee turnover rate percentage")
    department_breakdown: List[dict] = Field(..., description="Employment breakdown by department")
    position_breakdown: List[dict] = Field(..., description="Employment breakdown by position")
    
    class Config:
        schema_extra = {
            "example": {
                "total_employments": 150,
                "active_employments": 120,
                "terminated_employments": 30,
                "average_tenure_months": 18.5,
                "average_salary": 87500.00,
                "salary_statistics": {
                    "min": 45000.00,
                    "max": 180000.00,
                    "median": 82000.00,
                    "std_dev": 25000.00
                },
                "turnover_rate": 12.5,
                "department_breakdown": [
                    {
                        "department": "Engineering",
                        "active_count": 45,
                        "total_count": 60,
                        "average_salary": 95000.00
                    },
                    {
                        "department": "Sales",
                        "active_count": 30,
                        "total_count": 35,
                        "average_salary": 75000.00
                    }
                ],
                "position_breakdown": [
                    {
                        "position": "Software Engineer",
                        "active_count": 25,
                        "total_count": 35,
                        "average_salary": 90000.00
                    }
                ]
            }
        }


class EmploymentSearch(BaseSchema):
    """Schema for employment search parameters."""
    
    person_name: Optional[str] = Field(None, description="Search by employee name")
    person_email: Optional[str] = Field(None, description="Search by employee email")
    position: Optional[str] = Field(None, description="Filter by position title")
    department: Optional[str] = Field(None, description="Filter by department name")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    start_date_from: Optional[date] = Field(None, description="Filter by start date (from)")
    start_date_to: Optional[date] = Field(None, description="Filter by start date (to)")
    end_date_from: Optional[date] = Field(None, description="Filter by end date (from)")
    end_date_to: Optional[date] = Field(None, description="Filter by end date (to)")
    min_salary: Optional[float] = Field(None, ge=0, description="Minimum salary filter")
    max_salary: Optional[float] = Field(None, ge=0, description="Maximum salary filter")
    min_tenure_months: Optional[int] = Field(None, ge=0, description="Minimum tenure in months")
    max_tenure_months: Optional[int] = Field(None, ge=0, description="Maximum tenure in months")
    
    @field_validator('start_date_to')
    @classmethod
    def validate_start_date_range(cls, v, info):
        """Validate start date range."""
        if v is not None and hasattr(info.data, 'start_date_from') and info.data.start_date_from is not None:
            if v < info.data.start_date_from:
                raise ValueError('start_date_to must be greater than or equal to start_date_from')
        return v
    
    @field_validator('end_date_to')
    @classmethod
    def validate_end_date_range(cls, v, info):
        """Validate end date range."""
        if v is not None and hasattr(info.data, 'end_date_from') and info.data.end_date_from is not None:
            if v < info.data.end_date_from:
                raise ValueError('end_date_to must be greater than or equal to end_date_from')
        return v
    
    @field_validator('max_salary')
    @classmethod
    def validate_salary_range(cls, v, info):
        """Validate salary range."""
        if v is not None and hasattr(info.data, 'min_salary') and info.data.min_salary is not None:
            if v < info.data.min_salary:
                raise ValueError('max_salary must be greater than or equal to min_salary')
        return v
    
    @field_validator('max_tenure_months')
    @classmethod
    def validate_tenure_range(cls, v, info):
        """Validate tenure range."""
        if v is not None and hasattr(info.data, 'min_tenure_months') and info.data.min_tenure_months is not None:
            if v < info.data.min_tenure_months:
                raise ValueError('max_tenure_months must be greater than or equal to min_tenure_months')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "department": "Engineering",
                "is_active": True,
                "min_salary": 80000.00,
                "min_tenure_months": 12
            }
        }


class EmploymentBulkCreate(BaseSchema):
    """Schema for bulk employment creation."""
    
    employments: List[EmploymentCreate] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of employment records to create"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "employments": [
                    {
                        "person_id": "111e1111-e11b-11d1-a111-426614174111",
                        "position_id": "456e7890-e12b-34d5-a678-426614174111",
                        "start_date": "2023-01-15",
                        "salary": 85000.00
                    },
                    {
                        "person_id": "222e2222-e22b-22d2-a222-426614174222",
                        "position_id": "789e0123-e45b-67d8-a901-426614174222",
                        "start_date": "2023-02-01",
                        "salary": 90000.00
                    }
                ]
            }
        }


class EmploymentBulkTerminate(BaseSchema):
    """Schema for bulk employment termination."""
    
    employment_ids: List[UUID] = Field(
        ...,
        min_items=1,
        max_items=50,
        description="List of employment IDs to terminate"
    )
    end_date: date = Field(..., description="Termination date for all employments")
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Common reason for termination"
    )
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v):
        """Validate end date is not in the future."""
        if v and v > date.today():
            raise ValueError('End date cannot be in the future')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "employment_ids": [
                    "555e5555-e55b-55d5-a555-426614174555",
                    "666e6666-e66b-66d6-a666-426614174666"
                ],
                "end_date": "2024-01-31",
                "reason": "Company restructuring"
            }
        }


class EmploymentTransfer(BaseSchema):
    """Schema for transferring an employee to a different position."""
    
    new_position_id: UUID = get_uuid_field(description="ID of the new position")
    transfer_date: date = Field(..., description="Effective date of the transfer")
    new_salary: Optional[Decimal] = Field(
        None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="New salary (if different)"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Transfer notes or reason"
    )
    
    @field_validator('transfer_date')
    @classmethod
    def validate_transfer_date(cls, v):
        """Validate transfer date."""
        if v and v > date.today():
            raise ValueError('Transfer date cannot be in the future')
        return v
    
    @field_validator('new_salary')
    @classmethod
    def validate_salary(cls, v):
        """Validate salary amount."""
        if v is not None:
            if v < 0:
                raise ValueError('Salary cannot be negative')
            if v > 10_000_000:
                raise ValueError('Salary amount is unreasonably high')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "new_position_id": "789e0123-e45b-67d8-a901-426614174222",
                "transfer_date": "2024-02-01",
                "new_salary": 100000.00,
                "notes": "Promotion to senior role"
            }
        }