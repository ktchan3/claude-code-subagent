"""
Shared Person data models using Pydantic.

These models are used for data validation and serialization between client and server.
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class PersonStatus(str, Enum):
    """Status of a person in the system."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class PersonBase(BaseModel):
    """Base person model with common fields."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
    )
    
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    status: PersonStatus = Field(default=PersonStatus.ACTIVE, description="Person status")


class PersonCreate(PersonBase):
    """Model for creating a new person."""
    pass


class PersonUpdate(BaseModel):
    """Model for updating an existing person."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
    )
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    status: Optional[PersonStatus] = None


class Person(PersonBase):
    """Complete person model with all fields."""
    
    id: UUID = Field(..., description="Unique identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    @property
    def full_name(self) -> str:
        """Get the full name of the person."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> Optional[int]:
        """Calculate age from date of birth."""
        if not self.date_of_birth:
            return None
        
        today = date.today()
        age = today.year - self.date_of_birth.year
        
        # Adjust if birthday hasn't occurred this year
        if today.month < self.date_of_birth.month or (
            today.month == self.date_of_birth.month and today.day < self.date_of_birth.day
        ):
            age -= 1
            
        return age


class PersonList(BaseModel):
    """Model for paginated person lists."""
    
    items: list[Person] = Field(default_factory=list, description="List of people")
    total: int = Field(0, ge=0, description="Total number of people")
    page: int = Field(1, ge=1, description="Current page number")
    size: int = Field(10, ge=1, le=100, description="Number of items per page")
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.size == 0:
            return 0
        return (self.total + self.size - 1) // self.size