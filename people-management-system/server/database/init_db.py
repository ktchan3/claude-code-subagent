#!/usr/bin/env python3
"""
Database initialization script for the people management system.

This script provides utilities for initializing, resetting, and managing
the database including schema creation, data seeding, and health checks.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from server.database.db import (
    initialize_database,
    reset_database,
    check_database_connection,
    get_database_info,
    health_check,
    vacuum_database,
    analyze_database,
    close_database_connections
)
from server.database.seeders import seed_database, clear_all_data, reset_and_seed_database
from server.database.config import get_database_settings, ensure_database_directory


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_database(with_seed: bool = False, force: bool = False) -> bool:
    """
    Initialize the database with schema and optionally seed data.
    
    Args:
        with_seed: Whether to seed the database with sample data
        force: Whether to force initialization even if database exists
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Initializing database...")
        
        # Ensure database directory exists
        ensure_database_directory()
        
        # Check if database already exists and is working
        if not force:
            try:
                if check_database_connection():
                    logger.info("Database already exists and is accessible")
                    
                    if with_seed:
                        logger.info("Adding seed data to existing database...")
                        results = seed_database()
                        logger.info(f"Seed data added: {results}")
                    
                    return True
            except Exception:
                # Database doesn't exist or is not accessible, continue with initialization
                pass
        
        # Initialize database schema
        initialize_database()
        logger.info("Database schema created successfully")
        
        # Seed with sample data if requested
        if with_seed:
            logger.info("Seeding database with sample data...")
            results = seed_database()
            logger.info(f"Sample data created: {results}")
        
        # Verify the database is working
        if check_database_connection():
            logger.info("Database initialization completed successfully")
            return True
        else:
            logger.error("Database initialization failed - connection check failed")
            return False
    
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def reset_database_with_options(with_seed: bool = False) -> bool:
    """
    Reset the database by dropping and recreating all tables.
    
    Args:
        with_seed: Whether to seed the database with sample data after reset
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.warning("Resetting database - this will delete all data!")
        
        # Reset database schema
        reset_database()
        logger.info("Database reset completed")
        
        # Seed with sample data if requested
        if with_seed:
            logger.info("Seeding database with sample data...")
            results = seed_database()
            logger.info(f"Sample data created: {results}")
        
        return True
    
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False


def show_database_status() -> bool:
    """
    Show comprehensive database status information.
    
    Returns:
        True if database is healthy, False otherwise
    """
    try:
        logger.info("Checking database status...")
        
        # Basic connection check
        is_connected = check_database_connection()
        print(f"Database Connection: {'✓ Connected' if is_connected else '✗ Not Connected'}")
        
        if not is_connected:
            print("Database is not accessible. Run 'init' command to initialize.")
            return False
        
        # Database information
        db_info = get_database_info()
        print(f"\nDatabase Information:")
        print(f"  Type: {db_info.get('database_type', 'Unknown')}")
        print(f"  Version: {db_info.get('database_version', 'Unknown')}")
        print(f"  URL: {db_info.get('database_url', 'Unknown')}")
        
        # Tables information
        tables = db_info.get('tables', [])
        print(f"  Tables: {len(tables)} ({', '.join(tables)})")
        
        # Connection pool information
        pool_size = db_info.get('connection_pool_size', 'N/A')
        pool_checked_out = db_info.get('connection_pool_checked_out', 'N/A')
        print(f"  Connection Pool: {pool_checked_out}/{pool_size}")
        
        # Health check
        health = health_check()
        print(f"\nHealth Check:")
        print(f"  Connected: {'✓' if health['database_connected'] else '✗'}")
        print(f"  Tables Exist: {'✓' if health['tables_exist'] else '✗'}")
        print(f"  Can Read: {'✓' if health['can_read'] else '✗'}")
        print(f"  Can Write: {'✓' if health['can_write'] else '✗'}")
        
        if health['errors']:
            print(f"  Errors: {len(health['errors'])}")
            for error in health['errors']:
                print(f"    - {error}")
        
        # Data counts
        try:
            from server.database.db import get_db_session
            from server.database.models import Person, Department, Position, Employment
            
            with get_db_session() as session:
                person_count = session.query(Person).count()
                dept_count = session.query(Department).count()
                position_count = session.query(Position).count()
                employment_count = session.query(Employment).count()
                active_employment_count = session.query(Employment).filter_by(is_active=True).count()
            
            print(f"\nData Summary:")
            print(f"  People: {person_count}")
            print(f"  Departments: {dept_count}")
            print(f"  Positions: {position_count}")
            print(f"  Employments: {employment_count} ({active_employment_count} active)")
        
        except Exception as e:
            print(f"  Could not retrieve data counts: {e}")
        
        is_healthy = all([
            health['database_connected'],
            health['tables_exist'],
            health['can_read'],
            health['can_write']
        ])
        
        print(f"\nOverall Status: {'✓ Healthy' if is_healthy else '✗ Issues Detected'}")
        return is_healthy
    
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return False


def seed_data() -> bool:
    """
    Seed the database with sample data.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Seeding database with sample data...")
        results = seed_database()
        logger.info(f"Sample data created successfully: {results}")
        return True
    
    except Exception as e:
        logger.error(f"Database seeding failed: {e}")
        return False


def clear_data() -> bool:
    """
    Clear all data from the database.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.warning("Clearing all database data...")
        clear_all_data()
        logger.info("All data cleared successfully")
        return True
    
    except Exception as e:
        logger.error(f"Data clearing failed: {e}")
        return False


def optimize_database() -> bool:
    """
    Optimize the database by running VACUUM and ANALYZE.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("Optimizing database...")
        
        # Run VACUUM to reclaim space and optimize storage
        vacuum_database()
        logger.info("Database VACUUM completed")
        
        # Run ANALYZE to update query planner statistics
        analyze_database()
        logger.info("Database ANALYZE completed")
        
        logger.info("Database optimization completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        return False


def main():
    """Main entry point for the database initialization script."""
    parser = argparse.ArgumentParser(
        description="People Management System Database Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init                 # Initialize database schema
  %(prog)s init --seed          # Initialize database with sample data
  %(prog)s reset --seed         # Reset database and add sample data
  %(prog)s status               # Show database status
  %(prog)s seed                 # Add sample data to existing database
  %(prog)s clear                # Clear all data from database
  %(prog)s optimize             # Optimize database performance
        """
    )
    
    parser.add_argument(
        'command',
        choices=['init', 'reset', 'status', 'seed', 'clear', 'optimize'],
        help='Database management command to execute'
    )
    
    parser.add_argument(
        '--seed',
        action='store_true',
        help='Include sample data when initializing or resetting database'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force operation even if database exists (for init command)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    # Show configuration
    settings = get_database_settings()
    logger.info(f"Using database: {settings.database_url}")
    
    try:
        success = False
        
        if args.command == 'init':
            success = init_database(with_seed=args.seed, force=args.force)
        
        elif args.command == 'reset':
            # Confirm destructive operation
            if not args.force:
                confirm = input("This will delete all data. Are you sure? (y/N): ")
                if confirm.lower() != 'y':
                    print("Operation cancelled.")
                    return 0
            
            success = reset_database_with_options(with_seed=args.seed)
        
        elif args.command == 'status':
            success = show_database_status()
        
        elif args.command == 'seed':
            success = seed_data()
        
        elif args.command == 'clear':
            # Confirm destructive operation
            if not args.force:
                confirm = input("This will delete all data. Are you sure? (y/N): ")
                if confirm.lower() != 'y':
                    print("Operation cancelled.")
                    return 0
            
            success = clear_data()
        
        elif args.command == 'optimize':
            success = optimize_database()
        
        return 0 if success else 1
    
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    finally:
        # Clean up database connections
        close_database_connections()


if __name__ == '__main__':
    sys.exit(main())