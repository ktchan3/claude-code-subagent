"""
Application configuration settings for the People Management System API.

This module provides centralized configuration management using Pydantic settings
with support for environment variables and default values.
"""

import os
from functools import lru_cache
from typing import List, Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden using environment variables with the
    APP_ prefix (e.g., APP_DEBUG=true, APP_DATABASE_URL=sqlite:///test.db).
    """
    
    # Application metadata
    app_name: str = Field(default="People Management System API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    app_description: str = Field(
        default="A comprehensive API for managing people, departments, positions, and employment records",
        description="Application description"
    )
    
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    
    # API configuration
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    docs_url: str = Field(default="/docs", description="OpenAPI docs URL")
    redoc_url: str = Field(default="/redoc", description="ReDoc URL")
    openapi_url: str = Field(default="/openapi.json", description="OpenAPI schema URL")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001"
        ],
        description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(default=True, description="Allow credentials in CORS")
    cors_methods: List[str] = Field(default=["*"], description="Allowed CORS methods")
    cors_headers: List[str] = Field(default=["*"], description="Allowed CORS headers")
    
    # Database settings (inherited from database config)
    database_url: str = Field(
        default="sqlite:///./people_management.db",
        description="Database connection URL"
    )
    
    # Security settings
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT and other cryptographic operations"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration time in minutes"
    )
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    
    # Pagination settings
    default_page_size: int = Field(default=20, description="Default page size for pagination")
    max_page_size: int = Field(default=100, description="Maximum page size for pagination")
    
    # Rate limiting settings
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute per IP")
    
    # File upload settings
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum file size in bytes (10MB)")
    allowed_file_types: List[str] = Field(
        default=["image/jpeg", "image/png", "image/gif", "application/pdf"],
        description="Allowed file MIME types"
    )
    
    # Cache settings
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    
    # Health check settings
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Parse CORS origins from environment variable."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("cors_methods", mode="before")
    @classmethod
    def assemble_cors_methods(cls, v):
        """Parse CORS methods from environment variable."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("cors_headers", mode="before")
    @classmethod
    def assemble_cors_headers(cls, v):
        """Parse CORS headers from environment variable."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def assemble_allowed_file_types(cls, v):
        """Parse allowed file types from environment variable."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @field_validator("default_page_size", "max_page_size")
    @classmethod
    def validate_page_sizes(cls, v):
        """Validate pagination sizes."""
        if v <= 0:
            raise ValueError("Page size must be greater than 0")
        return v
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="APP_",
        case_sensitive=False
    )


class TestSettings(Settings):
    """Test-specific settings that override base settings."""
    
    debug: bool = True
    database_url: str = "sqlite:///./test_people_management.db"
    log_level: str = "DEBUG"
    
    # Disable rate limiting in tests
    rate_limit_per_minute: int = 1000
    
    # Smaller pagination for faster tests
    default_page_size: int = 5
    max_page_size: int = 20


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    The settings are cached to avoid re-parsing environment variables
    on every request. Use functools.lru_cache to enable caching.
    
    Returns:
        Application settings instance
    """
    # Check if we're in test mode
    if os.getenv("TESTING") or os.getenv("APP_TESTING"):
        return TestSettings()
    
    return Settings()


@lru_cache()
def get_test_settings() -> TestSettings:
    """
    Get test-specific settings with caching.
    
    Returns:
        Test settings instance
    """
    return TestSettings()


# Global settings instance for convenience
settings = get_settings()


def is_development() -> bool:
    """Check if the application is running in development mode."""
    return settings.debug


def is_production() -> bool:
    """Check if the application is running in production mode."""
    return not settings.debug and not is_testing()


def is_testing() -> bool:
    """Check if the application is running in test mode."""
    return os.getenv("TESTING") or os.getenv("APP_TESTING") or isinstance(settings, TestSettings)


def get_cors_config() -> dict:
    """
    Get CORS configuration for FastAPI.
    
    Returns:
        Dictionary with CORS configuration
    """
    return {
        "allow_origins": settings.cors_origins,
        "allow_credentials": settings.cors_credentials,
        "allow_methods": settings.cors_methods,
        "allow_headers": settings.cors_headers,
    }


def get_database_config() -> dict:
    """
    Get database configuration.
    
    Returns:
        Dictionary with database configuration
    """
    return {
        "database_url": settings.database_url,
        "echo": settings.debug,
    }


def get_logging_config() -> dict:
    """
    Get logging configuration.
    
    Returns:
        Dictionary with logging configuration
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": settings.log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "level": settings.log_level,
                "formatter": "standard",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {  # root logger
                "handlers": ["default"],
                "level": settings.log_level,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["default"],
                "level": settings.log_level,
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["default"],
                "level": settings.log_level,
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["default"],
                "level": "WARNING" if not settings.debug else "INFO",
                "propagate": False,
            },
        },
    }


def print_startup_info():
    """Print application startup information."""
    print(f"🚀 {settings.app_name} v{settings.app_version}")
    print(f"📝 {settings.app_description}")
    print(f"🌐 Server: http://{settings.host}:{settings.port}")
    print(f"📚 Docs: http://{settings.host}:{settings.port}{settings.docs_url}")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"💾 Database: {settings.database_url}")
    print(f"📊 Log level: {settings.log_level}")
    print(f"🌍 CORS origins: {', '.join(settings.cors_origins)}")