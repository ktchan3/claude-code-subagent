"""
Tests for database models.

This module tests all database models including Person, Department, Position,
and Employment models, their relationships, validation, and constraints.
"""

import pytest
import json
from datetime import date, datetime, timedelta
from uuid import uuid4, UUID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from server.database.models import Person, Department, Position, Employment


class TestPersonModel:
    """Tests for the Person model."""
    
    def test_create_person_minimal(self, db_session: Session):
        """Test creating a person with minimal required fields."""
        person = Person(
            first_name="John",
            last_name="Doe", 
            email="john.doe@example.com"
        )
        db_session.add(person)
        db_session.commit()
        
        assert person.id is not None
        assert isinstance(person.id, UUID)
        assert person.first_name == "John"
        assert person.last_name == "Doe"
        assert person.email == "john.doe@example.com"
        assert person.created_at is not None
        assert person.updated_at is not None
    
    def test_create_person_full_data(self, db_session: Session, sample_person_data):
        """Test creating a person with all fields."""
        # Convert sample data for database
        person_data = sample_person_data.copy()
        person_data["date_of_birth"] = datetime.strptime(person_data["date_of_birth"], "%d-%m-%Y").date()
        person_data["tags"] = json.dumps(person_data["tags"])
        
        person = Person(**person_data)
        db_session.add(person)
        db_session.commit()
        
        assert person.first_name == "John"
        assert person.last_name == "Doe"
        assert person.title == "Mr."
        assert person.email == "john.doe@example.com"
        assert person.phone == "+1-555-123-4567"
        assert person.mobile == "+1-555-987-6543"
        assert person.date_of_birth == date(1990, 1, 15)
        assert person.gender == "Male"
        assert person.marital_status == "Single"
        assert person.address == "123 Main St"
        assert person.city == "New York"
        assert person.state == "NY"
        assert person.zip_code == "10001"
        assert person.country == "United States"
        assert person.emergency_contact_name == "Jane Doe"
        assert person.emergency_contact_phone == "+1-555-111-2222"
        assert person.notes == "Test user for development"
        assert person.status == "Active"
    
    def test_person_email_uniqueness(self, db_session: Session):
        """Test that person email addresses must be unique."""
        person1 = Person(
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
        person2 = Person(
            first_name="Jane",
            last_name="Smith", 
            email="john.doe@example.com"  # Same email
        )
        
        db_session.add(person1)
        db_session.commit()
        
        db_session.add(person2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_person_name_validation(self, db_session: Session):
        """Test person name validation."""
        # Empty first name should fail
        with pytest.raises(ValueError, match="first_name cannot be empty"):
            person = Person(first_name="", last_name="Doe", email="test@example.com")
            db_session.add(person)
            db_session.commit()
        
        # Empty last name should fail
        with pytest.raises(ValueError, match="last_name cannot be empty"):
            person = Person(first_name="John", last_name="", email="test@example.com")
            db_session.add(person)
            db_session.commit()
    
    def test_person_email_validation(self, db_session: Session):
        """Test person email validation."""
        # Invalid email format should fail
        with pytest.raises(ValueError, match="Invalid email format"):
            person = Person(
                first_name="John",
                last_name="Doe",
                email="invalid-email"
            )
            db_session.add(person)
            db_session.commit()
    
    def test_person_status_validation(self, db_session: Session):
        """Test person status validation."""
        # Valid statuses should work
        valid_statuses = ["Active", "Inactive", "Pending", "Archived"]
        for status in valid_statuses:
            person = Person(
                first_name="John",
                last_name="Doe",
                email=f"john{status.lower()}@example.com",
                status=status
            )
            db_session.add(person)
            db_session.commit()
            assert person.status == status
            db_session.delete(person)
            db_session.commit()
        
        # Invalid status should fail
        with pytest.raises(ValueError):
            person = Person(
                first_name="John",
                last_name="Doe",
                email="test@example.com",
                status="InvalidStatus"
            )
            db_session.add(person)
            db_session.commit()
    
    def test_person_date_of_birth_validation(self, db_session: Session):
        """Test date of birth validation."""
        # Future date should fail
        future_date = date.today() + timedelta(days=1)
        with pytest.raises(ValueError, match="Date of birth cannot be in the future"):
            person = Person(
                first_name="John",
                last_name="Doe",
                email="test@example.com",
                date_of_birth=future_date
            )
            db_session.add(person)
            db_session.commit()
        
        # Valid past date should work
        past_date = date.today() - timedelta(days=365 * 25)  # 25 years ago
        person = Person(
            first_name="John",
            last_name="Doe",
            email="test@example.com",
            date_of_birth=past_date
        )
        db_session.add(person)
        db_session.commit()
        assert person.date_of_birth == past_date
    
    def test_person_full_name_property(self, test_person: Person):
        """Test the full_name property."""
        assert test_person.full_name == "John Doe"
    
    def test_person_age_property(self, db_session: Session):
        """Test the age property calculation."""
        # Create person with known birth date
        birth_date = date(1990, 1, 15)
        person = Person(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            date_of_birth=birth_date
        )
        db_session.add(person)
        db_session.commit()
        
        # Calculate expected age
        today = date.today()
        expected_age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            expected_age -= 1
        
        assert person.age == expected_age
    
    def test_person_age_property_no_birth_date(self, db_session: Session):
        """Test age property when no birth date is set."""
        person = Person(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        db_session.add(person)
        db_session.commit()
        
        assert person.age is None
    
    def test_person_tags_list_property(self, db_session: Session):
        """Test the tags_list property."""
        # Valid JSON tags
        tags = ["Developer", "Full-time", "Remote"]
        person = Person(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            tags=json.dumps(tags)
        )
        db_session.add(person)
        db_session.commit()
        
        assert person.tags_list == tags
    
    def test_person_tags_list_property_invalid_json(self, db_session: Session):
        """Test tags_list property with invalid JSON."""
        person = Person(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            tags="invalid json"
        )
        db_session.add(person)
        db_session.commit()
        
        assert person.tags_list == []
    
    def test_person_tags_list_property_none(self, db_session: Session):
        """Test tags_list property when tags is None."""
        person = Person(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            tags=None
        )
        db_session.add(person)
        db_session.commit()
        
        assert person.tags_list == []
    
    def test_person_current_employment_property(self, test_person: Person, test_employment: Employment):
        """Test the current_employment property."""
        assert test_person.current_employment == test_employment
        assert test_employment.is_active is True
    
    def test_person_str_representation(self, test_person: Person):
        """Test the __repr__ method."""
        expected = f"<Person(id={test_person.id}, name='John Doe', email='john.doe@example.com')>"
        assert repr(test_person) == expected


class TestDepartmentModel:
    """Tests for the Department model."""
    
    def test_create_department(self, db_session: Session, sample_department_data):
        """Test creating a department."""
        department = Department(**sample_department_data)
        db_session.add(department)
        db_session.commit()
        
        assert department.id is not None
        assert isinstance(department.id, UUID)
        assert department.name == "Engineering"
        assert department.description == "Software development and engineering teams"
        assert department.created_at is not None
        assert department.updated_at is not None
    
    def test_department_name_uniqueness(self, db_session: Session):
        """Test that department names must be unique."""
        dept1 = Department(name="Engineering", description="First dept")
        dept2 = Department(name="Engineering", description="Second dept")
        
        db_session.add(dept1)
        db_session.commit()
        
        db_session.add(dept2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_department_name_validation(self, db_session: Session):
        """Test department name validation."""
        # Empty name should fail
        with pytest.raises(ValueError, match="Department name cannot be empty"):
            department = Department(name="", description="Test")
            db_session.add(department)
            db_session.commit()
    
    def test_department_position_count_property(self, test_department: Department, test_position: Position):
        """Test the position_count property."""
        assert test_department.position_count == 1
    
    def test_department_active_employment_count_property(
        self, test_department: Department, test_position: Position, test_employment: Employment
    ):
        """Test the active_employment_count property."""
        assert test_department.active_employment_count == 1
    
    def test_department_str_representation(self, test_department: Department):
        """Test the __repr__ method."""
        expected = f"<Department(id={test_department.id}, name='Engineering')>"
        assert repr(test_department) == expected


class TestPositionModel:
    """Tests for the Position model."""
    
    def test_create_position(self, db_session: Session, test_department: Department, sample_position_data):
        """Test creating a position."""
        position_data = sample_position_data.copy()
        position_data["department_id"] = test_department.id
        position = Position(**position_data)
        db_session.add(position)
        db_session.commit()
        
        assert position.id is not None
        assert isinstance(position.id, UUID)
        assert position.title == "Software Engineer"
        assert position.description == "Full-stack software development"
        assert position.department_id == test_department.id
        assert position.created_at is not None
        assert position.updated_at is not None
    
    def test_position_title_validation(self, db_session: Session, test_department: Department):
        """Test position title validation."""
        # Empty title should fail
        with pytest.raises(ValueError, match="Position title cannot be empty"):
            position = Position(title="", department_id=test_department.id)
            db_session.add(position)
            db_session.commit()
    
    def test_position_unique_per_department(self, db_session: Session, test_department: Department):
        """Test that position titles must be unique within a department."""
        pos1 = Position(title="Engineer", department_id=test_department.id)
        pos2 = Position(title="Engineer", department_id=test_department.id)
        
        db_session.add(pos1)
        db_session.commit()
        
        db_session.add(pos2)
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_position_same_title_different_departments(self, db_session: Session):
        """Test that same position titles can exist in different departments."""
        dept1 = Department(name="Engineering", description="Eng dept")
        dept2 = Department(name="Marketing", description="Marketing dept")
        db_session.add_all([dept1, dept2])
        db_session.commit()
        
        pos1 = Position(title="Manager", department_id=dept1.id)
        pos2 = Position(title="Manager", department_id=dept2.id)
        
        db_session.add_all([pos1, pos2])
        db_session.commit()  # Should not raise error
        
        assert pos1.title == pos2.title
        assert pos1.department_id != pos2.department_id
    
    def test_position_department_relationship(self, test_position: Position, test_department: Department):
        """Test the department relationship."""
        assert test_position.department == test_department
        assert test_position in test_department.positions
    
    def test_position_current_employees_property(self, test_position: Position, test_employment: Employment):
        """Test the current_employees property."""
        assert len(test_position.current_employees) == 1
        assert test_employment in test_position.current_employees
    
    def test_position_employee_count_property(self, test_position: Position, test_employment: Employment):
        """Test the employee_count property."""
        assert test_position.employee_count == 1
    
    def test_position_str_representation(self, test_position: Position, test_department: Department):
        """Test the __repr__ method."""
        expected = f"<Position(id={test_position.id}, title='Software Engineer', department='Engineering')>"
        assert repr(test_position) == expected


class TestEmploymentModel:
    """Tests for the Employment model."""
    
    def test_create_employment(self, db_session: Session, test_person: Person, test_position: Position, sample_employment_data):
        """Test creating an employment record."""
        employment_data = sample_employment_data.copy()
        employment_data["person_id"] = test_person.id
        employment_data["position_id"] = test_position.id
        employment = Employment(**employment_data)
        db_session.add(employment)
        db_session.commit()
        
        assert employment.id is not None
        assert isinstance(employment.id, UUID)
        assert employment.person_id == test_person.id
        assert employment.position_id == test_position.id
        assert employment.start_date == date(2023, 1, 15)
        assert employment.end_date is None
        assert employment.is_active is True
        assert employment.salary == 85000.00
        assert employment.created_at is not None
        assert employment.updated_at is not None
    
    def test_employment_start_date_validation(self, db_session: Session, test_person: Person, test_position: Position):
        """Test employment start date validation."""
        # Missing start date should fail
        with pytest.raises(ValueError, match="Start date is required"):
            employment = Employment(
                person_id=test_person.id,
                position_id=test_position.id,
                start_date=None
            )
            db_session.add(employment)
            db_session.commit()
    
    def test_employment_end_date_validation(self, db_session: Session, test_person: Person, test_position: Position):
        """Test employment end date validation."""
        # End date before start date should fail
        start_date = date(2023, 1, 15)
        end_date = date(2022, 12, 31)  # Before start date
        
        with pytest.raises(ValueError, match="End date cannot be before start date"):
            employment = Employment(
                person_id=test_person.id,
                position_id=test_position.id,
                start_date=start_date,
                end_date=end_date
            )
            db_session.add(employment)
            db_session.commit()
    
    def test_employment_salary_validation(self, db_session: Session, test_person: Person, test_position: Position):
        """Test employment salary validation."""
        # Negative salary should fail
        with pytest.raises(ValueError, match="Salary cannot be negative"):
            employment = Employment(
                person_id=test_person.id,
                position_id=test_position.id,
                start_date=date(2023, 1, 15),
                salary=-1000.00
            )
            db_session.add(employment)
            db_session.commit()
    
    def test_employment_active_status_validation(self, db_session: Session, test_person: Person, test_position: Position):
        """Test employment active status validation."""
        # Active employment with end date should fail
        with pytest.raises(ValueError, match="Active employment cannot have an end date"):
            employment = Employment(
                person_id=test_person.id,
                position_id=test_position.id,
                start_date=date(2023, 1, 15),
                end_date=date(2023, 12, 31),
                is_active=True
            )
            db_session.add(employment)
            db_session.commit()
        
        # Inactive employment without end date should fail
        with pytest.raises(ValueError, match="Inactive employment must have an end date"):
            employment = Employment(
                person_id=test_person.id,
                position_id=test_position.id,
                start_date=date(2023, 1, 15),
                end_date=None,
                is_active=False
            )
            db_session.add(employment)
            db_session.commit()
    
    def test_employment_relationships(self, test_employment: Employment, test_person: Person, test_position: Position):
        """Test employment relationships."""
        assert test_employment.person == test_person
        assert test_employment.position == test_position
        assert test_employment in test_person.employments
        assert test_employment in test_position.employments
    
    def test_employment_duration_days_property(self, test_employment: Employment):
        """Test the duration_days property."""
        # Active employment should calculate duration to today
        expected_days = (date.today() - test_employment.start_date).days
        assert test_employment.duration_days == expected_days
    
    def test_employment_duration_days_property_with_end_date(self, db_session: Session, test_person: Person, test_position: Position):
        """Test duration_days property with end date."""
        start_date = date(2023, 1, 15)
        end_date = date(2023, 12, 31)
        
        employment = Employment(
            person_id=test_person.id,
            position_id=test_position.id,
            start_date=start_date,
            end_date=end_date,
            is_active=False
        )
        db_session.add(employment)
        db_session.commit()
        
        expected_days = (end_date - start_date).days
        assert employment.duration_days == expected_days
    
    def test_employment_duration_years_property(self, test_employment: Employment):
        """Test the duration_years property."""
        duration_days = test_employment.duration_days
        expected_years = round(duration_days / 365.25, 2) if duration_days else None
        assert test_employment.duration_years == expected_years
    
    def test_employment_terminate_method(self, test_employment: Employment):
        """Test the terminate method."""
        end_date = date(2023, 12, 31)
        test_employment.terminate(end_date)
        
        assert test_employment.end_date == end_date
        assert test_employment.is_active is False
    
    def test_employment_terminate_method_default_date(self, test_employment: Employment):
        """Test terminate method with default date."""
        test_employment.terminate()
        
        assert test_employment.end_date == date.today()
        assert test_employment.is_active is False
    
    def test_employment_str_representation(self, test_employment: Employment):
        """Test the __repr__ method."""
        expected = f"<Employment(id={test_employment.id}, person='John Doe', position='Software Engineer', status='Active')>"
        assert repr(test_employment) == expected


class TestModelConstraints:
    """Tests for database constraints and indexes."""
    
    def test_person_email_index(self, db_session: Session):
        """Test that person email is properly indexed."""
        # Create multiple people to test index performance
        people = []
        for i in range(10):
            person = Person(
                first_name=f"User{i}",
                last_name=f"Test{i}",
                email=f"user{i}@example.com"
            )
            people.append(person)
        
        db_session.add_all(people)
        db_session.commit()
        
        # Query by email should be fast (relies on index)
        result = db_session.query(Person).filter(Person.email == "user5@example.com").first()
        assert result is not None
        assert result.first_name == "User5"
    
    def test_cascade_delete_person_employments(self, db_session: Session, test_person: Person, test_position: Position):
        """Test that deleting a person cascades to employments."""
        # Create employment
        employment = Employment(
            person_id=test_person.id,
            position_id=test_position.id,
            start_date=date(2023, 1, 15),
            is_active=True
        )
        db_session.add(employment)
        db_session.commit()
        
        employment_id = employment.id
        
        # Delete person
        db_session.delete(test_person)
        db_session.commit()
        
        # Employment should be deleted
        deleted_employment = db_session.query(Employment).filter(Employment.id == employment_id).first()
        assert deleted_employment is None
    
    def test_cascade_delete_department_positions_employments(self, db_session: Session):
        """Test that deleting a department cascades to positions and employments."""
        # Create department, position, person, and employment
        department = Department(name="Test Dept", description="Test")
        person = Person(first_name="John", last_name="Doe", email="john@test.com")
        db_session.add_all([department, person])
        db_session.commit()
        
        position = Position(title="Test Position", department_id=department.id)
        db_session.add(position)
        db_session.commit()
        
        employment = Employment(
            person_id=person.id,
            position_id=position.id,
            start_date=date(2023, 1, 15),
            is_active=True
        )
        db_session.add(employment)
        db_session.commit()
        
        position_id = position.id
        employment_id = employment.id
        
        # Delete department
        db_session.delete(department)
        db_session.commit()
        
        # Position and employment should be deleted
        deleted_position = db_session.query(Position).filter(Position.id == position_id).first()
        deleted_employment = db_session.query(Employment).filter(Employment.id == employment_id).first()
        
        assert deleted_position is None
        assert deleted_employment is None


class TestModelTimestamps:
    """Tests for timestamp functionality."""
    
    def test_person_timestamps(self, db_session: Session):
        """Test person creation and update timestamps."""
        person = Person(
            first_name="John",
            last_name="Doe",
            email="john@example.com"
        )
        db_session.add(person)
        db_session.commit()
        
        created_at = person.created_at
        updated_at = person.updated_at
        
        assert created_at is not None
        assert updated_at is not None
        # Timestamps should be very close on creation (within 1 second)
        assert abs((created_at - updated_at).total_seconds()) < 1
        
        # Update person
        import time
        time.sleep(0.1)  # Longer delay to ensure different timestamp
        person.first_name = "Jonathan"
        db_session.commit()
        
        # Refresh the object to get updated timestamps from database
        db_session.refresh(person)
        
        assert person.updated_at > updated_at  # Should be updated
        assert person.created_at == created_at  # Should not change