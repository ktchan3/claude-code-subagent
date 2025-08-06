"""
Configuration Service for People Management System Client

Handles application configuration, user preferences, and secure credential storage.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

import keyring
from platformdirs import user_config_dir, user_data_dir
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class APIKeyValidationError(ValueError):
    """Raised when API key validation fails."""
    pass


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key format.
    
    Args:
        api_key: The API key to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    # Check for newlines or carriage returns (HTTP header killers)
    if '\n' in api_key or '\r' in api_key:
        return False
    
    # Check for other control characters that could break HTTP headers
    if any(ord(char) < 32 for char in api_key if char not in '\t'):
        return False
    
    # Check for reasonable length (API keys are typically 20-128 characters)
    if len(api_key.strip()) < 10 or len(api_key.strip()) > 256:
        return False
    
    # Basic format check - should contain alphanumeric chars and possibly hyphens/underscores
    if not re.match(r'^[a-zA-Z0-9\-_\.]+$', api_key.strip()):
        return False
    
    return True


def sanitize_api_key(api_key: str) -> str:
    """
    Sanitize API key by removing invalid characters.
    
    Args:
        api_key: The API key to sanitize
        
    Returns:
        Sanitized API key
        
    Raises:
        APIKeyValidationError: If the key cannot be sanitized to a valid format
    """
    if not api_key or not isinstance(api_key, str):
        raise APIKeyValidationError("API key must be a non-empty string")
    
    # Strip whitespace and remove newlines/carriage returns
    sanitized = api_key.strip().replace('\n', '').replace('\r', '')
    
    # Remove any control characters except tab (though tab shouldn't be in API keys)
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char == '\t')
    
    # Remove tabs as well since they shouldn't be in API keys
    sanitized = sanitized.replace('\t', '')
    
    if not validate_api_key(sanitized):
        raise APIKeyValidationError(
            f"API key contains invalid characters or format. "
            f"API keys should contain only alphanumeric characters, hyphens, underscores, and dots."
        )
    
    return sanitized


class ConnectionConfig(BaseModel):
    """API connection configuration."""
    
    base_url: str = Field(..., description="API base URL")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    timeout: float = Field(30.0, description="Request timeout in seconds")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        return v.rstrip('/')


class UIConfig(BaseModel):
    """User interface configuration."""
    
    theme: str = Field("light", description="Application theme (light/dark)")
    window_geometry: Optional[Dict[str, int]] = Field(None, description="Main window geometry")
    window_state: Optional[str] = Field(None, description="Window state (maximized, etc.)")
    sidebar_width: int = Field(250, description="Sidebar width in pixels")
    table_columns: Dict[str, list] = Field(default_factory=dict, description="Visible table columns per view")
    page_size: int = Field(20, description="Default page size for tables")
    auto_refresh: bool = Field(True, description="Auto-refresh data")
    refresh_interval: int = Field(30, description="Auto-refresh interval in seconds")


class ApplicationConfig(BaseModel):
    """Complete application configuration."""
    
    connection: ConnectionConfig
    ui: UIConfig = Field(default_factory=UIConfig)
    last_updated: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = Field("1.0.0", description="Config version")


@dataclass
class RecentConnection:
    """Recent connection information."""
    
    name: str
    base_url: str
    last_used: datetime
    successful: bool = True


class ConfigService:
    """Service for managing application configuration and user preferences."""
    
    SERVICE_NAME = "PeopleManagementSystem"
    CONFIG_FILENAME = "config.json"
    RECENT_CONNECTIONS_FILENAME = "recent_connections.json"
    
    def __init__(self):
        self.config_dir = Path(user_config_dir("PeopleManagementSystem"))
        self.data_dir = Path(user_data_dir("PeopleManagementSystem"))
        self.config_file = self.config_dir / self.CONFIG_FILENAME
        self.recent_connections_file = self.config_dir / self.RECENT_CONNECTIONS_FILENAME
        
        self._config: Optional[ApplicationConfig] = None
        self._recent_connections: list[RecentConnection] = []
        
        logger.info(f"Config directory: {self.config_dir}")
        logger.info(f"Data directory: {self.data_dir}")
    
    def initialize(self):
        """Initialize the configuration service."""
        # Create directories if they don't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing configuration
        self.load_config()
        self.load_recent_connections()
        
        # Automatically clean up any corrupted API keys on initialization
        try:
            cleared_count = self.clear_corrupted_api_keys()
            if cleared_count > 0:
                logger.warning(f"Automatically cleared {cleared_count} corrupted API key(s) on startup")
        except Exception as e:
            logger.error(f"Error clearing corrupted API keys on startup: {e}")
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """Load configuration from file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Load API key from keyring if not in config
                if 'connection' in config_data:
                    base_url = config_data['connection'].get('base_url')
                    if base_url and not config_data['connection'].get('api_key'):
                        api_key = keyring.get_password(self.SERVICE_NAME, base_url)
                        if api_key:
                            config_data['connection']['api_key'] = api_key
                
                self._config = ApplicationConfig(**config_data)
                logger.info("Configuration loaded successfully")
                
                return config_data
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._config = None
        
        return None
    
    def save_config(self, config: Optional[Union[ApplicationConfig, Dict[str, Any]]] = None):
        """Save configuration to file."""
        try:
            if config is None:
                config = self._config
            
            if config is None:
                logger.warning("No configuration to save")
                return
            
            if isinstance(config, ApplicationConfig):
                config_dict = config.dict()
            else:
                config_dict = config
            
            # Save API key to keyring and remove from config file
            if 'connection' in config_dict and 'api_key' in config_dict['connection']:
                api_key = config_dict['connection']['api_key']
                base_url = config_dict['connection']['base_url']
                
                if api_key and base_url:
                    try:
                        # Validate and sanitize the API key before saving
                        if not validate_api_key(api_key):
                            try:
                                api_key = sanitize_api_key(api_key)
                                logger.warning("API key was sanitized during config save")
                            except APIKeyValidationError as e:
                                logger.error(f"Invalid API key format during config save: {e}")
                                # Don't save invalid API keys
                                config_dict['connection']['api_key'] = None
                                return
                        
                        keyring.set_password(self.SERVICE_NAME, base_url, api_key)
                        # Remove API key from config file for security
                        config_dict['connection']['api_key'] = None
                    except Exception as e:
                        logger.warning(f"Failed to save API key to keyring: {e}")
            
            # Update timestamp
            config_dict['last_updated'] = datetime.utcnow().isoformat()
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            logger.info("Configuration saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def load_recent_connections(self) -> list[RecentConnection]:
        """Load recent connections from file."""
        try:
            if self.recent_connections_file.exists():
                with open(self.recent_connections_file, 'r') as f:
                    connections_data = json.load(f)
                
                self._recent_connections = [
                    RecentConnection(
                        name=conn['name'],
                        base_url=conn['base_url'],
                        last_used=datetime.fromisoformat(conn['last_used']),
                        successful=conn.get('successful', True)
                    )
                    for conn in connections_data
                ]
                
                # Sort by last used (most recent first)
                self._recent_connections.sort(key=lambda x: x.last_used, reverse=True)
                
                # Limit to 10 most recent
                self._recent_connections = self._recent_connections[:10]
                
                logger.info(f"Loaded {len(self._recent_connections)} recent connections")
            
        except Exception as e:
            logger.error(f"Failed to load recent connections: {e}")
            self._recent_connections = []
        
        return self._recent_connections
    
    def save_recent_connections(self):
        """Save recent connections to file."""
        try:
            connections_data = [
                {
                    'name': conn.name,
                    'base_url': conn.base_url,
                    'last_used': conn.last_used.isoformat(),
                    'successful': conn.successful
                }
                for conn in self._recent_connections
            ]
            
            with open(self.recent_connections_file, 'w') as f:
                json.dump(connections_data, f, indent=2)
            
            logger.info("Recent connections saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save recent connections: {e}")
    
    def add_recent_connection(self, name: str, base_url: str, successful: bool = True):
        """Add a connection to the recent connections list."""
        # Remove existing connection with same URL
        self._recent_connections = [
            conn for conn in self._recent_connections 
            if conn.base_url != base_url
        ]
        
        # Add new connection at the beginning
        new_connection = RecentConnection(
            name=name,
            base_url=base_url,
            last_used=datetime.utcnow(),
            successful=successful
        )
        self._recent_connections.insert(0, new_connection)
        
        # Limit to 10 connections
        self._recent_connections = self._recent_connections[:10]
        
        self.save_recent_connections()
    
    def get_config(self) -> Optional[ApplicationConfig]:
        """Get current configuration."""
        return self._config
    
    def set_config(self, config: ApplicationConfig):
        """Set current configuration."""
        self._config = config
    
    def get_connection_config(self) -> Optional[ConnectionConfig]:
        """Get connection configuration."""
        if self._config:
            return self._config.connection
        return None
    
    def get_ui_config(self) -> UIConfig:
        """Get UI configuration."""
        if self._config:
            return self._config.ui
        return UIConfig()
    
    def get_recent_connections(self) -> list[RecentConnection]:
        """Get recent connections list."""
        return self._recent_connections.copy()
    
    def update_connection_config(self, connection_config: ConnectionConfig):
        """Update connection configuration."""
        if self._config is None:
            self._config = ApplicationConfig(connection=connection_config)
        else:
            self._config.connection = connection_config
        
        self.save_config()
    
    def update_ui_config(self, ui_config: UIConfig):
        """Update UI configuration."""
        if self._config is None:
            self._config = ApplicationConfig(
                connection=ConnectionConfig(base_url="http://localhost:8000"),
                ui=ui_config
            )
        else:
            self._config.ui = ui_config
        
        self.save_config()
    
    def get_api_key(self, base_url: str) -> Optional[str]:
        """Get API key for a specific base URL from keyring."""
        try:
            return keyring.get_password(self.SERVICE_NAME, base_url)
        except Exception as e:
            logger.error(f"Failed to get API key from keyring: {e}")
            return None
    
    def set_api_key(self, base_url: str, api_key: str):
        """Set API key for a specific base URL in keyring."""
        try:
            # Validate and sanitize the API key before saving
            if not validate_api_key(api_key):
                try:
                    api_key = sanitize_api_key(api_key)
                    logger.warning("API key was sanitized before saving")
                except APIKeyValidationError as e:
                    logger.error(f"Invalid API key format: {e}")
                    raise ValueError(f"Invalid API key format: {e}")
            
            keyring.set_password(self.SERVICE_NAME, base_url, api_key)
        except Exception as e:
            logger.error(f"Failed to set API key in keyring: {e}")
            raise
    
    def delete_api_key(self, base_url: str):
        """Delete API key for a specific base URL from keyring."""
        try:
            keyring.delete_password(self.SERVICE_NAME, base_url)
        except Exception as e:
            logger.error(f"Failed to delete API key from keyring: {e}")
    
    def clear_corrupted_api_keys(self):
        """Clear any corrupted API keys from the keyring."""
        logger.info("Checking for and clearing corrupted API keys...")
        
        # Get all recent connections to check their API keys
        recent_connections = self.get_recent_connections()
        cleared_count = 0
        
        for conn in recent_connections:
            try:
                api_key = self.get_api_key(conn.base_url)
                if api_key and not validate_api_key(api_key):
                    logger.warning(f"Found corrupted API key for {conn.base_url}, clearing it")
                    self.delete_api_key(conn.base_url)
                    cleared_count += 1
            except Exception as e:
                logger.error(f"Error checking API key for {conn.base_url}: {e}")
        
        # Also check current config
        if self._config and self._config.connection:
            base_url = self._config.connection.base_url
            try:
                api_key = self.get_api_key(base_url)
                if api_key and not validate_api_key(api_key):
                    logger.warning(f"Found corrupted API key for current config {base_url}, clearing it")
                    self.delete_api_key(base_url)
                    cleared_count += 1
            except Exception as e:
                logger.error(f"Error checking current config API key: {e}")
        
        logger.info(f"Cleared {cleared_count} corrupted API keys")
        return cleared_count
    
    def get_logs_directory(self) -> Path:
        """Get logs directory path."""
        logs_dir = self.data_dir / "logs"
        logs_dir.mkdir(exist_ok=True)
        return logs_dir
    
    def get_cache_directory(self) -> Path:
        """Get cache directory path."""
        cache_dir = self.data_dir / "cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir
    
    def get_exports_directory(self) -> Path:
        """Get exports directory path."""
        exports_dir = self.data_dir / "exports"
        exports_dir.mkdir(exist_ok=True)
        return exports_dir
    
    def clear_cache(self):
        """Clear application cache."""
        cache_dir = self.get_cache_directory()
        try:
            for file in cache_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def export_config(self, file_path: Union[str, Path]):
        """Export configuration to a file."""
        if self._config is None:
            raise ValueError("No configuration to export")
        
        config_dict = self._config.dict()
        # Don't export sensitive information
        if 'connection' in config_dict and 'api_key' in config_dict['connection']:
            config_dict['connection']['api_key'] = None
        
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Configuration exported to {file_path}")
    
    def import_config(self, file_path: Union[str, Path]):
        """Import configuration from a file."""
        with open(file_path, 'r') as f:
            config_data = json.load(f)
        
        self._config = ApplicationConfig(**config_data)
        self.save_config()
        
        logger.info(f"Configuration imported from {file_path}")