"""
SQLAlchemy database models for the people management system.

This module defines all database models including People, Departments, Positions,
and Employment records with proper relationships, constraints, and indexes.
"""

from datetime import date, datetime
from typing import Optional, List
from uuid import uuid4, UUID

from sqlalchemy import (
    Boolean, Column, DateTime, Date, ForeignKey, Integer, 
    String, Text, Numeric, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.types import Uuid
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func


# Base class for all models
Base = declarative_base()


class TimestampMixin:
    """Mixin class for created_at and updated_at timestamps."""
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


class Person(Base, TimestampMixin):
    """
    Person model representing individuals in the system.
    
    This model stores personal information for employees, contractors,
    and other individuals managed by the system.
    """
    
    __tablename__ = "people"
    
    # Primary key
    id = Column(Uuid, primary_key=True, default=uuid4)
    
    # Personal information
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    title = Column(String(20), nullable=True)  # Mr., Ms., Dr., etc.
    suffix = Column(String(20), nullable=True)  # Jr., Sr., III, etc.
    email = Column(String(254), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)  # Mobile phone number
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(50), nullable=True)
    marital_status = Column(String(50), nullable=True)
    
    # Address information
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True, default="United States")
    
    # Emergency contact
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    
    # Additional information
    notes = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)  # JSON array stored as text
    status = Column(String(20), nullable=True, default="Active")
    
    # Relationships
    employments = relationship(
        "Employment", 
        back_populates="person",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("length(first_name) > 0", name="check_first_name_not_empty"),
        CheckConstraint("length(last_name) > 0", name="check_last_name_not_empty"),
        CheckConstraint("length(email) > 0", name="check_email_not_empty"),
        # Note: date_of_birth validation is done at application level, not database level
        # SQLite doesn't allow date('now') in CHECK constraints (non-deterministic)
        Index("idx_person_name", "first_name", "last_name"),
        Index("idx_person_location", "city", "state", "country"),
    )
    
    @validates('email')
    def validate_email(self, key, email):
        """Validate email format."""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")
        return email.lower().strip()
    
    @validates('first_name', 'last_name')
    def validate_names(self, key, name):
        """Validate name fields."""
        if not name or not name.strip():
            raise ValueError(f"{key} cannot be empty")
        return name.strip()
    
    @validates('title', 'suffix')
    def validate_title_suffix(self, key, value):
        """Validate title and suffix fields."""
        if value:
            return value.strip()
        return value
    
    @validates('phone', 'mobile', 'emergency_contact_phone')
    def validate_phone_numbers(self, key, phone):
        """Validate phone number fields."""
        if phone:
            return phone.strip()
        return phone
    
    @validates('tags')
    def validate_tags(self, key, tags):
        """Validate tags field."""
        if tags:
            return tags.strip()
        return tags
    
    @validates('status')
    def validate_status(self, key, status):
        """Validate status field."""
        if status:
            valid_statuses = ["Active", "Inactive", "Pending", "Archived"]
            if status not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return status
    
    @validates('date_of_birth')
    def validate_date_of_birth(self, key, date_of_birth):
        """Validate date of birth is not in the future."""
        if date_of_birth and date_of_birth > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return date_of_birth
    
    @property
    def full_name(self) -> str:
        """Get the full name of the person."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def tags_list(self) -> List[str]:
        """Get tags as a list."""
        if not self.tags:
            return []
        try:
            import json
            return json.loads(self.tags)
        except (json.JSONDecodeError, TypeError):
            return []
    
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
    
    @property
    def current_employment(self) -> Optional["Employment"]:
        """Get the current active employment record."""
        return next(
            (emp for emp in self.employments if emp.is_active), 
            None
        )
    
    def __repr__(self) -> str:
        return f"<Person(id={self.id}, name='{self.full_name}', email='{self.email}')>"


class Department(Base, TimestampMixin):
    """
    Department model representing organizational departments.
    
    Departments group positions and provide organizational structure.
    """
    
    __tablename__ = "departments"
    
    # Primary key
    id = Column(Uuid, primary_key=True, default=uuid4)
    
    # Department information
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    positions = relationship(
        "Position", 
        back_populates="department",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="check_department_name_not_empty"),
    )
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate department name."""
        if not name or not name.strip():
            raise ValueError("Department name cannot be empty")
        return name.strip()
    
    @property
    def position_count(self) -> int:
        """Get the number of positions in this department."""
        return len(self.positions)
    
    @property
    def active_employment_count(self) -> int:
        """Get the number of active employees in this department."""
        count = 0
        for position in self.positions:
            count += len([emp for emp in position.employments if emp.is_active])
        return count
    
    def __repr__(self) -> str:
        return f"<Department(id={self.id}, name='{self.name}')>"


class Position(Base, TimestampMixin):
    """
    Position model representing job positions within departments.
    
    Positions define roles that people can be employed in.
    """
    
    __tablename__ = "positions"
    
    # Primary key
    id = Column(Uuid, primary_key=True, default=uuid4)
    
    # Position information
    title = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Foreign keys
    department_id = Column(
        Uuid, 
        ForeignKey("departments.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Relationships
    department = relationship("Department", back_populates="positions")
    employments = relationship(
        "Employment", 
        back_populates="position",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("length(title) > 0", name="check_position_title_not_empty"),
        UniqueConstraint("title", "department_id", name="unique_position_per_department"),
        Index("idx_position_department", "department_id", "title"),
    )
    
    @validates('title')
    def validate_title(self, key, title):
        """Validate position title."""
        if not title or not title.strip():
            raise ValueError("Position title cannot be empty")
        return title.strip()
    
    @property
    def current_employees(self) -> List["Employment"]:
        """Get current active employees in this position."""
        return [emp for emp in self.employments if emp.is_active]
    
    @property
    def employee_count(self) -> int:
        """Get the number of current employees in this position."""
        return len(self.current_employees)
    
    def __repr__(self) -> str:
        return f"<Position(id={self.id}, title='{self.title}', department='{self.department.name if self.department else None}')>"


class Employment(Base, TimestampMixin):
    """
    Employment model linking people to positions.
    
    This model represents the employment relationship between a person
    and a position, including employment dates and salary information.
    """
    
    __tablename__ = "employments"
    
    # Primary key
    id = Column(Uuid, primary_key=True, default=uuid4)
    
    # Foreign keys
    person_id = Column(
        Uuid, 
        ForeignKey("people.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    position_id = Column(
        Uuid, 
        ForeignKey("positions.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Employment details
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    salary = Column(Numeric(10, 2), nullable=True)  # Annual salary in USD
    
    # Relationships
    person = relationship("Person", back_populates="employments")
    position = relationship("Position", back_populates="employments")
    
    # Constraints
    __table_args__ = (
        # Note: Date validation is done at application level, not database level
        # SQLite doesn't allow date('now') in CHECK constraints (non-deterministic)
        CheckConstraint("salary IS NULL OR salary >= 0", name="check_salary_non_negative"),
        CheckConstraint(
            "(is_active = 1 AND end_date IS NULL) OR (is_active = 0 AND end_date IS NOT NULL)",
            name="check_active_employment_logic"
        ),
        # Prevent overlapping active employments for the same person
        Index("idx_employment_person_active", "person_id", "is_active"),
        Index("idx_employment_position_active", "position_id", "is_active"),
        Index("idx_employment_dates", "start_date", "end_date"),
        Index("idx_employment_salary", "salary"),
    )
    
    @validates('start_date')
    def validate_start_date(self, key, start_date):
        """Validate start date."""
        if not start_date:
            raise ValueError("Start date is required")
        return start_date
    
    @validates('end_date')
    def validate_end_date(self, key, end_date):
        """Validate end date."""
        if end_date and self.start_date and end_date < self.start_date:
            raise ValueError("End date cannot be before start date")
        return end_date
    
    @validates('salary')
    def validate_salary(self, key, salary):
        """Validate salary."""
        if salary is not None and salary < 0:
            raise ValueError("Salary cannot be negative")
        return salary
    
    @validates('is_active')
    def validate_is_active(self, key, is_active):
        """Validate active status consistency."""
        if is_active and self.end_date:
            raise ValueError("Active employment cannot have an end date")
        elif not is_active and not self.end_date:
            raise ValueError("Inactive employment must have an end date")
        return is_active
    
    @property
    def duration_days(self) -> Optional[int]:
        """Calculate employment duration in days."""
        if not self.start_date:
            return None
        
        end = self.end_date or date.today()
        return (end - self.start_date).days
    
    @property
    def duration_years(self) -> Optional[float]:
        """Calculate employment duration in years."""
        duration = self.duration_days
        if duration is None:
            return None
        return round(duration / 365.25, 2)
    
    def terminate(self, end_date: date = None) -> None:
        """
        Terminate the employment.
        
        Args:
            end_date: The termination date (defaults to today)
        """
        self.end_date = end_date or date.today()
        self.is_active = False
    
    def __repr__(self) -> str:
        person_name = self.person.full_name if self.person else "Unknown"
        position_title = self.position.title if self.position else "Unknown"
        status = "Active" if self.is_active else "Inactive"
        return f"<Employment(id={self.id}, person='{person_name}', position='{position_title}', status='{status}')>"


# Index definitions for optimized queries
# These indexes support common query patterns in a people management system

# Indexes for finding people by name (case-insensitive search support)
Index("idx_person_first_name_lower", func.lower(Person.first_name))
Index("idx_person_last_name_lower", func.lower(Person.last_name))
Index("idx_person_email_lower", func.lower(Person.email))

# Indexes for department and position searches
Index("idx_department_name_lower", func.lower(Department.name))
Index("idx_position_title_lower", func.lower(Position.title))

# Composite indexes for complex queries
Index("idx_employment_person_position", Employment.person_id, Employment.position_id)
Index("idx_employment_active_dates", Employment.is_active, Employment.start_date, Employment.end_date)

# Indexes for reporting and analytics
Index("idx_person_birth_year", func.strftime("%Y", Person.date_of_birth))
Index("idx_employment_start_year", func.strftime("%Y", Employment.start_date))
Index("idx_employment_salary_range", Employment.salary, Employment.is_active)


def get_all_models():
    """Get all database model classes."""
    return [Person, Department, Position, Employment]


def get_model_by_name(name: str):
    """Get a model class by its name."""
    models = {
        "Person": Person,
        "Department": Department,
        "Position": Position,
        "Employment": Employment,
    }
    return models.get(name)