#!/usr/bin/env python3
"""
Comprehensive test to ensure ALL person fields are saved to database.
Tests creation, update, and retrieval of complete person records.
"""

import json
import urllib.request
import urllib.error
import sys
import time
from datetime import datetime

def create_complete_person():
    """Create a person with ALL possible fields filled."""
    print("\n📝 Creating person with ALL fields...")
    
    person_data = {
        # Basic required fields
        "first_name": "Alexandra",
        "last_name": "Johnson",
        "email": f"alex.johnson.{int(time.time())}@test.com",
        
        # Additional name fields
        "title": "Prof",
        "suffix": "PhD",
        
        # Contact information
        "phone": "+15550100123",
        "mobile": "+15550200456",
        
        # Personal information
        "date_of_birth": "25-12-1980",  # dd-mm-yyyy format
        "gender": "Female",
        "marital_status": "Single",
        
        # Address
        "address": "456 University Ave, Suite 200",
        "city": "San Francisco",
        "state": "CA",
        "zip_code": "94105",
        "country": "United States",
        
        # Emergency contact
        "emergency_contact_name": "Robert Johnson",
        "emergency_contact_phone": "+15550911789",
        
        # Additional fields
        "notes": "Professor of Computer Science, specializes in AI/ML",
        "tags": ["professor", "ai-expert", "research", "leadership"],
        "status": "Active"
    }
    
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
            return result, person_data
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ Error creating person: {error_body[:500]}")
        return None, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None


def verify_all_fields(saved_data, original_data, operation="Creation"):
    """Verify that all fields were saved correctly."""
    print(f"\n✅ Verifying {operation} - All Fields Saved:")
    print("-" * 50)
    
    field_checks = [
        # Basic fields
        ("First Name", original_data["first_name"], saved_data.get("first_name")),
        ("Last Name", original_data["last_name"], saved_data.get("last_name")),
        ("Email", original_data["email"], saved_data.get("email")),
        
        # Additional name fields
        ("Title", original_data.get("title"), saved_data.get("title")),
        ("Suffix", original_data.get("suffix"), saved_data.get("suffix")),
        
        # Contact
        ("Phone", original_data.get("phone"), saved_data.get("phone")),
        ("Mobile", original_data.get("mobile"), saved_data.get("mobile")),
        
        # Personal (date needs special handling)
        # For date, we need to check the expected ISO format
        ("Date of Birth", 
         "1981-01-01" if "1981" in str(original_data.get("date_of_birth", "")) else "1980-12-25", 
         saved_data.get("date_of_birth")),
        ("Gender", original_data.get("gender"), saved_data.get("gender")),
        ("Marital Status", original_data.get("marital_status"), saved_data.get("marital_status")),
        
        # Address
        ("Address", original_data.get("address"), saved_data.get("address")),
        ("City", original_data.get("city"), saved_data.get("city")),
        ("State", original_data.get("state"), saved_data.get("state")),
        ("Zip Code", original_data.get("zip_code"), saved_data.get("zip_code")),
        ("Country", original_data.get("country"), saved_data.get("country")),
        
        # Emergency
        ("Emergency Contact Name", original_data.get("emergency_contact_name"), 
         saved_data.get("emergency_contact_name")),
        ("Emergency Contact Phone", original_data.get("emergency_contact_phone"), 
         saved_data.get("emergency_contact_phone")),
        
        # Additional
        ("Notes", original_data.get("notes"), saved_data.get("notes")),
        ("Status", original_data.get("status"), saved_data.get("status")),
    ]
    
    all_passed = True
    failed_fields = []
    
    for field_name, expected, actual in field_checks:
        if expected == actual:
            print(f"  ✅ {field_name}: {actual}")
        else:
            print(f"  ❌ {field_name}: Expected '{expected}', Got '{actual}'")
            failed_fields.append(field_name)
            all_passed = False
    
    # Special check for tags (array field)
    expected_tags = set(original_data.get("tags", []))
    actual_tags = saved_data.get("tags", [])
    if isinstance(actual_tags, list):
        actual_tags_set = set(actual_tags)
        if expected_tags == actual_tags_set:
            print(f"  ✅ Tags: {actual_tags}")
        else:
            print(f"  ❌ Tags: Expected {list(expected_tags)}, Got {actual_tags}")
            failed_fields.append("Tags")
            all_passed = False
    else:
        print(f"  ❌ Tags: Not a list - {actual_tags}")
        failed_fields.append("Tags")
        all_passed = False
    
    print("-" * 50)
    
    if all_passed:
        print(f"🎉 {operation} SUCCESS: All 20 fields saved correctly!")
    else:
        print(f"⚠️ {operation} FAILED: {len(failed_fields)} fields not saved correctly:")
        for field in failed_fields:
            print(f"   - {field}")
    
    return all_passed


def update_person(person_id):
    """Update a person with different values for all fields."""
    print(f"\n📝 Updating person {person_id} with new values...")
    
    update_data = {
        "first_name": "Alexandra",
        "last_name": "Johnson-Smith",  # Changed
        "email": f"alex.smith.{int(time.time())}@test.com",  # Changed
        "title": "Dr",  # Changed from Prof
        "suffix": "MD",  # Changed from PhD
        "phone": "+15559999001",  # Changed
        "mobile": "+15558888002",  # Changed
        "date_of_birth": "01-01-1981",  # Changed date
        "gender": "Female",
        "marital_status": "Married",  # Changed
        "address": "789 Medical Center Blvd",  # Changed
        "city": "Boston",  # Changed
        "state": "MA",  # Changed
        "zip_code": "02115",  # Changed
        "country": "United States",
        "emergency_contact_name": "Michael Smith",  # Changed
        "emergency_contact_phone": "+15557777003",  # Changed
        "notes": "Changed to medical doctor, hospital director",  # Changed
        "tags": ["doctor", "director", "medical", "updated"],  # Changed
        "status": "Inactive"  # Changed
    }
    
    req = urllib.request.Request(
        f"http://localhost:8000/api/v1/people/{person_id}",
        data=json.dumps(update_data).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "dev-admin-key-12345"
        },
        method='PUT'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            # Override date for verification since it's returned in ISO format
            update_data["date_of_birth"] = "1981-01-01"
            return result, update_data
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ Error updating person: {error_body[:500]}")
        return None, None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None


def get_person(person_id):
    """Retrieve a person to verify data persistence."""
    print(f"\n📝 Retrieving person {person_id} to verify persistence...")
    
    req = urllib.request.Request(
        f"http://localhost:8000/api/v1/people/{person_id}",
        headers={"X-API-Key": "dev-admin-key-12345"},
        method='GET'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
            return result
    except Exception as e:
        print(f"❌ Error retrieving person: {e}")
        return None


def delete_person(person_id):
    """Clean up test person."""
    if not person_id:
        return
    
    try:
        req = urllib.request.Request(
            f"http://localhost:8000/api/v1/people/{person_id}",
            headers={"X-API-Key": "dev-admin-key-12345"},
            method='DELETE'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status in [200, 204]:
                print(f"\n🧹 Cleaned up test person {person_id}")
    except Exception as e:
        print(f"\n⚠️ Could not delete test person: {e}")


def main():
    print("=" * 70)
    print("🔬 COMPREHENSIVE TEST: All Person Fields Database Persistence")
    print("=" * 70)
    print("\nThis test ensures 100% of person data fields are saved to database")
    
    # Check server
    print("\n📡 Checking server status...")
    try:
        req = urllib.request.Request("http://localhost:8000/docs")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                print("✅ Server is running")
    except:
        print("❌ Server is not running! Start with: make run-server")
        return 1
    
    results = []
    person_id = None
    
    try:
        # Test 1: Create person with all fields
        print("\n" + "="*70)
        print("TEST 1: CREATE PERSON WITH ALL FIELDS")
        print("="*70)
        created_person, original_data = create_complete_person()
        
        if created_person:
            person_id = created_person.get('id')
            print(f"✅ Person created with ID: {person_id}")
            test1_passed = verify_all_fields(created_person, original_data, "Creation")
            results.append(("Creation with all fields", test1_passed))
        else:
            print("❌ Failed to create person")
            results.append(("Creation with all fields", False))
            return 1
        
        # Test 2: Update person with all fields
        print("\n" + "="*70)
        print("TEST 2: UPDATE PERSON WITH ALL FIELDS")
        print("="*70)
        updated_person, update_data = update_person(person_id)
        
        if updated_person:
            print(f"✅ Person updated successfully")
            test2_passed = verify_all_fields(updated_person, update_data, "Update")
            results.append(("Update with all fields", test2_passed))
        else:
            print("❌ Failed to update person")
            results.append(("Update with all fields", False))
        
        # Test 3: Retrieve person to verify persistence
        print("\n" + "="*70)
        print("TEST 3: RETRIEVE PERSON TO VERIFY PERSISTENCE")
        print("="*70)
        retrieved_person = get_person(person_id)
        
        if retrieved_person and update_data:
            print(f"✅ Person retrieved successfully")
            test3_passed = verify_all_fields(retrieved_person, update_data, "Retrieval")
            results.append(("Retrieval after update", test3_passed))
        else:
            print("❌ Failed to retrieve person")
            results.append(("Retrieval after update", False))
        
    finally:
        # Cleanup
        if person_id:
            delete_person(person_id)
    
    # Final Summary
    print("\n" + "="*70)
    print("📊 FINAL TEST RESULTS")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED - 100% DATA INTEGRITY VERIFIED!")
        print("\n✅ All 20 person fields are correctly saved to database")
        print("✅ All fields persist through create, update, and retrieve")
        print("✅ Date format dd-mm-yyyy is handled correctly")
        print("✅ Arrays (tags) are handled correctly")
        print("✅ No data loss occurs at any point")
        print("\n📌 The People Management System is DATA-SAFE!")
        return 0
    else:
        print("⚠️ SOME TESTS FAILED - Data may not be persisting correctly")
        print("\nTroubleshooting:")
        print("1. Restart the server: make run-server")
        print("2. Check server logs for errors")
        print("3. Verify database migrations are applied")
        return 1


if __name__ == "__main__":
    sys.exit(main())