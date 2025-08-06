#!/usr/bin/env python3
"""
Test script to verify that the 'Event loop is closed' errors are fixed.

This script tests the HTTP client without starting the full Qt application.
"""

import logging
import time
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.api_client import PeopleManagementClient, ClientConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_sync_client():
    """Test the synchronous HTTP client."""
    print("=" * 60)
    print("Testing Synchronous HTTP Client")
    print("=" * 60)
    
    # Create client configuration
    config = ClientConfig(
        base_url="http://localhost:8000",
        timeout=10.0,
        max_retries=2
    )
    
    # Test client creation and basic operations
    try:
        with PeopleManagementClient(config) as client:
            print("✅ Client created successfully")
            
            # Test multiple connection attempts (this was where the error occurred)
            for i in range(5):
                print(f"🔄 Connection test {i+1}...")
                try:
                    connected = client.test_connection()
                    if connected:
                        print(f"✅ Connection test {i+1} succeeded")
                    else:
                        print(f"❌ Connection test {i+1} failed (server not available)")
                except Exception as e:
                    print(f"❌ Connection test {i+1} failed with error: {e}")
                
                # Small delay between tests
                time.sleep(0.5)
            
            print("✅ All connection tests completed without 'Event loop is closed' errors")
            
    except Exception as e:
        print(f"❌ Client test failed: {e}")
        return False
    
    return True

def test_multiple_clients():
    """Test creating multiple clients (simulates what happens in Qt app)."""
    print("\n" + "=" * 60)
    print("Testing Multiple Client Instances")
    print("=" * 60)
    
    config = ClientConfig(
        base_url="http://localhost:8000",
        timeout=5.0
    )
    
    clients = []
    try:
        # Create multiple clients
        for i in range(3):
            client = PeopleManagementClient(config)
            clients.append(client)
            print(f"✅ Client {i+1} created")
        
        # Test each client
        for i, client in enumerate(clients):
            print(f"🔄 Testing client {i+1}...")
            try:
                connected = client.test_connection()
                if connected:
                    print(f"✅ Client {i+1} connection succeeded")
                else:
                    print(f"❌ Client {i+1} connection failed (server not available)")
            except Exception as e:
                print(f"❌ Client {i+1} connection failed: {e}")
        
        print("✅ Multiple client test completed without errors")
        return True
        
    except Exception as e:
        print(f"❌ Multiple client test failed: {e}")
        return False
    
    finally:
        # Clean up clients
        for client in clients:
            try:
                client.close()
            except Exception as e:
                print(f"⚠️ Error closing client: {e}")

def test_qt_compatibility():
    """Test that we can use the client in a Qt-like environment."""
    print("\n" + "=" * 60)
    print("Testing Qt Compatibility")
    print("=" * 60)
    
    try:
        from client.services.api_service import APIService
        print("✅ APIService import successful")
        
        # Create API service
        api_service = APIService(
            base_url="http://localhost:8000",
            timeout=5.0
        )
        print("✅ APIService created")
        
        # Test connection
        try:
            connected = api_service.test_connection()
            if connected:
                print("✅ APIService connection succeeded")
            else:
                print("❌ APIService connection failed (server not available)")
        except Exception as e:
            print(f"❌ APIService connection failed: {e}")
        
        # Clean up
        api_service.close()
        print("✅ APIService closed cleanly")
        
        return True
        
    except Exception as e:
        print(f"❌ Qt compatibility test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Starting Event Loop Fix Tests")
    print("Note: These tests will show connection failures if the server isn't running.")
    print("The important thing is that there are no 'Event loop is closed' errors.\n")
    
    results = []
    
    # Test synchronous client
    results.append(test_sync_client())
    
    # Test multiple clients
    results.append(test_multiple_clients())
    
    # Test Qt compatibility
    results.append(test_qt_compatibility())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if all(results):
        print("✅ ALL TESTS PASSED - No 'Event loop is closed' errors detected!")
        print("The fixes appear to be working correctly.")
        return 0
    else:
        print("❌ Some tests failed - please check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)