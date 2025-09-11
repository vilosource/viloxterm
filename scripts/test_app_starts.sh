#!/bin/bash
# Test if the application can start successfully
# Usage: ./scripts/test_app_starts.sh

# Launch app in background
.direnv/python-3.12.3/bin/python main.py &
APP_PID=$!

# Give it time to start
sleep 5

# Check if process is still running
if ps -p $APP_PID > /dev/null 2>&1; then
    echo "✅ App started successfully (PID: $APP_PID)"
    # Clean up - try graceful kill first, then force kill
    kill $APP_PID 2>/dev/null
    sleep 1
    
    # If still running, force kill
    if ps -p $APP_PID > /dev/null 2>&1; then
        echo "Process didn't terminate gracefully, force killing..."
        kill -9 $APP_PID 2>/dev/null
    fi
    
    # Also kill any child processes
    pkill -P $APP_PID 2>/dev/null
    
    wait $APP_PID 2>/dev/null
    exit 0
else
    echo "❌ App failed to start"
    exit 1
fi
