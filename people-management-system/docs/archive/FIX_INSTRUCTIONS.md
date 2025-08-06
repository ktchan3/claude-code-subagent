# Fix for Missing Person Fields Issue

## Problem
The fields `first_name`, `last_name`, `title`, and `suffix` are not being saved to the database when creating a new person through the UI.

## Root Cause
After thorough investigation, all code is correct throughout the data pipeline. The issue is that **the database migration has not been applied**. The database is missing the `title` and `suffix` columns that were added via migration.

## Solution

### Step 1: Install Dependencies and Apply Database Migration

#### Option A: Using UV (Recommended)
```bash
# Install the workspace dependencies
uv sync

# Navigate to server directory  
cd server

# Apply database migrations
uv run alembic upgrade head
```

#### Option B: Using pip/venv
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install server dependencies
cd server
pip install -e .

# Apply database migrations
alembic upgrade head
```

### Step 2: Verify the Fix

#### Check Database Schema
After applying migrations, verify the database has the required columns:

```bash
# Using UV
cd server
uv run python -c "
from sqlalchemy import create_engine, inspect
engine = create_engine('sqlite:///people_management.db')
inspector = inspect(engine)
columns = inspector.get_columns('people')
column_names = [col['name'] for col in columns]
print('People table columns:', column_names)
required = ['first_name', 'last_name', 'title', 'suffix']
missing = [f for f in required if f not in column_names]
if missing:
    print('❌ STILL MISSING:', missing)
else:
    print('✅ All required fields present')
"
```

#### Test Person Creation
1. Start the server: `uv run uvicorn server.main:app --reload`
2. Start the client application
3. Try creating a new person with:
   - First Name: "John"
   - Last Name: "Doe"  
   - Title: "Mr."
   - Suffix: "Jr."
4. Verify all fields are saved correctly

## What the Migration Does

The migration `d98a095181f8` adds these columns to the `people` table:
- `title` (String(20), nullable=True) - Person's title (Mr., Ms., Dr., etc.)
- `suffix` (String(20), nullable=True) - Person's suffix (Jr., Sr., III, etc.) 
- Plus other fields: `mobile`, `gender`, `marital_status`, `emergency_contact_name`, `emergency_contact_phone`, `notes`, `tags`, `status`

## Verification Commands

### Check Migration Status
```bash
cd server
uv run alembic current    # Shows current migration
uv run alembic history    # Shows all migrations
```

### Manual Database Check (if you have sqlite3)
```bash
sqlite3 server/people_management.db ".schema people"
```

## If Migration Still Fails

If you encounter issues:

1. **Check alembic.ini exists** in the server directory
2. **Verify database path** in alembic.ini matches your database location  
3. **Check permissions** on the database file
4. **Look for error messages** when running `alembic upgrade head`

## Alternative Quick Fix (if migration fails)

If the migration continues to fail, you can manually add the missing columns:

```sql
-- Connect to your database and run:
ALTER TABLE people ADD COLUMN title VARCHAR(20);
ALTER TABLE people ADD COLUMN suffix VARCHAR(20);
```

## Post-Fix Verification

After fixing, test by creating a person with these exact values:
- First Name: "Test"
- Last Name: "Person"
- Title: "Dr."  
- Suffix: "PhD"

Then verify in the database that all four fields are saved with the correct values.

---

## Technical Details

The investigation revealed:
- PersonForm.get_form_data(): ✅ Correctly extracts all fields
- PersonData (API client): ✅ Includes all fields  
- PersonCreate (server schema): ✅ Validates all fields correctly
- Person (database model): ✅ Defines all columns properly
- create_person endpoint: ✅ Maps all fields correctly

The only issue is the missing database columns due to unapplied migration.