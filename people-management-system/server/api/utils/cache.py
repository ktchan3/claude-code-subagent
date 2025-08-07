"""
Caching utilities for performance optimization.

This module provides caching functionality for static and semi-static data
to improve API response times and reduce database load.
"""

import time
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
from datetime import datetime, timedelta
from threading import Lock
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Cache configuration
DEFAULT_CACHE_TTL = 300  # 5 minutes
LONG_CACHE_TTL = 3600   # 1 hour
SHORT_CACHE_TTL = 60    # 1 minute


@dataclass
class CacheEntry:
    """Represents a cache entry with metadata."""
    value: Any
    created_at: float
    ttl: int
    hit_count: int = 0
    last_accessed: float = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() - self.created_at > self.ttl
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return time.time() - self.created_at
    
    def touch(self):
        """Update last accessed time and increment hit count."""
        self.hit_count += 1
        self.last_accessed = time.time()


class InMemoryCache:
    """
    Thread-safe in-memory cache with TTL and LRU eviction.
    
    This is a simple cache implementation suitable for single-instance deployments.
    For distributed deployments, consider using Redis or Memcached.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = DEFAULT_CACHE_TTL):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of items to store
            default_ttl: Default time-to-live in seconds
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = Lock()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self.created_at = time.time()
    
    def _generate_key(self, key_parts: Union[str, List[Any]]) -> str:
        """
        Generate a cache key from various inputs.
        
        Args:
            key_parts: Key components to generate cache key from
            
        Returns:
            Generated cache key
        """
        if isinstance(key_parts, str):
            return key_parts
        
        # Create a deterministic key from the parts
        key_str = ":".join(str(part) for part in key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, key: Union[str, List[Any]]) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key or key components
            
        Returns:
            Cached value or None if not found/expired
        """
        cache_key = self._generate_key(key)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired:
                # Remove expired entry
                del self._cache[cache_key]
                self._misses += 1
                return None
            
            # Update access metadata
            entry.touch()
            self._hits += 1
            
            logger.debug(f"Cache hit for key: {cache_key}")
            return entry.value
    
    def set(self, key: Union[str, List[Any]], value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key or key components
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl
        
        with self._lock:
            # Check if we need to evict items
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_lru()
            
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl
            )
            
            self._cache[cache_key] = entry
            logger.debug(f"Cached value for key: {cache_key} (TTL: {ttl}s)")
    
    def delete(self, key: Union[str, List[Any]]) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key or key components
            
        Returns:
            True if key was found and deleted, False otherwise
        """
        cache_key = self._generate_key(key)
        
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug(f"Deleted cache entry for key: {cache_key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            logger.info("Cache cleared")
    def _evict_lru(self) -> None:
        """Evict least recently used items."""
        if not self._cache:
            return
        
        # Find the least recently used entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        del self._cache[lru_key]
        self._evictions += 1
        logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0
            
            # Calculate memory usage estimation
            entry_sizes = []
            for entry in self._cache.values():
                try:
                    # Rough estimation of memory usage
                    import sys
                    size = sys.getsizeof(entry.value)
                    if hasattr(entry.value, '__len__'):
                        size += len(str(entry.value))
                    entry_sizes.append(size)
                except:
                    entry_sizes.append(0)
            
            return {
                'entries': len(self._cache),
                'max_size': self.max_size,
                'hits': self._hits,
                'misses': self._misses,
                'hit_rate_percent': round(hit_rate, 2),
                'evictions': self._evictions,
                'estimated_memory_bytes': sum(entry_sizes),
                'uptime_seconds': time.time() - self.created_at,
                'average_entry_age': sum(entry.age_seconds for entry in self._cache.values()) / len(self._cache) if self._cache else 0
            }


# Global cache instance
_global_cache = InMemoryCache(max_size=2000, default_ttl=DEFAULT_CACHE_TTL)


def get_cache() -> InMemoryCache:
    """Get the global cache instance."""
    return _global_cache


def cache_result(ttl: int = DEFAULT_CACHE_TTL, key_prefix: str = ""):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time-to-live for cached results
        key_prefix: Prefix for cache keys
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix, func.__name__]
            
            # Add args to key (exclude self for methods)
            if args and hasattr(args[0], func.__name__):
                # This is likely a method call, skip self
                key_parts.extend(str(arg) for arg in args[1:])
            else:
                key_parts.extend(str(arg) for arg in args)
            
            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            cache = get_cache()
            
            # Try to get from cache first
            cached_result = cache.get(key_parts)
            if cached_result is not None:
                return cached_result
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache.set(key_parts, result, ttl)
            
            return result
        
        # Add cache management methods to the decorated function
        def clear_cache():
            """Clear cache entries for this function."""
            cache = get_cache()
            # This is a simple implementation - in practice, you might want
            # to track keys more carefully for selective clearing
            cache.clear()
        
        def get_cache_stats():
            """Get cache statistics."""
            return get_cache().get_stats()
        
        wrapper.clear_cache = clear_cache
        wrapper.get_cache_stats = get_cache_stats
        
        return wrapper
    
    return decorator


# Convenience functions for common caching patterns
def cache_department_list(ttl: int = LONG_CACHE_TTL):
    """Cache decorator specifically for department lists."""
    return cache_result(ttl=ttl, key_prefix="departments")


def cache_position_list(ttl: int = LONG_CACHE_TTL):
    """Cache decorator specifically for position lists."""
    return cache_result(ttl=ttl, key_prefix="positions")


def cache_person_search(ttl: int = SHORT_CACHE_TTL):
    """Cache decorator for person search results (shorter TTL due to frequent updates)."""
    return cache_result(ttl=ttl, key_prefix="person_search")


def cache_statistics(ttl: int = DEFAULT_CACHE_TTL):
    """Cache decorator for statistics and reports."""
    return cache_result(ttl=ttl, key_prefix="statistics")


# Cache invalidation helpers
class CacheInvalidator:
    """Utility class for cache invalidation patterns."""
    
    @staticmethod
    def invalidate_person_caches():
        """Invalidate caches related to person data."""
        cache = get_cache()
        # In a more sophisticated implementation, you would track
        # which cache keys are related to persons
        logger.info("Invalidating person-related caches")
        # For now, we clear all - in production, implement selective clearing
        
    @staticmethod
    def invalidate_department_caches():
        """Invalidate caches related to department data."""
        cache = get_cache()
        logger.info("Invalidating department-related caches")
        
    @staticmethod
    def invalidate_position_caches():
        """Invalidate caches related to position data."""
        cache = get_cache()
        logger.info("Invalidating position-related caches")


# Background cache maintenance
class CacheMaintenanceService:
    """Service for periodic cache maintenance."""
    
    def __init__(self, cache: InMemoryCache):
        self.cache = cache
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 minutes
    
    def run_maintenance(self) -> Dict[str, int]:
        """
        Run cache maintenance tasks.
        
        Returns:
            Dictionary with maintenance results
        """
        current_time = time.time()
        
        if current_time - self.last_cleanup >= self.cleanup_interval:
            expired_count = self.cache.cleanup_expired()
            self.last_cleanup = current_time
            
            logger.info(f"Cache maintenance completed: {expired_count} expired entries removed")
            
            return {
                'expired_entries_removed': expired_count,
                'last_cleanup': self.last_cleanup
            }
        
        return {'message': 'No maintenance needed'}


# Global maintenance service
_maintenance_service = CacheMaintenanceService(_global_cache)


def get_maintenance_service() -> CacheMaintenanceService:
    """Get the global cache maintenance service."""
    return _maintenance_service


def get_cache_health() -> Dict[str, Any]:
    """
    Get comprehensive cache health information.
    
    Returns:
        Dictionary with cache health data
    """
    cache = get_cache()
    stats = cache.get_stats()
    
    # Determine health status
    health_status = "healthy"
    issues = []
    
    if stats['hit_rate_percent'] < 50:
        health_status = "warning"
        issues.append("Low cache hit rate")
    
    if stats['entries'] >= stats['max_size'] * 0.9:
        health_status = "warning"
        issues.append("Cache near capacity")
    
    if stats['evictions'] > stats['hits'] * 0.1:
        health_status = "warning"
        issues.append("High eviction rate")
    
    return {
        'status': health_status,
        'issues': issues,
        'stats': stats,
        'maintenance_info': _maintenance_service.run_maintenance()
    }