#!/usr/bin/env python3
"""
Fix Corrupted API Keys Script

This script cleans up any corrupted API keys that may have been saved 
with invalid characters (like newlines) that cause "Illegal header value" errors.

Usage:
    python fix_corrupted_api_keys.py

This script will:
1. Load the current configuration
2. Check all saved API keys for corruption
3. Remove any invalid API keys
4. Report what was cleaned up
"""

import sys
import logging
from pathlib import Path

# Add the project root to the path so we can import modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from client.services.config_service import ConfigService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main function to clean up corrupted API keys."""
    print("=" * 60)
    print("People Management System - API Key Cleanup Tool")
    print("=" * 60)
    print()
    
    try:
        # Initialize config service
        print("Initializing configuration service...")
        config_service = ConfigService()
        config_service.initialize()
        
        print(f"Configuration directory: {config_service.config_dir}")
        print()
        
        # Clear corrupted API keys
        print("Checking for and cleaning corrupted API keys...")
        cleared_count = config_service.clear_corrupted_api_keys()
        
        print()
        if cleared_count > 0:
            print(f"✓ Successfully cleaned {cleared_count} corrupted API key(s)")
            print("The corrupted API keys have been removed from your configuration.")
            print("You will need to re-enter your API key(s) when connecting to the server.")
        else:
            print("✓ No corrupted API keys found - your configuration is clean!")
        
        print()
        print("Cleanup completed successfully.")
        
    except Exception as e:
        print(f"✗ Error during cleanup: {e}")
        logger.error(f"Cleanup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()