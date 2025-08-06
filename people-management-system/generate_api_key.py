#!/usr/bin/env python3
"""
Generate API keys for the People Management System.

This script generates API keys for different access levels.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.api.auth import api_key_manager


def main():
    print("\n" + "="*60)
    print("People Management System - API Key Generator")
    print("="*60)
    
    # Check if running in debug mode
    if os.getenv("DEBUG", "true").lower() == "true":
        print("\n📌 Development Mode - Default API Keys Available:")
        print("-" * 60)
        print("\n🔑 Admin Key (Full Access):")
        print("   Key: dev-admin-key-12345")
        print("   Permissions: read, write, admin")
        print()
        print("🔑 Read-Only Key:")
        print("   Key: dev-readonly-key-67890")
        print("   Permissions: read")
        print("-" * 60)
    
    print("\n📝 Generate New API Key:")
    print("-" * 60)
    
    # Get client name
    client_name = input("Enter client name (e.g., 'My Application'): ").strip()
    if not client_name:
        client_name = "Default Client"
    
    # Select permissions
    print("\nSelect permissions (comma-separated):")
    print("  - read: Read access to all resources")
    print("  - write: Write/modify access to resources")
    print("  - admin: Administrative operations")
    print("  - statistics: Access to statistics endpoints")
    
    permissions_input = input("\nEnter permissions [read,write]: ").strip()
    if not permissions_input:
        permissions_input = "read,write"
    
    permissions = set(p.strip() for p in permissions_input.split(","))
    
    # Get expiration
    expires_input = input("\nExpiration in days (press Enter for 365): ").strip()
    expires_in_days = int(expires_input) if expires_input else 365
    
    # Generate the key
    api_key, key_id = api_key_manager.generate_api_key(
        client_name=client_name,
        permissions=permissions,
        expires_in_days=expires_in_days,
        metadata={"generated_by": "cli_tool"}
    )
    
    print("\n" + "="*60)
    print("✅ API Key Generated Successfully!")
    print("="*60)
    print(f"\n🔑 API Key: {api_key}")
    print(f"📌 Key ID: {key_id}")
    print(f"👤 Client: {client_name}")
    print(f"🔐 Permissions: {', '.join(permissions)}")
    print(f"📅 Expires in: {expires_in_days} days")
    print("\n⚠️  IMPORTANT: Save this API key securely!")
    print("    This key will not be shown again.")
    print("="*60)
    
    # Usage instructions
    print("\n📖 Usage Instructions:")
    print("-" * 60)
    print("Include the API key in your requests using the X-API-Key header:")
    print()
    print("  curl -H 'X-API-Key: YOUR_API_KEY' http://localhost:8000/api/v1/people")
    print()
    print("Or in Python with httpx:")
    print()
    print("  import httpx")
    print("  headers = {'X-API-Key': 'YOUR_API_KEY'}")
    print("  response = httpx.get('http://localhost:8000/api/v1/people', headers=headers)")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()