#!/bin/bash
# Test if the application can start successfully
# Usage: ./scripts/test_app_starts.sh [import|headless|syntax|full]

PYTHON=".direnv/python-3.12.3/bin/python"
TEST_TYPE="${1:-import}"

case "$TEST_TYPE" in
    "import")
        # Quick import test - fastest, no GUI
        echo "Testing imports..."
        $PYTHON -c "
import sys
try:
    from ui.workspace import Workspace
    from ui.main_window import MainWindow
    from services.workspace_service import WorkspaceService
    print('✅ Imports successful')
    sys.exit(0)
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
" 2>&1
        ;;

    "headless")
        # Headless GUI test - creates widgets without display
        echo "Testing headless startup..."
        QT_QPA_PLATFORM=offscreen $PYTHON -c "
import sys
try:
    from PySide6.QtWidgets import QApplication
    from ui.main_window import MainWindow
    app = QApplication(sys.argv)
    window = MainWindow()
    app.processEvents()
    print('✅ Headless startup OK')
    sys.exit(0)
except Exception as e:
    print(f'❌ Headless startup failed: {e}')
    sys.exit(1)
" 2>&1
        ;;

    "syntax")
        # Syntax check for a specific file
        FILE="${2:-ui/workspace.py}"
        echo "Checking syntax of $FILE..."
        $PYTHON -m py_compile "$FILE" && echo "✅ Syntax OK" || echo "❌ Syntax error"
        ;;

    "full")
        # Original full startup test with timeout
        echo "Testing full app startup..."
        timeout 3 $PYTHON main.py > /tmp/app_test.log 2>&1
        if [ $? -eq 124 ]; then
            # Timeout reached - app is running
            echo "✅ App started (timed out as expected)"
            pkill -f "python main.py" 2>/dev/null
            exit 0
        else
            # Check for errors in log
            if grep -q "Traceback\|Error" /tmp/app_test.log; then
                echo "❌ App crashed:"
                tail -5 /tmp/app_test.log
                exit 1
            else
                echo "✅ App started and exited"
                exit 0
            fi
        fi
        ;;

    *)
        echo "Usage: $0 [import|headless|syntax|full] [file]"
        echo "  import   - Test imports (fastest, default)"
        echo "  headless - Test headless GUI"
        echo "  syntax   - Check file syntax"
        echo "  full     - Full startup test"
        exit 1
        ;;
esac
