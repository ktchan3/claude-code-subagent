"""
API Service Layer for People Management System Client

Provides a Qt-friendly wrapper around the shared API client with signals,
threading support, and caching for the GUI application.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps

from PySide6.QtCore import QObject, Signal, QThread, QTimer
from PySide6.QtWidgets import QApplication

from shared.api_client import (
    PeopleManagementClient, 
    ClientConfig,
    PersonData,
    DepartmentData,
    PositionData,
    EmploymentData,
    PaginationParams,
    SearchParams,
    APIClientError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError
)

logger = logging.getLogger(__name__)


class SyncWorker(QThread):
    """Worker thread for synchronous API operations."""
    
    # Signals
    finished = Signal(object)  # Result of the operation
    error = Signal(Exception)  # Error that occurred
    progress = Signal(str)  # Progress message
    
    def __init__(self, sync_func, *args, **kwargs):
        super().__init__()
        self.sync_func = sync_func
        self.args = args
        self.kwargs = kwargs
        self.result = None
        self.exception = None
    
    def run(self):
        """Run the synchronous operation in this thread."""
        try:
            # Run the synchronous function
            self.result = self.sync_func(*self.args, **self.kwargs)
            self.finished.emit(self.result)
            
        except Exception as e:
            self.exception = e
            self.error.emit(e)


class CacheEntry:
    """Cache entry with expiration."""
    
    def __init__(self, data: Any, ttl_seconds: int = 300):
        self.data = data
        self.created_at = datetime.utcnow()
        self.expires_at = self.created_at + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class APIService(QObject):
    """
    Qt-friendly API service that wraps the shared API client.
    
    Provides signals for async operations, caching, and thread management
    suitable for GUI applications.
    """
    
    # Connection signals
    connection_status_changed = Signal(bool)  # Connected/disconnected
    connection_error = Signal(str)  # Connection error message
    
    # Data signals
    data_updated = Signal(str, object)  # Data type, updated data
    operation_completed = Signal(str, bool, str)  # Operation, success, message
    
    # Progress signals
    operation_started = Signal(str)  # Operation description
    operation_progress = Signal(str, int)  # Message, percentage
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, **kwargs):
        super().__init__()
        
        self.base_url = base_url
        self.api_key = api_key
        
        # Create client configuration
        self.config = ClientConfig(
            base_url=base_url,
            api_key=api_key,
            **kwargs
        )
        
        # Initialize API client
        self.client = PeopleManagementClient(self.config)
        
        # Connection state
        self.is_connected = False
        self.last_connection_test = None
        
        # Cache for API data
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl = 300  # 5 minutes default TTL
        
        # Active workers
        self.active_workers: List[SyncWorker] = []
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._auto_refresh)
        self.auto_refresh_enabled = False
        self.refresh_interval = 30000  # 30 seconds
        
        logger.info(f"API service initialized for {base_url}")
    
    def set_auto_refresh(self, enabled: bool, interval_seconds: int = 30):
        """Enable/disable auto-refresh of cached data."""
        self.auto_refresh_enabled = enabled
        self.refresh_interval = interval_seconds * 1000
        
        if enabled:
            self.refresh_timer.start(self.refresh_interval)
        else:
            self.refresh_timer.stop()
    
    def _auto_refresh(self):
        """Auto-refresh cached data."""
        if not self.is_connected:
            return
        
        # Refresh expired cache entries
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            if key.startswith('people_'):
                self.list_people_async()
            elif key.startswith('departments_'):
                self.list_departments_async()
            elif key.startswith('positions_'):
                self.list_positions_async()
            elif key.startswith('employment_'):
                self.list_employment_async()
    
    def _get_cache_key(self, operation: str, **params) -> str:
        """Generate cache key for operation and parameters."""
        param_str = "_".join(f"{k}_{v}" for k, v in sorted(params.items()) if v is not None)
        return f"{operation}_{param_str}" if param_str else operation
    
    def _get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if available and not expired."""
        entry = self.cache.get(cache_key)
        if entry and not entry.is_expired():
            return entry.data
        return None
    
    def _set_cached_data(self, cache_key: str, data: Any, ttl_seconds: Optional[int] = None):
        """Set data in cache."""
        ttl = ttl_seconds or self.cache_ttl
        self.cache[cache_key] = CacheEntry(data, ttl)
    
    def _create_worker(self, sync_func: Callable, *args, **kwargs) -> SyncWorker:
        """Create and configure a sync worker."""
        worker = SyncWorker(sync_func, *args, **kwargs)
        
        # Connect signals
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)
        worker.progress.connect(self._on_worker_progress)
        
        # Track worker
        self.active_workers.append(worker)
        
        return worker
    
    def _on_worker_finished(self, result):
        """Handle worker completion."""
        worker = self.sender()
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        
        worker.deleteLater()
    
    def _on_worker_error(self, error):
        """Handle worker error."""
        worker = self.sender()
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        
        logger.error(f"API operation failed: {error}")
        self.connection_error.emit(str(error))
        
        worker.deleteLater()
    
    def _on_worker_progress(self, message):
        """Handle worker progress update."""
        # Extract percentage if available
        # For now, just emit the message
        self.operation_progress.emit(message, -1)
    
    # Connection management
    
    def test_connection(self) -> bool:
        """Test API connection."""
        try:
            self.client.test_connection()
            self.is_connected = True
            self.last_connection_test = datetime.utcnow()
            self.connection_status_changed.emit(True)
            return True
            
        except Exception as e:
            self.is_connected = False
            self.connection_status_changed.emit(False)
            logger.error(f"Connection test failed: {e}")
            return False
    
    def test_connection_async(self):
        """Test connection asynchronously."""
        self.operation_started.emit("Testing connection...")
        worker = self._create_worker(self.test_connection)
        worker.start()
    
    def close(self):
        """Close the API client."""
        # Stop auto-refresh
        self.refresh_timer.stop()
        
        # Wait for active workers to finish
        for worker in self.active_workers[:]:
            if worker.isRunning():
                worker.quit()
                worker.wait(5000)  # Wait max 5 seconds
        
        # Close API client
        self.client.close()
        
        self.is_connected = False
        self.connection_status_changed.emit(False)
    
    # People operations
    
    def create_person(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new person."""
        logger.debug("=== API SERVICE CREATE PERSON ===")
        logger.debug(f"Input data: {person_data}")
        
        # Log specific fields we're concerned about
        logger.debug(f"Input title: '{person_data.get('title')}'")
        logger.debug(f"Input suffix: '{person_data.get('suffix')}'")
        logger.debug(f"Input first_name: '{person_data.get('first_name')}'")
        logger.debug(f"Input last_name: '{person_data.get('last_name')}'")
        
        person = PersonData(**person_data)
        
        # Log PersonData after conversion
        person_dict = person.dict()
        logger.debug(f"PersonData dict: {person_dict}")
        logger.debug(f"PersonData title: '{person_dict.get('title')}'")
        logger.debug(f"PersonData suffix: '{person_dict.get('suffix')}'")
        
        result = self.client.create_person(person)
        
        # Log result
        logger.debug(f"API result: {result}")
        logger.debug("=== END API SERVICE CREATE PERSON ===")
        
        # Invalidate people cache
        self._invalidate_cache('people_')
        
        return result
    
    def create_person_async(self, person_data: Dict[str, Any]):
        """Create person asynchronously."""
        self.operation_started.emit("Creating person...")
        worker = self._create_worker(self.create_person, person_data)
        worker.finished.connect(
            lambda result: self.operation_completed.emit("create_person", True, "Person created successfully")
        )
        worker.start()
    
    def list_people(self, 
                   page: int = 1, 
                   page_size: int = 20,
                   query: Optional[str] = None,
                   sort_by: Optional[str] = None,
                   sort_desc: bool = False,
                   active_only: Optional[bool] = None,
                   use_cache: bool = True) -> Dict[str, Any]:
        """List people with filtering and pagination."""
        
        cache_key = self._get_cache_key(
            'people_list',
            page=page,
            page_size=page_size,
            query=query,
            sort_by=sort_by,
            sort_desc=sort_desc,
            active_only=active_only
        )
        
        # Check cache first
        if use_cache:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
        
        # Prepare parameters
        pagination = PaginationParams(page=page, size=page_size)
        search = SearchParams(query=query, sort_by=sort_by, sort_desc=sort_desc)
        
        result = self.client.list_people(
            pagination=pagination,
            search=search,
            active_only=active_only
        )
        
        # Cache result
        self._set_cached_data(cache_key, result)
        
        return result
    
    def list_people_async(self, **kwargs):
        """List people asynchronously."""
        self.operation_started.emit("Loading people...")
        worker = self._create_worker(self.list_people, **kwargs)
        worker.finished.connect(
            lambda result: self.data_updated.emit("people", result)
        )
        worker.start()
    
    def get_person(self, person_id: str, use_cache: bool = True) -> Dict[str, Any]:
        """Get person by ID."""
        cache_key = f"person_{person_id}"
        
        if use_cache:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
        
        result = self.client.get_person(person_id)
        self._set_cached_data(cache_key, result)
        
        return result
    
    def get_person_async(self, person_id: str):
        """Get person asynchronously."""
        self.operation_started.emit(f"Loading person {person_id}...")
        worker = self._create_worker(self.get_person, person_id)
        worker.finished.connect(
            lambda result: self.data_updated.emit("person", result)
        )
        worker.start()
    
    def update_person(self, person_id: str, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update person."""
        result = self.client.update_person(person_id, person_data)
        
        # Invalidate cache
        self._invalidate_cache('people_')
        self._invalidate_cache(f'person_{person_id}')
        
        return result
    
    def update_person_async(self, person_id: str, person_data: Dict[str, Any]):
        """Update person asynchronously."""
        self.operation_started.emit(f"Updating person {person_id}...")
        worker = self._create_worker(self.update_person, person_id, person_data)
        worker.finished.connect(
            lambda result: self.operation_completed.emit("update_person", True, "Person updated successfully")
        )
        worker.start()
    
    def delete_person(self, person_id: str) -> Dict[str, Any]:
        """Delete person."""
        result = self.client.delete_person(person_id)
        
        # Invalidate cache
        self._invalidate_cache('people_')
        self._invalidate_cache(f'person_{person_id}')
        
        return result
    
    def delete_person_async(self, person_id: str):
        """Delete person asynchronously."""
        self.operation_started.emit(f"Deleting person {person_id}...")
        worker = self._create_worker(self.delete_person, person_id)
        worker.finished.connect(
            lambda result: self.operation_completed.emit("delete_person", True, "Person deleted successfully")
        )
        worker.start()
    
    # Department operations
    
    def list_departments(self, page: int = 1, page_size: int = 20, use_cache: bool = True) -> Dict[str, Any]:
        """List departments."""
        cache_key = self._get_cache_key('departments_list', page=page, page_size=page_size)
        
        if use_cache:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
        
        pagination = PaginationParams(page=page, size=page_size)
        result = self.client.list_departments(pagination=pagination)
        
        self._set_cached_data(cache_key, result)
        return result
    
    def list_departments_async(self, **kwargs):
        """List departments asynchronously."""
        self.operation_started.emit("Loading departments...")
        worker = self._create_worker(self.list_departments, **kwargs)
        worker.finished.connect(
            lambda result: self.data_updated.emit("departments", result)
        )
        worker.start()
    
    def create_department(self, department_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create department."""
        department = DepartmentData(**department_data)
        result = self.client.create_department(department)
        
        self._invalidate_cache('departments_')
        return result
    
    def create_department_async(self, department_data: Dict[str, Any]):
        """Create department asynchronously."""
        self.operation_started.emit("Creating department...")
        worker = self._create_worker(self.create_department, department_data)
        worker.finished.connect(
            lambda result: self.operation_completed.emit("create_department", True, "Department created successfully")
        )
        worker.start()
    
    # Position operations
    
    def list_positions(self, 
                      page: int = 1, 
                      page_size: int = 20,
                      department_id: Optional[str] = None,
                      use_cache: bool = True) -> Dict[str, Any]:
        """List positions."""
        cache_key = self._get_cache_key(
            'positions_list',
            page=page,
            page_size=page_size,
            department_id=department_id
        )
        
        if use_cache:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
        
        pagination = PaginationParams(page=page, size=page_size)
        result = self.client.list_positions(
            pagination=pagination,
            department_id=department_id
        )
        
        self._set_cached_data(cache_key, result)
        return result
    
    def list_positions_async(self, **kwargs):
        """List positions asynchronously."""
        self.operation_started.emit("Loading positions...")
        worker = self._create_worker(self.list_positions, **kwargs)
        worker.finished.connect(
            lambda result: self.data_updated.emit("positions", result)
        )
        worker.start()
    
    # Employment operations
    
    def list_employment(self,
                       page: int = 1,
                       page_size: int = 20,
                       person_id: Optional[str] = None,
                       position_id: Optional[str] = None,
                       active_only: Optional[bool] = None,
                       use_cache: bool = True) -> Dict[str, Any]:
        """List employment records."""
        cache_key = self._get_cache_key(
            'employment_list',
            page=page,
            page_size=page_size,
            person_id=person_id,
            position_id=position_id,
            active_only=active_only
        )
        
        if use_cache:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
        
        pagination = PaginationParams(page=page, size=page_size)
        result = self.client.list_employment(
            pagination=pagination,
            person_id=person_id,
            position_id=position_id,
            active_only=active_only
        )
        
        self._set_cached_data(cache_key, result)
        return result
    
    def list_employment_async(self, **kwargs):
        """List employment asynchronously."""
        self.operation_started.emit("Loading employment records...")
        worker = self._create_worker(self.list_employment, **kwargs)
        worker.finished.connect(
            lambda result: self.data_updated.emit("employment", result)
        )
        worker.start()
    
    # Statistics operations
    
    def get_statistics(self, use_cache: bool = True) -> Dict[str, Any]:
        """Get system statistics."""
        cache_key = "statistics"
        
        if use_cache:
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                return cached_data
        
        try:
            result = self.client.get_statistics()
            self._set_cached_data(cache_key, result, ttl_seconds=60)  # Cache for 1 minute
            return result
        except NotFoundError:
            # Statistics endpoint not available, return empty stats
            logger.warning("Statistics endpoint not found, returning empty statistics")
            empty_stats = {
                'total_people': 0,
                'active_employees': 0,
                'total_departments': 0,
                'total_positions': 0,
                'average_salary': None,
                'employment_statistics': {}
            }
            return empty_stats
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise
    
    def get_statistics_async(self):
        """Get statistics asynchronously."""
        self.operation_started.emit("Loading statistics...")
        worker = self._create_worker(self.get_statistics)
        worker.finished.connect(
            lambda result: self.data_updated.emit("statistics", result)
        )
        worker.start()
    
    # Cache management
    
    def _invalidate_cache(self, prefix: str):
        """Invalidate cache entries with given prefix."""
        keys_to_remove = [key for key in self.cache.keys() if key.startswith(prefix)]
        for key in keys_to_remove:
            del self.cache[key]
    
    def clear_cache(self):
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information."""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries
        }