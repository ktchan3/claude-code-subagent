# People Management System Database

This directory contains the complete database implementation for the People Management System, built with SQLAlchemy ORM and SQLite.

## Overview

The database system provides:

- **Complete schema** for managing people, departments, positions, and employment records
- **SQLAlchemy ORM models** with proper relationships and constraints
- **Database initialization** and connection management
- **Migration support** using Alembic
- **Sample data seeding** for development and testing
- **Performance optimization** with proper indexes
- **Health monitoring** and maintenance utilities

## Database Schema

### Core Tables

1. **People** - Individual records with personal information
   - Primary key: UUID
   - Fields: names, email, phone, birth date, address
   - Indexes: email (unique), names, location

2. **Departments** - Organizational departments
   - Primary key: UUID
   - Fields: name (unique), description
   - Indexes: name

3. **Positions** - Job positions within departments
   - Primary key: UUID
   - Fields: title, description, department_id
   - Indexes: title, department relationship
   - Constraints: unique title per department

4. **Employment** - Links people to positions
   - Primary key: UUID
   - Fields: person_id, position_id, dates, salary, active status
   - Indexes: person/position relationships, dates, salary, active status
   - Constraints: proper date logic, salary validation

### Relationships

- **Department → Positions**: One-to-many (cascade delete)
- **Person → Employments**: One-to-many (cascade delete)
- **Position → Employments**: One-to-many (cascade delete)

### Key Features

- **UUID primary keys** for better security and distributed systems support
- **Automatic timestamps** (created_at, updated_at) on all tables
- **Comprehensive validation** with custom validators
- **Performance indexes** for common query patterns
- **SQLite optimizations** with WAL mode and pragma settings
- **Foreign key constraints** properly enforced
- **Case-insensitive search** support with functional indexes

## Files Structure

```
server/database/
├── __init__.py          # Package exports and convenient imports
├── models.py            # SQLAlchemy ORM models
├── db.py               # Database connection and session management
├── config.py           # Database configuration settings
├── seeders.py          # Sample data creation utilities
├── init_db.py          # Database initialization CLI script
├── migrations/         # Alembic migration files
│   ├── env.py
│   ├── script.py.mako
│   └── versions/       # Migration version files
└── README.md           # This file
```

## Usage

### Quick Start

1. **Initialize the database with sample data:**
   ```bash
   python manage_db.py init --seed
   ```

2. **Check database status:**
   ```bash
   python manage_db.py status
   ```

### Database Management Commands

The system provides a comprehensive CLI for database operations:

```bash
# Initialize database schema
python manage_db.py init

# Initialize with sample data
python manage_db.py init --seed

# Reset database (WARNING: deletes all data)
python manage_db.py reset --seed

# Show database status and health
python manage_db.py status

# Add sample data to existing database
python manage_db.py seed

# Clear all data (WARNING: destructive)
python manage_db.py clear

# Optimize database performance
python manage_db.py optimize
```

### Python API Usage

```python
from server.database import (
    initialize_database,
    get_db_session,
    Person, Department, Position, Employment,
    seed_database
)

# Initialize database
initialize_database()

# Use database session
with get_db_session() as session:
    # Query people
    people = session.query(Person).all()
    
    # Create new person
    person = Person(
        first_name="John",
        last_name="Doe",
        email="john.doe@company.com"
    )
    session.add(person)
    session.commit()

# Seed with sample data
results = seed_database()
print(f"Created: {results}")
```

### FastAPI Integration

```python
from fastapi import Depends
from server.database import get_db, Person

@app.get("/people")
def get_people(db: Session = Depends(get_db)):
    return db.query(Person).all()
```

## Configuration

Database settings can be configured via environment variables or `.env` file:

```env
# Database connection
DB_DATABASE_URL=sqlite:///./people_management.db
DB_SQLITE_DB_PATH=./people_management.db

# Connection pool settings
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# Development settings
DB_ECHO_SQL=false
DB_ECHO_POOL=false

# Test database
DB_TEST_DATABASE_URL=sqlite:///./test_people_management.db
```

## Development and Testing

### Sample Data

The seeder creates realistic sample data:
- 7 departments (Engineering, HR, Marketing, Sales, Finance, Operations, Customer Success)
- 25+ positions across departments
- 10 people with realistic information
- Employment records with proper relationships and salary ranges

### Database Health Monitoring

The system includes comprehensive health checking:

```python
from server.database import health_check, get_database_info

# Quick health check
health = health_check()
print(f"Database healthy: {health['database_connected']}")

# Detailed information
info = get_database_info()
print(f"Database type: {info['database_type']}")
print(f"Tables: {info['tables']}")
```

### Performance Optimization

The database includes several performance optimizations:

1. **Strategic Indexes:**
   - Email lookups (unique constraint)
   - Name searches (case-insensitive)
   - Employment queries (person, position, dates, salary)
   - Department and position lookups

2. **SQLite Optimizations:**
   - WAL mode for better concurrency
   - Increased cache size (64MB)
   - Memory temp storage
   - Query planner optimizations

3. **Connection Management:**
   - Connection pooling with StaticPool
   - Proper connection cleanup
   - Automatic pragma settings

### Migrations with Alembic

Generate migrations when models change:

```bash
# Generate migration (requires alembic installation)
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade if needed
alembic downgrade -1
```

## Best Practices

### Model Design
- Use UUID primary keys for better scalability
- Include timestamp fields for audit trails
- Add proper validation with SQLAlchemy validators
- Use appropriate column types and constraints

### Query Optimization
- Use indexes for frequently queried columns
- Consider using `select_in_loading` for relationships
- Use session management properly with context managers
- Implement proper error handling

### Data Integrity
- Define foreign key relationships properly
- Use constraints to enforce business rules
- Validate data at the model level
- Handle cascade deletes appropriately

### Connection Management
- Use context managers for sessions
- Implement proper connection pooling
- Handle database errors gracefully
- Clean up connections on shutdown

## Troubleshooting

### Common Issues

1. **Database locked errors:**
   - Check for long-running transactions
   - Ensure proper session cleanup
   - Consider increasing timeout settings

2. **Migration errors:**
   - Verify model imports in alembic env.py
   - Check for naming conflicts
   - Ensure database is accessible

3. **Performance issues:**
   - Run database optimization (`manage_db.py optimize`)
   - Check for missing indexes
   - Analyze query patterns

### Debugging

Enable SQL logging for debugging:

```python
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

Or set environment variable:
```env
DB_ECHO_SQL=true
```

## Security Considerations

- Use UUID primary keys to prevent enumeration attacks
- Implement proper input validation
- Use parameterized queries (SQLAlchemy handles this)
- Consider encryption for sensitive data
- Implement proper access controls at the application level
- Regular database backups and security updates

## Maintenance

### Regular Tasks

1. **Run VACUUM periodically** to optimize storage:
   ```bash
   python manage_db.py optimize
   ```

2. **Monitor database health:**
   ```bash
   python manage_db.py status
   ```

3. **Backup database files** regularly (SQLite files)

4. **Review and clean up old data** as needed

5. **Update dependencies** and security patches

### Monitoring Metrics

Track these metrics for production systems:
- Connection pool utilization
- Query performance
- Database file size
- Error rates
- Response times
- Active vs. terminated employment ratios