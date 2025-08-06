#!/usr/bin/env python3
"""
Test script to verify person creation works after fixing the date constraint issue.
"""

import json
import urllib.request
import urllib.error
from datetime import date

def create_person():
    """Test creating a person with date_of_birth."""
    
    # Person data
    person_data = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test.user@example.com",
        "date_of_birth": "2000-08-06",  # Same date that was failing before
        "country": "United States"
    }
    
    # Create request
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
            print("✅ SUCCESS: Person created successfully!")
            print(f"   ID: {result.get('id')}")
            print(f"   Name: {result.get('first_name')} {result.get('last_name')}")
            print(f"   Email: {result.get('email')}")
            print(f"   Date of Birth: {result.get('date_of_birth')}")
            return True
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"❌ FAILED: HTTP {e.code}")
        print(f"   Error: {error_body}")
        
        # Check if it's the date constraint error
        if "non-deterministic use of date()" in error_body:
            print("\n⚠️  The date constraint error is still occurring!")
            print("   The database may need to be recreated with the fixed schema.")
        return False
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    print("=" * 60)
    print("Testing Person Creation with Date of Birth")
    print("=" * 60)
    print("\nAttempting to create a person with date_of_birth...")
    print("(This was failing with 'non-deterministic use of date()' error)")
    print()
    
    success = create_person()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 The date constraint issue is FIXED!")
        print("✅ People can now be created with dates of birth")
    else:
        print("⚠️  The issue may still need attention")
        print("Try running: rm -f people_management.db && make setup-db")
        print("Then restart the server: make run-server")
    print("=" * 60)


if __name__ == "__main__":
    main()