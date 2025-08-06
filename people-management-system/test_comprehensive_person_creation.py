#!/usr/bin/env python3

"""
Comprehensive test for person creation with all fields and dd-mm-yyyy date format.
"""

import requests
import json
from datetime import date


def test_person_creation_comprehensive():
    """Test creating a person with all fields including dd-mm-yyyy date format."""
    
    base_url = "http://localhost:8000"
    api_key = "test-api-key-12345-67890-abcde"
    
    # Person data with all fields
    person_data = {
        "first_name": "Jane",
        "last_name": "Smith", 
        "title": "Dr.",
        "suffix": "Jr.",
        "email": f"jane.smith.comprehensive.{int(__import__('time').time())}@example.com",
        "phone": "+1-555-123-4567",
        "mobile": "+1-555-987-6543",
        "date_of_birth": "15-01-1985",  # dd-mm-yyyy format
        "gender": "Female",
        "marital_status": "Married",
        "address": "123 Main Street",
        "city": "New York",
        "state": "NY", 
        "zip_code": "10001",
        "country": "United States",
        "emergency_contact_name": "John Smith",
        "emergency_contact_phone": "+1-555-111-2222",
        "notes": "Test person with all fields",
        "tags": ["VIP", "Client", "Test"],
        "status": "Active"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    print("Testing comprehensive person creation with dd-mm-yyyy date format...")
    print(f"Person data: {json.dumps(person_data, indent=2)}")
    
    try:
        # Create the person
        response = requests.post(f"{base_url}/api/v1/people/", json=person_data, headers=headers)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ Person created successfully!")
            print(f"Created person ID: {result.get('id')}")
            print(f"Created person data: {json.dumps(result, indent=2)}")
            
            # Verify all fields were saved
            saved_fields = [
                'first_name', 'last_name', 'title', 'suffix', 'email', 
                'phone', 'mobile', 'date_of_birth', 'gender', 'marital_status',
                'address', 'city', 'state', 'zip_code', 'country',
                'emergency_contact_name', 'emergency_contact_phone', 
                'notes', 'status'  # Note: tags might be handled differently
            ]
            
            missing_fields = []
            for field in saved_fields:
                if field not in result or result[field] is None:
                    if field in person_data and person_data[field] is not None:
                        missing_fields.append(field)
            
            if missing_fields:
                print(f"⚠️  Warning: Some fields were not saved: {missing_fields}")
            else:
                print("✅ All basic fields were saved successfully!")
            
            # Check date format in response
            saved_date = result.get('date_of_birth')
            if saved_date:
                print(f"Date of birth saved as: {saved_date}")
                # The API might return it in different format, that's ok
            
            return True
            
        else:
            print("❌ Person creation failed!")
            print(f"Error response: {response.text}")
            
            try:
                error_data = response.json()
                if 'detail' in error_data:
                    print(f"Error details: {json.dumps(error_data['detail'], indent=2)}")
            except:
                pass
            
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the server. Make sure the server is running at http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_date_format_handling():
    """Test various date formats to ensure dd-mm-yyyy works."""
    
    base_url = "http://localhost:8000"
    api_key = "test-api-key-12345-67890-abcde"
    
    test_dates = [
        ("01-01-1990", "Standard dd-mm-yyyy"),
        ("31-12-2000", "End of year dd-mm-yyyy"),
        ("15-06-1985", "Mid-year dd-mm-yyyy")
    ]
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    print("\nTesting date format handling...")
    
    for i, (date_str, description) in enumerate(test_dates):
        person_data = {
            "first_name": f"TestDate{i}",
            "last_name": "User",
            "email": f"testdate{i}.{int(__import__('time').time())}@example.com",
            "date_of_birth": date_str
        }
        
        print(f"\nTesting {description}: {date_str}")
        
        try:
            response = requests.post(f"{base_url}/api/v1/people/", json=person_data, headers=headers)
            
            if response.status_code == 201:
                result = response.json()
                print(f"✅ Date {date_str} accepted. Saved as: {result.get('date_of_birth')}")
            else:
                print(f"❌ Date {date_str} rejected: {response.status_code}")
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        print(f"Error: {error_data['detail']}")
                except:
                    print(f"Error response: {response.text}")
                    
        except Exception as e:
            print(f"❌ Error testing date {date_str}: {e}")


if __name__ == "__main__":
    print("🧪 Testing comprehensive person creation and date format handling")
    print("=" * 60)
    
    # Test comprehensive person creation
    success = test_person_creation_comprehensive()
    
    if success:
        # Test date format handling
        test_date_format_handling()
    
    print("\n" + "=" * 60)
    print("✅ Test completed!" if success else "❌ Test failed!")