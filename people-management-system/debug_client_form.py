#!/usr/bin/env python3
"""
Debug script to test the actual client form data handling.
"""

import json

def simulate_form_data():
    """Simulate what the form sends when title/suffix are empty."""
    
    print("=" * 60)
    print("Testing Form Data Handling")
    print("=" * 60)
    
    # Case 1: When title and suffix are empty (combo box returns empty string)
    form_data_empty = {
        'first_name': 'John',
        'last_name': 'Smith',
        'email': 'john.smith@test.com',
        'phone': None,
        'mobile': None,
        'address': None,
        'city': None,
        'state': None,
        'zip_code': None,
        'country': None,
        'date_of_birth': None,
        'gender': None,
        'marital_status': None,
        'emergency_contact_name': None,
        'emergency_contact_phone': None,
        'notes': None,
        'tags': [],
        'status': 'Active',
        'title': None,  # Empty combo box returns None
        'suffix': None  # Empty text returns None
    }
    
    # Case 2: When title and suffix have values
    form_data_filled = {
        'first_name': 'Jane',
        'last_name': 'Doe',
        'email': 'jane.doe@test.com',
        'phone': None,
        'mobile': None,
        'address': None,
        'city': None,
        'state': None,
        'zip_code': None,
        'country': None,
        'date_of_birth': None,
        'gender': None,
        'marital_status': None,
        'emergency_contact_name': None,
        'emergency_contact_phone': None,
        'notes': None,
        'tags': [],
        'status': 'Active',
        'title': 'Dr',  # Selected from combo
        'suffix': 'PhD'  # Typed in text field
    }
    
    print("\n📋 Case 1: Empty Title and Suffix")
    print("-" * 40)
    
    # Remove None values as the API client might do
    clean_data_1 = {k: v for k, v in form_data_empty.items() if v is not None}
    
    print("Form sends:")
    print(f"  first_name: {form_data_empty.get('first_name')}")
    print(f"  last_name: {form_data_empty.get('last_name')}")
    print(f"  title: {form_data_empty.get('title')} (None)")
    print(f"  suffix: {form_data_empty.get('suffix')} (None)")
    
    print("\nAfter removing None values:")
    print(f"  first_name: {clean_data_1.get('first_name')}")
    print(f"  last_name: {clean_data_1.get('last_name')}")
    print(f"  title: {clean_data_1.get('title', 'KEY NOT SENT')}")
    print(f"  suffix: {clean_data_1.get('suffix', 'KEY NOT SENT')}")
    
    print("\n📋 Case 2: Filled Title and Suffix")
    print("-" * 40)
    
    # Remove None values
    clean_data_2 = {k: v for k, v in form_data_filled.items() if v is not None}
    
    print("Form sends:")
    print(f"  first_name: {form_data_filled.get('first_name')}")
    print(f"  last_name: {form_data_filled.get('last_name')}")
    print(f"  title: {form_data_filled.get('title')}")
    print(f"  suffix: {form_data_filled.get('suffix')}")
    
    print("\nAfter removing None values:")
    print(f"  first_name: {clean_data_2.get('first_name')}")
    print(f"  last_name: {clean_data_2.get('last_name')}")
    print(f"  title: {clean_data_2.get('title')}")
    print(f"  suffix: {clean_data_2.get('suffix')}")
    
    print("\n" + "=" * 60)
    print("💡 Analysis:")
    print("=" * 60)
    
    print("\nThe issue might be:")
    print("1. When title/suffix are empty, they're set to None")
    print("2. None values might be removed before sending to API")
    print("3. API might not handle missing optional fields correctly")
    print("\nFirst name and last name should always work because they're")
    print("never None (required fields).")
    
    print("\nBut if the UI is not showing saved values, it might be:")
    print("1. The form is not properly loading saved data")
    print("2. The API response is not including these fields")
    print("3. The form's set_form_data is not being called correctly")


if __name__ == "__main__":
    simulate_form_data()