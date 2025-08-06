# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

The People Management System is a full-stack Python application with a FastAPI backend and PySide6 GUI client. It manages organizational data including people, departments, positions, and employment records.

### Key Components

- **Server**: FastAPI REST API with SQLAlchemy ORM and SQLite database
- **Client**: PySide6 desktop GUI application  
- **Shared**: Common models and utilities
- **Database**: SQLite with Alembic migrations

## Commands

### Development Setup
```bash
# Install dependencies
make dev-install
# or: uv sync

# Set up database
make setup-db
# or: uv run alembic upgrade head

# Set up pre-commit hooks
uv run pre-commit install
```

### Running the Application
```bash
# Start server (in one terminal)
make run-server
# or: uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# Start client (in another terminal)
make run-client  
# or: uv run python -m client.main
```

### Development Workflow
```bash
# Format code
make format
# or: uv run black . && uv run ruff format .

# Run linting
make lint
# or: uv run ruff check .

# Run tests
make test
# or: uv run pytest

# Run tests with coverage
make test-coverage
# or: uv run pytest --cov=server --cov=client --cov=shared --cov-report=html

# Type checking
uv run mypy server client shared
```

### Database Operations
```bash
# Create migration
make create-migration name="description"
# or: uv run alembic revision --autogenerate -m "description"

# Apply migrations
make setup-db
# or: uv run alembic upgrade head

# Reset database (WARNING: destroys data)
make reset-db
# or: rm -f people_management.db && make setup-db
```

## Architecture

### System Architecture
```
┌─────────────────┐    HTTP/REST API    ┌─────────────────┐
│   PySide6 GUI   │◄──────────────────►│   FastAPI       │
│     Client      │                     │    Server       │
└─────────────────┘                     └─────────────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │   SQLAlchemy    │
                                       │      ORM        │
                                       └─────────────────┘
                                                │
                                                ▼
                                       ┌─────────────────┐
                                       │     SQLite      │
                                       │    Database     │
                                       └─────────────────┘
```

### Key Directories
- `server/api/routes/` - API endpoint definitions
- `server/api/schemas/` - Pydantic models for request/response
- `server/database/models.py` - SQLAlchemy database models
- `client/ui/views/` - Main application views  
- `client/ui/widgets/` - Reusable UI components
- `shared/` - Common utilities and API client

### Database Models
- **Person**: Individual records with personal information
- **Department**: Organizational departments
- **Position**: Job positions within departments
- **Employment**: Relationships between people and positions

## Critical Bug Fixes and Patterns

### Pydantic Model Handling (CRITICAL)

**Always use `exclude_unset=True` and `exclude_none=True` when converting Pydantic models to dictionaries for database operations:**

```python
# CORRECT - Prevents None overrides
person_dict = person_data.dict(exclude_unset=True, exclude_none=True)
db_person = Person(**person_dict)

# INCORRECT - Will override fields with None
person_dict = person_data.dict()  # Don't do this!
```

### Date Handling
- Database stores dates as DATE type
- API expects DD-MM-YYYY format strings
- Client displays dates in localized format

### API Response Formatting
Always use explicit field mapping for consistent responses:
```python
response_data = {
    "id": db_object.id,
    "field": db_object.field,
    # ... explicit mapping for all fields
}
```

## Development Guidelines

### Code Style
- Use Black formatter with 88 character line length
- Follow PEP 8 with Ruff linting
- Full type hints required (mypy strict mode)
- Google-style docstrings

### Testing Strategy
- Unit tests for all business logic
- API integration tests for all endpoints
- GUI tests for critical user workflows
- Database tests for model validation

### Error Handling
- Use custom exception classes
- Log all errors with context
- Return user-friendly error messages
- Implement proper rollback on failures

### Security Considerations
- API key authentication (optional)
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- Secure credential storage with keyring

## Troubleshooting Quick Reference

### Common Issues
1. **Fields not saving**: Check Pydantic `.dict()` usage
2. **Database locked**: Kill processes using `people_management.db`
3. **Qt test failures**: Set `QT_QPA_PLATFORM=offscreen`
4. **Migration conflicts**: Use `alembic merge` command

### Debug Commands
```bash
# Check database schema
uv run python -c "from server.database.db import engine; print(engine.table_names())"

# Test API connectivity
curl http://localhost:8000/health

# View server logs with debug info
LOG_LEVEL=DEBUG make run-server
```

### File Locations
- Database: `people_management.db`
- Logs: Console output (no file logging by default)
- Config: Environment variables and `pyproject.toml`
- Migrations: `server/database/migrations/versions/`

This project uses modern Python tooling with UV for dependency management, comprehensive testing, and follows FastAPI/SQLAlchemy best practices.