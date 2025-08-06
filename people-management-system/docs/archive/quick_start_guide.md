# People Management System - Quick Start Guide

## Starting the System

### 1. Start the Server
```bash
make run-server
```
The server will start on `http://localhost:8000`

### 2. Start the Client
```bash
make run-client
```

### 3. Login with API Key
When the login dialog appears, enter:
- **Server URL:** `http://localhost:8000`
- **API Key:** `dev-admin-key-12345`

Click "Connect" to access the application.

## Available API Keys

### Admin Key (Full Access)
- **Key:** `dev-admin-key-12345`
- **Permissions:** read, write, admin

### Read-Only Key
- **Key:** `dev-readonly-key-67890`
- **Permissions:** read only

## Features

Once connected, you can:
- **Dashboard:** View system statistics
- **People:** Manage personal information
- **Departments:** Organize departments
- **Positions:** Define job positions
- **Employment:** Track employment records

## Testing Tools

### Show API Keys
```bash
uv run python show_api_keys.py
```

### Test API Connection
```bash
uv run python test_api_key.py
```

### Generate New API Keys
```bash
uv run python generate_api_key.py
```

## Troubleshooting

If you encounter issues:

1. **Server not running?**
   - Check if port 8000 is available
   - Verify database is initialized: `make setup-db`

2. **Client connection issues?**
   - Verify server is running
   - Check API key is correct
   - Ensure URL includes protocol: `http://localhost:8000`

3. **Database issues?**
   - Reset database: `rm people_management.db && make setup-db`

## All Issues Fixed ✅

The following issues have been resolved:
- ✅ UUID import errors
- ✅ Pydantic v2 migration
- ✅ SQLite cursor context manager
- ✅ Client async/event loop errors
- ✅ API endpoint redirects
- ✅ Connection indicator UI errors
- ✅ Import errors (QtAsyncHelper → QtSyncHelper)

The system is now fully operational!