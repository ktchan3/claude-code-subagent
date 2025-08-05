#!/usr/bin/env python3
"""
Convenient database management CLI for the people management system.

This script provides a simple interface for common database operations.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == '__main__':
    from server.database.init_db import main
    main()