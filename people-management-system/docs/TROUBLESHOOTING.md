# Troubleshooting Guide

This guide provides solutions to common issues encountered while developing, testing, or deploying the People Management System.

## Table of Contents

- [Critical Issues (RESOLVED)](#critical-issues-resolved)
- [Development Environment Issues](#development-environment-issues)
- [Database Issues](#database-issues)
- [API Issues](#api-issues)
- [Client Application Issues](#client-application-issues)
- [Testing Issues](#testing-issues)
- [Performance Issues](#performance-issues)
- [Deployment Issues](#deployment-issues)
- [Debugging Tips](#debugging-tips)

## Critical Issues (RESOLVED)

### Person Fields Not Saving to Database

**Status**: ✅ RESOLVED

**Symptoms**:
- Person form fields (First Name, Last Name, Title, Suffix) appear empty in database
- Fields show as None despite being entered in the form
- Data appears to be sent from client but not saved on server

**Root Cause**:
The server API was using `person_data.dict()` without exclusion parameters, causing Pydantic to include all Optional fields as None values, overwriting actual user input.

**Solution Applied**:
```python
# OLD (problematic):
person_dict = person_data.dict()

# NEW (fixed):
person_dict = person_data.dict(exclude_unset=True, exclude_none=True)
```

**Files Modified**:
- `/server/api/routes/people.py` - Lines 101, 404, 483, 548
- Added comprehensive debugging logs
- Enhanced schema validation

**Prevention**:
- Always use `exclude_unset=True` and `exclude_none=True` when converting Pydantic models
- Test all optional fields explicitly in test cases
- Add debug logging for critical data operations

**Verification**:
```bash
# Test the fix
python3 test_specific_fields.py

# Check database directly
python3 check_db_columns.py

# Run comprehensive tests
python3 test_all_fixes.py
```

### SQLite Date Constraint Error

**Status**: ✅ RESOLVED  

**Symptoms**:
- Server returns 500 error when creating person with date_of_birth
- Error: `sqlite3.OperationalError: non-deterministic use of date() in a CHECK constraint`

**Root Cause**:
SQLite doesn't allow non-deterministic functions like `date('now')` in CHECK constraints.

**Solution Applied**:
- Removed database-level CHECK constraints using `date('now')`
- Moved validation to application-level with SQLAlchemy validators
- Recreated database to apply changes

**Prevention**:
- Use application-level validation for dynamic constraints
- Avoid non-deterministic functions in database constraints
- Test database operations with realistic data

## Development Environment Issues

### UV Installation Problems

**Symptoms**:
- `uv: command not found`
- Installation fails with permission errors
- PATH issues after installation

**Solutions**:

1. **Manual Installation**:
```bash
# If automatic installation fails
pip install uv

# Add to PATH (Linux/macOS)
export PATH="$HOME/.cargo/bin:$PATH"
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Windows PowerShell
$env:PATH += ";$env:USERPROFILE\.cargo\bin"
```

2. **Permission Issues**:
```bash
# Linux/macOS - ensure proper permissions
sudo chown -R $(whoami) ~/.cargo
```

3. **Verification**:
```bash
uv --version
which uv
```

### Virtual Environment Issues

**Symptoms**:
- Import errors for installed packages
- Packages not found despite installation
- Environment corruption

**Solutions**:

1. **Recreate Environment**:
```bash
# Remove corrupted environment
rm -rf .venv

# Recreate with UV
uv sync

# Verify Python interpreter
which python
python --version
```

2. **Sync Issues**:
```bash
# Force refresh dependencies
uv sync --refresh

# Clear UV cache if needed
uv cache clean
```

3. **Path Issues**:
```bash
# Ensure correct Python interpreter
uv run python --version
uv run which python
```

### Pre-commit Hook Issues

**Symptoms**:
- Pre-commit hooks fail to run
- Formatting/linting errors preventing commits
- Hook installation errors

**Solutions**:

1. **Reinstall Hooks**:
```bash
uv run pre-commit uninstall
uv run pre-commit install
```

2. **Run Hooks Manually**:
```bash
# Run all hooks
uv run pre-commit run --all-files

# Run specific hook
uv run pre-commit run black --all-files
```

3. **Skip Hooks Temporarily** (for emergency commits):
```bash
git commit --no-verify -m "Emergency commit"
```

## Database Issues

### Database Locked Error

**Symptoms**:
- `database is locked` error
- Cannot access database file
- Operations hang indefinitely

**Solutions**:

1. **Find and Kill Processes**:
```bash
# Linux/macOS
lsof | grep people_management.db
kill -9 <process_id>

# Or force kill all Python processes
pkill -f python
```

2. **Check File Permissions**:
```bash
ls -la people_management.db*
chmod 664 people_management.db*
```

3. **Reset Database** (WARNING: loses data):
```bash
rm -f people_management.db*
make setup-db
```

### Migration Issues

**Symptoms**:
- Migration fails with constraint errors
- Multiple migration heads
- Database schema out of sync

**Solutions**:

1. **Multiple Heads**:
```bash
# Check heads
uv run alembic heads

# Merge conflicting migrations
uv run alembic merge -m "merge conflicts" head1 head2
uv run alembic upgrade head
```

2. **Failed Migration**:
```bash
# Downgrade to previous version
uv run alembic downgrade -1

# Or reset to base (loses data)
uv run alembic downgrade base
uv run alembic upgrade head
```

3. **Schema Sync Issues**:
```bash
# Generate new migration to sync
uv run alembic revision --autogenerate -m "sync schema"
uv run alembic upgrade head
```

### Database Connection Issues

**Symptoms**:
- Connection timeouts
- Too many connections error
- Connection pool exhausted

**Solutions**:

1. **Check Connection Pool**:
```python
# In server/database/db.py
engine = create_engine(
    DATABASE_URL,
    pool_size=10,        # Increase if needed
    max_overflow=20,     # Increase if needed
    pool_timeout=30,     # Connection timeout
    pool_recycle=3600    # Recycle connections
)
```

2. **Verify Database File**:
```bash
# Check database integrity
sqlite3 people_management.db "PRAGMA integrity_check;"

# Check schema
sqlite3 people_management.db ".schema"
```

## API Issues

### Server Won't Start

**Symptoms**:
- Port already in use error
- Import errors on startup
- Configuration errors

**Solutions**:

1. **Port Issues**:
```bash
# Find process using port 8000
lsof -i :8000
kill -9 <process_id>

# Or use different port
uv run uvicorn server.main:app --port 8001
```

2. **Import Errors**:
```bash
# Check Python path
uv run python -c "import sys; print(sys.path)"

# Verify all dependencies
uv run python -c "from server.main import app"
```

3. **Configuration Issues**:
```bash
# Check environment variables
env | grep -i log

# Run with debug logging
LOG_LEVEL=DEBUG make run-server
```

### API Key Authentication Issues

**Symptoms**:
- 401 Unauthorized errors
- API key not recognized
- Authentication bypass not working

**Solutions**:

1. **Check API Keys**:
```bash
# View available keys
python3 show_api_keys.py

# Generate new key if needed
python3 generate_api_key.py
```

2. **Test Authentication**:
```bash
# Test without auth (should work for most endpoints)
curl http://localhost:8000/api/v1/people

# Test with auth
curl -H "Authorization: Bearer your-key" http://localhost:8000/api/v1/people
```

3. **Debug Auth Issues**:
```python
# In server logs, look for:
# - "API key validation"
# - "Authentication bypass"
# - "Invalid API key"
```

### 500 Internal Server Errors

**Symptoms**:
- Server returns 500 for valid requests
- Generic error messages
- Stack traces in logs

**Common Causes and Solutions**:

1. **Pydantic Validation Issues**:
```python
# Check for proper exclusion parameters
data = model.dict(exclude_unset=True, exclude_none=True)
```

2. **Database Constraint Violations**:
```bash
# Check server logs for specific constraints
# Look for "UNIQUE constraint failed" or similar
```

3. **Import or Configuration Errors**:
```bash
# Test imports manually
uv run python -c "from server.api.routes.people import router"
```

## Client Application Issues

### GUI Won't Start

**Symptoms**:
- Qt initialization errors
- Display/graphics issues
- Import errors for PySide6

**Solutions**:

1. **Qt Environment Issues**:
```bash
# For headless environments
export QT_QPA_PLATFORM=offscreen

# For display issues
export QT_QPA_PLATFORM=xcb  # Linux
export QT_QPA_PLATFORM=cocoa  # macOS
```

2. **PySide6 Issues**:
```bash
# Reinstall PySide6
uv add --dev pyside6

# Check Qt installation
uv run python -c "from PySide6.QtWidgets import QApplication"
```

3. **Graphics Driver Issues**:
```bash
# Software rendering fallback
export QT_QUICK_BACKEND=software
```

### Connection to API Server

**Symptoms**:
- Cannot connect to server
- API endpoints not reachable
- Network timeout errors

**Solutions**:

1. **Check Server Status**:
```bash
# Verify server is running
curl http://localhost:8000/health

# Check server logs for errors
```

2. **Network Configuration**:
```python
# In client configuration, verify:
base_url = "http://localhost:8000"  # Correct port
timeout = 30  # Adequate timeout
```

3. **Firewall/Proxy Issues**:
```bash
# Test direct connection
telnet localhost 8000

# Check proxy settings
echo $HTTP_PROXY
echo $HTTPS_PROXY
```

### Data Not Displaying

**Symptoms**:
- Empty lists in GUI
- Data appears in API but not in client
- UI components not refreshing

**Solutions**:

1. **Check API Data Format**:
```bash
# Test API directly
curl http://localhost:8000/api/v1/people | jq
```

2. **Debug Client Data Handling**:
```python
# Add logging to client services
logger.debug(f"API response: {response.json()}")
```

3. **UI Refresh Issues**:
```python
# Force model refresh
self.model.refresh()
self.table_view.reset()
```

## Testing Issues

### Qt Test Failures

**Symptoms**:
- Tests fail with display errors
- Cannot create QApplication
- GUI tests time out

**Solutions**:

1. **Headless Testing**:
```bash
# Set platform before running tests
export QT_QPA_PLATFORM=offscreen
make test
```

2. **Test Isolation**:
```python
# Ensure proper test cleanup
@pytest.fixture
def qtapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    yield app
    app.quit()
```

3. **Virtual Display** (Linux):
```bash
# Install xvfb
sudo apt-get install xvfb

# Run tests with virtual display
xvfb-run -a make test
```

### Database Test Issues

**Symptoms**:
- Tests interfere with each other
- Database state persists between tests
- Foreign key constraint errors

**Solutions**:

1. **Test Database Isolation**:
```python
@pytest.fixture
def test_db():
    # Use in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    # ... rest of fixture
```

2. **Transaction Rollback**:
```python
@pytest.fixture
def db_session():
    with session.begin() as transaction:
        yield session
        transaction.rollback()
```

### Coverage Report Issues

**Symptoms**:
- Inaccurate coverage reports
- Missing coverage data
- Coverage files corrupted

**Solutions**:

1. **Clean Coverage Data**:
```bash
rm -rf .coverage htmlcov/
make test-coverage
```

2. **Fix Coverage Paths**:
```bash
# Check coverage configuration
uv run coverage report --show-missing
```

## Performance Issues

### Slow API Responses

**Symptoms**:
- API responses take several seconds
- Database queries are slow
- Client UI becomes unresponsive

**Solutions**:

1. **Database Optimization**:
```python
# Add indexes for frequently queried fields
class Person(Base):
    email = Column(String, unique=True, index=True)  # Add index
    last_name = Column(String, index=True)  # Add index
```

2. **Query Optimization**:
```python
# Use eager loading
people = session.query(Person).options(joinedload(Person.employments)).all()

# Add pagination
query = query.offset(offset).limit(limit)
```

3. **Connection Pool Tuning**:
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

### Memory Leaks

**Symptoms**:
- Application memory usage grows over time
- System becomes sluggish
- Out of memory errors

**Solutions**:

1. **Database Session Management**:
```python
# Always close sessions
try:
    session = SessionLocal()
    # ... operations
finally:
    session.close()

# Or use context manager
with SessionLocal() as session:
    # ... operations
```

2. **Qt Object Management**:
```python
# Proper widget cleanup
def closeEvent(self, event):
    self.cleanup_widgets()
    super().closeEvent(event)
```

3. **Monitor Memory Usage**:
```bash
# Check memory usage
ps aux | grep python
top -p $(pgrep python)
```

## Deployment Issues

### Environment Configuration

**Symptoms**:
- Application behaves differently in production
- Configuration not loading
- Missing environment variables

**Solutions**:

1. **Environment Variables**:
```bash
# Check environment
env | grep -E "(DATABASE|API|LOG)"

# Set production variables
export DATABASE_URL="postgresql://..."
export LOG_LEVEL="INFO"
export API_KEY_REQUIRED="true"
```

2. **Configuration Validation**:
```python
# Add configuration validation
from server.core.config import settings
print(f"Database: {settings.DATABASE_URL}")
print(f"Log Level: {settings.LOG_LEVEL}")
```

### Service Dependencies

**Symptoms**:
- Services fail to start
- Dependency conflicts
- Version mismatches

**Solutions**:

1. **Dependency Verification**:
```bash
# Check installed packages
uv tree

# Verify specific versions
uv run python -c "import fastapi; print(fastapi.__version__)"
```

2. **Lock File Issues**:
```bash
# Regenerate lock file
rm uv.lock
uv sync
```

## Debugging Tips

### Enable Debug Logging

```bash
# Server debug logging
LOG_LEVEL=DEBUG make run-server

# Client debug logging
export LOG_LEVEL=DEBUG
make run-client
```

### Database Inspection

```bash
# Connect to database
sqlite3 people_management.db

# Common inspection commands
.tables
.schema people
SELECT * FROM people LIMIT 5;
PRAGMA table_info(people);
```

### API Testing

```bash
# Test API endpoints
curl -v http://localhost:8000/api/v1/people
curl -X POST -H "Content-Type: application/json" \
  -d '{"first_name":"Test","last_name":"User","email":"test@example.com"}' \
  http://localhost:8000/api/v1/people
```

### Process Monitoring

```bash
# Find running processes
ps aux | grep -E "(uvicorn|python.*client)"

# Monitor resource usage
top -p $(pgrep -f "uvicorn\|python.*client")

# Check open files
lsof -p <process_id>
```

### Network Debugging

```bash
# Check port availability
netstat -tlnp | grep :8000

# Test network connectivity
telnet localhost 8000

# Monitor network traffic
sudo netstat -i
```

### Log Analysis

```bash
# Follow server logs
tail -f server.log

# Search for errors
grep -i error server.log
grep -B5 -A5 "500" server.log

# Analyze patterns
awk '/ERROR/ {print $1, $2, $5}' server.log | sort | uniq -c
```

## Getting Help

When encountering issues not covered in this guide:

1. **Check Recent Changes**: Review git log for recent modifications
2. **Search Issues**: Look for similar problems in project issues
3. **Enable Debug Logging**: Increase log verbosity for more details
4. **Isolate the Problem**: Create minimal reproduction case
5. **Document the Issue**: Include environment details, steps to reproduce, expected vs actual behavior

### Information to Include in Bug Reports

- Operating system and version
- Python version (`python --version`)
- UV version (`uv --version`)
- Package versions (`uv tree`)
- Complete error messages and stack traces
- Steps to reproduce the issue
- Expected vs actual behavior
- Relevant log files

---

This troubleshooting guide is updated based on real issues encountered during development. Keep it current as new issues are discovered and resolved.