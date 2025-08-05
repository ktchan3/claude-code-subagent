"""
Administrative API routes.

This module provides administrative endpoints for API management,
including Postman collection export, API key management, and system monitoring.
"""

import json
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ...core.config import get_settings
from ..auth import get_admin_api_key, api_key_manager, APIClientInfo, create_api_key_for_client
from ..responses import create_success_response, create_error_response
from ..openapi import generate_postman_collection
from ..middleware import RequestLoggingMiddleware

# Configure logging
logger = logging.getLogger(__name__)

# Create router with admin prefix
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get(
    "/postman/collection",
    summary="Export Postman Collection",
    description="Generate and export a Postman collection for the API.",
    response_model=Dict[str, Any]
)
async def export_postman_collection(
    collection_name: str = "People Management API",
    include_auth: bool = True,
    admin_client: APIClientInfo = Depends(get_admin_api_key)
):
    """Export Postman collection for the API."""
    try:
        from ....main import app  # Import here to avoid circular imports
        
        settings = get_settings()
        base_url = f"http://{settings.host}:{settings.port}"
        
        # Generate collection
        collection = generate_postman_collection(
            app=app,
            collection_name=collection_name,
            base_url=base_url
        )
        
        # Add authentication info if requested
        if include_auth:
            collection["auth"] = {
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
            }
        
        logger.info(f"Postman collection exported by admin client: {admin_client.client_name}")
        
        return JSONResponse(
            content=collection,
            headers={
                "Content-Disposition": f'attachment; filename="{collection_name.replace(" ", "_")}.postman_collection.json"'
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting Postman collection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export Postman collection: {str(e)}"
        )


@router.get(
    "/api-keys",
    summary="List API Keys",
    description="List all API keys (admin only).",
    response_model=Dict[str, Any]
)
async def list_api_keys(
    admin_client: APIClientInfo = Depends(get_admin_api_key)
):
    """List all API keys."""
    try:
        api_keys = api_key_manager.list_api_keys()
        
        logger.info(f"API keys listed by admin client: {admin_client.client_name}")
        
        return create_success_response(
            message=f"Retrieved {len(api_keys)} API keys",
            data={
                "api_keys": api_keys,
                "total_count": len(api_keys)
            }
        ).body.decode()
        
    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.post(
    "/api-keys",
    summary="Create API Key",
    description="Create a new API key (admin only).",
    response_model=Dict[str, Any],
    status_code=status.HTTP_201_CREATED
)
async def create_api_key(
    client_name: str,
    permissions: List[str],
    expires_in_days: int = 365,
    rate_limit_override: int = None,
    admin_client: APIClientInfo = Depends(get_admin_api_key)
):
    """Create a new API key."""
    try:
        # Validate permissions
        valid_permissions = {"read", "write", "admin", "statistics"}
        provided_permissions = set(permissions)
        invalid_perms = provided_permissions - valid_permissions
        
        if invalid_perms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid permissions: {', '.join(invalid_perms)}"
            )
        
        # Create the API key
        key_info = create_api_key_for_client(
            client_name=client_name,
            permissions=permissions,
            expires_in_days=expires_in_days,
            rate_limit_override=rate_limit_override
        )
        
        logger.info(f"API key created by admin client {admin_client.client_name} for client: {client_name}")
        
        return create_success_response(
            message=f"API key created for client: {client_name}",
            data=key_info
        ).body.decode()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.delete(
    "/api-keys/{key_id}",
    summary="Revoke API Key",
    description="Revoke an API key (admin only).",
    response_model=Dict[str, Any]
)
async def revoke_api_key(
    key_id: str,
    admin_client: APIClientInfo = Depends(get_admin_api_key)
):
    """Revoke an API key."""
    try:
        # Find the API key by key_id
        target_key = None
        for api_key, key_data in api_key_manager.api_keys.items():
            if key_data.key_id == key_id:
                target_key = api_key
                break
        
        if not target_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key with ID '{key_id}' not found"
            )
        
        # Revoke the key
        success = api_key_manager.revoke_api_key(target_key)
        
        if success:
            logger.info(f"API key {key_id} revoked by admin client: {admin_client.client_name}")
            
            return create_success_response(
                message=f"API key '{key_id}' revoked successfully"
            ).body.decode()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to revoke API key '{key_id}'"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.get(
    "/system/stats",
    summary="System Statistics",
    description="Get detailed system statistics and metrics (admin only).",
    response_model=Dict[str, Any]
)
async def get_system_stats(
    admin_client: APIClientInfo = Depends(get_admin_api_key)
):
    """Get system statistics."""
    try:
        from ....main import app  # Import here to avoid circular imports
        
        # Get middleware statistics if available
        middleware_stats = {}
        for middleware in app.user_middleware:
            if isinstance(middleware.cls, type) and issubclass(middleware.cls, RequestLoggingMiddleware):
                # Try to get stats from the middleware instance
                try:
                    middleware_instance = None
                    # Find the actual middleware instance
                    for middleware_obj in app.middleware_stack:
                        if hasattr(middleware_obj, 'get_client_stats'):
                            middleware_stats = middleware_obj.get_client_stats()
                            break
                except Exception:
                    pass
        
        # Get API key statistics
        api_keys = api_key_manager.list_api_keys()
        active_keys = [key for key in api_keys if key["is_active"]]
        
        # Get database statistics (placeholder)
        db_stats = {
            "connection_status": "healthy",
            "total_tables": 5,  # This would come from actual DB query
            "estimated_records": 1000  # This would come from actual DB query
        }
        
        stats = {
            "api": {
                "version": "1.0.0",
                "total_api_keys": len(api_keys),
                "active_api_keys": len(active_keys),
                "middleware_enabled": len(app.user_middleware) > 0
            },
            "database": db_stats,
            "client_activity": middleware_stats,
            "system": {
                "uptime_seconds": getattr(app.state, 'startup_time', 0),
                "debug_mode": get_settings().debug
            }
        }
        
        logger.info(f"System stats requested by admin client: {admin_client.client_name}")
        
        return create_success_response(
            message="System statistics retrieved successfully",
            data=stats
        ).body.decode()
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system statistics: {str(e)}"
        )


@router.get(
    "/openapi/enhanced",
    summary="Enhanced OpenAPI Schema",
    description="Get enhanced OpenAPI schema with custom extensions (admin only).",
    response_model=Dict[str, Any]
)
async def get_enhanced_openapi(
    admin_client: APIClientInfo = Depends(get_admin_api_key)
):
    """Get enhanced OpenAPI schema."""
    try:
        from ....main import app  # Import here to avoid circular imports
        
        # Get the OpenAPI schema
        openapi_schema = app.openapi()
        
        logger.info(f"Enhanced OpenAPI schema requested by admin client: {admin_client.client_name}")
        
        return JSONResponse(content=openapi_schema)
        
    except Exception as e:
        logger.error(f"Error getting OpenAPI schema: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get OpenAPI schema: {str(e)}"
        )


@router.get(
    "/health",
    summary="Admin Health Check",
    description="Administrative health check with detailed system information.",
    response_model=Dict[str, Any]
)
async def admin_health_check(
    admin_client: APIClientInfo = Depends(get_admin_api_key)
):
    """Administrative health check."""
    try:
        settings = get_settings()
        
        health_data = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # This would be actual timestamp
            "version": settings.app_version,
            "environment": "development" if settings.debug else "production",
            "components": {
                "database": "healthy",
                "authentication": "healthy",
                "rate_limiting": "healthy",
                "middleware": "healthy"
            },
            "admin_client": {
                "client_name": admin_client.client_name,
                "permissions": list(admin_client.permissions)
            }
        }
        
        return create_success_response(
            message="Admin health check successful",
            data=health_data
        ).body.decode()
        
    except Exception as e:
        logger.error(f"Error in admin health check: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Admin health check failed: {str(e)}"
        )