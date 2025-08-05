#!/usr/bin/env python3
"""
Simple runner script for the People Management System API.

This script provides an easy way to start the FastAPI server with
proper configuration and logging.
"""

import sys
import os
import argparse
import uvicorn

# Add the parent directory to the Python path so we can import from server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.core.config import get_settings, get_logging_config
from server.database.db import initialize_database


def main():
    """Main entry point for running the server."""
    parser = argparse.ArgumentParser(description="Run the People Management System API")
    parser.add_argument(
        "--host", 
        default=None, 
        help="Host to bind to (default: from config)"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=None, 
        help="Port to bind to (default: from config)"
    )
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload on code changes"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug mode"
    )
    parser.add_argument(
        "--init-db", 
        action="store_true", 
        help="Initialize database before starting server"
    )
    
    args = parser.parse_args()
    
    # Get settings
    settings = get_settings()
    
    # Override settings with command line arguments
    if args.debug:
        os.environ["APP_DEBUG"] = "true"
        settings = get_settings()  # Reload settings
    
    host = args.host or settings.host
    port = args.port or settings.port
    reload = args.reload or settings.reload
    
    print(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    print(f"🌐 Server will be available at: http://{host}:{port}")
    print(f"📚 API documentation: http://{host}:{port}{settings.docs_url}")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"🔄 Auto-reload: {reload}")
    
    # Initialize database if requested
    if args.init_db:
        print("🗄️  Initializing database...")
        try:
            initialize_database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            sys.exit(1)
    
    # Configure logging
    log_config = get_logging_config()
    
    try:
        # Run the server
        uvicorn.run(
            "server.main:app",
            host=host,
            port=port,
            reload=reload,
            log_config=log_config,
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()