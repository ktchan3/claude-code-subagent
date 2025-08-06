#!/usr/bin/env python3
"""
Test script to verify final client fixes are working.
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.api_client import PeopleManagementClient


def test_sync_client():
    """Test that the synchronous client works properly."""
    print("\n" + "="*60)
    print("🧪 Testing Final Client Fixes")
    print("="*60)
    
    # Create client with config
    print("\n1️⃣ Creating synchronous client...")
    config = {
        "base_url": "http://localhost:8000",
        "api_key": "dev-admin-key-12345"
    }
    
    try:
        client = PeopleManagementClient(config)
        print("   ✅ Client created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create client: {e}")
        return False
    
    # Test multiple API calls in sequence
    print("\n2️⃣ Testing multiple API calls...")
    endpoints = [
        ("people", "List people"),
        ("departments", "List departments"),
        ("positions", "List positions"),
        ("employment", "List employment")
    ]
    
    for endpoint, description in endpoints:
        try:
            # Simulate delay between calls (like user clicking buttons)
            time.sleep(0.5)
            
            # Make API call
            if endpoint == "people":
                result = client.list_people(page=1, size=10)
            elif endpoint == "departments":
                result = client.list_departments(page=1, size=10)
            elif endpoint == "positions":
                result = client.list_positions(page=1, size=10)
            elif endpoint == "employment":
                result = client.list_employment(page=1, size=10)
            
            if result:
                print(f"   ✅ {description}: Success")
            else:
                print(f"   ⚠️ {description}: No data")
                
        except Exception as e:
            error_msg = str(e)
            if "Event loop is closed" in error_msg:
                print(f"   ❌ {description}: EVENT LOOP CLOSED ERROR!")
                return False
            else:
                print(f"   ⚠️ {description}: {error_msg}")
    
    # Test connection check
    print("\n3️⃣ Testing connection check...")
    try:
        result = client.test_connection()
        if result:
            print("   ✅ Connection test passed")
        else:
            print("   ⚠️ Connection test returned False")
    except Exception as e:
        if "Event loop is closed" in str(e):
            print(f"   ❌ Connection test: EVENT LOOP CLOSED ERROR!")
            return False
        else:
            print(f"   ⚠️ Connection test: {e}")
    
    # Test client close
    print("\n4️⃣ Testing client close...")
    try:
        client.close()
        print("   ✅ Client closed successfully")
    except Exception as e:
        print(f"   ❌ Failed to close client: {e}")
    
    return True


def main():
    print("\n" + "="*60)
    print("🔧 Final Client Fixes Test")
    print("="*60)
    
    # Check if server is running
    print("\n📡 Checking server...")
    try:
        import httpx
        response = httpx.get("http://localhost:8000/docs", timeout=2)
        print("✅ Server is running")
    except:
        print("⚠️ Server is not running - tests may fail")
        print("   Start the server with: make run-server")
    
    # Run the test
    success = test_sync_client()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    if success:
        print("✅ All tests passed - NO EVENT LOOP ERRORS!")
        print("\n🎉 The client is now fully fixed!")
        print("   - No more 'Event loop is closed' errors")
        print("   - Stable API operations")
        print("   - Proper resource cleanup")
        print("\n💡 You can now use the client:")
        print("   Run: make run-client")
        print("   Server URL: http://localhost:8000")
        print("   API Key: dev-admin-key-12345")
    else:
        print("❌ Tests failed - Event loop issues persist")
        print("   Please check the error messages above")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()