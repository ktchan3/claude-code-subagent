"""
Test fixtures and configuration for the people management system tests.

This module provides database fixtures, test client setup, and sample data
for comprehensive testing of the system.
"""

import os
import tempfile
import pytest

# Set testing environment variables before any imports
os.environ["TESTING"] = "true"
os.environ["LOG_LEVEL"] = "INFO"

# Clear settings cache to ensure test settings are used
from server.core.config import get_settings, get_test_settings
get_settings.cache_clear()
get_test_settings.cache_clear()
from datetime import date, datetime
from uuid import uuid4
from typing import Generator, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

# Import application components
from server.main import app
from server.database.db import get_db, Base, initialize_database, close_database_connections
from server.database.models import Person, Department, Position, Employment
from server.api.dependencies import get_database_session
from server.core.config import settings


@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Create a temporary database URL for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    return f"sqlite:///{db_path}"


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create a test database engine."""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False},
        echo=False  # Set to True for SQL debugging
    )
    # Initialize the database properly
    initialize_database(test_db_url, testing=True)
    yield engine
    # Cleanup
    close_database_connections()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="session")
def test_session_maker(test_engine):
    """Create a test session maker."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def db_session(test_session_maker) -> Generator[Session, None, None]:
    """Create a test database session with proper transaction handling."""
    session = test_session_maker()
    
    try:
        yield session
        # Commit any pending changes during the test, if session is not in rollback state
        if session.get_transaction() and session.get_transaction().is_active:
            session.commit()
    except Exception:
        # Roll back on exception
        session.rollback()
        raise
    finally:
        # Clean up all data after test - do a fresh rollback and delete everything
        session.rollback()
        try:
            # Clean up in reverse dependency order to avoid foreign key constraints
            session.query(Employment).delete()
            session.query(Position).delete() 
            session.query(Department).delete()
            session.query(Person).delete()
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()


@pytest.fixture
def test_client(db_session) -> TestClient:
    """Create a test client with database dependency override."""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    def override_get_database_session():
        return db_session
    
    # Override dependencies
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_database_session] = override_get_database_session
    
    client = TestClient(app)
    yield client
    
    # Clean up overrides
    app.dependency_overrides.clear()


# Sample data fixtures
@pytest.fixture
def sample_department_data() -> Dict[str, Any]:
    """Sample department data for testing."""
    return {
        "name": "Engineering",
        "description": "Software development and engineering teams"
    }


@pytest.fixture
def sample_position_data() -> Dict[str, Any]:
    """Sample position data for testing."""
    return {
        "title": "Software Engineer",
        "description": "Full-stack software development"
    }


@pytest.fixture
def sample_person_data() -> Dict[str, Any]:
    """Sample person data for testing."""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "title": "Mr.",
        "suffix": None,
        "email": "john.doe@example.com",
        "phone": "+1-555-123-4567",
        "mobile": "+1-555-987-6543",
        "date_of_birth": "15-01-1990",
        "gender": "Male",
        "marital_status": "Single",
        "address": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "country": "United States",
        "emergency_contact_name": "Jane Doe",
        "emergency_contact_phone": "+1-555-111-2222",
        "notes": "Test user for development",
        "tags": ["Developer", "Full-time"],
        "status": "Active"
    }


@pytest.fixture
def sample_person_update_data() -> Dict[str, Any]:
    """Sample person update data for testing."""
    return {
        "first_name": "Jonathan",
        "phone": "+1-555-999-8888",
        "city": "San Francisco",
        "state": "CA"
    }


@pytest.fixture
def sample_employment_data() -> Dict[str, Any]:
    """Sample employment data for testing."""
    return {
        "start_date": date(2023, 1, 15),
        "end_date": None,
        "is_active": True,
        "salary": 85000.00
    }


@pytest.fixture
def test_department(db_session: Session, sample_department_data: Dict[str, Any]) -> Department:
    """Create a test department in the database."""
    department = Department(**sample_department_data)
    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)
    return department


@pytest.fixture
def test_position(db_session: Session, test_department: Department, sample_position_data: Dict[str, Any]) -> Position:
    """Create a test position in the database."""
    position_data = sample_position_data.copy()
    position_data["department_id"] = test_department.id
    position = Position(**position_data)
    db_session.add(position)
    db_session.commit()
    db_session.refresh(position)
    return position


@pytest.fixture
def test_person(db_session: Session, sample_person_data: Dict[str, Any]) -> Person:
    """Create a test person in the database."""
    # Convert date string to date object for database
    person_data = sample_person_data.copy()
    if person_data.get("date_of_birth"):
        person_data["date_of_birth"] = datetime.strptime(person_data["date_of_birth"], "%d-%m-%Y").date()
    
    # Convert tags list to JSON string for database
    if person_data.get("tags"):
        import json
        person_data["tags"] = json.dumps(person_data["tags"])
    
    person = Person(**person_data)
    db_session.add(person)
    db_session.commit()
    db_session.refresh(person)
    return person


@pytest.fixture
def test_employment(
    db_session: Session, 
    test_person: Person, 
    test_position: Position, 
    sample_employment_data: Dict[str, Any]
) -> Employment:
    """Create a test employment record in the database."""
    employment_data = sample_employment_data.copy()
    employment_data["person_id"] = test_person.id
    employment_data["position_id"] = test_position.id
    
    employment = Employment(**employment_data)
    db_session.add(employment)
    db_session.commit()
    db_session.refresh(employment)
    return employment


@pytest.fixture
def multiple_test_people(db_session: Session) -> list[Person]:
    """Create multiple test people for testing pagination and search."""
    people_data = [
        {
            "first_name": "Alice",
            "last_name": "Johnson",
            "email": "alice.johnson@example.com",
            "phone": "+1-555-111-1111",
            "date_of_birth": date(1985, 3, 20),
            "city": "Seattle",
            "state": "WA",
            "status": "Active"
        },
        {
            "first_name": "Bob",
            "last_name": "Smith",
            "email": "bob.smith@example.com", 
            "phone": "+1-555-222-2222",
            "date_of_birth": date(1992, 7, 10),
            "city": "Portland",
            "state": "OR",
            "status": "Active"
        },
        {
            "first_name": "Charlie",
            "last_name": "Brown",
            "email": "charlie.brown@example.com",
            "phone": "+1-555-333-3333",
            "date_of_birth": date(1988, 11, 5),
            "city": "Denver",
            "state": "CO",
            "status": "Inactive"
        },
        {
            "first_name": "Diana",
            "last_name": "Wilson",
            "email": "diana.wilson@example.com",
            "phone": "+1-555-444-4444",
            "date_of_birth": date(1995, 2, 28),
            "city": "Austin",
            "state": "TX",
            "status": "Active"
        }
    ]
    
    people = []
    for person_data in people_data:
        person = Person(**person_data)
        db_session.add(person)
        people.append(person)
    
    db_session.commit()
    for person in people:
        db_session.refresh(person)
    
    return people


@pytest.fixture
def invalid_person_data() -> Dict[str, Any]:
    """Invalid person data for testing validation."""
    return {
        "first_name": "",  # Empty name should fail
        "last_name": "Doe",
        "email": "invalid-email",  # Invalid email format
        "phone": "123",  # Too short phone number
        "date_of_birth": "32-13-2025",  # Invalid date
        "status": "InvalidStatus"  # Invalid status
    }


@pytest.fixture
def malicious_input_data() -> Dict[str, Any]:
    """Malicious input data for security testing."""
    return {
        "first_name": "<script>alert('xss')</script>",
        "last_name": "'; DROP TABLE people; --",
        "email": "test@example.com",
        "notes": "javascript:alert('xss')",
        "address": "../../../etc/passwd"
    }


# Auth fixtures for API testing
@pytest.fixture
def auth_headers() -> Dict[str, str]:
    """Basic auth headers for API testing."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


# Test data cleanup is now handled in the db_session fixture


# Performance testing fixtures
@pytest.fixture
def large_dataset(db_session: Session) -> list[Person]:
    """Create a large dataset for performance testing."""
    people = []
    for i in range(100):
        person = Person(
            first_name=f"User{i}",
            last_name=f"Test{i}",
            email=f"user{i}@example.com",
            phone=f"+1-555-{i:03d}-{i:04d}",
            date_of_birth=date(1980 + (i % 40), 1 + (i % 12), 1 + (i % 28)),
            city=f"City{i % 10}",
            state=f"ST{i % 50}",
            status="Active" if i % 4 != 0 else "Inactive"
        )
        people.append(person)
        db_session.add(person)
    
    db_session.commit()
    return people


# Mock fixtures for external dependencies
@pytest.fixture
def mock_cache():
    """Mock cache for testing cache-dependent functionality."""
    from unittest.mock import Mock
    cache_mock = Mock()
    cache_mock.get.return_value = None
    cache_mock.set.return_value = True
    cache_mock.delete.return_value = True
    return cache_mock


# Error testing fixtures
@pytest.fixture
def database_error_session(test_session_maker):
    """Session that simulates database errors."""
    from unittest.mock import Mock
    mock_session = Mock()
    mock_session.query.side_effect = Exception("Database connection failed")
    return mock_session


# Parameterized test data
@pytest.fixture(params=[
    ("valid_email", "test@example.com", True),
    ("invalid_email_no_at", "testexample.com", False),
    ("invalid_email_no_domain", "test@", False),
    ("invalid_email_no_tld", "test@example", False),
    ("empty_email", "", False),
])
def email_test_data(request):
    """Parameterized email test data."""
    return request.param


@pytest.fixture(params=[
    ("valid_phone", "+1-555-123-4567", True),
    ("valid_phone_minimal", "5551234567", True),
    ("invalid_phone_short", "123", False),
    ("invalid_phone_long", "123456789012345678", False),
    ("invalid_phone_letters", "555-CALL-NOW", False),
])
def phone_test_data(request):
    """Parameterized phone test data."""
    return request.param


@pytest.fixture(params=[
    ("active", "Active"),
    ("inactive", "Inactive"),
    ("pending", "Pending"),
    ("archived", "Archived"),
])
def valid_status_data(request):
    """Parameterized valid status test data."""
    return request.param