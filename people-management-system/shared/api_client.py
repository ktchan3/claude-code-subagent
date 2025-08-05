"""
People Management System API Client SDK.

This module provides a comprehensive Python client for interacting with
the People Management System API, with support for authentication,
error handling, pagination, and all API operations.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin
import httpx
from pydantic import BaseModel, Field

from .models.response import APIResponse, PaginatedResponse, ErrorResponse


# Configure logging
logger = logging.getLogger(__name__)


class APIClientError(Exception):
    """Base exception for API client errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code


class AuthenticationError(APIClientError):
    """Authentication failed."""
    pass


class ValidationError(APIClientError):
    """Request validation failed."""
    
    def __init__(self, message: str, validation_errors: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message, 422, "VALIDATION_ERROR")
        self.validation_errors = validation_errors or []


class NotFoundError(APIClientError):
    """Resource not found."""
    
    def __init__(self, resource: str, identifier: str):
        super().__init__(f"{resource} with identifier '{identifier}' not found", 404, "RESOURCE_NOT_FOUND")
        self.resource = resource
        self.identifier = identifier


class RateLimitError(APIClientError):
    """Rate limit exceeded."""
    
    def __init__(self, limit: int, retry_after: int):
        super().__init__(f"Rate limit exceeded: {limit} requests per minute", 429, "RATE_LIMITED")
        self.limit = limit
        self.retry_after = retry_after


class ClientConfig(BaseModel):
    """API client configuration."""
    
    base_url: str = Field(..., description="Base API URL")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    timeout: float = Field(30.0, description="Request timeout in seconds")
    max_retries: int = Field(3, description="Maximum number of retries")
    retry_delay: float = Field(1.0, description="Delay between retries in seconds")
    user_agent: str = Field("PeopleManagementClient/1.0.0", description="User agent string")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")


class PaginationParams(BaseModel):
    """Pagination parameters for list requests."""
    
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Items per page")


class SearchParams(BaseModel):
    """Search parameters for filtering requests."""
    
    query: Optional[str] = Field(None, description="Search query")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_desc: bool = Field(False, description="Sort in descending order")


class PersonData(BaseModel):
    """Person data model."""
    
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None


class DepartmentData(BaseModel):
    """Department data model."""
    
    name: str
    description: Optional[str] = None
    manager_email: Optional[str] = None


class PositionData(BaseModel):
    """Position data model."""
    
    title: str
    description: Optional[str] = None
    department_id: str
    requirements: Optional[List[str]] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None


class EmploymentData(BaseModel):
    """Employment data model."""
    
    person_id: str
    position_id: str
    start_date: str
    end_date: Optional[str] = None
    salary: Optional[float] = None
    employment_type: str = Field(default="full_time")
    is_active: bool = Field(default=True)


class PeopleManagementClient:
    """
    Comprehensive client for the People Management System API.
    
    Provides methods for all API operations with proper error handling,
    authentication, pagination, and retry logic.
    """
    
    def __init__(self, config: Union[ClientConfig, Dict[str, Any]]):
        if isinstance(config, dict):
            config = ClientConfig(**config)
        
        self.config = config
        self._client = httpx.AsyncClient(
            timeout=config.timeout,
            verify=config.verify_ssl,
            headers={
                "User-Agent": config.user_agent,
                "Content-Type": "application/json"
            }
        )
        
        if config.api_key:
            self._client.headers["X-API-Key"] = config.api_key
        
        self._session_stats = {
            "requests_made": 0,
            "errors_encountered": 0,
            "last_request_time": None,
            "session_start": time.time()
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        if endpoint.startswith("/"):
            endpoint = endpoint[1:]
        return urljoin(self.config.base_url.rstrip("/") + "/", endpoint)
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make HTTP request with error handling and retries."""
        url = self._build_url(endpoint)
        self._session_stats["requests_made"] += 1
        self._session_stats["last_request_time"] = time.time()
        
        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    **kwargs
                )
                
                # Handle successful responses
                if 200 <= response.status_code < 300:
                    return response.json()
                
                # Handle error responses
                await self._handle_error_response(response)
                
            except httpx.RequestError as e:
                logger.warning(f"Request error on attempt {attempt + 1}: {e}")
                if attempt == self.config.max_retries:
                    self._session_stats["errors_encountered"] += 1
                    raise APIClientError(f"Request failed after {self.config.max_retries} retries: {e}")
                
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
            
            except httpx.HTTPStatusError as e:
                # Don't retry on client errors (4xx)
                if 400 <= e.response.status_code < 500:
                    await self._handle_error_response(e.response)
                
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt == self.config.max_retries:
                    self._session_stats["errors_encountered"] += 1
                    raise APIClientError(f"HTTP error: {e}")
                
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
    
    async def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses and raise appropriate exceptions."""
        self._session_stats["errors_encountered"] += 1
        
        try:
            error_data = response.json()
        except ValueError:
            error_data = {"message": response.text or "Unknown error", "error_code": "UNKNOWN_ERROR"}
        
        error_message = error_data.get("message", "Unknown error")
        error_code = error_data.get("error_code", "UNKNOWN_ERROR")
        
        if response.status_code == 401:
            raise AuthenticationError(error_message, response.status_code, error_code)
        elif response.status_code == 404:
            raise NotFoundError("Resource", "unknown")
        elif response.status_code == 422:
            validation_errors = error_data.get("validation_errors", [])
            raise ValidationError(error_message, validation_errors)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            limit = int(response.headers.get("X-RateLimit-Limit", 60))
            raise RateLimitError(limit, retry_after)
        else:
            raise APIClientError(error_message, response.status_code, error_code)
    
    # Health and Status endpoints
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health status."""
        return await self._request("GET", "/health")
    
    async def get_version(self) -> Dict[str, Any]:
        """Get API version information."""
        return await self._request("GET", "/version")
    
    async def get_api_info(self) -> Dict[str, Any]:
        """Get API information and capabilities."""
        return await self._request("GET", "/api/v1/")
    
    # People endpoints
    
    async def create_person(self, person_data: Union[PersonData, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new person."""
        if isinstance(person_data, PersonData):
            person_data = person_data.dict()
        
        return await self._request("POST", "/api/v1/people", json_data=person_data)
    
    async def get_person(self, person_id: str) -> Dict[str, Any]:
        """Get person by ID."""
        return await self._request("GET", f"/api/v1/people/{person_id}")
    
    async def get_person_by_email(self, email: str) -> Dict[str, Any]:
        """Get person by email address."""
        return await self._request("GET", f"/api/v1/people/by-email/{email}")
    
    async def list_people(
        self,
        pagination: Optional[Union[PaginationParams, Dict[str, Any]]] = None,
        search: Optional[Union[SearchParams, Dict[str, Any]]] = None,
        active_only: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List people with pagination and filtering."""
        params = {}
        
        if pagination:
            if isinstance(pagination, PaginationParams):
                params.update(pagination.dict())
            else:
                params.update(pagination)
        
        if search:
            if isinstance(search, SearchParams):
                search_params = search.dict(exclude_none=True)
                if search_params.get("sort_desc"):
                    search_params["sort_desc"] = "true"
                params.update(search_params)
            else:
                params.update(search)
        
        if active_only is not None:
            params["active"] = "true" if active_only else "false"
        
        return await self._request("GET", "/api/v1/people", params=params)
    
    async def update_person(self, person_id: str, person_data: Union[PersonData, Dict[str, Any]]) -> Dict[str, Any]:
        """Update person information."""
        if isinstance(person_data, PersonData):
            person_data = person_data.dict(exclude_unset=True)
        
        return await self._request("PUT", f"/api/v1/people/{person_id}", json_data=person_data)
    
    async def delete_person(self, person_id: str) -> Dict[str, Any]:
        """Delete a person."""
        return await self._request("DELETE", f"/api/v1/people/{person_id}")
    
    async def bulk_create_people(self, people_data: List[Union[PersonData, Dict[str, Any]]]) -> Dict[str, Any]:
        """Create multiple people in bulk."""
        people_list = []
        for person in people_data:
            if isinstance(person, PersonData):
                people_list.append(person.dict())
            else:
                people_list.append(person)
        
        return await self._request("POST", "/api/v1/people/bulk", json_data={"people": people_list})
    
    # Department endpoints
    
    async def create_department(self, department_data: Union[DepartmentData, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new department."""
        if isinstance(department_data, DepartmentData):
            department_data = department_data.dict()
        
        return await self._request("POST", "/api/v1/departments", json_data=department_data)
    
    async def get_department(self, department_id: str) -> Dict[str, Any]:
        """Get department by ID."""
        return await self._request("GET", f"/api/v1/departments/{department_id}")
    
    async def list_departments(
        self,
        pagination: Optional[Union[PaginationParams, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """List departments."""
        params = {}
        if pagination:
            if isinstance(pagination, PaginationParams):
                params.update(pagination.dict())
            else:
                params.update(pagination)
        
        return await self._request("GET", "/api/v1/departments", params=params)
    
    async def update_department(self, department_id: str, department_data: Union[DepartmentData, Dict[str, Any]]) -> Dict[str, Any]:
        """Update department information."""
        if isinstance(department_data, DepartmentData):
            department_data = department_data.dict(exclude_unset=True)
        
        return await self._request("PUT", f"/api/v1/departments/{department_id}", json_data=department_data)
    
    async def delete_department(self, department_id: str) -> Dict[str, Any]:
        """Delete a department."""
        return await self._request("DELETE", f"/api/v1/departments/{department_id}")
    
    # Position endpoints
    
    async def create_position(self, position_data: Union[PositionData, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new position."""
        if isinstance(position_data, PositionData):
            position_data = position_data.dict()
        
        return await self._request("POST", "/api/v1/positions", json_data=position_data)
    
    async def get_position(self, position_id: str) -> Dict[str, Any]:
        """Get position by ID."""
        return await self._request("GET", f"/api/v1/positions/{position_id}")
    
    async def list_positions(
        self,
        pagination: Optional[Union[PaginationParams, Dict[str, Any]]] = None,
        department_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """List positions."""
        params = {}
        if pagination:
            if isinstance(pagination, PaginationParams):
                params.update(pagination.dict())
            else:
                params.update(pagination)
        
        if department_id:
            params["department_id"] = department_id
        
        return await self._request("GET", "/api/v1/positions", params=params)
    
    async def update_position(self, position_id: str, position_data: Union[PositionData, Dict[str, Any]]) -> Dict[str, Any]:
        """Update position information."""
        if isinstance(position_data, PositionData):
            position_data = position_data.dict(exclude_unset=True)
        
        return await self._request("PUT", f"/api/v1/positions/{position_id}", json_data=position_data)
    
    async def delete_position(self, position_id: str) -> Dict[str, Any]:
        """Delete a position."""
        return await self._request("DELETE", f"/api/v1/positions/{position_id}")
    
    # Employment endpoints
    
    async def create_employment(self, employment_data: Union[EmploymentData, Dict[str, Any]]) -> Dict[str, Any]:
        """Create a new employment record."""
        if isinstance(employment_data, EmploymentData):
            employment_data = employment_data.dict()
        
        return await self._request("POST", "/api/v1/employment", json_data=employment_data)
    
    async def get_employment(self, employment_id: str) -> Dict[str, Any]:
        """Get employment record by ID."""
        return await self._request("GET", f"/api/v1/employment/{employment_id}")
    
    async def list_employment(
        self,
        pagination: Optional[Union[PaginationParams, Dict[str, Any]]] = None,
        person_id: Optional[str] = None,
        position_id: Optional[str] = None,
        active_only: Optional[bool] = None
    ) -> Dict[str, Any]:
        """List employment records."""
        params = {}
        if pagination:
            if isinstance(pagination, PaginationParams):
                params.update(pagination.dict())
            else:
                params.update(pagination)
        
        if person_id:
            params["person_id"] = person_id
        if position_id:
            params["position_id"] = position_id
        if active_only is not None:
            params["active"] = "true" if active_only else "false"
        
        return await self._request("GET", "/api/v1/employment", params=params)
    
    async def update_employment(self, employment_id: str, employment_data: Union[EmploymentData, Dict[str, Any]]) -> Dict[str, Any]:
        """Update employment record."""
        if isinstance(employment_data, EmploymentData):
            employment_data = employment_data.dict(exclude_unset=True)
        
        return await self._request("PUT", f"/api/v1/employment/{employment_id}", json_data=employment_data)
    
    async def end_employment(self, employment_id: str, end_date: Optional[str] = None) -> Dict[str, Any]:
        """End an employment record."""
        data = {
            "is_active": False,
            "end_date": end_date or datetime.utcnow().isoformat()
        }
        return await self._request("PATCH", f"/api/v1/employment/{employment_id}", json_data=data)
    
    # Statistics endpoints
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        return await self._request("GET", "/api/v1/statistics")
    
    async def get_department_statistics(self, department_id: str) -> Dict[str, Any]:
        """Get statistics for a specific department."""
        return await self._request("GET", f"/api/v1/statistics/departments/{department_id}")
    
    # Utility methods
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get client session statistics."""
        current_time = time.time()
        session_duration = current_time - self._session_stats["session_start"]
        
        return {
            **self._session_stats,
            "session_duration_seconds": session_duration,
            "requests_per_minute": (self._session_stats["requests_made"] / session_duration) * 60 if session_duration > 0 else 0,
            "error_rate": self._session_stats["errors_encountered"] / max(1, self._session_stats["requests_made"])
        }
    
    async def test_connection(self) -> bool:
        """Test API connection and authentication."""
        try:
            await self.health_check()
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


# Synchronous wrapper for compatibility
class SyncPeopleManagementClient:
    """Synchronous wrapper for the async PeopleManagementClient."""
    
    def __init__(self, config: Union[ClientConfig, Dict[str, Any]]):
        self._async_client = PeopleManagementClient(config)
    
    def _run_async(self, coro):
        """Run async coroutine synchronously."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the client."""
        self._run_async(self._async_client.close())
    
    # Wrap all async methods
    def health_check(self) -> Dict[str, Any]:
        return self._run_async(self._async_client.health_check())
    
    def create_person(self, person_data: Union[PersonData, Dict[str, Any]]) -> Dict[str, Any]:
        return self._run_async(self._async_client.create_person(person_data))
    
    def get_person(self, person_id: str) -> Dict[str, Any]:
        return self._run_async(self._async_client.get_person(person_id))
    
    def list_people(self, **kwargs) -> Dict[str, Any]:
        return self._run_async(self._async_client.list_people(**kwargs))
    
    # Add other methods as needed...


# Convenience functions
def create_client(
    base_url: str,
    api_key: Optional[str] = None,
    **kwargs
) -> PeopleManagementClient:
    """Create an async API client with default configuration."""
    config = ClientConfig(base_url=base_url, api_key=api_key, **kwargs)
    return PeopleManagementClient(config)


def create_sync_client(
    base_url: str,
    api_key: Optional[str] = None,
    **kwargs
) -> SyncPeopleManagementClient:
    """Create a sync API client with default configuration."""
    config = ClientConfig(base_url=base_url, api_key=api_key, **kwargs)
    return SyncPeopleManagementClient(config)


# Export public interface
__all__ = [
    # Main clients
    "PeopleManagementClient",
    "SyncPeopleManagementClient",
    
    # Configuration
    "ClientConfig",
    "PaginationParams", 
    "SearchParams",
    
    # Data models
    "PersonData",
    "DepartmentData",
    "PositionData", 
    "EmploymentData",
    
    # Exceptions
    "APIClientError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    
    # Convenience functions
    "create_client",
    "create_sync_client"
]