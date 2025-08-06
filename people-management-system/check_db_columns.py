#!/usr/bin/env python3
"""
Check database columns for the people table.
"""

import sqlite3
import os

db_path = "people_management.db"

if not os.path.exists(db_path):
    print(f"❌ Database file not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table info
cursor.execute("PRAGMA table_info(people)")
columns = cursor.fetchall()

print("=" * 60)
print("People Table Columns:")
print("=" * 60)

# Check for specific fields
required_fields = ['first_name', 'last_name', 'title', 'suffix']
found_fields = []
missing_fields = []

for col in columns:
    col_id, name, type_, notnull, default, pk = col
    print(f"  {name:30} {type_:15} {'NOT NULL' if notnull else 'NULL'}")
    
    if name in required_fields:
        found_fields.append(name)

# Check what's missing
for field in required_fields:
    if field not in [col[1] for col in columns]:
        missing_fields.append(field)

print("\n" + "=" * 60)
print("Field Status Check:")
print("=" * 60)

for field in required_fields:
    if field in [col[1] for col in columns]:
        print(f"  ✅ {field} - EXISTS")
    else:
        print(f"  ❌ {field} - MISSING")

if missing_fields:
    print("\n⚠️  Missing columns:", ", ".join(missing_fields))
    print("\nTo fix this, run:")
    print("  1. rm -f people_management.db")
    print("  2. make setup-db")
    print("  3. Restart the server")
else:
    print("\n✅ All required columns exist!")

conn.close()