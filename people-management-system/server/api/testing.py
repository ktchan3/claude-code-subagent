"""
Comprehensive API Testing Utilities.

This module provides utilities for testing the People Management System API,
including test clients, fixtures, mock data generators, and assertion helpers.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from ..core.config import get_settings
from .auth import api_key_manager, create_api_key_for_client


class APITestClient:
    """Enhanced test client for API testing with authentication and utilities."""
    
    def __init__(self, app: FastAPI, api_key: Optional[str] = None):
        self.app = app
        self.client = TestClient(app)
        self.api_key = api_key
        self.base_headers = {"Content-Type": "application/json"}
        
        if api_key:
            self.base_headers["X-API-Key"] = api_key
    
    def set_api_key(self, api_key: str) -> None:
        """Set API key for authenticated requests."""
        self.api_key = api_key
        self.base_headers["X-API-Key"] = api_key
    
    def clear_api_key(self) -> None:
        """Clear API key for unauthenticated requests."""
        self.api_key = None
        if "X-API-Key" in self.base_headers:
            del self.base_headers["X-API-Key"]
    
    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """Make a request with default headers."""
        request_headers = self.base_headers.copy()
        if headers:
            request_headers.update(headers)
        
        return self.client.request(method, url, headers=request_headers, **kwargs)
    
    def get(self, url: str, **kwargs) -> httpx.Response:
        """GET request."""
        return self.request("GET", url, **kwargs)
    
    def post(self, url: str, **kwargs) -> httpx.Response:  
        """POST request."""
        return self.request("POST", url, **kwargs)
    
    def put(self, url: str, **kwargs) -> httpx.Response:
        """PUT request."""
        return self.request("PUT", url, **kwargs)
    
    def patch(self, url: str, **kwargs) -> httpx.Response:
        """PATCH request."""
        return self.request("PATCH", url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> httpx.Response:
        """DELETE request."""
        return self.request("DELETE", url, **kwargs)
    
    def create_person(self, person_data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Helper to create a person."""
        if person_data is None:
            person_data = generate_person_data()
        
        return self.post("/api/v1/people", json=person_data)
    
    def create_department(self, department_data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Helper to create a department."""
        if department_data is None:
            department_data = generate_department_data()
        
        return self.post("/api/v1/departments", json=department_data)
    
    def create_position(self, position_data: Optional[Dict[str, Any]] = None) -> httpx.Response:
        """Helper to create a position."""
        if position_data is None:
            position_data = generate_position_data()
        
        return self.post("/api/v1/positions", json=position_data)
    
    def assert_response_success(self, response: httpx.Response, expected_status: int = 200) -> Dict[str, Any]:
        """Assert response is successful and return data."""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") is True, f"Response not successful: {data}"
        
        return data
    
    def assert_response_error(self, response: httpx.Response, expected_status: int, expected_error_code: Optional[str] = None) -> Dict[str, Any]:
        """Assert response is an error and return data."""
        assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") is False, f"Response should be error: {data}"
        
        if expected_error_code:
            assert data.get("error_code") == expected_error_code, f"Expected error code {expected_error_code}, got {data.get('error_code')}"
        
        return data
    
    def assert_paginated_response(self, response: httpx.Response, expected_items: Optional[int] = None) -> Dict[str, Any]:
        """Assert response is paginated and return data."""
        data = self.assert_response_success(response)
        
        assert "pagination" in data, "Response should have pagination"
        assert "data" in data, "Response should have data array"
        assert isinstance(data["data"], list), "Data should be a list"
        
        pagination = data["pagination"]
        required_fields = ["page", "size", "total", "total_pages", "has_next", "has_previous"]
        for field in required_fields:
            assert field in pagination, f"Pagination missing field: {field}"
        
        if expected_items is not None:
            assert len(data["data"]) == expected_items, f"Expected {expected_items} items, got {len(data['data'])}"
        
        return data


class MockDataGenerator:
    """Generate mock data for testing."""
    
    @staticmethod
    def person_data(**overrides) -> Dict[str, Any]:
        """Generate mock person data."""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": f"john.doe.{uuid4().hex[:8]}@example.com",
            "phone": "+1-555-0123",
            "date_of_birth": "1990-01-15",
            "address": "123 Main St, City, State 12345"
        }
        data.update(overrides)
        return data
    
    @staticmethod
    def department_data(**overrides) -> Dict[str, Any]:
        """Generate mock department data."""
        data = {
            "name": f"Test Department {uuid4().hex[:8]}",
            "description": "A test department for API testing",
            "manager_email": None
        }
        data.update(overrides)
        return data
    
    @staticmethod
    def position_data(department_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Generate mock position data."""
        data = {
            "title": f"Test Position {uuid4().hex[:8]}",
            "description": "A test position for API testing",
            "department_id": department_id or str(uuid4()),
            "requirements": ["Bachelor's degree", "2+ years experience"],
            "salary_min": 50000,
            "salary_max": 80000
        }
        data.update(overrides)
        return data
    
    @staticmethod
    def employment_data(person_id: Optional[str] = None, position_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Generate mock employment data."""
        data = {
            "person_id": person_id or str(uuid4()),
            "position_id": position_id or str(uuid4()),
            "start_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
            "salary": 65000,
            "employment_type": "full_time",
            "is_active": True
        }
        data.update(overrides)
        return data
    
    @staticmethod
    def bulk_people_data(count: int = 5) -> List[Dict[str, Any]]:
        """Generate multiple person records."""
        return [MockDataGenerator.person_data() for _ in range(count)]


# Convenience functions that use the MockDataGenerator
def generate_person_data(**overrides) -> Dict[str, Any]:
    """Generate mock person data."""
    return MockDataGenerator.person_data(**overrides)


def generate_department_data(**overrides) -> Dict[str, Any]:
    """Generate mock department data."""
    return MockDataGenerator.department_data(**overrides)


def generate_position_data(**overrides) -> Dict[str, Any]:
    """Generate mock position data."""
    return MockDataGenerator.position_data(**overrides)


def generate_employment_data(**overrides) -> Dict[str, Any]:
    """Generate mock employment data."""
    return MockDataGenerator.employment_data(**overrides)


class APITestFixtures:
    """Common test fixtures and setup utilities."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.client = APITestClient(app)
        self._created_resources: Dict[str, List[str]] = {
            "people": [],
            "departments": [],
            "positions": [],
            "employments": [],
            "api_keys": []
        }
    
    def create_test_api_key(
        self,
        client_name: str = "Test Client",
        permissions: List[str] = None
    ) -> Dict[str, str]:
        """Create a test API key."""
        if permissions is None:
            permissions = ["read", "write"]
        
        key_info = create_api_key_for_client(
            client_name=client_name,
            permissions=permissions,
            expires_in_days=1  # Short expiry for tests
        )
        
        self._created_resources["api_keys"].append(key_info["api_key"])
        return key_info
    
    def create_authenticated_client(
        self,
        client_name: str = "Test Client",
        permissions: List[str] = None
    ) -> APITestClient:
        """Create an authenticated test client."""
        key_info = self.create_test_api_key(client_name, permissions)
        return APITestClient(self.app, api_key=key_info["api_key"])
    
    def create_test_person(self, **overrides) -> Dict[str, Any]:
        """Create a test person and return the response data."""
        person_data = generate_person_data(**overrides)
        response = self.client.create_person(person_data)
        data = self.client.assert_response_success(response, 201)
        
        if "data" in data and "id" in data["data"]:
            self._created_resources["people"].append(data["data"]["id"])
        
        return data
    
    def create_test_department(self, **overrides) -> Dict[str, Any]:
        """Create a test department and return the response data."""
        department_data = generate_department_data(**overrides)
        response = self.client.create_department(department_data)
        data = self.client.assert_response_success(response, 201)
        
        if "data" in data and "id" in data["data"]:
            self._created_resources["departments"].append(data["data"]["id"])
        
        return data
    
    def create_test_position(self, department_id: Optional[str] = None, **overrides) -> Dict[str, Any]:
        """Create a test position and return the response data."""
        if department_id is None:
            dept_data = self.create_test_department()
            department_id = dept_data["data"]["id"]
        
        position_data = generate_position_data(department_id=department_id, **overrides)
        response = self.client.create_position(position_data)
        data = self.client.assert_response_success(response, 201)
        
        if "data" in data and "id" in data["data"]:
            self._created_resources["positions"].append(data["data"]["id"])
        
        return data
    
    def cleanup(self) -> None:
        """Clean up created test resources."""
        # Clean up in reverse dependency order
        
        # Clean up employments
        for employment_id in self._created_resources["employments"]:
            try:
                self.client.delete(f"/api/v1/employment/{employment_id}")
            except Exception:
                pass  # Ignore cleanup errors
        
        # Clean up people
        for person_id in self._created_resources["people"]:  
            try:
                self.client.delete(f"/api/v1/people/{person_id}")
            except Exception:
                pass
        
        # Clean up positions
        for position_id in self._created_resources["positions"]:
            try:
                self.client.delete(f"/api/v1/positions/{position_id}")
            except Exception:
                pass
        
        # Clean up departments
        for department_id in self._created_resources["departments"]:
            try:
                self.client.delete(f"/api/v1/departments/{department_id}")
            except Exception:
                pass
        
        # Clean up API keys
        for api_key in self._created_resources["api_keys"]:
            try:
                api_key_manager.revoke_api_key(api_key)
            except Exception:
                pass
        
        # Clear tracking
        for resource_list in self._created_resources.values():
            resource_list.clear()


class APITestCase:
    """Base class for API test cases."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.fixtures = APITestFixtures(app)
        self.client = self.fixtures.client
    
    def setup(self) -> None:
        """Setup before each test."""
        pass
    
    def teardown(self) -> None:
        """Cleanup after each test."""
        self.fixtures.cleanup()
    
    def run_test(self, test_method) -> None:
        """Run a test method with setup and teardown."""
        try:
            self.setup()
            test_method()
        finally:
            self.teardown()


class APIEndpointTester:
    """Utility class for comprehensive endpoint testing."""
    
    def __init__(self, client: APITestClient):
        self.client = client
    
    def test_crud_endpoints(
        self,
        base_url: str,
        create_data: Dict[str, Any],
        update_data: Dict[str, Any],
        list_expected_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """Test full CRUD operations for an endpoint."""
        results = {}
        
        # Test CREATE
        response = self.client.post(base_url, json=create_data)
        create_result = self.client.assert_response_success(response, 201)
        resource_id = create_result["data"]["id"]
        results["create"] = create_result
        
        # Test READ (single)
        response = self.client.get(f"{base_url}/{resource_id}")
        read_result = self.client.assert_response_success(response)
        results["read"] = read_result
        
        # Test UPDATE  
        response = self.client.put(f"{base_url}/{resource_id}", json=update_data)
        update_result = self.client.assert_response_success(response)
        results["update"] = update_result
        
        # Test LIST
        response = self.client.get(base_url)
        list_result = self.client.assert_paginated_response(response, list_expected_count)
        results["list"] = list_result
        
        # Test DELETE
        response = self.client.delete(f"{base_url}/{resource_id}")
        delete_result = self.client.assert_response_success(response)
        results["delete"] = delete_result
        
        # Verify deletion
        response = self.client.get(f"{base_url}/{resource_id}")
        self.client.assert_response_error(response, 404, "RESOURCE_NOT_FOUND")
        
        return results
    
    def test_pagination(
        self,
        url: str,
        expected_total: Optional[int] = None,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """Test pagination functionality."""
        results = {}
        
        # Test first page
        response = self.client.get(f"{url}?page=1&size={page_size}")
        first_page = self.client.assert_paginated_response(response)
        results["first_page"] = first_page
        
        pagination = first_page["pagination"]
        total = pagination["total"]
        
        if expected_total is not None:
            assert total == expected_total, f"Expected total {expected_total}, got {total}"
        
        # Test page size enforcement
        assert len(first_page["data"]) <= page_size, f"Page size exceeded: {len(first_page['data'])}"
        
        # If there are multiple pages, test second page
        if pagination["has_next"]:
            response = self.client.get(f"{url}?page=2&size={page_size}")
            second_page = self.client.assert_paginated_response(response)
            results["second_page"] = second_page
            
            # Verify different data
            first_ids = {item.get("id") for item in first_page["data"]}
            second_ids = {item.get("id") for item in second_page["data"]}
            assert not first_ids.intersection(second_ids), "Pages should have different items"
        
        return results
    
    def test_validation_errors(
        self,
        url: str,
        invalid_data_sets: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Test validation error responses."""
        results = []
        
        for invalid_data in invalid_data_sets:
            response = self.client.post(url, json=invalid_data)
            error_result = self.client.assert_response_error(response, 422, "VALIDATION_ERROR")
            results.append({
                "input": invalid_data,
                "response": error_result
            })
        
        return results
    
    def test_authentication_requirements(
        self,
        url: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test authentication requirements for an endpoint."""
        # Save current API key
        original_key = self.client.api_key
        
        try:
            # Test without API key
            self.client.clear_api_key()
            
            if method.upper() == "GET":
                response = self.client.get(url)
            elif method.upper() == "POST":
                response = self.client.post(url, json=data or {})
            elif method.upper() == "PUT":
                response = self.client.put(url, json=data or {})
            elif method.upper() == "DELETE":
                response = self.client.delete(url)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Should succeed for optional auth or fail for required auth
            if response.status_code == 401:
                result = self.client.assert_response_error(response, 401, "UNAUTHORIZED")
                return {"auth_required": True, "response": result}
            else:
                result = self.client.assert_response_success(response)
                return {"auth_required": False, "response": result}
        
        finally:
            # Restore original API key
            if original_key:
                self.client.set_api_key(original_key)


# Export public interface
__all__ = [
    "APITestClient",
    "MockDataGenerator", 
    "APITestFixtures",
    "APITestCase",
    "APIEndpointTester",
    "generate_person_data",
    "generate_department_data",
    "generate_position_data",
    "generate_employment_data"
]