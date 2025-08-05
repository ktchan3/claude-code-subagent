"""
Database module for the people management server.

Contains SQLAlchemy models, database configuration, connection management,
and utilities for database operations.
"""

# Import main database components for easy access
from .models import Base, Person, Department, Position, Employment
from .db import (
    initialize_database,
    get_db_session,
    create_db_session,
    get_db,  # FastAPI dependency
    check_database_connection,
    health_check,
    get_database_info
)
from .config import get_database_settings, get_database_url
from .seeders import seed_database, clear_all_data, DatabaseSeeder

__all__ = [
    # Models
    'Base',
    'Person',
    'Department', 
    'Position',
    'Employment',
    
    # Database operations
    'initialize_database',
    'get_db_session',
    'create_db_session',
    'get_db',
    'check_database_connection',
    'health_check',
    'get_database_info',
    
    # Configuration
    'get_database_settings',
    'get_database_url',
    
    # Seeding
    'seed_database',
    'clear_all_data',
    'DatabaseSeeder',
]