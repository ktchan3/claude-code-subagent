#!/usr/bin/env python3
"""
Display available API keys for the People Management System.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.api.auth import api_key_manager


def main():
    print("\n" + "="*70)
    print("🔑 People Management System - Available API Keys")
    print("="*70)
    
    # Check if running in debug mode
    if os.getenv("DEBUG", "true").lower() == "true":
        print("\n📌 Development Mode - Default API Keys:")
        print("-" * 70)
        
        print("\n1️⃣  ADMIN KEY (Full Access)")
        print("   API Key: dev-admin-key-12345")
        print("   Permissions: read, write, admin")
        print("   Description: Full access to all API endpoints")
        
        print("\n2️⃣  READ-ONLY KEY")
        print("   API Key: dev-readonly-key-67890")
        print("   Permissions: read")
        print("   Rate Limit: 120 requests/minute")
        print("   Description: Read-only access to view data")
        
        print("\n" + "-" * 70)
        print("\n📖 How to use these API keys:")
        print("-" * 70)
        
        print("\n🔹 With curl:")
        print("   curl -H 'X-API-Key: dev-admin-key-12345' \\")
        print("        http://localhost:8000/api/v1/people")
        
        print("\n🔹 With httpx (Python):")
        print("   import httpx")
        print("   headers = {'X-API-Key': 'dev-admin-key-12345'}")
        print("   response = httpx.get('http://localhost:8000/api/v1/people', headers=headers)")
        
        print("\n🔹 With requests (Python):")
        print("   import requests")
        print("   headers = {'X-API-Key': 'dev-admin-key-12345'}")
        print("   response = requests.get('http://localhost:8000/api/v1/people', headers=headers)")
        
        print("\n🔹 With JavaScript (fetch):")
        print("   fetch('http://localhost:8000/api/v1/people', {")
        print("     headers: { 'X-API-Key': 'dev-admin-key-12345' }")
        print("   })")
        
        print("\n" + "-" * 70)
        print("⚠️  Note: These are development keys for testing only!")
        print("   Generate production keys using: python generate_api_key.py")
        
    else:
        print("\n⚠️  Production Mode - No default keys available")
        print("   Please generate API keys using: python generate_api_key.py")
    
    # List all registered keys (without showing the actual key values)
    all_keys = api_key_manager.list_api_keys()
    if all_keys:
        print("\n" + "="*70)
        print("📊 Registered API Keys Summary:")
        print("-" * 70)
        for key_info in all_keys:
            print(f"\n• Key ID: {key_info['key_id']}")
            print(f"  Client: {key_info['client_name']}")
            print(f"  Permissions: {', '.join(key_info['permissions'])}")
            print(f"  Active: {'✅' if key_info['is_active'] else '❌'}")
            print(f"  Usage Count: {key_info['usage_count']}")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()