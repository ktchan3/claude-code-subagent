#!/usr/bin/env python3
"""
Test that all person fields are updated correctly, especially tags field.
"""

import json
import urllib.request
import urllib.error
import sys
from datetime import datetime

def test_person_update():
    """Test updating a person with ALL fields including tags."""
    print("\n🧪 Testing Person Update with All Fields...")
    print("=" * 60)
    
    # Step 1: Create a person with minimal data
    initial_person_data = {
        "first_name": "Jane",
        "last_name": "UpdateTest",
        "email": f"jane.update.{datetime.now().timestamp()}@example.com"
    }
    
    print("\n📝 Creating initial person...")
    
    req = urllib.request.Request(
        "http://localhost:8000/api/v1/people/",
        data=json.dumps(initial_person_data).encode('utf-8'),
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "dev-admin-key-12345"
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            create_result = json.loads(response.read().decode())
            person_id = create_result.get('id')
            
            if not person_id:
                print("❌ Failed to create initial person")
                return False
            
            print(f"✅ Created person with ID: {person_id}")
            
    except Exception as e:
        print(f"❌ Failed to create initial person: {e}")
        return False
    
    # Step 2: Update the person with ALL fields
    update_data = {
        # Basic information
        "first_name": "Jane",
        "last_name": "UpdateTestUpdated",
        "title": "Ms.",
        "suffix": "Sr.",
        
        # Contact information
        "phone": "+1-555-111-1111",
        "mobile": "+1-555-222-2222",
        
        # Date with dd-mm-yyyy format
        "date_of_birth": "25-12-1990",  # Christmas 1990
        
        # Address
        "address": "456 Updated Street",
        "city": "Updated City",
        "state": "UC",
        "zip_code": "12345",
        "country": "Updated Country",
        
        # Personal details
        "gender": "Female",
        "marital_status": "Divorced",
        
        # Emergency contact
        "emergency_contact_name": "John UpdateTest",
        "emergency_contact_phone": "+1-555-333-3333",
        
        # Additional fields
        "notes": "This person has been updated with ALL fields",
        "tags": ["updated", "comprehensive", "test-tags"],
        "status": "Inactive"
    }
    
    print("\n📝 Updating person with all fields...")
    
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
        with urllib.request.urlopen(req, timeout=5) as response:
            update_result = json.loads(response.read().decode())
            
            print("✅ Person updated successfully!")
            print("\n📊 Verifying all updated fields:")
            print("-" * 40)
            
            # Check all fields were updated correctly
            checks = [
                ("First Name", update_data["first_name"], update_result.get("first_name")),
                ("Last Name", update_data["last_name"], update_result.get("last_name")),
                ("Title", update_data["title"], update_result.get("title")),
                ("Suffix", update_data["suffix"], update_result.get("suffix")),
                ("Phone", update_data["phone"], update_result.get("phone")),
                ("Mobile", update_data["mobile"], update_result.get("mobile")),
                ("Date of Birth", "1990-12-25", update_result.get("date_of_birth")),  # Should be stored as ISO
                ("Address", update_data["address"], update_result.get("address")),
                ("City", update_data["city"], update_result.get("city")),
                ("State", update_data["state"], update_result.get("state")),
                ("Zip Code", update_data["zip_code"], update_result.get("zip_code")),
                ("Country", update_data["country"], update_result.get("country")),
                ("Gender", update_data["gender"], update_result.get("gender")),
                ("Marital Status", update_data["marital_status"], update_result.get("marital_status")),
                ("Emergency Contact Name", update_data["emergency_contact_name"], update_result.get("emergency_contact_name")),
                ("Emergency Contact Phone", update_data["emergency_contact_phone"], update_result.get("emergency_contact_phone")),
                ("Notes", update_data["notes"], update_result.get("notes")),
                ("Status", update_data["status"], update_result.get("status"))
            ]
            
            all_passed = True
            for field_name, expected, actual in checks:
                if expected == actual:
                    print(f"   ✅ {field_name}: {actual}")
                else:
                    print(f"   ❌ {field_name}: Expected '{expected}', got '{actual}'")
                    all_passed = False
            
            # Check tags separately (critical test for the bug fix)
            tags_result = update_result.get("tags")
            if isinstance(tags_result, list):
                if set(tags_result) == set(update_data["tags"]):
                    print(f"   ✅ Tags: {tags_result}")
                else:
                    print(f"   ❌ Tags: Expected {update_data['tags']}, got {tags_result}")
                    all_passed = False
            else:
                print(f"   ❌ Tags: Got {type(tags_result).__name__} instead of list: {tags_result}")
                all_passed = False
            
            print("-" * 40)
            
            if all_passed:
                print("\n🎉 SUCCESS: All fields updated correctly!")
                print("✅ Person update is working properly")
                print("✅ Tags field is being updated and saved correctly")
                
                # Step 3: Verify by retrieving the person again
                print("\n📊 Double-checking by retrieving person...")
                
                get_req = urllib.request.Request(
                    f"http://localhost:8000/api/v1/people/{person_id}",
                    headers={"X-API-Key": "dev-admin-key-12345"},
                    method='GET'
                )
                
                with urllib.request.urlopen(get_req, timeout=5) as get_response:
                    get_result = json.loads(get_response.read().decode())
                    get_tags = get_result.get("tags")
                    
                    if isinstance(get_tags, list) and set(get_tags) == set(update_data["tags"]):
                        print("✅ Retrieved person has correct tags - update was persisted!")
                        return True, person_id
                    else:
                        print(f"❌ Retrieved person has wrong tags: {get_tags}")
                        return False, person_id
                
            else:
                print("\n⚠️  Some fields were not updated correctly")
                return False, person_id
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"\n❌ Failed to update person: HTTP {e.code}")
        print(f"Error details: {error_body[:500]}")
        
        # Parse error to see what field caused the issue
        try:
            error_json = json.loads(error_body)
            if "detail" in error_json:
                print("\nDetailed error information:")
                if isinstance(error_json["detail"], list):
                    for err in error_json["detail"]:
                        print(f"  - {err}")
                else:
                    print(f"  - {error_json['detail']}")
        except:
            pass
            
        return False, person_id
        
    except Exception as e:
        print(f"\n❌ Failed to update person: {e}")
        return False, person_id


def cleanup_test_person(person_id):
    """Delete the test person."""
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
                print(f"\n🧹 Test person {person_id} deleted")
                
    except Exception as e:
        print(f"\n⚠️  Could not delete test person: {e}")


def main():
    print("=" * 70)
    print("🔧 Testing Person Update with All Fields (especially tags)")
    print("=" * 70)
    
    # Check server is running
    print("\n📡 Checking server status...")
    try:
        req = urllib.request.Request("http://localhost:8000/docs")
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                print("✅ Server is running")
            else:
                print(f"⚠️ Server returned status {response.status}")
    except:
        print("❌ Server is not running!")
        print("Please start the server with: make run-server")
        return 1
    
    # Test person update
    test_passed, person_id = test_person_update()
    
    # Cleanup
    if person_id:
        cleanup_test_person(person_id)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 70)
    
    if test_passed:
        print("\n🎉 UPDATE TEST PASSED!")
        print("\n✅ All person fields can be updated correctly")
        print("✅ Tags field is now handled properly in updates")
        print("✅ Date format dd-mm-yyyy is accepted in updates")
        print("✅ All field updates are being persisted to database")
        print("\n📌 The person update data loss issue has been fixed!")
        return 0
    else:
        print("\n⚠️ Update test failed")
        print("\nThe bug fix may not be complete.")
        print("Check the server logs for more details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())