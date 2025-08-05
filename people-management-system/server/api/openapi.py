"""
OpenAPI Documentation Customization and Enhancement.

This module provides advanced OpenAPI schema customization,
documentation enhancement, and API specification utilities.
"""

import json
from typing import Any, Dict, List, Optional, Union
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute
from pydantic import BaseModel

from ..core.config import get_settings


class APIInfo(BaseModel):
    """Extended API information model."""
    
    title: str
    version: str
    description: str
    contact: Optional[Dict[str, str]] = None
    license: Optional[Dict[str, str]] = None
    terms_of_service: Optional[str] = None


class APIServer(BaseModel):
    """API server information."""
    
    url: str
    description: str
    variables: Optional[Dict[str, Dict[str, Any]]] = None


class SecurityScheme(BaseModel):
    """Security scheme definition."""
    
    type: str
    name: Optional[str] = None
    in_: Optional[str] = None
    scheme: Optional[str] = None
    bearer_format: Optional[str] = None
    description: Optional[str] = None


class ExternalDocs(BaseModel):
    """External documentation reference."""
    
    url: str
    description: Optional[str] = None


def create_openapi_schema(
    app: FastAPI,
    title: Optional[str] = None,
    version: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a comprehensive OpenAPI schema with custom enhancements.
    
    Args:
        app: FastAPI application instance
        title: Override application title
        version: Override application version
        description: Override application description
        
    Returns:
        Enhanced OpenAPI schema dictionary
    """
    settings = get_settings()
    
    # Use provided values or fallback to settings
    api_title = title or settings.app_name
    api_version = version or settings.app_version
    api_description = description or settings.app_description
    
    # Generate base OpenAPI schema
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=api_title,
        version=api_version,
        description=api_description,
        routes=app.routes,
    )
    
    # Add enhanced metadata
    openapi_schema["info"].update({
        "contact": {
            "name": "People Management System API Support",
            "url": "https://github.com/your-org/people-management-system",
            "email": "support@example.com"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        "termsOfService": "https://example.com/terms",
        "x-logo": {
            "url": "https://example.com/logo.png",
            "altText": "People Management System"
        }
    })
    
    # Add server information
    servers = [
        {
            "url": f"http://{settings.host}:{settings.port}",
            "description": "Development server"
        }
    ]
    
    if not settings.debug:
        servers.append({
            "url": "https://api.example.com",
            "description": "Production server"
        })
    
    openapi_schema["servers"] = servers
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for client authentication. Optional for most endpoints."
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT token authentication (future implementation)"
        }
    }
    
    # Add global security (optional API key)
    openapi_schema["security"] = [
        {"ApiKeyAuth": []},
        {}  # Allow unauthenticated access
    ]
    
    # Add custom extensions
    openapi_schema["x-api-id"] = "people-management-api"
    openapi_schema["x-api-category"] = "Human Resources"
    openapi_schema["x-audience"] = "Internal"
    
    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "Find more info here",
        "url": "https://docs.example.com/people-management-api"
    }
    
    # Enhance tags with descriptions
    openapi_schema["tags"] = [
        {
            "name": "people",
            "description": "Operations related to person management",
            "externalDocs": {
                "description": "People API Documentation",
                "url": "https://docs.example.com/people"
            }
        },
        {
            "name": "departments",
            "description": "Department and organizational structure management"
        },
        {
            "name": "positions",
            "description": "Job position and role management"
        },
        {
            "name": "employment",
            "description": "Employment history and relationship tracking"
        },
        {
            "name": "statistics",
            "description": "Analytics and reporting endpoints"
        },
        {
            "name": "health",
            "description": "System health and monitoring"
        },
        {
            "name": "version-info",
            "description": "API version information and capabilities"
        },
        {
            "name": "admin",
            "description": "Administrative operations (requires admin permissions)"
        }
    ]
    
    # Add response examples and schemas
    _enhance_response_schemas(openapi_schema)
    
    # Add request/response examples
    _add_api_examples(openapi_schema)
    
    # Add rate limiting information
    _add_rate_limiting_info(openapi_schema, settings.rate_limit_per_minute)
    
    # Cache the schema
    app.openapi_schema = openapi_schema
    return openapi_schema


def _enhance_response_schemas(openapi_schema: Dict[str, Any]) -> None:
    """Add enhanced response schemas to OpenAPI specification."""
    
    # Standard error response schema
    error_response_schema = {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": False},
            "message": {"type": "string", "example": "An error occurred"},
            "error_code": {"type": "string", "example": "VALIDATION_ERROR"},
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "field": {"type": "string", "nullable": True},
                        "details": {"type": "object", "nullable": True}
                    }
                }
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "request_id": {"type": "string"},
                    "timestamp": {"type": "number"},
                    "version": {"type": "string"}
                }
            }
        },
        "required": ["success", "message", "error_code", "metadata"]
    }
    
    # Pagination schema
    pagination_schema = {
        "type": "object",
        "properties": {
            "page": {"type": "integer", "minimum": 1, "example": 1},
            "size": {"type": "integer", "minimum": 1, "maximum": 100, "example": 20},
            "total": {"type": "integer", "minimum": 0, "example": 150},
            "total_pages": {"type": "integer", "minimum": 0, "example": 8},
            "has_next": {"type": "boolean", "example": True},
            "has_previous": {"type": "boolean", "example": False}
        },
        "required": ["page", "size", "total", "total_pages", "has_next", "has_previous"]
    }
    
    # Add to components
    openapi_schema["components"]["schemas"].update({
        "ErrorResponse": error_response_schema,
        "PaginationMeta": pagination_schema,
        "APIMetadata": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string", "format": "uuid"},
                "timestamp": {"type": "number", "format": "float"},
                "version": {"type": "string", "example": "1.0.0"},
                "server": {"type": "string", "example": "people-management-api"}
            }
        }
    })


def _add_api_examples(openapi_schema: Dict[str, Any]) -> None:
    """Add comprehensive examples to API endpoints."""
    
    # Example responses for common scenarios
    examples = {
        "PersonResponse": {
            "summary": "Person details",
            "value": {
                "success": True,
                "message": "Person retrieved successfully",
                "data": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "phone": "+1-555-0123",
                    "date_of_birth": "1990-01-15",
                    "address": "123 Main St, City, State 12345"
                },
                "metadata": {
                    "request_id": "req_123456789",
                    "timestamp": 1640995200.123,
                    "version": "1.0.0"
                }
            }
        },
        "ValidationError": {
            "summary": "Validation error response",
            "value": {
                "success": False,
                "message": "Validation failed",
                "error_code": "VALIDATION_ERROR",
                "validation_errors": [
                    {
                        "field": "email",
                        "message": "Invalid email format",
                        "value": "invalid-email"
                    }
                ],
                "metadata": {
                    "request_id": "req_123456789",
                    "timestamp": 1640995200.123,
                    "version": "1.0.0"
                }
            }
        },
        "NotFound": {
            "summary": "Resource not found",
            "value": {
                "success": False,
                "message": "Person not found",
                "error_code": "RESOURCE_NOT_FOUND",
                "errors": [
                    {
                        "code": "NOT_FOUND",
                        "message": "Person with identifier '123' was not found",
                        "details": {
                            "resource": "Person",
                            "identifier": "123"
                        }
                    }
                ],
                "metadata": {
                    "request_id": "req_123456789",
                    "timestamp": 1640995200.123,
                    "version": "1.0.0"
                }
            }
        },
        "RateLimit": {
            "summary": "Rate limit exceeded",
            "value": {
                "success": False,
                "message": "Rate limit exceeded",
                "error_code": "RATE_LIMITED",
                "errors": [
                    {
                        "code": "RATE_LIMITED",
                        "message": "Too many requests. Limit: 60 per 1 minute",
                        "details": {
                            "limit": 60,
                            "window": "1 minute",
                            "retry_after": 60
                        }
                    }
                ],
                "metadata": {
                    "request_id": "req_123456789",
                    "timestamp": 1640995200.123,
                    "version": "1.0.0"
                }
            }
        }
    }
    
    # Add examples to components
    if "examples" not in openapi_schema["components"]:
        openapi_schema["components"]["examples"] = {}
    
    openapi_schema["components"]["examples"].update(examples)


def _add_rate_limiting_info(openapi_schema: Dict[str, Any], rate_limit: int) -> None:
    """Add rate limiting information to OpenAPI schema."""
    
    # Add rate limiting extension
    openapi_schema["x-rate-limiting"] = {
        "default_limit": rate_limit,
        "window": "1 minute",
        "headers": {
            "X-RateLimit-Limit": "Number of requests allowed per window",
            "X-RateLimit-Remaining": "Number of requests remaining in current window",
            "X-RateLimit-Reset": "Unix timestamp when the current window resets"
        },
        "error_code": "RATE_LIMITED",
        "retry_after_header": "Retry-After"
    }


def customize_openapi_tags(app: FastAPI) -> None:
    """Customize OpenAPI tags with descriptions and external docs."""
    
    # This will be called after all routes are registered
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        return create_openapi_schema(app)
    
    app.openapi = custom_openapi


def add_api_route_metadata(route: APIRoute, metadata: Dict[str, Any]) -> None:
    """Add custom metadata to an API route."""
    
    if not hasattr(route, 'x_metadata'):
        route.x_metadata = {}
    
    route.x_metadata.update(metadata)


def generate_postman_collection(
    app: FastAPI,
    collection_name: str = "People Management API",
    base_url: str = None
) -> Dict[str, Any]:
    """
    Generate a Postman collection from the OpenAPI schema.
    
    Args:
        app: FastAPI application instance
        collection_name: Name for the Postman collection
        base_url: Base URL for the API
        
    Returns:
        Postman collection dictionary
    """
    settings = get_settings()
    base_url = base_url or f"http://{settings.host}:{settings.port}"
    
    openapi_schema = app.openapi()
    
    collection = {
        "info": {
            "name": collection_name,
            "description": openapi_schema.get("info", {}).get("description", ""),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "baseUrl",
                "value": base_url,
                "type": "string"
            },
            {
                "key": "apiKey",
                "value": "your-api-key-here",
                "type": "string"
            }
        ],
        "auth": {
            "type": "apikey",
            "apikey": [
                {
                    "key": "key",
                    "value": "X-API-Key",
                    "type": "string"
                },
                {
                    "key": "value",
                    "value": "{{apiKey}}",
                    "type": "string"
                },
                {
                    "key": "in",
                    "value": "header",
                    "type": "string"
                }
            ]
        },
        "item": []
    }
    
    # Group endpoints by tags
    endpoints_by_tag = {}
    
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, operation in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                tags = operation.get("tags", ["default"])
                tag = tags[0] if tags else "default"
                
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                
                endpoints_by_tag[tag].append({
                    "path": path,
                    "method": method.upper(),
                    "operation": operation
                })
    
    # Create Postman folders and requests
    for tag, endpoints in endpoints_by_tag.items():
        folder = {
            "name": tag.title(),
            "item": []
        }
        
        for endpoint in endpoints:
            request = _create_postman_request(endpoint, base_url)
            folder["item"].append(request)
        
        collection["item"].append(folder)
    
    return collection


def _create_postman_request(endpoint: Dict[str, Any], base_url: str) -> Dict[str, Any]:
    """Create a Postman request from an OpenAPI endpoint."""
    
    operation = endpoint["operation"]
    method = endpoint["method"]
    path = endpoint["path"]
    
    # Convert OpenAPI path parameters to Postman format
    postman_path = path.replace("{", ":").replace("}", "")
    
    request = {
        "name": operation.get("summary", f"{method} {path}"),
        "request": {
            "method": method,
            "header": [
                {
                    "key": "Content-Type",
                    "value": "application/json",
                    "type": "text"
                }
            ],
            "url": {
                "raw": f"{{{{baseUrl}}}}{postman_path}",
                "host": ["{{baseUrl}}"],
                "path": postman_path.strip("/").split("/") if postman_path.strip("/") else []
            },
            "description": operation.get("description", "")
        }
    }
    
    # Add request body for POST/PUT/PATCH
    if method in ["POST", "PUT", "PATCH"] and "requestBody" in operation:
        request_body = operation["requestBody"]
        if "application/json" in request_body.get("content", {}):
            schema = request_body["content"]["application/json"].get("schema", {})
            example = _generate_example_from_schema(schema)
            
            request["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(example, indent=2),
                "options": {
                    "raw": {
                        "language": "json"
                    }
                }
            }
    
    # Add query parameters
    parameters = operation.get("parameters", [])
    query_params = [p for p in parameters if p.get("in") == "query"]
    
    if query_params:
        request["request"]["url"]["query"] = []
        for param in query_params:
            request["request"]["url"]["query"].append({
                "key": param["name"],
                "value": param.get("example", ""),
                "description": param.get("description", ""),
                "disabled": not param.get("required", False)
            })
    
    return request


def _generate_example_from_schema(schema: Dict[str, Any]) -> Any:
    """Generate example data from OpenAPI schema."""
    
    if "example" in schema:
        return schema["example"]
    
    if "examples" in schema and schema["examples"]:
        return list(schema["examples"].values())[0]
    
    schema_type = schema.get("type", "object")
    
    if schema_type == "object":
        example = {}
        properties = schema.get("properties", {})
        
        for prop_name, prop_schema in properties.items():
            example[prop_name] = _generate_example_from_schema(prop_schema)
        
        return example
    
    elif schema_type == "array":
        items_schema = schema.get("items", {})
        return [_generate_example_from_schema(items_schema)]
    
    elif schema_type == "string":
        return schema.get("example", "string_value")
    
    elif schema_type == "integer":
        return schema.get("example", 123)
    
    elif schema_type == "number":
        return schema.get("example", 123.45)
    
    elif schema_type == "boolean":
        return schema.get("example", True)
    
    else:
        return None


# Export public interface
__all__ = [
    "create_openapi_schema",
    "customize_openapi_tags",
    "add_api_route_metadata",
    "generate_postman_collection",
    "APIInfo",
    "APIServer",
    "SecurityScheme",
    "ExternalDocs"
]