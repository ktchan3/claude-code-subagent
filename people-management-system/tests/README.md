# Test Suite for People Management System

This directory contains a comprehensive test suite for the People Management System, covering all critical functionality including database models, API endpoints, security utilities, and business logic.

## Test Structure

```
tests/
├── conftest.py           # Test fixtures and configuration
├── test_models.py        # Database model tests
├── test_security.py      # Security utility tests  
├── test_api_people.py    # People API endpoint tests
└── README.md            # This documentation
```

## Test Categories

### 1. Model Tests (`test_models.py`)
Tests for SQLAlchemy database models including:

- **Person Model Tests**
  - Creation with minimal and full data
  - Email uniqueness constraints
  - Name, email, status, and date validation
  - Property methods (`full_name`, `age`, `tags_list`)
  - Relationships with employment records

- **Department Model Tests**
  - Creation and validation
  - Name uniqueness constraints
  - Relationship with positions
  - Property methods for counts

- **Position Model Tests**
  - Creation and validation
  - Unique titles per department
  - Department relationships
  - Employee counting methods

- **Employment Model Tests**
  - Creation with proper relationships
  - Date and salary validation
  - Active status logic validation
  - Duration calculation properties
  - Termination methods

- **Constraint and Relationship Tests**
  - Cascade deletion behavior
  - Index performance verification
  - Timestamp functionality

### 2. Security Tests (`test_security.py`)
Comprehensive security testing including:

- **InputSanitizer Class Tests**
  - String sanitization and HTML escaping
  - Length limits and dangerous pattern detection
  - Search query sanitization with SQL injection prevention
  - Email and phone number validation
  - Filename sanitization and path traversal prevention
  - UUID validation
  - Nested dictionary and list sanitization

- **RequestValidator Class Tests**
  - Content type validation
  - User agent security checks
  - Request size limits

- **Utility Function Tests**
  - `sanitize_search_term()` function
  - `sanitize_person_data()` function
  - Security header creation
  - Security event logging

- **Integration Security Tests**
  - Full sanitization workflows
  - Bypass attempt prevention
  - Nested malicious content handling
  - Edge case validation

### 3. API Tests (`test_api_people.py`)
Comprehensive API endpoint testing including:

#### CRUD Operations
- **Create Person**
  - Successful creation with full and minimal data
  - Duplicate email prevention
  - Invalid data handling
  - Malicious input sanitization

- **Read Person**
  - Retrieval by ID and email
  - Employment details inclusion
  - Not found error handling
  - Invalid UUID format handling

- **Update Person**
  - Full updates and partial updates (contact, address)
  - Duplicate email prevention during updates
  - Invalid data validation

- **Delete Person**
  - Successful deletion with cascade effects
  - Not found error handling

#### Search and Listing
- **Basic Listing**
  - Default parameters
  - Pagination support
  - Sorting options
  - Active status filtering

- **Search Functionality**
  - Name and email searches
  - Security and sanitization of search terms
  - Advanced search with multiple filters

- **Bulk Operations**
  - Bulk person creation
  - Error handling for partial failures
  - Validation error handling

#### Error Handling and Security
- **Error Scenarios**
  - Invalid JSON requests
  - Missing required fields
  - Invalid field types
  - Oversized requests
  - Concurrent request handling

- **Security Tests**
  - SQL injection prevention
  - XSS attack prevention
  - Malformed UUID handling
  - Input sanitization verification

#### Performance Tests
- Large dataset handling
- Search performance optimization
- Pagination consistency

## Test Fixtures

The `conftest.py` file provides comprehensive fixtures for testing:

### Database Fixtures
- `test_db_url`: Temporary SQLite database URL
- `test_engine`: Database engine for testing
- `test_session_maker`: Session factory
- `db_session`: Individual test database sessions
- `test_client`: FastAPI test client with database override

### Sample Data Fixtures
- `sample_department_data`: Test department data
- `sample_position_data`: Test position data
- `sample_person_data`: Complete person data
- `sample_person_update_data`: Update operation data
- `sample_employment_data`: Employment record data

### Database Object Fixtures
- `test_department`: Department instance in database
- `test_position`: Position instance linked to department
- `test_person`: Person instance in database
- `test_employment`: Employment record linking person and position
- `multiple_test_people`: Multiple person records for pagination/search testing
- `large_dataset`: 100 person records for performance testing

### Validation and Security Fixtures
- `invalid_person_data`: Invalid data for validation testing
- `malicious_input_data`: Malicious input for security testing
- `auth_headers`: HTTP headers for API requests

### Testing Utilities
- `cleanup_test_data`: Automatic cleanup after each test
- `mock_cache`: Mock cache for testing cached functionality
- `database_error_session`: Simulated database error conditions

## Running Tests

### Using Pytest Directly

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_models.py

# Run with coverage
pytest tests/ --cov=server --cov-report=html

# Run specific test class
pytest tests/test_api_people.py::TestPeopleAPI

# Run specific test method
pytest tests/test_models.py::TestPersonModel::test_create_person_minimal

# Run tests matching pattern
pytest tests/ -k "security"

# Run with verbose output
pytest tests/ -v --tb=short
```

### Using the Test Runner Script

```bash
# Run all tests with coverage
python run_tests.py --all

# Run only unit tests
python run_tests.py --unit

# Run only API tests
python run_tests.py --api

# Run security-focused tests
python run_tests.py --security

# Run performance tests
python run_tests.py --performance

# Run quick development tests
python run_tests.py --quick

# Check test dependencies
python run_tests.py --check-deps
```

## Test Configuration

The test suite is configured through `pytest.ini`:

- **Coverage**: Minimum 80% coverage required
- **Test Discovery**: Automatic discovery of test files
- **Reporting**: HTML coverage reports generated in `htmlcov/`
- **Logging**: Detailed logging during test execution
- **Markers**: Tests categorized by type (unit, integration, security, etc.)

## Test Data Management

### Database Isolation
- Each test gets a fresh database session
- Automatic cleanup after each test
- Temporary SQLite database for testing
- No interference between tests

### Test Data Creation
- Fixtures provide consistent test data
- Factory patterns for generating multiple records
- Parameterized tests for testing multiple scenarios
- Mock objects for external dependencies

### Data Validation
- Comprehensive validation testing
- Edge case coverage
- Error condition testing
- Security vulnerability testing

## Security Testing Focus

Given the critical bug fixes mentioned in CLAUDE.md, the test suite places special emphasis on:

### Pydantic Model Handling
- Tests verify correct usage of `.dict(exclude_unset=True, exclude_none=True)`
- Validation that None values don't override existing data
- Proper field mapping and data conversion

### Input Sanitization
- Comprehensive testing of `InputSanitizer` class
- SQL injection prevention validation
- XSS attack prevention testing
- Path traversal protection verification

### Search Term Security
- Testing of `sanitize_search_term()` function
- Malicious input filtering
- Bypass attempt prevention
- Integration with API endpoints

### Data Integrity
- Proper date format handling (DD-MM-YYYY)
- Email normalization and validation
- Phone number format validation
- Status and enumeration validation

## Performance Considerations

### Test Efficiency
- Database operations are optimized for testing
- Fixtures reuse objects where appropriate
- Large datasets are generated efficiently
- Performance benchmarks included

### Memory Management
- Test data is cleaned up after each test
- Database connections are properly closed
- Memory usage is monitored for large dataset tests

## Continuous Integration

The test suite is designed to work well with CI/CD pipelines:

- Exit codes indicate success/failure
- Coverage reports are generated automatically
- Test results are formatted for CI consumption
- Dependencies are clearly specified
- Environment setup is automated

## Adding New Tests

When adding new functionality, ensure:

1. **Model Changes**: Add tests in `test_models.py`
2. **API Changes**: Add tests in `test_api_people.py`
3. **Security Changes**: Add tests in `test_security.py`
4. **New Fixtures**: Add to `conftest.py` if reusable
5. **Documentation**: Update this README

### Test Naming Convention
- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names that explain what is being tested

### Test Structure
```python
def test_specific_functionality(self, fixture1, fixture2):
    """Test description explaining what this test verifies."""
    # Arrange
    setup_data = create_test_data()
    
    # Act
    result = perform_operation(setup_data)
    
    # Assert
    assert result.success is True
    assert result.data == expected_data
```

## Troubleshooting

### Common Issues

1. **Database Lock Errors**
   - Ensure all database sessions are properly closed
   - Check for uncommitted transactions

2. **Import Errors**
   - Verify Python path includes project root
   - Check all dependencies are installed

3. **Test Data Conflicts**
   - Use unique data for each test
   - Verify cleanup fixtures are working

4. **Permission Issues**
   - Ensure test database directory is writable
   - Check file permissions on test files

### Debug Mode
```bash
# Run tests with debugging
pytest tests/ --pdb --tb=long

# Run with extra logging
LOG_LEVEL=DEBUG pytest tests/ -s
```

This comprehensive test suite ensures the People Management System maintains high quality, security, and reliability standards while preventing regression of previously fixed bugs.