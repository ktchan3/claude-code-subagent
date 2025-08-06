# Changelog

All notable changes to the People Management System are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2024-XX-XX

### Fixed

#### Critical Bug: Person Fields Not Saving to Database
- **Issue**: Person form fields (First Name, Last Name, Title, Suffix) were not being properly saved to the database
- **Root Cause**: Server API was using `person_data.dict()` without exclusion parameters, causing Pydantic to include Optional fields as None values
- **Solution**: Updated `/server/api/routes/people.py` to use `person_data.dict(exclude_unset=True, exclude_none=True)`
- **Impact**: All person creation and update operations now properly save all provided fields
- **Files Modified**: `server/api/routes/people.py` (lines 101, 404, 483, 548)

#### SQLite Date Constraint Error
- **Issue**: Server returned 500 error when creating person with date_of_birth due to non-deterministic CHECK constraints
- **Solution**: Removed database-level CHECK constraints using `date('now')`, moved validation to application level
- **Files Modified**: `server/database/models.py`
- **Migration**: Database recreation required to remove problematic constraints

#### Qt Deprecation Warnings
- **Issue**: PySide6/Qt6 showing deprecation warnings for `AA_EnableHighDpiScaling` and `AA_UseHighDpiPixmaps`
- **Solution**: Removed deprecated attributes from `client/main.py` (HiDPI is automatic in Qt6)
- **Files Modified**: `client/main.py`

#### Client Shutdown Error
- **Issue**: "Cannot call None function" error when closing the client application
- **Solution**: Fixed function reference in `client/ui/main_window.py` by wrapping in lambda
- **Files Modified**: `client/ui/main_window.py`

#### Health Endpoint 500 Error
- **Issue**: Health check failing with email uniqueness constraint violations
- **Solution**: Updated `server/database/db.py` to use unique test emails with UUID
- **Files Modified**: `server/database/db.py`

#### Missing Person Data Fields
- **Issue**: `PersonData` model in `shared/api_client.py` was missing many fields causing data loss
- **Solution**: Updated `PersonData` class to include all person fields (title, suffix, mobile, etc.)
- **Files Modified**: `shared/api_client.py`

### Enhanced

#### Debugging and Logging
- Added comprehensive debug logging for person creation and update operations
- Enhanced error messages with specific field information
- Added data flow tracking from client to database

#### Schema Validation
- Enhanced Pydantic models with proper field validation
- Added comprehensive field validation for person records
- Improved error handling for validation failures

#### API Key Validation
- Enhanced API key validation and error handling
- Improved authentication bypass logic for optional authentication

## [1.0.0] - 2024-XX-XX

### Added

#### Core Features
- **People Management**: Complete CRUD operations for person records
- **Department Management**: Organizational structure management
- **Position Management**: Job positions within departments  
- **Employment Tracking**: Current and historical employment relationships

#### Architecture
- **FastAPI Backend**: RESTful API with automatic OpenAPI documentation
- **PySide6 Client**: Modern desktop GUI application
- **SQLAlchemy ORM**: Type-safe database operations with SQLite
- **Pydantic Validation**: Comprehensive request/response validation
- **Alembic Migrations**: Database schema version control

#### API Endpoints
- `/api/v1/people/` - Full CRUD operations for people
- `/api/v1/departments/` - Department management
- `/api/v1/positions/` - Position management
- `/api/v1/employment/` - Employment relationship tracking
- `/api/v1/statistics/` - Organizational analytics

#### Client Features
- **Modern GUI**: PySide6-based desktop application
- **Data Management**: Create, read, update, delete operations for all entities
- **Search and Filtering**: Advanced search capabilities
- **Error Handling**: User-friendly error messages and validation

#### Development Tools
- **UV Package Manager**: Fast Python package management
- **Code Quality**: Black, Ruff, MyPy integration
- **Testing**: Comprehensive test suite with pytest
- **Pre-commit Hooks**: Automated code quality checks
- **Documentation**: Complete API and development documentation

#### Database Schema
- **Person Model**: Comprehensive personal information storage
  - Basic info: first_name, last_name, email, phone, mobile
  - Extended info: title, suffix, date_of_birth, gender, marital_status
  - Address info: address, city, state, zip_code, country
  - Emergency contact: emergency_contact_name, emergency_contact_phone
  - Metadata: notes, tags, status, timestamps
- **Department Model**: Organizational departments
- **Position Model**: Job positions within departments
- **Employment Model**: People-to-position relationships with history

#### Security Features
- **Optional API Key Authentication**: Configurable security
- **Input Validation**: Comprehensive Pydantic validation
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **Secure Credential Storage**: Keyring integration for client

#### Performance Features
- **Database Indexing**: Optimized queries for common operations
- **Pagination**: Efficient large dataset handling  
- **Connection Pooling**: Optimized database connections
- **Async Support**: Asynchronous client-server communication

### Technical Specifications

#### Backend Requirements
- Python 3.9+
- FastAPI 0.100+
- SQLAlchemy 2.0+
- Pydantic 2.0+
- Uvicorn ASGI server
- SQLite database

#### Frontend Requirements  
- PySide6/Qt6
- Python requests library
- Keyring for credential storage
- Modern desktop environment

#### Development Requirements
- UV package manager
- Pytest testing framework
- Black code formatter
- Ruff linter
- MyPy type checker
- Pre-commit hooks

---

## Version History Summary

- **v1.0.1**: Critical bug fixes for person field saving, date constraints, and UI issues
- **v1.0.0**: Initial release with full feature set

## Breaking Changes

None in v1.0.1 - all changes are backward compatible.

## Migration Notes

### Upgrading to v1.0.1

1. **Database Migration**: 
   ```bash
   # Remove old database with problematic constraints
   rm -f people_management.db
   make setup-db
   ```

2. **Code Updates**: No client code changes required
3. **Configuration**: No configuration changes required

## Known Issues

- None in current version

## Planned Features

See GitHub Issues for upcoming features and enhancements.