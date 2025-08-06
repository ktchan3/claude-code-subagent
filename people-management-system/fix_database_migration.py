#!/usr/bin/env python3
"""
Fix script to ensure database migration is applied and verify the database schema.
This script will check the current database schema and apply migrations if needed.
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n{description}")
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="server")
        if result.returncode == 0:
            print(f"✓ Success: {description}")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
        else:
            print(f"✗ Failed: {description}")
            print(f"Error: {result.stderr.strip()}")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"✗ Exception running command: {e}")
        return False, "", str(e)

def check_alembic_installation():
    """Check if alembic is available"""
    success, stdout, stderr = run_command("alembic --version", "Checking Alembic installation")
    return success

def check_current_migration_status():
    """Check current migration status"""
    success, stdout, stderr = run_command("alembic current", "Checking current migration status")
    return success, stdout

def show_migration_history():
    """Show migration history"""
    success, stdout, stderr = run_command("alembic history --verbose", "Showing migration history")
    return success, stdout

def apply_migrations():
    """Apply all pending migrations"""
    success, stdout, stderr = run_command("alembic upgrade head", "Applying all migrations")
    return success, stdout

def check_database_schema():
    """Check if the database has the required columns"""
    print("\n=== Checking Database Schema ===")
    
    # Try to check the database schema using Python
    check_script = """
import sys
sys.path.append('.')
try:
    from sqlalchemy import create_engine, inspect
    
    # Try different database locations
    db_paths = ['people_management.db', '../people_management.db', 'server/people_management.db']
    
    for db_path in db_paths:
        try:
            engine = create_engine(f'sqlite:///{db_path}')
            inspector = inspect(engine)
            
            if 'people' in inspector.get_table_names():
                columns = inspector.get_columns('people')
                column_names = [col['name'] for col in columns]
                
                print(f"Database found at: {db_path}")
                print(f"People table columns: {column_names}")
                
                # Check for the problematic fields
                required_fields = ['first_name', 'last_name', 'title', 'suffix']
                missing_fields = [field for field in required_fields if field not in column_names]
                
                if missing_fields:
                    print(f"❌ MISSING FIELDS: {missing_fields}")
                    print("This confirms the migration hasn't been applied!")
                else:
                    print("✅ All required fields are present in the database")
                
                break
        except Exception as e:
            continue
    else:
        print("Could not find or access the database")
        
except ImportError as e:
    print(f"Cannot check database schema: {e}")
    print("SQLAlchemy not available")
"""
    
    success, stdout, stderr = run_command(f'python3 -c "{check_script}"', "Checking database schema")
    return success

def main():
    """Main fix function"""
    print("Database Migration Fix Script")
    print("=" * 50)
    
    # Change to server directory
    if not os.path.exists("server"):
        print("❌ Server directory not found. Please run this from the project root.")
        return False
    
    print("Checking server directory structure...")
    server_path = Path("server")
    migration_path = server_path / "database" / "migrations"
    
    if not migration_path.exists():
        print(f"❌ Migration directory not found: {migration_path}")
        return False
    
    print(f"✓ Migration directory found: {migration_path}")
    
    # Step 1: Check if Alembic is available
    if not check_alembic_installation():
        print("\n❌ Alembic is not installed or not available")
        print("Try installing it with: pip install alembic")
        print("Or if using UV: uv pip install alembic")
        return False
    
    # Step 2: Check current migration status
    print("\n" + "=" * 30)
    success, current_output = check_current_migration_status()
    if success:
        print(f"Current migration: {current_output.strip()}")
    
    # Step 3: Show migration history
    success, history_output = show_migration_history()
    
    # Step 4: Check database schema before migration
    check_database_schema()
    
    # Step 5: Apply migrations
    print("\n" + "=" * 30)
    print("Applying migrations...")
    success, migration_output = apply_migrations()
    
    if success:
        print("✅ Migrations applied successfully!")
        print(f"Output: {migration_output}")
        
        # Step 6: Check database schema after migration
        print("\n" + "=" * 30)
        print("Verifying database schema after migration...")
        check_database_schema()
        
        print("\n🎉 Fix completed! The database should now have all required fields.")
        print("\nNext steps:")
        print("1. Restart your server application")
        print("2. Test creating a new person through the UI")
        print("3. Verify that first_name, last_name, title, and suffix are saved")
        
        return True
    else:
        print("❌ Migration failed!")
        print("Please check the error messages above and:")
        print("1. Ensure you're in the correct directory")
        print("2. Check that alembic.ini exists in the server directory")
        print("3. Verify database permissions")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)