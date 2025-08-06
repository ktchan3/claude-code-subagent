#!/usr/bin/env python3
"""
Debug script to test person creation and verify what data is being saved to the database.
This script will help identify where the first_name, last_name, title, and suffix fields are being lost.
"""

import sys
import os
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Test data that mimics what would come from the PersonForm
test_person_data = {
    'first_name': 'John',
    'last_name': 'Doe', 
    'title': 'Mr.',
    'suffix': 'Jr.',
    'email': f'john.doe.test.{datetime.now().strftime("%Y%m%d_%H%M%S")}@example.com',
    'phone': '+1-555-123-4567',
    'mobile': '+1-555-987-6543',
    'address': '123 Main St',
    'city': 'New York',
    'state': 'NY',
    'zip_code': '10001',
    'country': 'United States',
    'date_of_birth': '15-01-1990',
    'gender': 'Male',
    'marital_status': 'Single',
    'emergency_contact_name': 'Jane Doe',
    'emergency_contact_phone': '+1-555-111-2222',
    'notes': 'Test person for debugging',
    'tags': ['VIP', 'Test'],
    'status': 'Active'
}

def test_shared_api_client():
    """Test the shared API client PersonData model"""
    print("=== Testing Shared API Client PersonData ===")
    try:
        from shared.api_client import PersonData
        
        print(f"Input data: {json.dumps(test_person_data, indent=2)}")
        
        # Create PersonData object
        person_data = PersonData(**test_person_data)
        print(f"PersonData created successfully")
        print(f"PersonData dict: {json.dumps(person_data.dict(), indent=2)}")
        
        # Check specific fields
        print(f"first_name: {person_data.first_name}")
        print(f"last_name: {person_data.last_name}")
        print(f"title: {person_data.title}")
        print(f"suffix: {person_data.suffix}")
        
        return person_data
        
    except Exception as e:
        print(f"Error in shared API client test: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_server_schema():
    """Test the server-side schema validation"""
    print("\n=== Testing Server Schema ===")
    try:
        from server.api.schemas.person import PersonCreate
        
        # Test PersonCreate schema
        person_create = PersonCreate(**test_person_data)
        print(f"PersonCreate validation passed")
        print(f"PersonCreate dict: {json.dumps(person_create.dict(), indent=2)}")
        
        # Check specific fields
        print(f"first_name: {person_create.first_name}")
        print(f"last_name: {person_create.last_name}")
        print(f"title: {person_create.title}")
        print(f"suffix: {person_create.suffix}")
        
        return person_create
        
    except Exception as e:
        print(f"Error in server schema test: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_database_model():
    """Test database model creation"""
    print("\n=== Testing Database Model ===")
    try:
        from server.database.models import Person
        import json
        
        # Prepare data for database model
        db_data = test_person_data.copy()
        
        # Convert tags to JSON string as expected by the model
        if 'tags' in db_data and db_data['tags'] is not None:
            db_data['tags'] = json.dumps(db_data['tags'])
        
        # Convert date_of_birth if needed
        if 'date_of_birth' in db_data and db_data['date_of_birth']:
            from datetime import datetime
            try:
                # Parse dd-mm-yyyy format
                parsed_date = datetime.strptime(db_data['date_of_birth'], '%d-%m-%Y').date()
                db_data['date_of_birth'] = parsed_date
            except ValueError:
                print(f"Date parsing failed for: {db_data['date_of_birth']}")
        
        print(f"Database input data: {db_data}")
        
        # Create Person object (without actually saving to database)
        person = Person(**db_data)
        print(f"Person object created successfully")
        
        # Check specific fields
        print(f"first_name: {person.first_name}")
        print(f"last_name: {person.last_name}")
        print(f"title: {person.title}")
        print(f"suffix: {person.suffix}")
        print(f"full_name: {person.full_name}")
        
        return person
        
    except Exception as e:
        print(f"Error in database model test: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all tests to identify where the issue is"""
    print("Person Creation Debug Script")
    print("=" * 50)
    
    # Test each component in the pipeline
    person_data = test_shared_api_client()
    person_create = test_server_schema()
    person_model = test_database_model()
    
    print("\n=== Summary ===")
    if person_data:
        print("✓ Shared API client PersonData works correctly")
    else:
        print("✗ Issue found in shared API client PersonData")
        
    if person_create:
        print("✓ Server PersonCreate schema works correctly")
    else:
        print("✗ Issue found in server PersonCreate schema")
        
    if person_model:
        print("✓ Database Person model works correctly")
    else:
        print("✗ Issue found in database Person model")
    
    if person_data and person_create and person_model:
        print("\nAll components pass individual tests.")
        print("The issue might be in:")
        print("1. Database migration not applied")
        print("2. Network/API communication")
        print("3. Data processing in the actual API endpoint")
        print("4. UI form data collection")

if __name__ == "__main__":
    main()