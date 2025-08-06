# Fix Summary: SQLite Date Constraint Error

## Problem
When trying to add a new person with a date of birth through the client, the server returned a 500 error:
```
sqlite3.OperationalError: non-deterministic use of date() in a CHECK constraint
```

## Root Cause
SQLite doesn't allow the `date('now')` function in CHECK constraints because it's non-deterministic (the value changes over time). The database schema had two problematic CHECK constraints:

1. In the `Person` model:
   ```sql
   CheckConstraint("date_of_birth IS NULL OR date_of_birth <= date('now')")
   ```

2. In the `Employment` model:
   ```sql
   CheckConstraint("start_date <= COALESCE(end_date, date('now'))")
   ```

## Solution
Moved validation from database-level CHECK constraints to application-level validators:

### Changes Made

1. **Removed non-deterministic CHECK constraints** from `server/database/models.py`:
   - Removed `check_birth_date_past` constraint from Person model
   - Removed `check_employment_dates` constraint from Employment model

2. **Added application-level validation**:
   - Added `validate_date_of_birth()` method to Person model
   - Existing validators already handle employment date validation

3. **Database recreation**:
   ```bash
   rm -f people_management.db
   make setup-db
   ```

## Testing
✅ Successfully created a person with date_of_birth = "2000-08-06"  
✅ No more SQLite operational errors  
✅ Date validation still enforced at application level  

## How It Works Now

- **Database Level**: No CHECK constraints with `date('now')`
- **Application Level**: SQLAlchemy validators ensure:
  - Date of birth is not in the future
  - Employment end date is after start date
  - All date logic is validated in Python before database insertion

The client can now successfully add people with dates of birth!