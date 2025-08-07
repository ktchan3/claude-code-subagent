"""
Cache-specific configuration settings.

This module provides cache configuration with support for different
cache backends and cache policies.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class CacheBackend(str, Enum):
    """Supported cache backends."""
    MEMORY = "memory"
    REDIS = "redis"
    MEMCACHED = "memcached"
    DUMMY = "dummy"  # No caching (for testing)


class CacheEvictionPolicy(str, Enum):
    """Cache eviction policies."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In, First Out
    RANDOM = "random"  # Random eviction


class CacheConfig(BaseModel):
    """
    Cache configuration with support for multiple backends and policies.
    
    Provides configuration for caching behavior, TTLs, and cache policies
    across different cache backends.
    """
    
    # Backend Configuration
    backend: CacheBackend = Field(
        default=CacheBackend.MEMORY,
        description="Cache backend to use"
    )
    enabled: bool = Field(
        default=True,
        description="Enable caching globally"
    )
    
    # Connection Settings (for Redis/Memcached)
    host: str = Field(
        default="localhost",
        description="Cache server host"
    )
    port: int = Field(
        default=6379,
        ge=1,
        le=65535,
        description="Cache server port"
    )
    database: int = Field(
        default=0,
        ge=0,
        le=15,
        description="Redis database number (Redis only)"
    )
    password: Optional[str] = Field(
        default=None,
        description="Cache server password"
    )
    username: Optional[str] = Field(
        default=None,
        description="Cache server username"
    )
    
    # Connection Pool Settings
    max_connections: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of connections"
    )
    connection_timeout: float = Field(
        default=5.0,
        ge=0.1,
        le=60.0,
        description="Connection timeout in seconds"
    )
    socket_timeout: float = Field(
        default=5.0,
        ge=0.1,
        le=60.0,
        description="Socket timeout in seconds"
    )
    
    # Memory Cache Settings
    max_size: int = Field(
        default=1000,
        ge=10,
        le=100000,
        description="Maximum number of cache entries (memory backend)"
    )
    eviction_policy: CacheEvictionPolicy = Field(
        default=CacheEvictionPolicy.LRU,
        description="Cache eviction policy"
    )
    
    # TTL Settings
    default_ttl: int = Field(
        default=300,
        ge=1,
        le=86400,
        description="Default TTL in seconds (5 minutes)"
    )
    max_ttl: int = Field(
        default=3600,
        ge=60,
        le=604800,
        description="Maximum allowed TTL in seconds (1 hour)"
    )
    
    # Cache Key Settings
    key_prefix: str = Field(
        default="pms:",
        description="Prefix for all cache keys"
    )
    key_version: int = Field(
        default=1,
        ge=1,
        description="Cache key version (for invalidating all cache)"
    )
    
    # Serialization Settings
    serializer: str = Field(
        default="json",
        description="Serialization format (json, pickle, msgpack)"
    )
    compress: bool = Field(
        default=False,
        description="Enable compression for cached values"
    )
    compression_threshold: int = Field(
        default=1024,
        ge=100,
        le=10240,
        description="Minimum size in bytes to trigger compression"
    )
    
    # Performance Settings
    async_writes: bool = Field(
        default=True,
        description="Enable async writes (fire-and-forget)"
    )
    batch_operations: bool = Field(
        default=True,
        description="Enable batch operations for better performance"
    )
    pipeline_size: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum operations in a pipeline"
    )
    
    # Cache Warming Settings
    warm_on_startup: bool = Field(
        default=False,
        description="Warm cache on application startup"
    )
    warm_endpoints: List[str] = Field(
        default_factory=list,
        description="Endpoints to warm on startup"
    )
    
    # Cache Tags and Invalidation
    enable_tags: bool = Field(
        default=True,
        description="Enable cache tagging for selective invalidation"
    )
    tag_separator: str = Field(
        default=":",
        description="Separator for cache tag keys"
    )
    
    # Per-endpoint Cache Settings
    endpoint_configs: Dict[str, Dict[str, Any]] = Field(
        default_factory=lambda: {
            "people": {
                "ttl": 300,
                "tags": ["people", "data"],
                "enabled": True
            },
            "departments": {
                "ttl": 600,
                "tags": ["departments", "data"],
                "enabled": True
            },
            "positions": {
                "ttl": 600,
                "tags": ["positions", "data"],
                "enabled": True
            },
            "employment": {
                "ttl": 300,
                "tags": ["employment", "data"],
                "enabled": True
            },
            "statistics": {
                "ttl": 60,
                "tags": ["statistics"],
                "enabled": True
            },
            "search": {
                "ttl": 120,
                "tags": ["search"],
                "enabled": True
            }
        },
        description="Per-endpoint cache configurations"
    )
    
    # Monitoring and Statistics
    collect_stats: bool = Field(
        default=True,
        description="Collect cache statistics"
    )
    stats_ttl: int = Field(
        default=60,
        ge=10,
        le=3600,
        description="TTL for cache statistics"
    )
    
    # Health Check Settings
    health_check_enabled: bool = Field(
        default=True,
        description="Enable cache health checks"
    )
    health_check_interval: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Health check interval in seconds"
    )
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v):
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @field_validator("serializer")
    @classmethod
    def validate_serializer(cls, v):
        """Validate serializer type."""
        valid_serializers = ["json", "pickle", "msgpack"]
        if v not in valid_serializers:
            raise ValueError(f"Serializer must be one of: {valid_serializers}")
        return v
    
    @field_validator("max_ttl")
    @classmethod
    def validate_max_ttl(cls, v, values):
        """Ensure max_ttl is greater than default_ttl."""
        if isinstance(values, dict) and "default_ttl" in values:
            if v <= values["default_ttl"]:
                raise ValueError("max_ttl must be greater than default_ttl")
        return v
    
    def get_connection_url(self) -> Optional[str]:
        """
        Get cache connection URL for the configured backend.
        
        Returns:
            Connection URL string or None for memory backend
        """
        if self.backend == CacheBackend.MEMORY:
            return None
        elif self.backend == CacheBackend.REDIS:
            auth = ""
            if self.username and self.password:
                auth = f"{self.username}:{self.password}@"
            elif self.password:
                auth = f":{self.password}@"
            
            return f"redis://{auth}{self.host}:{self.port}/{self.database}"
        elif self.backend == CacheBackend.MEMCACHED:
            auth = ""
            if self.username and self.password:
                auth = f"{self.username}:{self.password}@"
            
            return f"memcached://{auth}{self.host}:{self.port}"
        elif self.backend == CacheBackend.DUMMY:
            return "dummy://"
        
        return None
    
    def get_endpoint_config(self, endpoint: str) -> Dict[str, Any]:
        """
        Get cache configuration for a specific endpoint.
        
        Args:
            endpoint: Endpoint name
            
        Returns:
            Dictionary with endpoint-specific cache configuration
        """
        default_config = {
            "ttl": self.default_ttl,
            "tags": [endpoint],
            "enabled": self.enabled
        }
        
        return {**default_config, **self.endpoint_configs.get(endpoint, {})}
    
    def get_cache_key(self, base_key: str, **params) -> str:
        """
        Generate a cache key with prefix and versioning.
        
        Args:
            base_key: Base cache key
            **params: Additional parameters to include in key
            
        Returns:
            Formatted cache key
        """
        key_parts = [self.key_prefix, f"v{self.key_version}", base_key]
        
        if params:
            param_parts = []
            for k, v in sorted(params.items()):
                if v is not None:
                    param_parts.append(f"{k}={v}")
            if param_parts:
                key_parts.append("_".join(param_parts))
        
        return ":".join(key_parts)
    
    def get_tag_key(self, tag: str) -> str:
        """
        Generate a cache tag key.
        
        Args:
            tag: Tag name
            
        Returns:
            Formatted tag key
        """
        return f"{self.key_prefix}tag{self.tag_separator}{tag}"
    
    def should_compress(self, data_size: int) -> bool:
        """
        Determine if data should be compressed based on size.
        
        Args:
            data_size: Size of data in bytes
            
        Returns:
            True if data should be compressed
        """
        return self.compress and data_size >= self.compression_threshold
    
    def get_connection_params(self) -> Dict[str, Any]:
        """
        Get connection parameters for the cache backend.
        
        Returns:
            Dictionary with connection parameters
        """
        base_params = {
            "host": self.host,
            "port": self.port,
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "connection_timeout": self.connection_timeout,
        }
        
        if self.username:
            base_params["username"] = self.username
        if self.password:
            base_params["password"] = self.password
        
        if self.backend == CacheBackend.REDIS:
            base_params["db"] = self.database
        
        return base_params