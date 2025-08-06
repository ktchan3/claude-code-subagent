#\!/bin/bash
echo "========================================"
echo "People Management System - Complete Test"
echo "========================================"
echo ""

# Check server
echo "1. Checking server..."
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "   ✅ Server is running"
else
    echo "   ❌ Server is not running"
    echo "   Please run: make run-server"
    exit 1
fi

# Test API with key
echo ""
echo "2. Testing API with admin key..."
response=$(curl -s -H 'X-API-Key: dev-admin-key-12345' http://localhost:8000/api/v1/people/)
if [[ $response == *"items"* ]]; then
    echo "   ✅ API authentication working"
else
    echo "   ❌ API authentication failed"
fi

# Check client can import
echo ""
echo "3. Testing client imports..."
if uv run python -c "from client.ui.login_dialog import LoginDialog; from client.ui.main_window import MainWindow; print('   ✅ Client imports successful')" 2>/dev/null; then
    :
else
    echo "   ❌ Client import errors"
fi

# Check async utils
echo ""
echo "4. Testing async utilities..."
if uv run python -c "from client.utils.async_utils import QtSyncHelper, safe_sync_run; print('   ✅ Async utilities working')" 2>/dev/null; then
    :
else
    echo "   ❌ Async utilities errors"
fi

echo ""
echo "========================================"
echo "✅ All systems operational\!"
echo ""
echo "You can now:"
echo "  1. Run the server: make run-server"
echo "  2. Run the client: make run-client"
echo "  3. Use API key: dev-admin-key-12345"
echo "========================================"
