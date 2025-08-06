"""
Database configuration for the people management system.

This module provides database configuration settings including SQLite connection
parameters, connection pooling, and environment-specific configurations.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from typing import Optional
from sqlalchemy.pool import StaticPool


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    
    # Database connection settings
    database_url: str = Field(
        default="sqlite:///./people_management.db",
        description="Database connection URL"
    )
    
    # SQLite specific settings
    sqlite_db_path: str = Field(
        default="./people_management.db",
        description="Path to SQLite database file"
    )
    
    # Connection pool settings for SQLite
    pool_size: int = Field(
        default=5,
        description="Connection pool size"
    )
    
    max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections"
    )
    
    pool_timeout: int = Field(
        default=30,
        description="Connection pool timeout in seconds"
    )
    
    pool_recycle: int = Field(
        default=3600,
        description="Connection pool recycle time in seconds"
    )
    
    # SQLite specific connection arguments
    sqlite_connect_args: dict = Field(
        default_factory=lambda: {
            "check_same_thread": False,  # Allow SQLite to be used across threads
            "timeout": 20,  # Connection timeout
            "isolation_level": None,  # Use autocommit mode
        },
        description="SQLite connection arguments"
    )
    
    # Database behavior settings
    echo_sql: bool = Field(
        default=False,
        description="Echo SQL statements to console"
    )
    
    echo_pool: bool = Field(
        default=False,
        description="Echo connection pool activity to console"
    )
    
    # Migration settings
    migrations_dir: str = Field(
        default="server/database/migrations",
        description="Directory for database migrations"
    )
    
    # Test database settings
    test_database_url: str = Field(
        default="sqlite:///./test_people_management.db",
        description="Test database connection URL"
    )
    
    test_sqlite_db_path: str = Field(
        default="./test_people_management.db",
        description="Path to test SQLite database file"
    )
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="DB_",
        case_sensitive=False
    )


def get_database_settings() -> DatabaseSettings:
    """Get database settings instance."""
    return DatabaseSettings()


def ensure_database_directory() -> None:
    """Ensure the database directory exists."""
    settings = get_database_settings()
    db_path = Path(settings.sqlite_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)


def get_database_url(testing: bool = False) -> str:
    """
    Get the database URL for the current environment.
    
    Args:
        testing: Whether to use test database URL
        
    Returns:
        Database connection URL
    """
    settings = get_database_settings()
    
    if testing:
        return settings.test_database_url
    
    # Check for environment variable override
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]
    
    return settings.database_url


def get_sqlite_connect_args() -> dict:
    """Get SQLite connection arguments."""
    settings = get_database_settings()
    return settings.sqlite_connect_args


def get_engine_kwargs(testing: bool = False) -> dict:
    """
    Get SQLAlchemy engine configuration.
    
    Args:
        testing: Whether this is for testing
        
    Returns:
        Dictionary of engine configuration parameters
    """
    settings = get_database_settings()
    
    engine_kwargs = {
        "echo": settings.echo_sql,
        "echo_pool": settings.echo_pool,
        "connect_args": get_sqlite_connect_args(),
    }
    
    # For SQLite, we use StaticPool for connection pooling
    # to ensure proper handling of the single-file database
    # Note: SQLite doesn't support all pool parameters
    if 'sqlite' in get_database_url(testing).lower():
        engine_kwargs.update({
            "poolclass": StaticPool,
        })
    else:
        # For other databases, include pool parameters
        engine_kwargs.update({
            "pool_timeout": settings.pool_timeout,
            "pool_recycle": settings.pool_recycle,
        })
    
    if testing:
        # For testing, use in-memory database or separate test file
        engine_kwargs["echo"] = False  # Reduce noise in tests
    
    return engine_kwargs


# Global settings instance
database_settings = get_database_settings()