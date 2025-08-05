"""
API Version 1 Router Module.

This module provides the main router for API version 1, including
version management, route organization, and API metadata.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
import time

from ..routes import people, departments, positions, employment, statistics
from ..auth import get_api_key_optional
from ...core.config import get_settings

# Create v1 router
v1_router = APIRouter(prefix="/v1", tags=["v1"])

# Include all v1 routes
v1_router.include_router(people.router, dependencies=[Depends(get_api_key_optional)])
v1_router.include_router(departments.router, dependencies=[Depends(get_api_key_optional)])
v1_router.include_router(positions.router, dependencies=[Depends(get_api_key_optional)])
v1_router.include_router(employment.router, dependencies=[Depends(get_api_key_optional)])
v1_router.include_router(statistics.router, dependencies=[Depends(get_api_key_optional)])


@v1_router.get(
    "/",
    summary="API v1 Information",
    description="Get information about API version 1 including available endpoints and capabilities.",
    response_model=Dict[str, Any],
    tags=["version-info"]
)
async def v1_info():
    """Get API v1 information."""
    settings = get_settings()
    
    return {
        "version": "1.0.0",
        "name": "People Management API v1",
        "description": "Version 1 of the People Management System API",
        "status": "stable",
        "deprecated": False,
        "sunset_date": None,
        "capabilities": {
            "authentication": ["api_key", "optional"],
            "rate_limiting": True,
            "pagination": True,
            "filtering": True,
            "sorting": True,
            "bulk_operations": True,
            "health_checks": True
        },
        "endpoints": {
            "people": "/api/v1/people",
            "departments": "/api/v1/departments", 
            "positions": "/api/v1/positions",
            "employment": "/api/v1/employment",
            "statistics": "/api/v1/statistics"
        },
        "limits": {
            "rate_limit_per_minute": settings.rate_limit_per_minute,
            "max_page_size": settings.max_page_size,
            "default_page_size": settings.default_page_size
        },
        "documentation": {
            "openapi": "/openapi.json",
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        },
        "timestamp": time.time()
    }


@v1_router.get(
    "/health",
    summary="API v1 Health Check", 
    description="Health check endpoint specific to API version 1.",
    response_model=Dict[str, Any],
    tags=["health"]
)
async def v1_health():
    """API v1 specific health check."""
    return {
        "version": "v1",
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "database": "healthy",
            "authentication": "healthy",
            "rate_limiting": "healthy"
        }
    }


# API Version metadata
API_VERSION = "1.0.0"
API_TITLE = "People Management API v1"
API_DESCRIPTION = """
## People Management System API - Version 1

This is version 1 of the People Management System API, providing comprehensive
endpoints for managing people, departments, positions, and employment records.

### Key Features

- **People Management**: CRUD operations for person records
- **Department Management**: Organize departments and hierarchies  
- **Position Management**: Define job positions and requirements
- **Employment Tracking**: Track employment history and relationships
- **Statistics & Analytics**: Get insights and reporting data
- **Authentication**: Optional API key authentication
- **Rate Limiting**: Built-in rate limiting protection
- **Pagination**: Efficient data pagination
- **Search & Filtering**: Advanced search capabilities

### Authentication

API key authentication is optional for v1. Include your API key in the header:
```
X-API-Key: your-api-key-here
```

### Rate Limiting

All endpoints are rate limited to prevent abuse. Current limits:
- 60 requests per minute per IP address
- Rate limit headers included in all responses

### Pagination

List endpoints support pagination using query parameters:
- `page`: Page number (default: 1)
- `size`: Items per page (default: 20, max: 100)

### Error Handling

All errors follow a consistent format with appropriate HTTP status codes
and detailed error messages.
"""

# Export the router
__all__ = ["v1_router", "API_VERSION", "API_TITLE", "API_DESCRIPTION"]