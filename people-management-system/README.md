# People Management System

A comprehensive client-server application for managing people, departments, positions, and employment records. Built with modern Python technologies including FastAPI, PySide6, and SQLAlchemy.

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- UV (Python package installer and project manager)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd people-management-system
```

2. Install dependencies:
```bash
make dev-install
# or manually: uv sync
```

3. Set up the database:
```bash
make setup-db
# or manually: uv run alembic upgrade head
```

4. Run the application:

**Start the server:**
```bash
make run-server
# or manually: uv run uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

**Start the client (in a separate terminal):**
```bash
make run-client
# or manually: uv run python -m client.main
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## 📋 Overview

The People Management System is a modern, full-featured application designed to manage organizational data including:

- **People**: Employee personal information, contact details, and employment history
- **Departments**: Organizational structure and department management
- **Positions**: Job roles and position definitions within departments
- **Employment Records**: Current and historical employment relationships

### Key Features

- **Modern REST API**: Built with FastAPI, featuring automatic OpenAPI documentation
- **Rich GUI Client**: Native desktop application using PySide6 with a modern interface
- **Robust Database**: SQLAlchemy ORM with SQLite backend and migration support
- **Type Safety**: Full type hints throughout the codebase with Pydantic validation
- **Comprehensive Testing**: Unit tests for all components with pytest
- **Code Quality**: Automated formatting, linting, and type checking
- **Developer Experience**: Hot reload, comprehensive error handling, and detailed logging

## 🏗️ Architecture

The system follows a clean, modular architecture:

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

### Components

1. **Server (`/server/`)**: FastAPI-based REST API
2. **Client (`/client/`)**: PySide6 desktop GUI application
3. **Shared (`/shared/`)**: Common models and utilities
4. **Database**: SQLite with SQLAlchemy ORM and Alembic migrations

## 🛠️ Technology Stack

### Backend (Server)
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy 2.x**: Python SQL toolkit and ORM
- **Alembic**: Database migration tool
- **Pydantic**: Data validation using Python type annotations
- **Uvicorn**: ASGI server implementation
- **SQLite**: Lightweight, serverless database

### Frontend (Client)
- **PySide6**: Official Python bindings for Qt
- **Qt**: Cross-platform GUI framework
- **Requests**: HTTP library for API communication
- **Keyring**: Secure credential storage

### Development Tools
- **UV**: Fast Python package installer and project manager
- **Pytest**: Testing framework
- **Ruff**: Fast Python linter and formatter
- **Black**: Code formatter
- **MyPy**: Static type checker
- **Pre-commit**: Git hooks framework

## 📁 Project Structure

```
people-management-system/
├── client/                 # PySide6 GUI client
│   ├── main.py            # Application entry point
│   ├── services/          # API and configuration services
│   ├── ui/                # User interface components
│   │   ├── views/         # Main application views
│   │   └── widgets/       # Reusable UI widgets
│   └── resources/         # Icons, styles, and themes
├── server/                # FastAPI REST API server
│   ├── main.py           # FastAPI application
│   ├── api/              # API routes and middleware
│   │   ├── routes/       # Endpoint definitions
│   │   └── schemas/      # Pydantic models for API
│   ├── core/             # Core configuration and exceptions
│   └── database/         # Database models and migrations
├── shared/               # Shared utilities and models
├── docs/                 # Documentation
├── Makefile             # Development automation
├── pyproject.toml       # Project configuration
├── uv.lock             # Dependency lock file
└── alembic.ini         # Database migration configuration
```

## 🎯 Usage Examples

### API Usage

The REST API provides comprehensive endpoints for all operations:

```bash
# Get all people
curl http://localhost:8000/api/v1/people

# Create a new person
curl -X POST http://localhost:8000/api/v1/people \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1-555-123-4567"
  }'

# Get person by ID
curl http://localhost:8000/api/v1/people/{person_id}
```

### Client GUI

The PySide6 client provides a user-friendly interface with:

- **Dashboard**: Overview of system statistics and recent activity
- **People Management**: Add, edit, search, and manage person records
- **Department Management**: Organize departments and their positions
- **Employment Tracking**: Manage current and historical employment records
- **Search and Filtering**: Advanced search capabilities across all entities

## 🔧 Development Setup

### Environment Setup

1. **Install UV** (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Set up development environment**:
```bash
# Install development dependencies
make dev-install

# Set up pre-commit hooks
uv run pre-commit install

# Initialize database
make setup-db
```

### Development Workflow

```bash
# Format code
make format

# Run linting
make lint

# Run tests
make test

# Run tests with coverage
make test-coverage

# Clean build artifacts
make clean
```

### Database Operations

```bash
# Create a new migration
make create-migration name="add_new_field"

# Apply migrations
make setup-db

# Reset database (warning: destroys data)
make reset-db
```

## 📚 Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)**: Detailed system architecture and design decisions
- **[Development Guide](docs/DEVELOPMENT.md)**: Setup, workflows, and contribution guidelines
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Production deployment and configuration
- **[API Reference](docs/API.md)**: Complete API documentation and examples

## 🖼️ Screenshots

*Screenshots will be added here to showcase the application interface*

### Dashboard View
*[Screenshot of the main dashboard showing system overview]*

### People Management
*[Screenshot of the people management interface]*

### Department Structure
*[Screenshot of department and position management]*

## 🧪 Testing

The project includes comprehensive test coverage:

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# Run specific test file
uv run pytest tests/test_api.py -v
```

Test coverage includes:
- API endpoint testing
- Database model validation
- GUI component testing
- Integration tests
- Performance benchmarks

## 🚀 Deployment

For production deployment, see the [Deployment Guide](docs/DEPLOYMENT.md) which covers:

- Environment configuration
- Database setup and optimization
- Security considerations
- Performance tuning
- Monitoring and logging
- Backup strategies

## 🤝 Contributing

We welcome contributions! Please see our [Development Guide](docs/DEVELOPMENT.md) for:

- Code style guidelines
- Development workflow
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please:

1. Check the documentation in the `docs/` directory
2. Search existing issues on GitHub
3. Create a new issue with detailed information
4. Contact the development team

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

---

**Built with ❤️ using modern Python technologies**