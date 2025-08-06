#!/usr/bin/env python3
"""
Test that all person fields are saved correctly with dd-mm-yyyy date format.
"""

import json
import urllib.request
import urllib.error
import sys
from datetime import datetime

def test_complete_person_creation():
    """Test creating a person with ALL fields including the new dd-mm-yyyy date format."""
    print("\n🧪 Testing Complete Person Creation with dd-mm-yyyy Date Format...")
    print("=" * 60)
    
    # Complete person data with dd-mm-yyyy date format
    person_data = {
        # Basic information
        "first_name": "John",
        "last_name": "Smith",
        "email": f"john.smith.{datetime.now().timestamp()}@example.com",  # Unique email
        
        # Additional basic fields
        "title": "Dr",
        "suffix": "Jr",
        
        # Contact information
        "phone": "+1-555-123-4567",
        "mobile": "+1-555-987-6543",
        
        # Date with dd-mm-yyyy format
        "date_of_birth": "15-03-1985",  # March 15, 1985 in dd-mm-yyyy
        
        # Address
        "address": "123 Main Street",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "country": "United States",
        
        # Personal details
        "gender": "Male",
        "marital_status": "Married",
        
        # Emergency contact
        "emergency_contact_name": "Jane Smith",
        "emergency_contact_phone": "+1-555-111-2222",
        
        # Additional fields
        "notes": "This is a test person with all fields filled",
        "tags": ["test", "complete", "dd-mm-yyyy"],
        "status": "Active"
    }
    
    print("\n📝 Sending person data with dd-mm-yyyy date format...")
    print(f"   Date of Birth: {person_data['date_of_birth']}")
    
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
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            
            print("\n✅ Person created successfully!")
            print("\n📊 Verifying all fields were saved:")
            print("-" * 40)
            
            # Check all important fields
            checks = [
                ("First Name", person_data["first_name"], result.get("first_name")),
                ("Last Name", person_data["last_name"], result.get("last_name")),
                ("Title", person_data["title"], result.get("title")),
                ("Suffix", person_data["suffix"], result.get("suffix")),
                ("Email", person_data["email"], result.get("email")),
                ("Phone", person_data["phone"], result.get("phone")),
                ("Mobile", person_data["mobile"], result.get("mobile")),
                ("Date of Birth", "1985-03-15", result.get("date_of_birth")),  # Should be stored as ISO
                ("Address", person_data["address"], result.get("address")),
                ("City", person_data["city"], result.get("city")),
                ("State", person_data["state"], result.get("state")),
                ("Zip Code", person_data["zip_code"], result.get("zip_code")),
                ("Country", person_data["country"], result.get("country")),
                ("Gender", person_data["gender"], result.get("gender")),
                ("Marital Status", person_data["marital_status"], result.get("marital_status")),
                ("Emergency Contact Name", person_data["emergency_contact_name"], result.get("emergency_contact_name")),
                ("Emergency Contact Phone", person_data["emergency_contact_phone"], result.get("emergency_contact_phone")),
                ("Notes", person_data["notes"], result.get("notes")),
                ("Status", person_data["status"], result.get("status"))
            ]
            
            all_passed = True
            for field_name, expected, actual in checks:
                if expected == actual:
                    print(f"   ✅ {field_name}: {actual}")
                else:
                    print(f"   ❌ {field_name}: Expected '{expected}', got '{actual}'")
                    all_passed = False
            
            # Check tags separately (might be returned as list or string)
            tags_result = result.get("tags")
            if isinstance(tags_result, list):
                if set(tags_result) == set(person_data["tags"]):
                    print(f"   ✅ Tags: {tags_result}")
                else:
                    print(f"   ❌ Tags: Expected {person_data['tags']}, got {tags_result}")
                    all_passed = False
            else:
                print(f"   ⚠️  Tags: Got {type(tags_result).__name__} instead of list: {tags_result}")
            
            print("-" * 40)
            
            if all_passed:
                print("\n🎉 SUCCESS: All fields saved correctly!")
                print("✅ Basic information is being committed to database")
                print("✅ Date format dd-mm-yyyy is accepted and processed correctly")
            else:
                print("\n⚠️  Some fields were not saved correctly")
            
            return result.get('id'), all_passed
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"\n❌ Failed to create person: HTTP {e.code}")
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
            
        return None, False
        
    except Exception as e:
        print(f"\n❌ Failed to create person: {e}")
        return None, False


def test_date_formats():
    """Test various dd-mm-yyyy date formats."""
    print("\n📅 Testing various dd-mm-yyyy date formats...")
    print("-" * 40)
    
    test_dates = [
        ("01-01-1990", "1990-01-01"),
        ("31-12-2000", "2000-12-31"),
        ("15-06-1985", "1985-06-15"),
        ("29-02-2000", "2000-02-29"),  # Leap year
    ]
    
    all_passed = True
    for input_date, expected_iso in test_dates:
        person_data = {
            "first_name": "Test",
            "last_name": "Date",
            "email": f"test.date.{datetime.now().timestamp()}@example.com",
            "date_of_birth": input_date
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
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode())
                saved_date = result.get("date_of_birth")
                
                if saved_date == expected_iso:
                    print(f"   ✅ Date {input_date} accepted. Saved as: {saved_date}")
                    
                    # Clean up test person
                    try:
                        del_req = urllib.request.Request(
                            f"http://localhost:8000/api/v1/people/{result['id']}",
                            headers={"X-API-Key": "dev-admin-key-12345"},
                            method='DELETE'
                        )
                        urllib.request.urlopen(del_req, timeout=5)
                    except:
                        pass
                else:
                    print(f"   ❌ Date {input_date} saved incorrectly as: {saved_date}")
                    all_passed = False
                    
        except urllib.error.HTTPError as e:
            print(f"   ❌ Date {input_date} rejected: {e.code}")
            all_passed = False
        except Exception as e:
            print(f"   ❌ Date {input_date} error: {e}")
            all_passed = False
    
    return all_passed


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
    print("🔧 Testing Complete Person Save with dd-mm-yyyy Date Format")
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
    
    # Test 1: Complete person creation
    person_id, test1_passed = test_complete_person_creation()
    
    # Test 2: Various date formats
    test2_passed = test_date_formats()
    
    # Cleanup
    if person_id:
        cleanup_test_person(person_id)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 70)
    
    if test1_passed and test2_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Basic information is now being saved to database")
        print("✅ All additional fields (title, suffix, emergency contacts) are saved")
        print("✅ Date of Birth accepts dd-mm-yyyy format (e.g., 15-03-1985)")
        print("✅ Dates are correctly parsed and stored in the database")
        print("\n📌 The issues have been completely fixed!")
        return 0
    else:
        print("\n⚠️ Some tests failed")
        print("\nPossible solutions:")
        print("1. Restart the server to apply database changes:")
        print("   - Stop server (Ctrl+C)")
        print("   - Run: make run-server")
        print("\n2. If database schema errors occur:")
        print("   - Run: rm -f people_management.db")
        print("   - Run: make setup-db")
        print("   - Run: make run-server")
        return 1


if __name__ == "__main__":
    sys.exit(main())