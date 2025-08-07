"""
Configuration management package for People Management System.

This package provides environment-specific configuration management
with support for development, staging, and production environments.
"""

from .environments import (
    BaseConfig, DevelopmentConfig, StagingConfig, ProductionConfig,
    get_config_for_environment, get_current_environment
)
from .database import DatabaseConfig
from .security import SecurityConfig
from .cache import CacheConfig

__all__ = [
    'BaseConfig',
    'DevelopmentConfig', 
    'StagingConfig',
    'ProductionConfig',
    'get_config_for_environment',
    'get_current_environment',
    'DatabaseConfig',
    'SecurityConfig',
    'CacheConfig'
]