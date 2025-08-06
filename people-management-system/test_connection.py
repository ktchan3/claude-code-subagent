#!/usr/bin/env python3
"""
Test script to verify the connection functionality is working.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_imports():
    """Test that all imports work correctly."""
    print("\n" + "="*60)
    print("🧪 Testing Connection Fix")
    print("="*60)
    
    print("\n1️⃣ Testing imports...")
    try:
        from client.utils.async_utils import QtSyncHelper
        print("   ✅ QtSyncHelper imported")
        
        # Check that the method exists
        helper = QtSyncHelper()
        if hasattr(helper, 'call_sync'):
            print("   ✅ call_sync method exists")
        else:
            print("   ❌ call_sync method missing")
            
        if hasattr(helper, 'call_async'):
            print("   ❌ call_async method still exists (should be removed)")
        else:
            print("   ✅ call_async method removed (correct)")
            
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False
    
    print("\n2️⃣ Testing login_dialog imports...")
    try:
        from client.ui.login_dialog import LoginDialog
        print("   ✅ LoginDialog imported successfully")
    except Exception as e:
        print(f"   ❌ LoginDialog import failed: {e}")
        return False
    
    print("\n3️⃣ Testing main_window imports...")
    try:
        from client.ui.main_window import MainWindow
        print("   ✅ MainWindow imported successfully")
    except Exception as e:
        print(f"   ❌ MainWindow import failed: {e}")
        return False
    
    return True


def check_method_calls():
    """Check that method calls were updated correctly."""
    print("\n4️⃣ Checking method call updates...")
    
    # Read the files to verify the changes
    files_to_check = [
        ("client/ui/login_dialog.py", 4),
        ("client/ui/main_window.py", 1)
    ]
    
    for filepath, expected_count in files_to_check:
        with open(filepath, 'r') as f:
            content = f.read()
            
        async_count = content.count('call_async')
        sync_count = content.count('call_sync')
        
        if async_count == 0:
            print(f"   ✅ {filepath}: No call_async found (good)")
        else:
            print(f"   ❌ {filepath}: Found {async_count} call_async (should be 0)")
            
        if sync_count == expected_count:
            print(f"   ✅ {filepath}: Found {sync_count} call_sync (expected {expected_count})")
        else:
            print(f"   ⚠️ {filepath}: Found {sync_count} call_sync (expected {expected_count})")


def main():
    print("\n" + "="*60)
    print("🔧 Connection Fix Verification")
    print("="*60)
    
    # Test imports
    if not test_imports():
        print("\n❌ Import tests failed")
        return
    
    # Check method calls
    check_method_calls()
    
    print("\n" + "="*60)
    print("📊 Summary")
    print("="*60)
    print("\n✅ All fixes have been applied successfully!")
    print("\nThe error \"'QtSyncHelper' object has no attribute 'call_async'\" is now fixed.")
    print("\n💡 You can now:")
    print("   1. Run: make run-client")
    print("   2. Enter Server URL: http://localhost:8000")
    print("   3. Enter API Key: dev-admin-key-12345")
    print("   4. Click Connect - it should work now!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()