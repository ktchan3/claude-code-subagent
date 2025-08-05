# System Architecture

This document provides a comprehensive overview of the People Management System architecture, including system design, components, data flow, and technical decisions.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Patterns](#architecture-patterns)
- [Component Architecture](#component-architecture)
- [Database Design](#database-design)
- [API Design](#api-design)
- [Security Architecture](#security-architecture)
- [Data Flow](#data-flow)
- [Technology Stack](#technology-stack)
- [Design Decisions](#design-decisions)

## System Overview

The People Management System follows a client-server architecture with clear separation of concerns:

```
┌─────────────────────┐
│    Presentation     │  ← PySide6 GUI Client
│       Layer         │
└─────────────────────┘
          │ HTTP/REST
          ▼
┌─────────────────────┐
│    Application      │  ← FastAPI Server
│       Layer         │
└─────────────────────┘
          │ ORM
          ▼
┌─────────────────────┐
│     Data Access     │  ← SQLAlchemy
│       Layer         │
└─────────────────────┘
          │ SQL
          ▼
┌─────────────────────┐
│    Data Storage     │  ← SQLite Database
│       Layer         │
└─────────────────────┘
```

### Key Architectural Principles

1. **Separation of Concerns**: Clear boundaries between presentation, business logic, and data layers
2. **Modularity**: Loosely coupled components that can be developed and tested independently
3. **Scalability**: Design supports horizontal scaling of server components
4. **Maintainability**: Clean code structure with comprehensive documentation and testing
5. **Type Safety**: Strong typing throughout the application using Python type hints

## Architecture Patterns

### 1. Client-Server Pattern

The system uses a traditional client-server model where:
- **Client**: PySide6 GUI application handling user interface and user experience
- **Server**: FastAPI REST API handling business logic and data operations
- **Communication**: HTTP/REST with JSON payloads

### 2. Layered Architecture

Each component follows a layered architecture pattern:

#### Server Layers
```
┌─────────────────────┐
│   API Routes        │  ← HTTP endpoints, request/response handling
├─────────────────────┤
│   Business Logic    │  ← Core application logic, validation
├─────────────────────┤
│   Data Access       │  ← ORM models, database operations
├─────────────────────┤
│   Database          │  ← Data persistence layer
└─────────────────────┘
```

#### Client Layers
```
┌─────────────────────┐
│   UI Views          │  ← User interface components
├─────────────────────┤
│   Services          │  ← API communication, configuration
├─────────────────────┤
│   Models            │  ← Data models and validation
└─────────────────────┘
```

### 3. Repository Pattern

Database operations are abstracted through SQLAlchemy ORM, providing:
- Database vendor independence
- Query optimization
- Transaction management
- Migration support

## Component Architecture

### Server Component (`/server/`)

```
server/
├── main.py                 # FastAPI application factory
├── api/                    # API layer
│   ├── routes/            # REST endpoints
│   ├── schemas/           # Pydantic models for validation
│   ├── dependencies.py    # Dependency injection
│   └── middleware.py      # Custom middleware
├── core/                  # Core functionality
│   ├── config.py         # Configuration management
│   └── exceptions.py     # Custom exceptions
└── database/             # Data layer
    ├── models.py         # SQLAlchemy models
    ├── db.py            # Database connection
    └── migrations/       # Alembic migrations
```

#### Key Components

1. **FastAPI Application**: Central application instance with routing and middleware
2. **API Routes**: RESTful endpoints organized by domain (people, departments, etc.)
3. **Pydantic Schemas**: Request/response validation and serialization
4. **SQLAlchemy Models**: Database entity definitions with relationships
5. **Configuration**: Environment-based settings management

### Client Component (`/client/`)

```
client/
├── main.py                # Application entry point
├── ui/                    # User interface
│   ├── main_window.py    # Main application window
│   ├── views/            # Feature-specific views
│   └── widgets/          # Reusable UI components
├── services/             # Business services
│   ├── api_service.py    # HTTP client for API communication
│   └── config_service.py # Configuration management
└── resources/            # Static resources
    ├── icons/           # Application icons
    └── styles.qss       # Qt stylesheets
```

#### Key Components

1. **Main Window**: Central application window with navigation
2. **Views**: Feature-specific UI components (people, departments, etc.)
3. **Services**: Business logic and external communication
4. **Resources**: Static assets and styling

### Shared Component (`/shared/`)

Common utilities and models shared between client and server:

```
shared/
├── api_client.py         # HTTP client utilities
└── models/              # Shared data models
    ├── person.py        # Person-related models
    └── response.py      # API response models
```

## Database Design

### Entity Relationship Diagram

```
┌─────────────────┐         ┌─────────────────┐
│     Person      │         │   Department    │
├─────────────────┤         ├─────────────────┤
│ id (UUID)       │         │ id (UUID)       │
│ first_name      │         │ name            │
│ last_name       │         │ description     │
│ email           │         │ created_at      │
│ phone           │         │ updated_at      │
│ date_of_birth   │         └─────────────────┘
│ address         │                   │
│ city            │                   │ 1:N
│ state           │                   ▼
│ zip_code        │         ┌─────────────────┐
│ country         │         │    Position     │
│ created_at      │         ├─────────────────┤
│ updated_at      │         │ id (UUID)       │
└─────────────────┘         │ title           │
          │                 │ description     │
          │ 1:N             │ department_id   │
          ▼                 │ created_at      │
┌─────────────────┐         │ updated_at      │
│   Employment    │         └─────────────────┘
├─────────────────┤                   │
│ id (UUID)       │                   │ 1:N
│ person_id       │◄──────────────────┘
│ position_id     │
│ start_date      │
│ end_date        │
│ is_active       │
│ salary          │
│ created_at      │
│ updated_at      │
└─────────────────┘
```

### Database Schema

#### Person Table
- **Primary Key**: UUID for global uniqueness
- **Indexes**: Email (unique), name fields, location fields
- **Constraints**: Email format validation, required fields
- **Relationships**: One-to-many with Employment

#### Department Table
- **Primary Key**: UUID
- **Indexes**: Name (unique)
- **Constraints**: Non-empty name
- **Relationships**: One-to-many with Position

#### Position Table
- **Primary Key**: UUID
- **Foreign Keys**: Department ID
- **Indexes**: Department + title combination
- **Constraints**: Unique title per department
- **Relationships**: Many-to-one with Department, one-to-many with Employment

#### Employment Table
- **Primary Key**: UUID
- **Foreign Keys**: Person ID, Position ID
- **Indexes**: Person, position, dates, active status
- **Constraints**: Date validation, salary validation, active status logic
- **Relationships**: Many-to-one with Person and Position

### Database Features

1. **UUID Primary Keys**: Globally unique identifiers for all entities
2. **Timestamps**: Automatic created_at and updated_at for audit trail
3. **Constraints**: Data integrity through database-level constraints
4. **Indexes**: Optimized queries for common access patterns
5. **Migrations**: Version-controlled schema changes with Alembic

## API Design

### RESTful Principles

The API follows REST architectural constraints:

1. **Resource-Based URLs**: `/api/v1/people`, `/api/v1/departments`
2. **HTTP Methods**: GET, POST, PUT, DELETE for CRUD operations
3. **Stateless**: Each request contains all necessary information
4. **Uniform Interface**: Consistent response formats and error handling

### API Structure

```
/api/v1/
├── people/
│   ├── GET    /           # List people with pagination
│   ├── POST   /           # Create new person
│   ├── GET    /{id}       # Get person by ID
│   ├── PUT    /{id}       # Update person
│   └── DELETE /{id}       # Delete person
├── departments/
│   ├── GET    /           # List departments
│   ├── POST   /           # Create department
│   ├── GET    /{id}       # Get department by ID
│   ├── PUT    /{id}       # Update department
│   └── DELETE /{id}       # Delete department
├── positions/
│   └── ... (similar structure)
└── employment/
    └── ... (similar structure)
```

### Request/Response Format

#### Standard Response Format
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0",
    "request_id": "uuid"
  }
}
```

#### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": { ... }
  },
  "meta": {
    "timestamp": "2024-01-01T12:00:00Z",
    "version": "1.0.0",
    "request_id": "uuid"
  }
}
```

### API Features

1. **Versioning**: URL path versioning (`/api/v1/`)
2. **Pagination**: Cursor and offset-based pagination
3. **Filtering**: Query parameter-based filtering
4. **Sorting**: Multi-field sorting support
5. **Validation**: Pydantic model validation
6. **Documentation**: Automatic OpenAPI/Swagger documentation

## Security Architecture

### Security Layers

1. **Transport Security**: HTTPS in production
2. **Input Validation**: Pydantic model validation
3. **SQL Injection Prevention**: SQLAlchemy ORM parameterized queries
4. **Cross-Origin Resource Sharing (CORS)**: Configured allowed origins
5. **Error Handling**: Sanitized error messages in production

### Authentication & Authorization

The current implementation provides:
- Optional API key authentication
- Basic rate limiting
- Request ID tracking for audit trails

**Future Enhancements**:
- JWT-based authentication
- Role-based access control (RBAC)
- OAuth 2.0 integration
- Audit logging

### Data Protection

1. **Data Validation**: Server-side validation for all inputs
2. **SQL Injection Prevention**: ORM-based queries
3. **XSS Prevention**: Proper data encoding in responses
4. **Error Information**: Limited error details in production

## Data Flow

### Typical Request Flow

```
┌─────────────┐    1. User Action    ┌─────────────┐
│   Client    │────────────────────►│     UI      │
│   (User)    │                     │   Component │
└─────────────┘                     └─────────────┘
                                            │
                                   2. Service Call
                                            ▼
                                    ┌─────────────┐
                                    │ API Service │
                                    └─────────────┘
                                            │
                                   3. HTTP Request
                                            ▼
┌─────────────┐  4. SQL Query    ┌─────────────┐
│  Database   │◄─────────────────│ FastAPI     │
│             │                  │ Server      │
│             │  5. Result       │             │
│             │─────────────────►│             │
└─────────────┘                  └─────────────┘
                                            │
                                   6. HTTP Response
                                            ▼
                                    ┌─────────────┐
                                    │ API Service │
                                    └─────────────┘
                                            │
                                   7. Update UI
                                            ▼
                                    ┌─────────────┐
                                    │     UI      │
                                    │   Component │
                                    └─────────────┘
```

### Error Handling Flow

```
┌─────────────┐    Error Occurs    ┌─────────────┐
│   Server    │────────────────────►│  Exception  │
│             │                     │   Handler   │
└─────────────┘                     └─────────────┘
                                            │
                                   Log Error
                                            ▼
                                    ┌─────────────┐
                                    │   Logger    │
                                    └─────────────┘
                                            │
                                   Create Response
                                            ▼
                                    ┌─────────────┐
                                    │   Client    │
                                    │ (Error UI)  │
                                    └─────────────┘
```

## Technology Stack

### Backend Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Web Framework | FastAPI | >=0.104.0 | REST API development |
| ASGI Server | Uvicorn | >=0.24.0 | Production ASGI server |
| ORM | SQLAlchemy | >=2.0.0 | Database operations |
| Validation | Pydantic | >=2.5.0 | Data validation and serialization |
| Database | SQLite | Built-in | Data storage |
| Migrations | Alembic | >=1.13.0 | Database schema versioning |

### Frontend Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| GUI Framework | PySide6 | >=6.6.0 | Cross-platform GUI |
| HTTP Client | Requests | >=2.31.0 | API communication |
| Configuration | Python-dotenv | >=1.0.0 | Environment management |
| Security | Keyring | >=24.0.0 | Credential storage |

### Development Tools

| Tool | Purpose |
|------|---------|
| UV | Package management and virtual environments |
| Pytest | Testing framework |
| Ruff | Linting and formatting |
| Black | Code formatting |
| MyPy | Static type checking |
| Pre-commit | Git hooks automation |

## Design Decisions

### 1. FastAPI vs Django/Flask

**Decision**: FastAPI

**Rationale**:
- Modern async support
- Automatic API documentation
- Built-in data validation with Pydantic
- High performance
- Excellent type hint support

### 2. PySide6 vs PyQt6/Tkinter

**Decision**: PySide6

**Rationale**:
- Official Qt bindings for Python
- Modern, native-looking interface
- Cross-platform compatibility
- Rich widget ecosystem
- LGPL license compatibility

### 3. SQLite vs PostgreSQL/MySQL

**Decision**: SQLite for initial version

**Rationale**:
- Zero configuration
- Embedded database
- Perfect for development and small deployments
- Easy to backup and deploy
- Can migrate to PostgreSQL later if needed

### 4. SQLAlchemy 2.x vs Raw SQL

**Decision**: SQLAlchemy ORM

**Rationale**:
- Type safety with modern SQLAlchemy
- Database vendor independence
- Automatic query optimization
- Migration support with Alembic
- Relationship management

### 5. Workspace vs Monorepo

**Decision**: UV workspace (monorepo)

**Rationale**:
- Shared dependencies management
- Atomic changes across components
- Simplified development workflow
- Consistent tooling across all components

### 6. UUID vs Integer IDs

**Decision**: UUID primary keys

**Rationale**:
- Globally unique identifiers
- No collision in distributed systems
- Security through obscurity
- Future-proof for scaling

### Future Architecture Considerations

1. **Microservices**: Consider splitting into separate services as the system grows
2. **Caching**: Add Redis for caching frequently accessed data
3. **Message Queue**: Implement async processing with Celery/RQ
4. **Database**: Migrate to PostgreSQL for production deployments
5. **Authentication**: Implement OAuth 2.0 and JWT tokens
6. **Monitoring**: Add application performance monitoring (APM)
7. **Container Deployment**: Docker containerization for easier deployment

---

This architecture provides a solid foundation for the People Management System while remaining flexible for future enhancements and scaling requirements.