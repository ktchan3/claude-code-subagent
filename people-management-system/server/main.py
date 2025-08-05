"""
Main FastAPI application for the People Management System.

This module creates and configures the FastAPI application with all routes,
middleware, exception handlers, and database initialization.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

# Import core modules
from .core.config import get_settings, print_startup_info, get_cors_config, get_logging_config
from .core.exceptions import (
    PeopleManagementException, create_http_exception_from_domain_exception,
    format_validation_error
)
from .api.responses import (
    map_http_exception_to_error_response, add_request_id_to_response,
    add_api_version_to_response, add_processing_time_to_response,
    create_success_response, create_health_response
)

# Import database
from .database.db import initialize_database, close_database_connections, health_check

# Import middleware
from .api.middleware import setup_middleware

# Import API routes
from .api.routes import people, departments, positions, employment, statistics, admin
from .api.v1 import v1_router
from .api.openapi import create_openapi_schema, customize_openapi_tags

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events for the FastAPI application.
    """
    # Startup
    logger.info("Starting People Management System API...")
    
    try:
        # Initialize database
        initialize_database()
        logger.info("Database initialized successfully")
        
        # Print startup information
        print_startup_info()
        
        # Store startup time
        app.state.startup_time = time.time()
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down People Management System API...")
    
    try:
        # Close database connections
        close_database_connections()
        logger.info("Database connections closed")
        
        logger.info("Application shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()
    
    # Create FastAPI app with enhanced configuration
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url=settings.docs_url,
        redoc_url=settings.redoc_url,
        openapi_url=settings.openapi_url,
        lifespan=lifespan,
        # Enhanced OpenAPI configuration
        contact={
            "name": "People Management System API Support",
            "url": "https://github.com/your-org/people-management-system",
            "email": "support@example.com"
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        },
        servers=[
            {
                "url": f"http://{settings.host}:{settings.port}",
                "description": "Development server"
            }
        ] if settings.debug else [
            {
                "url": "https://api.example.com",
                "description": "Production server"
            }
        ]
    )
    
    # Customize OpenAPI schema
    customize_openapi_tags(app)
    
    # Override the openapi method with our enhanced version
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        app.openapi_schema = create_openapi_schema(app)
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        **get_cors_config()
    )
    
    # Setup custom middleware (including enhanced logging and rate limiting)
    setup_middleware(app)
    
    # Include versioned API router (v1)
    app.include_router(v1_router, prefix="/api")
    
    # Include admin router (requires admin permissions)
    app.include_router(admin.router, prefix="/api/v1")
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Add root endpoints
    setup_root_endpoints(app)
    
    return app


def setup_exception_handlers(app: FastAPI):
    """
    Setup custom exception handlers for the application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(PeopleManagementException)
    async def domain_exception_handler(request: Request, exc: PeopleManagementException):
        """Handle domain-specific exceptions."""
        logger.warning(f"Domain exception in {request.url.path}: {exc.message}")
        
        http_exception = create_http_exception_from_domain_exception(exc)
        
        # Get request ID if available
        request_id = getattr(request.state, 'request_id', None)
        
        # Create standardized error response
        response = map_http_exception_to_error_response(
            status_code=http_exception.status_code,
            detail=http_exception.detail,
            request_id=request_id
        )
        
        # Add standard headers
        if request_id:
            response = add_request_id_to_response(response, request_id)
        response = add_api_version_to_response(response, "1.0.0")
        
        return response
    
    @app.exception_handler(HTTPException)
    async def custom_http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions with standardized formatting."""
        logger.warning(f"HTTP exception in {request.url.path}: {exc.detail}")
        
        # Get request ID if available
        request_id = getattr(request.state, 'request_id', None)
        
        # Create standardized error response
        response = map_http_exception_to_error_response(
            status_code=exc.status_code,
            detail=exc.detail,
            request_id=request_id
        )
        
        # Add standard headers
        if request_id:
            response = add_request_id_to_response(response, request_id)
        response = add_api_version_to_response(response, "1.0.0")
        
        # Add any custom headers from the original exception
        if exc.headers:
            response.headers.update(exc.headers)
        
        return response
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Handle ValueError exceptions."""
        logger.warning(f"Value error in {request.url.path}: {str(exc)}")
        
        # Get request ID if available
        request_id = getattr(request.state, 'request_id', None)
        
        # Create standardized error response
        response = map_http_exception_to_error_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid value: {str(exc)}",
            request_id=request_id
        )
        
        # Add standard headers
        if request_id:
            response = add_request_id_to_response(response, request_id)
        response = add_api_version_to_response(response, "1.0.0")
        
        return response
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle all other exceptions."""
        logger.error(f"Unhandled exception in {request.url.path}: {str(exc)}", exc_info=True)
        
        settings = get_settings()
        
        # Get request ID if available
        request_id = getattr(request.state, 'request_id', None)
        
        # In debug mode, include more details
        error_detail = str(exc) if settings.debug else "An internal server error occurred"
        
        # Create standardized error response
        response = map_http_exception_to_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
            request_id=request_id
        )
        
        # Add standard headers
        if request_id:
            response = add_request_id_to_response(response, request_id)
        response = add_api_version_to_response(response, "1.0.0")
        
        return response


def setup_root_endpoints(app: FastAPI):
    """
    Setup root-level endpoints for the application.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get(
        "/",
        summary="API Root",
        description="Get basic API information and available endpoints.",
        response_model=Dict[str, Any]
    )
    async def root(request: Request):
        """Root endpoint with API information."""
        settings = get_settings()
        request_id = getattr(request.state, 'request_id', None)
        
        api_info = {
            "name": settings.app_name,
            "version": settings.app_version,
            "description": settings.app_description,
            "status": "operational",
            "features": {
                "authentication": "API Key (optional)",
                "rate_limiting": "60 requests/minute default",
                "versioning": "URL path versioning (/api/v1/)",
                "pagination": "Cursor and offset-based",
                "documentation": "OpenAPI 3.0 with Swagger UI"
            },
            "endpoints": {
                "docs": settings.docs_url,
                "redoc": settings.redoc_url,
                "openapi": settings.openapi_url,
                "health": "/health",
                "api_v1": "/api/v1/",
                "admin": "/api/v1/admin/"
            }
        }
        
        response = create_success_response(
            message="Welcome to the People Management System API",
            data=api_info,
            request_id=request_id
        )
        
        return response.body.decode() if hasattr(response, 'body') else api_info
    
    @app.get(
        "/health",
        summary="Health Check",
        description="Check the health status of the API and its dependencies.",
        response_model=Dict[str, Any]
    )
    async def health_check_endpoint(request: Request):
        """Health check endpoint."""
        try:
            # Check database health
            db_health = health_check()
            
            # Calculate uptime
            startup_time = getattr(app.state, 'startup_time', time.time())
            uptime_seconds = time.time() - startup_time
            
            settings = get_settings()
            status_value = "healthy" if db_health.get("database_connected", False) else "unhealthy"
            
            components = {
                "database": "healthy" if db_health.get("database_connected", False) else "unhealthy",
                "authentication": "healthy",
                "rate_limiting": "healthy",
                "middleware": "healthy"
            }
            
            details = {
                "database": db_health,
                "environment": {
                    "debug": settings.debug,
                    "cors_enabled": len(settings.cors_origins) > 0
                }
            }
            
            health_response = create_health_response(
                status=status_value,
                version=settings.app_version,
                uptime_seconds=uptime_seconds,
                components=components,
                details=details
            )
            
            # If unhealthy, return 503 status
            if status_value == "unhealthy":
                return JSONResponse(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    content=health_response.dict()
                )
            
            return health_response.dict()
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            
            error_health = create_health_response(
                status="unhealthy",
                version=get_settings().app_version,
                components={"database": "error", "system": "error"},
                details={"error": str(e)}
            )
            
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=error_health.dict()
            )
    
    @app.get(
        "/version",
        summary="API Version",
        description="Get the current API version information.",
        response_model=Dict[str, str]
    )
    async def version():
        """Version endpoint."""
        settings = get_settings()
        
        return {
            "version": settings.app_version,
            "name": settings.app_name,
            "build_time": "2024-01-01T00:00:00Z"  # This would be set during build
        }
    
    @app.get(
        "/status",
        summary="System Status",
        description="Get detailed system status and metrics.",
        response_model=Dict[str, Any]
    )
    async def status():
        """System status endpoint."""
        try:
            # Get database health
            db_health = health_check()
            
            # Calculate uptime
            startup_time = getattr(app.state, 'startup_time', time.time())
            uptime_seconds = time.time() - startup_time
            
            settings = get_settings()
            
            return {
                "system": {
                    "status": "operational",
                    "uptime_seconds": uptime_seconds,
                    "version": settings.app_version,
                    "environment": "development" if settings.debug else "production"
                },
                "database": {
                    "status": "connected" if db_health.get("database_connected", False) else "disconnected",
                    "health": db_health
                },
                "api": {
                    "endpoints_available": True,
                    "cors_enabled": len(settings.cors_origins) > 0,
                    "rate_limiting": True
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "system": {
                        "status": "error",
                        "error": str(e)
                    },
                    "timestamp": time.time()
                }
            )


# Create the application instance
app = create_application()


# Entry point for running the application
if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    
    # Configure logging for uvicorn
    log_config = get_logging_config()
    
    uvicorn.run(
        "server.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_config=log_config,
        access_log=True
    )