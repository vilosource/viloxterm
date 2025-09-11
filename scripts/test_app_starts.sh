#!/bin/bash
# Test if the application can start successfully
# Usage: ./scripts/test_app_starts.sh

# Launch app in background
.direnv/python-3.12.3/bin/python main.py &
APP_PID=$!

# Give it time to start
sleep 3

# Check if process is still running
if ps -p $APP_PID > /dev/null 2>&1; then
    echo "✅ App started successfully (PID: $APP_PID)"
    # Clean up
    kill $APP_PID 2>/dev/null
    wait $APP_PID 2>/dev/null
    exit 0
else
    echo "❌ App failed to start"
    exit 1
fi