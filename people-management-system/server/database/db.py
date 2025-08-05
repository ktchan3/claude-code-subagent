"""
Database initialization and connection management for the people management system.

This module provides database engine creation, session management, and
database initialization utilities with proper connection pooling for SQLite.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional
from pathlib import Path

from sqlalchemy import create_engine, event, Engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool

from .config import get_database_url, get_engine_kwargs, ensure_database_directory
from .models import Base


# Configure logging
logger = logging.getLogger(__name__)

# Global database components
engine: Optional[Engine] = None
SessionLocal: Optional[sessionmaker] = None
ScopedSession: Optional[scoped_session] = None


def configure_sqlite_pragmas(dbapi_connection, connection_record):
    """
    Configure SQLite-specific pragmas for optimal performance and reliability.
    
    This function is called for each new SQLite connection to set important
    database configuration options.
    """
    with dbapi_connection.cursor() as cursor:
        # Enable foreign key constraints (disabled by default in SQLite)
        cursor.execute("PRAGMA foreign_keys=ON")
        
        # Use WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Optimize for faster writes at the cost of some durability
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Increase cache size for better performance (negative value = KB)
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        
        # Optimize for faster queries
        cursor.execute("PRAGMA temp_store=MEMORY")
        
        # Enable query planner optimizations
        cursor.execute("PRAGMA optimize")


def create_database_engine(database_url: str = None, testing: bool = False) -> Engine:
    """
    Create and configure the database engine.
    
    Args:
        database_url: Database connection URL (optional)
        testing: Whether this is for testing
        
    Returns:
        Configured SQLAlchemy engine
    """
    if database_url is None:
        database_url = get_database_url(testing=testing)
    
    # Ensure database directory exists
    if not testing:
        ensure_database_directory()
    
    # Get engine configuration
    engine_kwargs = get_engine_kwargs(testing=testing)
    
    # Create the engine
    db_engine = create_engine(database_url, **engine_kwargs)
    
    # Configure SQLite-specific settings
    if database_url.startswith("sqlite"):
        event.listen(db_engine, "connect", configure_sqlite_pragmas)
    
    logger.info(f"Database engine created for URL: {database_url}")
    return db_engine


def initialize_database(database_url: str = None, testing: bool = False) -> None:
    """
    Initialize the database with tables and constraints.
    
    Args:
        database_url: Database connection URL (optional)
        testing: Whether this is for testing
    """
    global engine, SessionLocal, ScopedSession
    
    # Create engine if not exists
    if engine is None or testing:
        engine = create_database_engine(database_url, testing=testing)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
    
    # Create scoped session for thread-safe access
    ScopedSession = scoped_session(SessionLocal)
    
    logger.info("Database initialized successfully")


def get_engine() -> Engine:
    """
    Get the global database engine.
    
    Returns:
        SQLAlchemy engine instance
        
    Raises:
        RuntimeError: If database hasn't been initialized
    """
    if engine is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return engine


def get_session_factory() -> sessionmaker:
    """
    Get the session factory.
    
    Returns:
        SQLAlchemy session factory
        
    Raises:
        RuntimeError: If database hasn't been initialized
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return SessionLocal


def get_scoped_session() -> scoped_session:
    """
    Get the scoped session for thread-safe database access.
    
    Returns:
        Scoped session instance
        
    Raises:
        RuntimeError: If database hasn't been initialized
    """
    if ScopedSession is None:
        raise RuntimeError("Database not initialized. Call initialize_database() first.")
    return ScopedSession


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Provides automatic session management with proper cleanup and error handling.
    
    Yields:
        Database session
        
    Example:
        with get_db_session() as session:
            person = session.query(Person).first()
            # Session is automatically closed
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def create_db_session() -> Session:
    """
    Create a new database session.
    
    Note: Caller is responsible for closing the session.
    Consider using get_db_session() context manager instead.
    
    Returns:
        New database session
    """
    session_factory = get_session_factory()
    return session_factory()


def close_database_connections() -> None:
    """
    Close all database connections and clean up resources.
    
    This should be called during application shutdown.
    """
    global engine, SessionLocal, ScopedSession
    
    if ScopedSession:
        ScopedSession.remove()
        ScopedSession = None
    
    if engine:
        engine.dispose()
        engine = None
    
    SessionLocal = None
    
    logger.info("Database connections closed")


def reset_database(database_url: str = None, testing: bool = False) -> None:
    """
    Reset the database by dropping and recreating all tables.
    
    WARNING: This will delete all data in the database!
    
    Args:
        database_url: Database connection URL (optional)
        testing: Whether this is for testing
    """
    global engine
    
    if database_url is None:
        database_url = get_database_url(testing=testing)
    
    # Close existing connections
    close_database_connections()
    
    # Create new engine
    engine = create_database_engine(database_url, testing=testing)
    
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")
    
    # Reinitialize database
    initialize_database(database_url, testing=testing)
    logger.info("Database reset completed")


def check_database_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        True if connection is working, False otherwise
    """
    try:
        with get_db_session() as session:
            # Execute a simple query
            session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get information about the current database.
    
    Returns:
        Dictionary with database information
    """
    try:
        db_engine = get_engine()
        
        with get_db_session() as session:
            # Get database version and info
            if db_engine.url.drivername == "sqlite":
                result = session.execute("SELECT sqlite_version()").scalar()
                db_version = result
                db_type = "SQLite"
            else:
                db_version = "Unknown"
                db_type = db_engine.url.drivername
            
            # Get table information
            from .models import get_all_models
            tables = [model.__tablename__ for model in get_all_models()]
            
            return {
                "database_type": db_type,
                "database_version": db_version,
                "database_url": str(db_engine.url),
                "tables": tables,
                "connection_pool_size": getattr(db_engine.pool, 'size', 'N/A'),
                "connection_pool_checked_out": getattr(db_engine.pool, 'checkedout', 'N/A'),
            }
    
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"error": str(e)}


def vacuum_database() -> None:
    """
    Run VACUUM command on SQLite database to optimize storage.
    
    This should be run periodically to reclaim unused space and optimize
    the database file structure.
    """
    try:
        db_engine = get_engine()
        
        if db_engine.url.drivername == "sqlite":
            with db_engine.connect() as connection:
                connection.execute("VACUUM")
            logger.info("Database vacuum completed")
        else:
            logger.warning("VACUUM command only supported for SQLite databases")
    
    except Exception as e:
        logger.error(f"Database vacuum failed: {e}")
        raise


def analyze_database() -> None:
    """
    Run ANALYZE command on SQLite database to update query planner statistics.
    
    This should be run periodically to ensure optimal query performance.
    """
    try:
        db_engine = get_engine()
        
        if db_engine.url.drivername == "sqlite":
            with db_engine.connect() as connection:
                connection.execute("ANALYZE")
            logger.info("Database analysis completed")
        else:
            logger.warning("ANALYZE command only supported for SQLite databases")
    
    except Exception as e:
        logger.error(f"Database analysis failed: {e}")
        raise


# Utility functions for FastAPI dependency injection
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting database sessions.
    
    This function is designed to be used as a FastAPI dependency.
    
    Yields:
        Database session
    """
    with get_db_session() as session:
        yield session


# Database health check functions
def health_check() -> dict:
    """
    Perform a comprehensive database health check.
    
    Returns:
        Dictionary with health check results
    """
    health_status = {
        "database_connected": False,
        "tables_exist": False,
        "can_read": False,
        "can_write": False,
        "errors": []
    }
    
    try:
        # Check connection
        health_status["database_connected"] = check_database_connection()
        
        if health_status["database_connected"]:
            with get_db_session() as session:
                # Check if tables exist
                from .models import Person
                
                try:
                    session.query(Person).first()
                    health_status["tables_exist"] = True
                    health_status["can_read"] = True
                except Exception as e:
                    health_status["errors"].append(f"Read test failed: {e}")
                
                # Test write capability (rollback to avoid side effects)
                try:
                    person = Person(
                        first_name="Test",
                        last_name="User",
                        email="test@example.com"
                    )
                    session.add(person)
                    session.flush()  # Test constraints without committing
                    session.rollback()  # Rollback the test record
                    health_status["can_write"] = True
                except Exception as e:
                    health_status["errors"].append(f"Write test failed: {e}")
    
    except Exception as e:
        health_status["errors"].append(f"Health check failed: {e}")
    
    return health_status


# Initialize logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)