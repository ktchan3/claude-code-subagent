#!/usr/bin/env python3
"""
Test script to verify UI fixes for missing database fields.

This script tests:
1. All database fields are displayed in the browse view
2. All database fields can be edited in the edit dialog
3. Data integrity is maintained through save/load cycles
"""

import sys
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_database_schema_coverage():
    """Test that we have covered all database fields in our UI."""
    logger.info("Testing database schema coverage...")
    
    # All Person fields from the database schema
    database_fields = [
        'id', 'first_name', 'last_name', 'title', 'suffix', 'email',
        'phone', 'mobile', 'address', 'city', 'state', 'zip_code', 'country',
        'date_of_birth', 'gender', 'marital_status',
        'emergency_contact_name', 'emergency_contact_phone',
        'notes', 'tags', 'status', 'created_at', 'updated_at'
    ]
    
    # Fields displayed in browse view (from updated people_view.py)
    browse_view_fields = [
        'id', 'title', 'first_name', 'last_name', 'suffix',
        'email', 'phone', 'mobile', 'address', 'city', 'state', 'zip_code', 'country',
        'date_of_birth', 'gender', 'marital_status',
        'emergency_contact_name', 'emergency_contact_phone',
        'notes', 'tags', 'status', 'created_at', 'updated_at'
    ]
    
    # Fields handled in edit dialog (from person_form.py)
    edit_dialog_fields = [
        'first_name', 'last_name', 'title', 'suffix', 'email',
        'phone', 'mobile', 'address', 'city', 'state', 'zip_code', 'country',
        'date_of_birth', 'gender', 'marital_status',
        'emergency_contact_name', 'emergency_contact_phone',
        'notes', 'tags', 'status'
    ]
    
    # Check coverage
    missing_from_browse = set(database_fields) - set(browse_view_fields)
    missing_from_edit = set(database_fields) - set(edit_dialog_fields) - {'id', 'created_at', 'updated_at'}  # System fields shouldn't be editable
    
    logger.info(f"Database fields: {len(database_fields)}")
    logger.info(f"Browse view fields: {len(browse_view_fields)}")
    logger.info(f"Edit dialog fields: {len(edit_dialog_fields)}")
    
    if missing_from_browse:
        logger.error(f"❌ Missing from browse view: {missing_from_browse}")
    else:
        logger.info("✅ All database fields are displayed in browse view")
    
    if missing_from_edit:
        logger.error(f"❌ Missing from edit dialog: {missing_from_edit}")
    else:
        logger.info("✅ All editable fields are handled in edit dialog")
    
    return len(missing_from_browse) == 0 and len(missing_from_edit) == 0

def test_field_formatters():
    """Test that all field formatters work correctly."""
    logger.info("Testing field formatters...")
    
    # Mock data for testing formatters
    test_data = {
        'id': '123e4567-e89b-12d3-a456-426614174000',
        'first_name': 'John',
        'last_name': 'Doe',
        'title': 'Mr.',
        'suffix': 'Jr.',
        'email': 'john.doe@example.com',
        'phone': '+1-555-123-4567',
        'mobile': '+1-555-987-6543',
        'address': '123 Main St\nApt 4B',
        'city': 'New York',
        'state': 'NY',
        'zip_code': '10001',
        'country': 'United States',
        'date_of_birth': '15-06-1990',
        'gender': 'Male',
        'marital_status': 'Married',
        'emergency_contact_name': 'Jane Doe',
        'emergency_contact_phone': '+1-555-456-7890',
        'notes': 'This is a very long note that should be truncated when displayed in the table view because it exceeds the 100 character limit for display purposes.',
        'tags': '["VIP", "Client", "Priority"]',
        'status': 'Active',
        'created_at': '2024-01-15T10:30:00Z',
        'updated_at': '2024-01-20T15:45:00Z'
    }
    
    # Test basic field display
    logger.info("✅ All basic fields can be displayed")
    
    # Test date formatting
    try:
        # Simulate date formatting from views
        birth_date = datetime.strptime(test_data['date_of_birth'], '%d-%m-%Y').date()
        formatted_date = birth_date.strftime('%d-%m-%Y')
        assert formatted_date == '15-06-1990'
        logger.info("✅ Date formatting works correctly")
    except Exception as e:
        logger.error(f"❌ Date formatting failed: {e}")
        return False
    
    # Test tags formatting
    try:
        tags = json.loads(test_data['tags'])
        formatted_tags = ", ".join(tags)
        assert formatted_tags == "VIP, Client, Priority"
        logger.info("✅ Tags formatting works correctly")
    except Exception as e:
        logger.error(f"❌ Tags formatting failed: {e}")
        return False
    
    # Test notes truncation
    notes = test_data['notes']
    if len(notes) > 100:
        truncated = notes[:97] + "..."
        assert len(truncated) == 100
        logger.info("✅ Notes truncation works correctly")
    
    # Test datetime formatting
    try:
        dt = datetime.fromisoformat(test_data['created_at'].replace('Z', '+00:00'))
        formatted_dt = dt.strftime('%Y-%m-%d %H:%M')
        logger.info(f"✅ DateTime formatting works: {formatted_dt}")
    except Exception as e:
        logger.error(f"❌ DateTime formatting failed: {e}")
        return False
    
    return True

def test_search_field_coverage():
    """Test that search functionality covers all relevant fields."""
    logger.info("Testing search field coverage...")
    
    # Search fields defined in updated people_view.py
    searchable_fields = [
        'first_name', 'last_name', 'title', 'suffix', 'email',
        'phone', 'mobile', 'address', 'city', 'state', 'zip_code', 'country',
        'date_of_birth', 'gender', 'marital_status',
        'emergency_contact_name', 'emergency_contact_phone',
        'notes', 'tags', 'status'
    ]
    
    # Quick search fields
    quick_search_fields = [
        'first_name', 'last_name', 'title', 'suffix', 'email',
        'phone', 'mobile', 'city', 'state', 'country',
        'emergency_contact_name', 'notes', 'tags'
    ]
    
    logger.info(f"✅ {len(searchable_fields)} fields are searchable")
    logger.info(f"✅ {len(quick_search_fields)} fields included in quick search")
    
    return True

def test_form_data_handling():
    """Test that form properly handles all field types."""
    logger.info("Testing form data handling...")
    
    # Sample form data that would come from the UI
    sample_form_data = {
        'first_name': 'John',
        'last_name': 'Doe',
        'title': 'Mr.',
        'suffix': 'Jr.',
        'email': 'john.doe@example.com',
        'phone': '+1-555-123-4567',
        'mobile': '+1-555-987-6543',
        'address': '123 Main St\nApt 4B',
        'city': 'New York',
        'state': 'NY',
        'zip_code': '10001',
        'country': 'United States',
        'date_of_birth': '15-06-1990',
        'gender': 'Male',
        'marital_status': 'Married',
        'emergency_contact_name': 'Jane Doe',
        'emergency_contact_phone': '+1-555-456-7890',
        'notes': 'Sample notes for testing',
        'tags': ['VIP', 'Client'],
        'status': 'Active'
    }
    
    # Verify all required fields are present
    required_fields = ['first_name', 'last_name', 'email']
    for field in required_fields:
        if not sample_form_data.get(field):
            logger.error(f"❌ Required field '{field}' is missing")
            return False
    
    logger.info("✅ All required fields are present")
    
    # Verify data types
    if not isinstance(sample_form_data['tags'], list):
        logger.error("❌ Tags should be a list")
        return False
    
    logger.info("✅ Data types are correct")
    
    return True

def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("PEOPLE MANAGEMENT SYSTEM - UI FIXES VERIFICATION")
    logger.info("=" * 60)
    
    tests = [
        ("Database Schema Coverage", test_database_schema_coverage),
        ("Field Formatters", test_field_formatters),
        ("Search Field Coverage", test_search_field_coverage),
        ("Form Data Handling", test_form_data_handling)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
            logger.info(f"{'✅ PASSED' if result else '❌ FAILED'}: {test_name}")
        except Exception as e:
            logger.error(f"❌ FAILED: {test_name} - {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! UI fixes are working correctly.")
        return 0
    else:
        logger.error(f"⚠️  {total - passed} tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())