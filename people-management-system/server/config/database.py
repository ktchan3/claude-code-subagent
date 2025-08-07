"""
Database-specific configuration settings.

This module provides database configuration with support for different
database backends and connection pool settings.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class DatabaseBackend(str, Enum):
    """Supported database backends."""
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"


class DatabaseConfig(BaseModel):
    """
    Database configuration with support for multiple backends.
    
    Provides configuration for database connections, connection pooling,
    and database-specific settings.
    """
    
    # Connection settings
    url: str = Field(
        default="sqlite:///./people_management.db",
        description="Database connection URL"
    )
    backend: DatabaseBackend = Field(
        default=DatabaseBackend.SQLITE,
        description="Database backend type"
    )
    
    # Connection pool settings
    pool_size: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Size of the connection pool"
    )
    max_overflow: int = Field(
        default=10,
        ge=0,
        le=100,
        description="Number of connections that can overflow the pool"
    )
    pool_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout in seconds for getting connection from pool"
    )
    pool_recycle: int = Field(
        default=3600,
        ge=300,
        le=86400,
        description="Time in seconds after which connection is recycled"
    )
    
    # Query and performance settings
    echo: bool = Field(
        default=False,
        description="Enable SQL query logging"
    )
    echo_pool: bool = Field(
        default=False,
        description="Enable connection pool logging"
    )
    
    # Transaction settings
    autocommit: bool = Field(
        default=False,
        description="Enable autocommit mode"
    )
    isolation_level: Optional[str] = Field(
        default=None,
        description="Transaction isolation level"
    )
    
    # SQLite-specific settings
    sqlite_pragma: Dict[str, Any] = Field(
        default_factory=lambda: {
            "journal_mode": "WAL",
            "cache_size": -2000,  # 2MB cache
            "foreign_keys": 1,
            "synchronous": "NORMAL",
            "temp_store": "memory",
            "mmap_size": 268435456,  # 256MB
        },
        description="SQLite PRAGMA settings"
    )
    
    # PostgreSQL-specific settings
    postgresql_schema: Optional[str] = Field(
        default=None,
        description="Default PostgreSQL schema"
    )
    postgresql_sslmode: str = Field(
        default="prefer",
        description="PostgreSQL SSL mode"
    )
    
    # MySQL-specific settings
    mysql_charset: str = Field(
        default="utf8mb4",
        description="MySQL character set"
    )
    mysql_sql_mode: str = Field(
        default="STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO",
        description="MySQL SQL mode"
    )
    
    # Migration settings
    migration_timeout: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Timeout in seconds for migration operations"
    )
    auto_migrate: bool = Field(
        default=True,
        description="Automatically run migrations on startup"
    )
    
    # Backup and maintenance settings
    backup_enabled: bool = Field(
        default=True,
        description="Enable automatic backups"
    )
    backup_interval_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Backup interval in hours"
    )
    backup_retention_days: int = Field(
        default=30,
        ge=1,
        le=365,
        description="Number of days to retain backups"
    )
    
    # Monitoring settings
    slow_query_threshold: float = Field(
        default=1.0,
        ge=0.1,
        le=60.0,
        description="Slow query threshold in seconds"
    )
    log_slow_queries: bool = Field(
        default=True,
        description="Log queries slower than threshold"
    )
    
    @field_validator("backend", mode="before")
    @classmethod
    def detect_backend_from_url(cls, v, values):
        """Auto-detect database backend from URL if not specified."""
        if isinstance(values, dict) and "url" in values:
            url = values["url"]
            if url.startswith("sqlite"):
                return DatabaseBackend.SQLITE
            elif url.startswith("postgresql"):
                return DatabaseBackend.POSTGRESQL
            elif url.startswith("mysql"):
                return DatabaseBackend.MYSQL
        return v
    
    @field_validator("isolation_level")
    @classmethod
    def validate_isolation_level(cls, v):
        """Validate transaction isolation level."""
        if v is not None:
            valid_levels = [
                "READ_UNCOMMITTED", "READ_COMMITTED", 
                "REPEATABLE_READ", "SERIALIZABLE"
            ]
            if v.upper() not in valid_levels:
                raise ValueError(f"Isolation level must be one of: {valid_levels}")
            return v.upper()
        return v
    
    def get_engine_options(self) -> Dict[str, Any]:
        """
        Get SQLAlchemy engine options for this configuration.
        
        Returns:
            Dictionary of engine options
        """
        options = {
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
        }
        
        # Add isolation level if specified
        if self.isolation_level:
            options["isolation_level"] = self.isolation_level
        
        # Backend-specific options
        if self.backend == DatabaseBackend.SQLITE:
            options.update({
                "connect_args": {
                    "check_same_thread": False,
                    **{f"PRAGMA {key} = {value}": None for key, value in self.sqlite_pragma.items()}
                }
            })
        elif self.backend == DatabaseBackend.POSTGRESQL:
            connect_args = {}
            if self.postgresql_sslmode:
                connect_args["sslmode"] = self.postgresql_sslmode
            if self.postgresql_schema:
                connect_args["options"] = f"-csearch_path={self.postgresql_schema}"
            if connect_args:
                options["connect_args"] = connect_args
        elif self.backend == DatabaseBackend.MYSQL:
            options.update({
                "connect_args": {
                    "charset": self.mysql_charset,
                    "sql_mode": self.mysql_sql_mode,
                }
            })
        
        return options
    
    def get_backup_settings(self) -> Dict[str, Any]:
        """
        Get backup configuration settings.
        
        Returns:
            Dictionary of backup settings
        """
        return {
            "enabled": self.backup_enabled,
            "interval_hours": self.backup_interval_hours,
            "retention_days": self.backup_retention_days,
        }
    
    def get_monitoring_settings(self) -> Dict[str, Any]:
        """
        Get monitoring configuration settings.
        
        Returns:
            Dictionary of monitoring settings
        """
        return {
            "slow_query_threshold": self.slow_query_threshold,
            "log_slow_queries": self.log_slow_queries,
        }