# People Management System API

A comprehensive FastAPI-based REST API for managing people, departments, positions, and employment records.

## Features

### Core Functionality
- **People Management**: CRUD operations for individuals with personal information
- **Department Management**: Organize positions into departments
- **Position Management**: Define roles within departments
- **Employment Management**: Track employment relationships, history, and transitions
- **Statistics & Analytics**: Comprehensive reporting and insights

### Technical Features
- **FastAPI Framework**: Modern, fast, and well-documented API
- **SQLAlchemy ORM**: Robust database operations with relationship management
- **Pydantic Validation**: Automatic request/response validation and serialization
- **Comprehensive Error Handling**: Detailed error responses with proper HTTP status codes
- **Middleware Stack**: Request logging, security headers, rate limiting, and CORS
- **Database Health Checks**: Monitor database connectivity and performance
- **Pagination**: Efficient handling of large datasets
- **Advanced Search**: Flexible filtering and search capabilities
- **Bulk Operations**: Create multiple records in single requests

## Project Structure

```
server/
├── main.py                 # FastAPI application entry point
├── run.py                  # Development server runner
├── api/                    # API layer
│   ├── dependencies.py     # Common dependencies and utilities
│   ├── middleware.py       # Custom middleware components
│   ├── routes/            # API endpoint definitions
│   │   ├── people.py      # People management endpoints
│   │   ├── departments.py # Department management endpoints
│   │   ├── positions.py   # Position management endpoints
│   │   ├── employment.py  # Employment management endpoints
│   │   └── statistics.py  # Statistics and analytics endpoints
│   └── schemas/           # Pydantic models for requests/responses
│       ├── common.py      # Shared schemas and utilities
│       ├── person.py      # Person-related schemas
│       ├── department.py  # Department-related schemas
│       ├── position.py    # Position-related schemas
│       └── employment.py  # Employment-related schemas
├── core/                  # Core application components
│   ├── config.py         # Application configuration and settings
│   └── exceptions.py     # Custom exception definitions
└── database/             # Database layer (inherited)
    ├── models.py         # SQLAlchemy database models
    ├── db.py            # Database connection and session management
    └── config.py        # Database configuration
```

## Quick Start

### Prerequisites

- Python 3.8+
- SQLite (included with Python)
- Dependencies listed in `pyproject.toml`

### Installation

1. **Navigate to the server directory**:
   ```bash
   cd server/
   ```

2. **Install dependencies** (if using uv):
   ```bash
   uv sync
   ```

3. **Initialize the database** (optional, will be created automatically):
   ```bash
   python run.py --init-db
   ```

4. **Start the development server**:
   ```bash
   python run.py
   ```

   Or with auto-reload:
   ```bash
   python run.py --reload
   ```

   Or with debug mode:
   ```bash
   python run.py --debug --reload
   ```

### Using the API

Once the server is running, you can access:

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Health Check**: http://localhost:8000/health
- **System Status**: http://localhost:8000/status

## API Endpoints

### Core Resources

#### People (`/api/v1/people`)
- `GET /` - List people with pagination and search
- `POST /` - Create a new person
- `GET /{id}` - Get person details
- `PUT /{id}` - Update person information
- `PATCH /{id}/contact` - Update contact information only
- `PATCH /{id}/address` - Update address information only
- `DELETE /{id}` - Delete person
- `GET /{id}/employment` - Get person with employment history
- `GET /by-email/{email}` - Find person by email
- `GET /search/advanced` - Advanced search with filters
- `POST /bulk` - Bulk create people

#### Departments (`/api/v1/departments`)
- `GET /` - List departments with pagination
- `POST /` - Create a new department
- `GET /{id}` - Get department details
- `PUT /{id}` - Update department
- `DELETE /{id}` - Delete department
- `GET /{id}/positions` - Get department with positions
- `GET /{id}/employees` - Get department with employees
- `GET /{id}/statistics` - Get department statistics
- `GET /search/advanced` - Advanced search
- `POST /bulk` - Bulk create departments

#### Positions (`/api/v1/positions`)
- `GET /` - List positions with pagination
- `POST /` - Create a new position
- `GET /{id}` - Get position details
- `PUT /{id}` - Update position
- `DELETE /{id}` - Delete position
- `GET /{id}/employees` - Get position with employees
- `GET /{id}/history` - Get position employment history
- `GET /{id}/statistics` - Get position statistics
- `POST /{id}/transfer` - Transfer position to another department
- `GET /search/advanced` - Advanced search
- `POST /bulk` - Bulk create positions

#### Employment (`/api/v1/employment`)
- `GET /` - List employment records with pagination
- `POST /` - Create employment record
- `GET /{id}` - Get employment details
- `PUT /{id}` - Update employment
- `DELETE /{id}` - Delete employment record
- `POST /{id}/terminate` - Terminate employment
- `POST /{id}/transfer` - Transfer employee to new position
- `GET /person/{id}` - Get employment history for person
- `GET /search/advanced` - Advanced search
- `GET /statistics/overview` - Employment statistics
- `POST /bulk` - Bulk create employment records

#### Statistics (`/api/v1/statistics`)
- `GET /overview` - System overview statistics
- `GET /departments` - Department statistics
- `GET /positions` - Position statistics
- `GET /salary` - Salary analysis and statistics
- `GET /tenure` - Employee tenure statistics
- `GET /hiring-trends` - Hiring trends over time

### System Endpoints

- `GET /` - API root information
- `GET /health` - Health check
- `GET /version` - API version
- `GET /status` - Detailed system status

## Configuration

The API can be configured through environment variables or a `.env` file:

### Application Settings
```bash
APP_DEBUG=false                    # Debug mode
APP_HOST=0.0.0.0                  # Server host
APP_PORT=8000                     # Server port
APP_RELOAD=false                  # Auto-reload on changes
```

### CORS Settings
```bash
APP_CORS_ORIGINS=http://localhost:3000,http://localhost:3001
APP_CORS_CREDENTIALS=true
APP_CORS_METHODS=*
APP_CORS_HEADERS=*
```

### Database Settings
```bash
APP_DATABASE_URL=sqlite:///./people_management.db
```

### Rate Limiting
```bash
APP_RATE_LIMIT_PER_MINUTE=60      # Requests per minute per IP
```

### Pagination
```bash
APP_DEFAULT_PAGE_SIZE=20          # Default page size
APP_MAX_PAGE_SIZE=100            # Maximum page size
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=server

# Run specific test file
python -m pytest tests/test_people.py
```

### Code Quality

```bash
# Format code
black server/

# Lint code
flake8 server/

# Type checking
mypy server/
```

### Database Management

```bash
# Initialize database
python run.py --init-db

# Reset database (drops all data)
python -c "from server.database.db import reset_database; reset_database()"

# Run database health check
python -c "from server.database.db import health_check; print(health_check())"
```

## API Usage Examples

### Create a Person
```bash
curl -X POST "http://localhost:8000/api/v1/people" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567"
  }'
```

### Create a Department
```bash
curl -X POST "http://localhost:8000/api/v1/departments" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Engineering",
    "description": "Software development team"
  }'
```

### Create a Position
```bash
curl -X POST "http://localhost:8000/api/v1/positions" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Engineer",
    "description": "Develops and maintains software applications",
    "department_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

### Create Employment
```bash
curl -X POST "http://localhost:8000/api/v1/employment" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "111e1111-e11b-11d1-a111-426614174111",
    "position_id": "456e7890-e12b-34d5-a678-426614174111",
    "start_date": "2024-01-15",
    "salary": 85000.00
  }'
```

### Search People
```bash
curl "http://localhost:8000/api/v1/people/search/advanced?name=john&department=Engineering&active_only=true"
```

### Get Statistics
```bash
curl "http://localhost:8000/api/v1/statistics/overview"
```

## Error Handling

The API uses standard HTTP status codes and returns consistent error responses:

```json
{
  "error": true,
  "message": "Person with ID 'invalid-id' not found",
  "status_code": 404,
  "path": "/api/v1/people/invalid-id",
  "timestamp": 1704067200.123
}
```

### Common Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `409` - Conflict (duplicate resources)
- `422` - Unprocessable Entity (business logic errors)
- `429` - Too Many Requests (rate limiting)
- `500` - Internal Server Error

## Security Features

- **CORS**: Configurable cross-origin resource sharing
- **Rate Limiting**: Per-IP request rate limiting
- **Security Headers**: Comprehensive security headers
- **Input Validation**: Strict input validation using Pydantic
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Error Sanitization**: Sensitive information filtered from error responses

## Performance Features

- **Database Connection Pooling**: Efficient database connection management
- **Pagination**: Memory-efficient data retrieval
- **Lazy Loading**: Optimized relationship loading
- **Database Indexes**: Optimized query performance
- **Response Caching**: Configurable response caching headers

## Monitoring and Observability

- **Health Checks**: Database and system health monitoring
- **Request Logging**: Comprehensive request/response logging
- **Error Tracking**: Detailed error logging and tracking
- **Performance Metrics**: Request timing and performance monitoring
- **Database Statistics**: Connection pool and query performance metrics

## Production Deployment

### Using Uvicorn directly
```bash
uvicorn server.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn with Uvicorn workers
```bash
gunicorn server.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Configuration
Set `APP_DEBUG=false` for production and configure appropriate database, CORS, and security settings.

## License

This project is part of the People Management System and follows the same licensing terms.