"""
Environment-specific configuration settings.

This module provides different configuration classes for different environments
(development, staging, production) with appropriate defaults and validation.
"""

import os
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """Available environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging" 
    PRODUCTION = "production"
    TESTING = "testing"


class BaseConfig(BaseSettings):
    """
    Base configuration with common settings for all environments.
    
    This class contains settings that are shared across all environments
    and can be inherited by environment-specific configurations.
    """
    
    # Environment identification
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Current environment"
    )
    
    # Application metadata
    app_name: str = Field(
        default="People Management System API",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    app_description: str = Field(
        default="A comprehensive API for managing people, departments, positions, and employment records",
        description="Application description"
    )
    
    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    
    # API configuration
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    docs_url: Optional[str] = Field(default="/docs", description="OpenAPI docs URL")
    redoc_url: Optional[str] = Field(default="/redoc", description="ReDoc URL") 
    openapi_url: Optional[str] = Field(default="/openapi.json", description="OpenAPI schema URL")
    
    # Database configuration
    database_url: str = Field(
        default="sqlite:///./people_management.db",
        description="Database connection URL"
    )
    database_pool_size: int = Field(default=5, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, description="Database max overflow connections")
    database_echo: bool = Field(default=False, description="Enable SQL query logging")
    
    # Security configuration
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT and other cryptographic operations"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="JWT access token expiration time in minutes"
    )
    password_hash_rounds: int = Field(default=12, description="Password hash rounds")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default_factory=lambda: [
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
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )
    enable_access_logs: bool = Field(default=True, description="Enable access logging")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute per client")
    rate_limit_burst: int = Field(default=100, description="Rate limit burst capacity")
    
    # Pagination
    default_page_size: int = Field(default=20, description="Default page size")
    max_page_size: int = Field(default=100, description="Maximum page size")
    
    # Cache configuration
    cache_ttl: int = Field(default=300, description="Default cache TTL in seconds")
    cache_max_size: int = Field(default=1000, description="Maximum cache size")
    enable_caching: bool = Field(default=True, description="Enable caching")
    
    # File handling
    max_file_size: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum file size in bytes (10MB)"
    )
    allowed_file_types: List[str] = Field(
        default_factory=lambda: [
            "image/jpeg", "image/png", "image/gif", 
            "application/pdf", "text/csv"
        ],
        description="Allowed file MIME types"
    )
    
    # Monitoring and health checks
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_tracing: bool = Field(default=False, description="Enable request tracing")
    
    # Feature flags
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "bulk_operations": True,
            "advanced_search": True,
            "file_uploads": True,
            "audit_logging": True,
            "real_time_notifications": False
        },
        description="Feature flags"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from environment variable."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or []
    
    @field_validator("cors_methods", mode="before")
    @classmethod
    def parse_cors_methods(cls, v):
        """Parse CORS methods from environment variable."""
        if isinstance(v, str):
            return [method.strip() for method in v.split(",") if method.strip()]
        return v or ["*"]
    
    @field_validator("cors_headers", mode="before")
    @classmethod
    def parse_cors_headers(cls, v):
        """Parse CORS headers from environment variable."""
        if isinstance(v, str):
            return [header.strip() for header in v.split(",") if header.strip()]
        return v or ["*"]
    
    @field_validator("allowed_file_types", mode="before")
    @classmethod
    def parse_allowed_file_types(cls, v):
        """Parse allowed file types from environment variable."""
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",") if file_type.strip()]
        return v or []
    
    @field_validator("features", mode="before")
    @classmethod
    def parse_features(cls, v):
        """Parse feature flags from environment variable."""
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                # Fallback to simple key=value format
                features = {}
                for feature in v.split(","):
                    if "=" in feature:
                        key, value = feature.split("=", 1)
                        features[key.strip()] = value.strip().lower() in ("true", "1", "yes")
                return features
        return v or {}
    
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
    
    @field_validator("workers")
    @classmethod
    def validate_workers(cls, v):
        """Validate worker count."""
        if v < 1:
            raise ValueError("Worker count must be at least 1")
        return v
    
    model_config = ConfigDict(
        env_file=".env",
        env_prefix="APP_",
        case_sensitive=False,
        extra="ignore"
    )


class DevelopmentConfig(BaseConfig):
    """Development environment configuration."""
    
    environment: Environment = Environment.DEVELOPMENT
    
    # Development-specific overrides
    debug: bool = True
    reload: bool = True
    log_level: str = "DEBUG"
    database_echo: bool = True
    enable_access_logs: bool = True
    enable_tracing: bool = True
    
    # Relaxed security for development
    secret_key: str = "dev-secret-key-not-for-production"
    access_token_expire_minutes: int = 480  # 8 hours
    password_hash_rounds: int = 4  # Faster hashing
    
    # More generous rate limits for development
    rate_limit_per_minute: int = 1000
    rate_limit_burst: int = 500
    
    # Smaller cache for development
    cache_max_size: int = 100
    
    # Keep docs available
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    
    # Enable all features in development
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "bulk_operations": True,
            "advanced_search": True,
            "file_uploads": True,
            "audit_logging": True,
            "real_time_notifications": True
        }
    )


class StagingConfig(BaseConfig):
    """Staging environment configuration."""
    
    environment: Environment = Environment.STAGING
    
    # Staging-specific overrides
    debug: bool = False
    reload: bool = False
    log_level: str = "INFO"
    database_echo: bool = False
    enable_access_logs: bool = True
    enable_tracing: bool = True
    enable_metrics: bool = True
    
    # Production-like security but with longer tokens for testing
    access_token_expire_minutes: int = 120  # 2 hours
    password_hash_rounds: int = 10
    
    # Moderate rate limits for testing
    rate_limit_per_minute: int = 300
    rate_limit_burst: int = 150
    
    # Medium cache size
    cache_max_size: int = 500
    
    # Keep docs available for testing
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    openapi_url: str = "/openapi.json"
    
    # Enable most features in staging
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "bulk_operations": True,
            "advanced_search": True,
            "file_uploads": True,
            "audit_logging": True,
            "real_time_notifications": True
        }
    )


class ProductionConfig(BaseConfig):
    """Production environment configuration."""
    
    environment: Environment = Environment.PRODUCTION
    
    # Production-specific overrides
    debug: bool = False
    reload: bool = False
    log_level: str = "INFO"
    database_echo: bool = False
    enable_access_logs: bool = True
    enable_tracing: bool = False  # Disable for performance
    enable_metrics: bool = True
    
    # Production worker configuration
    workers: int = Field(default_factory=lambda: os.cpu_count() or 1)
    
    # Secure production settings
    access_token_expire_minutes: int = 30
    password_hash_rounds: int = 12
    
    # Production rate limits
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 100
    
    # Large cache for production
    cache_max_size: int = 5000
    
    # Disable docs in production by default
    docs_url: Optional[str] = None
    redoc_url: Optional[str] = None
    openapi_url: Optional[str] = None
    
    # Production CORS should be more restrictive
    cors_origins: List[str] = Field(
        default_factory=lambda: [],  # Must be set explicitly in production
        description="Allowed CORS origins (must be configured for production)"
    )
    
    # Conservative feature flags for production
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "bulk_operations": True,
            "advanced_search": True,
            "file_uploads": True,
            "audit_logging": True,
            "real_time_notifications": False  # Disable until proven stable
        }
    )
    
    @field_validator("secret_key")
    @classmethod
    def validate_production_secret_key(cls, v):
        """Ensure secret key is changed in production."""
        if v == "your-secret-key-change-in-production" or v == "dev-secret-key-not-for-production":
            raise ValueError(
                "Secret key must be changed in production. "
                "Set APP_SECRET_KEY environment variable to a secure random value."
            )
        if len(v) < 32:
            raise ValueError("Production secret key must be at least 32 characters long")
        return v
    
    @field_validator("cors_origins")
    @classmethod
    def validate_production_cors_origins(cls, v):
        """Validate CORS origins in production."""
        if not v:
            raise ValueError(
                "CORS origins must be explicitly configured in production. "
                "Set APP_CORS_ORIGINS environment variable."
            )
        # Ensure no wildcard origins in production
        if "*" in v:
            raise ValueError("Wildcard CORS origins are not allowed in production")
        return v


class TestingConfig(BaseConfig):
    """Testing environment configuration."""
    
    environment: Environment = Environment.TESTING
    
    # Testing-specific overrides
    debug: bool = True
    reload: bool = False
    log_level: str = "WARNING"  # Reduce log noise in tests
    database_url: str = "sqlite:///:memory:"  # In-memory database for tests
    database_echo: bool = False
    enable_access_logs: bool = False
    enable_tracing: bool = False
    enable_metrics: bool = False
    enable_caching: bool = False  # Disable caching in tests
    
    # Fast settings for tests
    password_hash_rounds: int = 4
    access_token_expire_minutes: int = 5
    
    # No rate limiting in tests
    rate_limit_per_minute: int = 10000
    rate_limit_burst: int = 1000
    
    # Small pagination for tests
    default_page_size: int = 5
    max_page_size: int = 20
    
    # Enable all features for comprehensive testing
    features: Dict[str, bool] = Field(
        default_factory=lambda: {
            "bulk_operations": True,
            "advanced_search": True,
            "file_uploads": True,
            "audit_logging": True,
            "real_time_notifications": True
        }
    )


def get_current_environment() -> Environment:
    """
    Determine the current environment from environment variables.
    
    Checks the following environment variables in order:
    1. APP_ENVIRONMENT
    2. ENVIRONMENT
    3. ENV
    4. Defaults to DEVELOPMENT
    
    Returns:
        Current environment enum value
    """
    env_value = (
        os.getenv("APP_ENVIRONMENT") or 
        os.getenv("ENVIRONMENT") or 
        os.getenv("ENV") or 
        "development"
    ).lower()
    
    # Special case for testing
    if os.getenv("TESTING") or os.getenv("APP_TESTING") or env_value in ("test", "testing"):
        return Environment.TESTING
    
    # Map common environment names
    env_mapping = {
        "dev": Environment.DEVELOPMENT,
        "development": Environment.DEVELOPMENT,
        "stage": Environment.STAGING,
        "staging": Environment.STAGING,
        "prod": Environment.PRODUCTION,
        "production": Environment.PRODUCTION,
        "test": Environment.TESTING,
        "testing": Environment.TESTING
    }
    
    return env_mapping.get(env_value, Environment.DEVELOPMENT)


def get_config_for_environment(environment: Optional[Environment] = None) -> BaseConfig:
    """
    Get configuration for the specified or current environment.
    
    Args:
        environment: Target environment, defaults to current environment
        
    Returns:
        Configuration instance for the environment
    """
    if environment is None:
        environment = get_current_environment()
    
    config_map = {
        Environment.DEVELOPMENT: DevelopmentConfig,
        Environment.STAGING: StagingConfig,
        Environment.PRODUCTION: ProductionConfig,
        Environment.TESTING: TestingConfig
    }
    
    config_class = config_map.get(environment, DevelopmentConfig)
    return config_class()


# Environment detection helpers
def is_development() -> bool:
    """Check if running in development environment."""
    return get_current_environment() == Environment.DEVELOPMENT


def is_staging() -> bool:
    """Check if running in staging environment."""
    return get_current_environment() == Environment.STAGING


def is_production() -> bool:
    """Check if running in production environment."""
    return get_current_environment() == Environment.PRODUCTION


def is_testing() -> bool:
    """Check if running in testing environment."""
    return get_current_environment() == Environment.TESTING