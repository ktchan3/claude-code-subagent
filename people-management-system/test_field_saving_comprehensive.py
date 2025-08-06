#!/usr/bin/env python3
"""
Comprehensive Test Script for Person Field Saving Issues

This script tests the entire data flow from form -> API client -> server -> database
to identify exactly where the title and suffix fields are being lost.
"""

import sys
import os
import json
import asyncio
import sqlite3
from datetime import datetime, date
from typing import Dict, Any
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "client"))
sys.path.insert(0, str(project_root / "server"))
sys.path.insert(0, str(project_root / "shared"))

print("=== Person Field Saving Comprehensive Test ===")
print(f"Project root: {project_root}")
print(f"Current working directory: {os.getcwd()}")

# Test data with all fields including the problematic ones
TEST_PERSON_DATA = {
    "first_name": "John",
    "last_name": "Doe",
    "title": "Dr.",
    "suffix": "Jr.",
    "email": "john.doe.test@example.com",
    "phone": "+1-555-123-4567",
    "mobile": "+1-555-987-6543",
    "date_of_birth": "15-01-1990",
    "gender": "Male",
    "marital_status": "Single",
    "address": "123 Test Street",
    "city": "Test City",
    "state": "TX",
    "zip_code": "12345",
    "country": "United States",
    "emergency_contact_name": "Jane Doe",
    "emergency_contact_phone": "+1-555-111-2222",
    "notes": "Test person for field saving verification",
    "tags": ["test", "debug"],
    "status": "Active"
}


def test_form_data_collection():
    """Test 1: Verify client form data collection includes all fields."""
    print("\n1. Testing Client Form Data Collection")
    print("-" * 50)
    
    try:
        from client.ui.widgets.person_form import PersonForm
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QDate
        
        # Create QApplication if it doesn't exist
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # Create form
        form = PersonForm()
        
        # Set test data
        form.set_form_data(TEST_PERSON_DATA)
        
        # Get form data back
        collected_data = form.get_form_data()
        
        print("✓ Form created and data set successfully")
        print(f"✓ Form collected data keys: {sorted(collected_data.keys())}")
        
        # Check critical fields
        critical_fields = ['first_name', 'last_name', 'title', 'suffix', 'email']
        missing_fields = []
        
        for field in critical_fields:
            if field not in collected_data or collected_data[field] is None:
                missing_fields.append(field)
            else:
                print(f"✓ {field}: '{collected_data[field]}'")
        
        if missing_fields:
            print(f"✗ MISSING FIELDS in form data: {missing_fields}")
            return False, collected_data
        else:
            print("✓ All critical fields present in form data")
            return True, collected_data
            
    except Exception as e:
        print(f"✗ ERROR in form data collection test: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def test_shared_api_client_model():
    """Test 2: Verify shared API client PersonData model handles all fields."""
    print("\n2. Testing Shared API Client PersonData Model")
    print("-" * 50)
    
    try:
        from shared.api_client import PersonData
        
        # Create PersonData model with test data
        person_data = PersonData(**TEST_PERSON_DATA)
        person_dict = person_data.dict()
        
        print("✓ PersonData model created successfully")
        print(f"✓ PersonData fields: {sorted(person_dict.keys())}")
        
        # Check critical fields
        critical_fields = ['first_name', 'last_name', 'title', 'suffix', 'email']
        missing_fields = []
        
        for field in critical_fields:
            if field not in person_dict or person_dict[field] is None:
                missing_fields.append(field)
            else:
                print(f"✓ {field}: '{person_dict[field]}'")
        
        if missing_fields:
            print(f"✗ MISSING FIELDS in PersonData model: {missing_fields}")
            return False, person_dict
        else:
            print("✓ All critical fields present in PersonData model")
            return True, person_dict
            
    except Exception as e:
        print(f"✗ ERROR in PersonData model test: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def test_server_schema_validation():
    """Test 3: Verify server-side schema validation accepts all fields."""
    print("\n3. Testing Server Schema Validation")
    print("-" * 50)
    
    try:
        from server.api.schemas.person import PersonCreate, PersonResponse
        
        # Test PersonCreate schema
        person_create = PersonCreate(**TEST_PERSON_DATA)
        create_dict = person_create.dict()
        
        print("✓ PersonCreate schema validation successful")
        print(f"✓ PersonCreate fields: {sorted(create_dict.keys())}")
        
        # Check critical fields
        critical_fields = ['first_name', 'last_name', 'title', 'suffix', 'email']
        missing_fields = []
        
        for field in critical_fields:
            if field not in create_dict:
                missing_fields.append(field)
            else:
                print(f"✓ {field}: '{create_dict[field]}'")
        
        if missing_fields:
            print(f"✗ MISSING FIELDS in PersonCreate schema: {missing_fields}")
            return False, create_dict
        else:
            print("✓ All critical fields present in PersonCreate schema")
            return True, create_dict
            
    except Exception as e:
        print(f"✗ ERROR in server schema validation test: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def test_database_model():
    """Test 4: Verify database model has all required columns."""
    print("\n4. Testing Database Model")
    print("-" * 50)
    
    try:
        from server.database.models import Person
        import inspect
        
        # Get all Person model columns
        columns = [col.name for col in Person.__table__.columns]
        print(f"✓ Person model columns: {sorted(columns)}")
        
        # Check critical columns
        critical_columns = ['first_name', 'last_name', 'title', 'suffix', 'email']
        missing_columns = []
        
        for col in critical_columns:
            if col not in columns:
                missing_columns.append(col)
            else:
                print(f"✓ Column '{col}' exists")
        
        if missing_columns:
            print(f"✗ MISSING COLUMNS in Person model: {missing_columns}")
            return False, columns
        else:
            print("✓ All critical columns present in Person model")
            return True, columns
            
    except Exception as e:
        print(f"✗ ERROR in database model test: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def test_database_direct_insertion():
    """Test 5: Test direct database insertion to verify columns work."""
    print("\n5. Testing Direct Database Insertion")
    print("-" * 50)
    
    db_path = project_root / "people_management.db"
    
    try:
        # Connect to database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # First, let's check what columns actually exist in the database
        cursor.execute("PRAGMA table_info(people)")
        actual_columns = [row[1] for row in cursor.fetchall()]
        print(f"✓ Database table 'people' columns: {sorted(actual_columns)}")
        
        # Check critical columns
        critical_columns = ['first_name', 'last_name', 'title', 'suffix', 'email']
        missing_columns = []
        
        for col in critical_columns:
            if col not in actual_columns:
                missing_columns.append(col)
            else:
                print(f"✓ Database column '{col}' exists")
        
        if missing_columns:
            print(f"✗ MISSING COLUMNS in database: {missing_columns}")
            conn.close()
            return False, actual_columns
        
        # Test insert with all fields
        test_data = TEST_PERSON_DATA.copy()
        
        # Convert date format for database
        if test_data.get('date_of_birth'):
            try:
                dob = datetime.strptime(test_data['date_of_birth'], '%d-%m-%Y').date()
                test_data['date_of_birth'] = dob.isoformat()
            except:
                test_data['date_of_birth'] = None
        
        # Convert tags to JSON
        if test_data.get('tags'):
            test_data['tags'] = json.dumps(test_data['tags'])
        
        # Delete any existing test record
        cursor.execute("DELETE FROM people WHERE email = ?", (test_data['email'],))
        
        # Insert new record
        columns_to_insert = [col for col in test_data.keys() if col in actual_columns]
        placeholders = ', '.join(['?' for _ in columns_to_insert])
        column_names = ', '.join(columns_to_insert)
        values = [test_data[col] for col in columns_to_insert]
        
        insert_sql = f"INSERT INTO people ({column_names}) VALUES ({placeholders})"
        cursor.execute(insert_sql, values)
        
        # Verify insertion
        cursor.execute(
            "SELECT first_name, last_name, title, suffix, email FROM people WHERE email = ?",
            (test_data['email'],)
        )
        result = cursor.fetchone()
        
        if result:
            print(f"✓ Database insertion successful")
            print(f"✓ Retrieved data: {result}")
            
            # Check if title and suffix were saved
            first_name, last_name, title, suffix, email = result
            
            issues = []
            if title != TEST_PERSON_DATA['title']:
                issues.append(f"title: expected '{TEST_PERSON_DATA['title']}', got '{title}'")
            if suffix != TEST_PERSON_DATA['suffix']:
                issues.append(f"suffix: expected '{TEST_PERSON_DATA['suffix']}', got '{suffix}'")
            
            if issues:
                print(f"✗ FIELD SAVING ISSUES: {', '.join(issues)}")
                conn.commit()
                conn.close()
                return False, result
            else:
                print("✓ All critical fields saved correctly to database")
        else:
            print("✗ No record found after insertion")
            conn.close()
            return False, None
        
        conn.commit()
        conn.close()
        return True, result
        
    except Exception as e:
        print(f"✗ ERROR in database insertion test: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return False, None


def test_api_endpoint_direct():
    """Test 6: Test API endpoint directly (if server is running)."""
    print("\n6. Testing API Endpoint (if server running)")
    print("-" * 50)
    
    try:
        import httpx
        
        # Test if server is running
        try:
            response = httpx.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code != 200:
                print("✗ Server not running or not healthy, skipping API test")
                return False, None
        except:
            print("✗ Server not running, skipping API test")
            return False, None
        
        # Test creating a person via API
        api_data = TEST_PERSON_DATA.copy()
        api_data['email'] = 'john.doe.api.test@example.com'  # Different email for API test
        
        response = httpx.post(
            "http://localhost:8000/api/people/",
            json=api_data,
            timeout=10.0,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            result_data = response.json()
            print("✓ API person creation successful")
            print(f"✓ API response data keys: {sorted(result_data.keys())}")
            
            # Check if title and suffix are in response
            if 'title' in result_data and result_data['title'] == TEST_PERSON_DATA['title']:
                print(f"✓ title field correct: '{result_data['title']}'")
            else:
                print(f"✗ title field issue: expected '{TEST_PERSON_DATA['title']}', got '{result_data.get('title')}'")
                
            if 'suffix' in result_data and result_data['suffix'] == TEST_PERSON_DATA['suffix']:
                print(f"✓ suffix field correct: '{result_data['suffix']}'")
            else:
                print(f"✗ suffix field issue: expected '{TEST_PERSON_DATA['suffix']}', got '{result_data.get('suffix')}'")
            
            return True, result_data
        else:
            print(f"✗ API request failed: {response.status_code} - {response.text}")
            return False, None
            
    except Exception as e:
        print(f"✗ ERROR in API endpoint test: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def main():
    """Run all tests to identify the root cause."""
    print("Starting comprehensive field saving tests...")
    
    results = {}
    
    # Run all tests
    test_functions = [
        ("Client Form Data Collection", test_form_data_collection),
        ("Shared API Client Model", test_shared_api_client_model),
        ("Server Schema Validation", test_server_schema_validation),
        ("Database Model", test_database_model),
        ("Database Direct Insertion", test_database_direct_insertion),
        ("API Endpoint Direct", test_api_endpoint_direct),
    ]
    
    for test_name, test_func in test_functions:
        try:
            success, data = test_func()
            results[test_name] = {"success": success, "data": data}
        except Exception as e:
            print(f"✗ Test '{test_name}' failed with exception: {e}")
            results[test_name] = {"success": False, "data": None}
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    failed_tests = []
    for test_name, result in results.items():
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        print(f"{test_name}: {status}")
        if not result["success"]:
            failed_tests.append(test_name)
    
    if failed_tests:
        print(f"\n🔍 FAILED TESTS: {', '.join(failed_tests)}")
        print("\nThese failed tests indicate where the issue lies in the data flow.")
    else:
        print("\n✅ ALL TESTS PASSED - No issues found in the data flow!")
    
    return results


if __name__ == "__main__":
    results = main()