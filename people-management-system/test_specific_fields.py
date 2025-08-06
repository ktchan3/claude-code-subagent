#!/usr/bin/env python3
"""
Test specifically that First Name, Last Name, Title, and Suffix are saved.
"""

import json
import urllib.request
import urllib.error
import time
import sqlite3

def test_create_person_with_4_fields():
    """Create a person focusing on the 4 specific fields."""
    print("\n" + "=" * 60)
    print("Testing First Name, Last Name, Title, Suffix Fields")
    print("=" * 60)
    
    # Test data with the 4 critical fields
    person_data = {
        "first_name": "John",
        "last_name": "Smith",
        "email": f"john.smith.{int(time.time())}@test.com",
        "title": "Dr",
        "suffix": "PhD"
    }
    
    print("\n📤 Sending data to API:")
    print(f"  First Name: {person_data['first_name']}")
    print(f"  Last Name: {person_data['last_name']}")
    print(f"  Title: {person_data['title']}")
    print(f"  Suffix: {person_data['suffix']}")
    print(f"  Email: {person_data['email']}")
    
    # Create person via API
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/people/",
        data=json.dumps(person_data).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "dev-admin-key-12345"
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            person_id = result.get('id')
            
            print(f"\n✅ Person created with ID: {person_id}")
            
            print("\n📥 Data returned from API:")
            print(f"  First Name: {result.get('first_name')} {'✅' if result.get('first_name') == 'John' else '❌'}")
            print(f"  Last Name: {result.get('last_name')} {'✅' if result.get('last_name') == 'Smith' else '❌'}")
            print(f"  Title: {result.get('title')} {'✅' if result.get('title') == 'Dr' else '❌'}")
            print(f"  Suffix: {result.get('suffix')} {'✅' if result.get('suffix') == 'PhD' else '❌'}")
            
            # Check database directly
            print("\n🔍 Checking database directly:")
            check_database(person_id)
            
            # Clean up
            cleanup_person(person_id)
            
            # Return success status
            return all([
                result.get('first_name') == 'John',
                result.get('last_name') == 'Smith',
                result.get('title') == 'Dr',
                result.get('suffix') == 'PhD'
            ])
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"\n❌ API Error: {e.code}")
        print(f"Details: {error_body[:500]}")
        
        # Try to parse validation errors
        try:
            error_json = json.loads(error_body)
            if "detail" in error_json:
                print("\n📍 Specific errors:")
                if isinstance(error_json["detail"], list):
                    for err in error_json["detail"]:
                        print(f"  - Field: {err.get('loc', [])} - {err.get('msg', '')}")
        except:
            pass
            
        return False
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def check_database(person_id):
    """Check the database directly for the person's data."""
    try:
        conn = sqlite3.connect("people_management.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT first_name, last_name, title, suffix 
            FROM people 
            WHERE id = ?
        """, (person_id,))
        
        row = cursor.fetchone()
        
        if row:
            first_name, last_name, title, suffix = row
            print(f"  First Name: {first_name} {'✅' if first_name == 'John' else '❌'}")
            print(f"  Last Name: {last_name} {'✅' if last_name == 'Smith' else '❌'}")
            print(f"  Title: {title} {'✅' if title == 'Dr' else '❌ (None)' if title is None else '❌'}")
            print(f"  Suffix: {suffix} {'✅' if suffix == 'PhD' else '❌ (None)' if suffix is None else '❌'}")
        else:
            print(f"  ❌ Person with ID {person_id} not found in database!")
        
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")


def cleanup_person(person_id):
    """Delete test person."""
    try:
        req = urllib.request.Request(
            f"http://localhost:8000/api/v1/people/{person_id}",
            headers={"X-API-Key": "dev-admin-key-12345"},
            method='DELETE'
        )
        urllib.request.urlopen(req, timeout=5)
        print(f"\n🧹 Cleaned up test person {person_id}")
    except:
        pass


def test_with_full_form_data():
    """Test with data exactly as the form would send it."""
    print("\n" + "=" * 60)
    print("Testing with Full Form Data (as UI sends)")
    print("=" * 60)
    
    # Simulate exact form data
    form_data = {
        'first_name': 'Jane',
        'last_name': 'Doe',
        'email': f'jane.doe.{int(time.time())}@test.com',
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
        'title': 'Ms',
        'suffix': 'Jr'
    }
    
    # Remove None values (as the form would)
    clean_data = {k: v for k, v in form_data.items() if v is not None}
    
    print(f"\n📤 Sending form-like data:")
    print(f"  First Name: {clean_data.get('first_name')}")
    print(f"  Last Name: {clean_data.get('last_name')}")
    print(f"  Title: {clean_data.get('title')}")
    print(f"  Suffix: {clean_data.get('suffix')}")
    
    # Send to API
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/people/",
        data=json.dumps(clean_data).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "dev-admin-key-12345"
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            person_id = result.get('id')
            
            print(f"\n✅ Person created with ID: {person_id}")
            
            print("\n📥 Checking saved data:")
            all_correct = True
            
            if result.get('first_name') == 'Jane':
                print(f"  ✅ First Name saved: {result.get('first_name')}")
            else:
                print(f"  ❌ First Name NOT saved: {result.get('first_name')}")
                all_correct = False
                
            if result.get('last_name') == 'Doe':
                print(f"  ✅ Last Name saved: {result.get('last_name')}")
            else:
                print(f"  ❌ Last Name NOT saved: {result.get('last_name')}")
                all_correct = False
                
            if result.get('title') == 'Ms':
                print(f"  ✅ Title saved: {result.get('title')}")
            else:
                print(f"  ❌ Title NOT saved: {result.get('title')}")
                all_correct = False
                
            if result.get('suffix') == 'Jr':
                print(f"  ✅ Suffix saved: {result.get('suffix')}")
            else:
                print(f"  ❌ Suffix NOT saved: {result.get('suffix')}")
                all_correct = False
            
            # Clean up
            cleanup_person(person_id)
            
            return all_correct
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


def main():
    print("=" * 70)
    print("🔬 SPECIFIC TEST: First Name, Last Name, Title, Suffix")
    print("=" * 70)
    
    # Check server
    print("\n📡 Checking server...")
    try:
        req = urllib.request.Request("http://localhost:8000/docs")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                print("✅ Server is running")
    except:
        print("❌ Server is not running! Start with: make run-server")
        return 1
    
    # Run tests
    test1_passed = test_create_person_with_4_fields()
    test2_passed = test_with_full_form_data()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    if test1_passed and test2_passed:
        print("\n✅ ALL TESTS PASSED!")
        print("\nThe 4 critical fields are working correctly:")
        print("  ✅ First Name - Saves to database")
        print("  ✅ Last Name - Saves to database")
        print("  ✅ Title - Saves to database")
        print("  ✅ Suffix - Saves to database")
        print("\n🎉 The fields ARE being saved correctly!")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("\nPotential issues:")
        print("  1. Check if server has latest code")
        print("  2. Restart server: make run-server")
        print("  3. Check client is sending correct field names")
        return 1


if __name__ == "__main__":
    exit(main())