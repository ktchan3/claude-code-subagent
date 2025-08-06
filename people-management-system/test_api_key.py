#!/usr/bin/env python3
"""
Test script to verify API key authentication is working.
"""

import httpx
import json
import sys

def test_api_with_key(api_key: str, key_name: str):
    """Test API access with the given key."""
    print(f"\n{'='*60}")
    print(f"Testing: {key_name}")
    print(f"API Key: {api_key}")
    print('='*60)
    
    headers = {'X-API-Key': api_key}
    base_url = "http://localhost:8000"
    
    # Test endpoints
    endpoints = [
        ("/api/v1/people/", "GET", "List people"),
        ("/api/v1/departments/", "GET", "List departments"),
        ("/api/v1/positions/", "GET", "List positions"),
    ]
    
    for endpoint, method, description in endpoints:
        url = base_url + endpoint
        print(f"\n📍 {description} ({method} {endpoint})")
        print("-" * 40)
        
        try:
            response = httpx.request(method, url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Success! Status: {response.status_code}")
                data = response.json()
                if isinstance(data, dict):
                    if 'data' in data:
                        print(f"   Items returned: {len(data.get('data', []))}")
                    else:
                        print(f"   Response keys: {', '.join(data.keys())}")
            else:
                print(f"❌ Failed! Status: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data.get('detail', error_data.get('message', 'Unknown error'))}")
                except:
                    print(f"   Error: {response.text[:100]}")
                    
        except httpx.ConnectError:
            print("❌ Connection failed! Is the server running?")
            print("   Start the server with: make run-server")
            return False
        except httpx.TimeoutException:
            print("❌ Request timed out!")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return True


def main():
    print("\n" + "="*60)
    print("🔑 API Key Authentication Test")
    print("="*60)
    
    # Check if server is running
    print("\n📡 Checking server connection...")
    try:
        response = httpx.get("http://localhost:8000/docs", timeout=2)
        print("✅ Server is running!")
    except:
        print("❌ Server is not running!")
        print("   Please start the server with: make run-server")
        sys.exit(1)
    
    # Test with admin key
    admin_key = "dev-admin-key-12345"
    success1 = test_api_with_key(admin_key, "Admin Key (Full Access)")
    
    # Test with read-only key
    readonly_key = "dev-readonly-key-67890"
    success2 = test_api_with_key(readonly_key, "Read-Only Key")
    
    # Test without key (should fail)
    print(f"\n{'='*60}")
    print("Testing: No API Key (Should Fail)")
    print('='*60)
    
    try:
        response = httpx.get("http://localhost:8000/api/v1/people/", timeout=5)
        if response.status_code == 401:
            print("✅ Correctly rejected request without API key!")
        else:
            print(f"⚠️  Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Summary")
    print('='*60)
    if success1 and success2:
        print("✅ All API key tests passed!")
        print("\n🎉 The API key authentication is working correctly!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print(f"\n💡 To use in the GUI client:")
    print(f"   1. Run: make run-client")
    print(f"   2. Enter server URL: http://localhost:8000")
    print(f"   3. Enter API Key: {admin_key}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()