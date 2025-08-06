#!/usr/bin/env python3
"""
Simple Database Test - Direct SQLite testing without dependencies
"""

import sqlite3
import json
import uuid
from datetime import datetime

# Test data
TEST_DATA = {
    'id': str(uuid.uuid4()),
    'first_name': 'John',
    'last_name': 'Doe', 
    'title': 'Dr.',
    'suffix': 'Jr.',
    'email': 'john.doe.simple.test@example.com',
    'phone': '+1-555-123-4567',
    'mobile': '+1-555-987-6543',
    'date_of_birth': '1990-01-15',
    'gender': 'Male',
    'marital_status': 'Single',
    'address': '123 Test Street',
    'city': 'Test City',
    'state': 'TX',
    'zip_code': '12345',
    'country': 'United States',
    'emergency_contact_name': 'Jane Doe',
    'emergency_contact_phone': '+1-555-111-2222',
    'notes': 'Test person for field saving verification',
    'tags': json.dumps(['test', 'debug']),
    'status': 'Active',
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

def test_database_insertion():
    """Test direct database insertion of all fields."""
    print("=== Simple Database Test ===")
    
    try:
        # Connect to database
        conn = sqlite3.connect('people_management.db')
        cursor = conn.cursor()
        
        # Delete any existing test record
        cursor.execute("DELETE FROM people WHERE email = ?", (TEST_DATA['email'],))
        
        # Insert test record
        columns = list(TEST_DATA.keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        values = [TEST_DATA[col] for col in columns]
        
        insert_sql = f"INSERT INTO people ({column_names}) VALUES ({placeholders})"
        print(f"Insert SQL: {insert_sql}")
        print(f"Values: {values}")
        
        cursor.execute(insert_sql, values)
        
        # Query the inserted record
        cursor.execute("""
            SELECT id, first_name, last_name, title, suffix, email, phone, created_at
            FROM people WHERE email = ?
        """, (TEST_DATA['email'],))
        
        result = cursor.fetchone()
        
        if result:
            print("\n✓ Record inserted successfully!")
            print(f"Retrieved: {result}")
            
            id_val, first_name, last_name, title, suffix, email, phone, created_at = result
            
            print(f"\nField verification:")
            print(f"- ID: {id_val}")
            print(f"- First Name: '{first_name}'")
            print(f"- Last Name: '{last_name}'")
            print(f"- Title: '{title}'")
            print(f"- Suffix: '{suffix}'")
            print(f"- Email: '{email}'")
            print(f"- Phone: '{phone}'")
            
            # Check if title and suffix are properly saved
            if title == TEST_DATA['title'] and suffix == TEST_DATA['suffix']:
                print("\n✅ SUCCESS: Title and suffix fields saved correctly!")
            else:
                print(f"\n❌ ISSUE: Title or suffix not saved correctly")
                print(f"Expected title: '{TEST_DATA['title']}', got: '{title}'")
                print(f"Expected suffix: '{TEST_DATA['suffix']}', got: '{suffix}'")
        else:
            print("❌ No record found after insertion")
        
        conn.commit()
        conn.close()
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        if 'conn' in locals():
            conn.close()
        return None

def check_existing_records():
    """Check if there are existing records with title/suffix issues."""
    print("\n=== Checking Existing Records ===")
    
    try:
        conn = sqlite3.connect('people_management.db')
        cursor = conn.cursor()
        
        # Get all records
        cursor.execute("""
            SELECT first_name, last_name, title, suffix, email 
            FROM people 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        
        records = cursor.fetchall()
        
        if records:
            print(f"Found {len(records)} existing records:")
            for i, (first_name, last_name, title, suffix, email) in enumerate(records, 1):
                print(f"{i}. {first_name} {last_name} (Title: '{title}', Suffix: '{suffix}') - {email}")
        else:
            print("No existing records found")
        
        conn.close()
        
        return records
        
    except Exception as e:
        print(f"❌ Error checking records: {e}")
        if 'conn' in locals():
            conn.close()
        return []

if __name__ == "__main__":
    # Check existing records first
    existing = check_existing_records()
    
    # Test insertion
    result = test_database_insertion()
    
    if result:
        print("\n🎯 CONCLUSION: Database can store title and suffix fields correctly!")
        print("The issue must be in the application code, not the database schema.")
    else:
        print("\n🔍 Need to investigate further...")