"""
Advanced cache invalidation system with selective clearing and cache tagging.

This module provides a sophisticated cache invalidation system that allows
for selective cache clearing based on tags, dependencies, and data relationships.
"""

import logging
import time
from typing import Dict, List, Set, Any, Optional, Union
from threading import Lock
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class CacheTag:
    """Represents a cache tag for selective invalidation."""
    name: str
    created_at: float = field(default_factory=time.time)
    keys: Set[str] = field(default_factory=set)
    
    def add_key(self, key: str):
        """Add a cache key to this tag."""
        self.keys.add(key)
    
    def remove_key(self, key: str):
        """Remove a cache key from this tag."""
        self.keys.discard(key)


class SmartCacheInvalidator:
    """
    Advanced cache invalidation system with tag-based selective clearing.
    
    This system allows for fine-grained cache invalidation based on:
    - Tags: Group related cache entries for batch invalidation
    - Dependencies: Invalidate dependent caches when parent data changes
    - Patterns: Use key patterns for bulk invalidation
    - Time-based: Automatic expiration of tagged groups
    """
    
    def __init__(self, cache_instance):
        """
        Initialize the cache invalidator.
        
        Args:
            cache_instance: The cache instance to manage
        """
        self.cache = cache_instance
        self._lock = Lock()
        
        # Tag management
        self._tags: Dict[str, CacheTag] = {}
        self._key_to_tags: Dict[str, Set[str]] = defaultdict(set)
        
        # Dependency tracking
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)  # tag -> dependent tags
        self._reverse_dependencies: Dict[str, Set[str]] = defaultdict(set)  # tag -> parent tags
        
        # Pattern tracking
        self._patterns: Dict[str, List[str]] = defaultdict(list)  # pattern -> keys
        
        # Statistics
        self._invalidation_stats = {
            'total_invalidations': 0,
            'tag_invalidations': 0,
            'pattern_invalidations': 0,
            'dependency_invalidations': 0,
            'keys_invalidated': 0
        }
    
    def tag_cache_key(self, key: str, tags: Union[str, List[str]]):
        """
        Associate cache key with one or more tags.
        
        Args:
            key: Cache key to tag
            tags: Tag name or list of tag names
        """
        if isinstance(tags, str):
            tags = [tags]
        
        with self._lock:
            for tag_name in tags:
                # Create tag if it doesn't exist
                if tag_name not in self._tags:
                    self._tags[tag_name] = CacheTag(name=tag_name)
                
                # Add key to tag
                self._tags[tag_name].add_key(key)
                self._key_to_tags[key].add(tag_name)
                
                logger.debug(f"Tagged cache key '{key}' with tag '{tag_name}'")
    
    def set_cache_with_tags(self, key: str, value: Any, tags: Union[str, List[str]], ttl: Optional[int] = None):
        """
        Set cache value with automatic tagging.
        
        Args:
            key: Cache key
            value: Value to cache
            tags: Tag name or list of tag names
            ttl: Time-to-live in seconds
        """
        # Set the cache value
        self.cache.set(key, value, ttl)
        
        # Tag the key
        self.tag_cache_key(key, tags)
    
    def add_dependency(self, parent_tag: str, dependent_tag: str):
        """
        Add a dependency relationship between tags.
        
        When parent_tag is invalidated, dependent_tag will also be invalidated.
        
        Args:
            parent_tag: Parent tag that controls the dependency
            dependent_tag: Dependent tag that gets invalidated with parent
        """
        with self._lock:
            self._dependencies[parent_tag].add(dependent_tag)
            self._reverse_dependencies[dependent_tag].add(parent_tag)
            
            logger.debug(f"Added dependency: {parent_tag} -> {dependent_tag}")
    
    def add_pattern(self, pattern: str, key: str):
        """
        Associate a cache key with a pattern for pattern-based invalidation.
        
        Args:
            pattern: Pattern identifier (e.g., "person_*", "department_list")
            key: Cache key matching this pattern
        """
        with self._lock:
            self._patterns[pattern].append(key)
            logger.debug(f"Added key '{key}' to pattern '{pattern}'")
    
    def invalidate_by_tag(self, tag_names: Union[str, List[str]], cascade: bool = True) -> Dict[str, Any]:
        """
        Invalidate all cache entries associated with the given tags.
        
        Args:
            tag_names: Tag name or list of tag names to invalidate
            cascade: Whether to invalidate dependent tags as well
            
        Returns:
            Dictionary with invalidation results
        """
        if isinstance(tag_names, str):
            tag_names = [tag_names]
        
        invalidated_keys = set()
        invalidated_tags = set()
        
        with self._lock:
            # Collect all tags to invalidate (including dependencies)
            tags_to_process = set(tag_names)
            
            if cascade:
                # Add dependent tags
                for tag_name in tag_names:
                    tags_to_process.update(self._get_dependent_tags(tag_name))
            
            # Invalidate each tag
            for tag_name in tags_to_process:
                if tag_name in self._tags:
                    tag = self._tags[tag_name]
                    
                    # Collect keys to invalidate
                    keys_to_invalidate = tag.keys.copy()
                    
                    # Remove from cache
                    for key in keys_to_invalidate:
                        if self.cache.delete(key):
                            invalidated_keys.add(key)
                            
                        # Clean up key-to-tag mapping
                        self._key_to_tags[key].discard(tag_name)
                        if not self._key_to_tags[key]:
                            del self._key_to_tags[key]
                    
                    # Clear the tag
                    tag.keys.clear()
                    invalidated_tags.add(tag_name)
                    
                    logger.info(f"Invalidated tag '{tag_name}' with {len(keys_to_invalidate)} keys")
        
        # Update statistics
        self._invalidation_stats['total_invalidations'] += 1
        self._invalidation_stats['tag_invalidations'] += len(invalidated_tags)
        self._invalidation_stats['keys_invalidated'] += len(invalidated_keys)
        
        if cascade:
            self._invalidation_stats['dependency_invalidations'] += 1
        
        result = {
            'invalidated_tags': list(invalidated_tags),
            'invalidated_keys': len(invalidated_keys),
            'cascade_enabled': cascade
        }
        
        logger.info(f"Tag invalidation complete: {result}")
        return result
    
    def invalidate_by_pattern(self, patterns: Union[str, List[str]]) -> Dict[str, Any]:
        """
        Invalidate cache entries matching the given patterns.
        
        Args:
            patterns: Pattern or list of patterns to invalidate
            
        Returns:
            Dictionary with invalidation results
        """
        if isinstance(patterns, str):
            patterns = [patterns]
        
        invalidated_keys = set()
        
        with self._lock:
            for pattern in patterns:
                if pattern in self._patterns:
                    keys_to_invalidate = self._patterns[pattern].copy()
                    
                    for key in keys_to_invalidate:
                        if self.cache.delete(key):
                            invalidated_keys.add(key)
                            
                        # Clean up pattern mapping
                        self._patterns[pattern].remove(key)
                        
                        # Clean up tag mappings
                        if key in self._key_to_tags:
                            for tag_name in self._key_to_tags[key]:
                                if tag_name in self._tags:
                                    self._tags[tag_name].remove_key(key)
                            del self._key_to_tags[key]
                    
                    logger.info(f"Invalidated pattern '{pattern}' with {len(keys_to_invalidate)} keys")
        
        # Update statistics
        self._invalidation_stats['total_invalidations'] += 1
        self._invalidation_stats['pattern_invalidations'] += len(patterns)
        self._invalidation_stats['keys_invalidated'] += len(invalidated_keys)
        
        result = {
            'invalidated_patterns': patterns,
            'invalidated_keys': len(invalidated_keys)
        }
        
        logger.info(f"Pattern invalidation complete: {result}")
        return result
    
    def _get_dependent_tags(self, tag_name: str) -> Set[str]:
        """
        Get all tags that depend on the given tag (recursive).
        
        Args:
            tag_name: Tag name to get dependencies for
            
        Returns:
            Set of dependent tag names
        """
        dependents = set()
        to_process = [tag_name]
        processed = set()
        
        while to_process:
            current_tag = to_process.pop()
            if current_tag in processed:
                continue
            
            processed.add(current_tag)
            
            # Add direct dependencies
            direct_deps = self._dependencies.get(current_tag, set())
            dependents.update(direct_deps)
            
            # Add to processing queue for recursive dependencies
            to_process.extend(direct_deps - processed)
        
        return dependents
    
    def cleanup_empty_tags(self) -> int:
        """
        Remove tags that have no associated cache keys.
        
        Returns:
            Number of tags removed
        """
        with self._lock:
            empty_tags = [
                tag_name for tag_name, tag in self._tags.items()
                if not tag.keys
            ]
            
            for tag_name in empty_tags:
                del self._tags[tag_name]
                
                # Clean up dependencies
                if tag_name in self._dependencies:
                    del self._dependencies[tag_name]
                
                for parent_tag in self._reverse_dependencies[tag_name]:
                    self._dependencies[parent_tag].discard(tag_name)
                
                if tag_name in self._reverse_dependencies:
                    del self._reverse_dependencies[tag_name]
            
            if empty_tags:
                logger.info(f"Cleaned up {len(empty_tags)} empty tags")
            
            return len(empty_tags)
    
    def get_tag_info(self, tag_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific tag.
        
        Args:
            tag_name: Name of the tag
            
        Returns:
            Dictionary with tag information or None if tag doesn't exist
        """
        with self._lock:
            if tag_name not in self._tags:
                return None
            
            tag = self._tags[tag_name]
            return {
                'name': tag.name,
                'created_at': tag.created_at,
                'key_count': len(tag.keys),
                'keys': list(tag.keys),
                'dependencies': list(self._dependencies.get(tag_name, set())),
                'dependent_on': list(self._reverse_dependencies.get(tag_name, set()))
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache invalidation statistics.
        
        Returns:
            Dictionary with invalidation statistics
        """
        with self._lock:
            return {
                **self._invalidation_stats,
                'total_tags': len(self._tags),
                'total_patterns': len(self._patterns),
                'total_dependencies': sum(len(deps) for deps in self._dependencies.values()),
                'keys_with_tags': len(self._key_to_tags)
            }
    
    def reset_stats(self):
        """Reset invalidation statistics."""
        with self._lock:
            self._invalidation_stats = {
                'total_invalidations': 0,
                'tag_invalidations': 0,
                'pattern_invalidations': 0,
                'dependency_invalidations': 0,
                'keys_invalidated': 0
            }


# Predefined cache invalidation strategies for common operations
class CacheInvalidationStrategies:
    """
    Predefined cache invalidation strategies for common data operations.
    
    This class provides methods for invalidating caches based on specific
    business logic and data relationships.
    """
    
    def __init__(self, invalidator: SmartCacheInvalidator):
        self.invalidator = invalidator
        self._setup_dependencies()
    
    def _setup_dependencies(self):
        """Set up common cache dependencies."""
        # Person operations affect statistics and search results
        self.invalidator.add_dependency("people", "statistics")
        self.invalidator.add_dependency("people", "search_results")
        self.invalidator.add_dependency("people", "reports")
        
        # Employment operations affect people, statistics, and reports
        self.invalidator.add_dependency("employment", "people")
        self.invalidator.add_dependency("employment", "statistics")
        self.invalidator.add_dependency("employment", "reports")
        
        # Department operations affect positions and employment
        self.invalidator.add_dependency("departments", "positions")
        self.invalidator.add_dependency("departments", "employment")
        
        # Position operations affect employment
        self.invalidator.add_dependency("positions", "employment")
    
    def invalidate_person_created(self, person_id: str):
        """Invalidate caches when a person is created."""
        tags_to_invalidate = [
            "people_list",
            "statistics",
            "search_results"
        ]
        return self.invalidator.invalidate_by_tag(tags_to_invalidate)
    
    def invalidate_person_updated(self, person_id: str):
        """Invalidate caches when a person is updated."""
        tags_to_invalidate = [
            "people_list",
            f"person_{person_id}",
            "search_results"
        ]
        return self.invalidator.invalidate_by_tag(tags_to_invalidate)
    
    def invalidate_person_deleted(self, person_id: str):
        """Invalidate caches when a person is deleted."""
        tags_to_invalidate = [
            "people_list",
            f"person_{person_id}",
            "statistics",
            "search_results",
            "reports"
        ]
        return self.invalidator.invalidate_by_tag(tags_to_invalidate)
    
    def invalidate_employment_created(self, person_id: str, position_id: str):
        """Invalidate caches when employment is created."""
        tags_to_invalidate = [
            "employment_list",
            f"person_{person_id}",
            f"position_{position_id}",
            "statistics",
            "reports"
        ]
        return self.invalidator.invalidate_by_tag(tags_to_invalidate)
    
    def invalidate_employment_updated(self, employment_id: str, person_id: str, position_id: str):
        """Invalidate caches when employment is updated."""
        tags_to_invalidate = [
            "employment_list",
            f"employment_{employment_id}",
            f"person_{person_id}",
            f"position_{position_id}",
            "statistics"
        ]
        return self.invalidator.invalidate_by_tag(tags_to_invalidate)
    
    def invalidate_department_created(self, department_id: str):
        """Invalidate caches when a department is created."""
        tags_to_invalidate = [
            "departments_list",
            "statistics"
        ]
        return self.invalidator.invalidate_by_tag(tags_to_invalidate)
    
    def invalidate_department_updated(self, department_id: str):
        """Invalidate caches when a department is updated."""
        tags_to_invalidate = [
            "departments_list",
            f"department_{department_id}",
            "positions_list",  # Positions display department name
            "employment_list"  # Employment records show department
        ]
        return self.invalidator.invalidate_by_tag(tags_to_invalidate)
    
    def invalidate_position_created(self, position_id: str, department_id: str):
        """Invalidate caches when a position is created."""
        tags_to_invalidate = [
            "positions_list",
            f"department_{department_id}",
            "statistics"
        ]
        return self.invalidator.invalidate_by_tag(tags_to_invalidate)
    
    def invalidate_bulk_operation(self, operation_type: str, count: int):
        """Invalidate caches for bulk operations."""
        if operation_type == "bulk_person_create":
            tags_to_invalidate = [
                "people_list",
                "statistics",
                "search_results"
            ]
        elif operation_type == "bulk_person_update":
            tags_to_invalidate = [
                "people_list",
                "search_results"
            ]
        elif operation_type == "bulk_employment_create":
            tags_to_invalidate = [
                "employment_list",
                "statistics",
                "reports",
                "people_list"  # Employment affects person display
            ]
        else:
            # Generic bulk operation
            tags_to_invalidate = [
                "statistics",
                "search_results",
                "reports"
            ]
        
        return self.invalidator.invalidate_by_tag(tags_to_invalidate)


# Create global instances
from .cache import get_cache

# Initialize smart cache invalidator with the global cache
_smart_invalidator = SmartCacheInvalidator(get_cache())
_cache_strategies = CacheInvalidationStrategies(_smart_invalidator)


def get_smart_invalidator() -> SmartCacheInvalidator:
    """Get the global smart cache invalidator."""
    return _smart_invalidator


def get_cache_strategies() -> CacheInvalidationStrategies:
    """Get the global cache invalidation strategies."""
    return _cache_strategies