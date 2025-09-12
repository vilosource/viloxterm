#!/usr/bin/env python3
"""
Test script to verify Chrome mode components work correctly.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QTimer

def test_chrome_components():
    """Test that Chrome mode components can be imported and instantiated."""
    print("Testing Chrome mode components...")
    
    # Test imports
    try:
        from ui.widgets.window_controls import WindowControls
        print("✓ WindowControls imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import WindowControls: {e}")
        return False
    
    try:
        from ui.widgets.chrome_title_bar import ChromeTitleBar
        print("✓ ChromeTitleBar imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ChromeTitleBar: {e}")
        return False
    
    try:
        from ui.chrome_main_window import ChromeMainWindow
        print("✓ ChromeMainWindow imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import ChromeMainWindow: {e}")
        return False
    
    # Test instantiation
    app = QApplication(sys.argv)
    
    try:
        # Test window controls
        controls = WindowControls()
        print("✓ WindowControls instantiated successfully")
        
        # Test title bar
        title_bar = ChromeTitleBar()
        print("✓ ChromeTitleBar instantiated successfully")
        
        # Test Chrome mode setting
        settings = QSettings("ViloApp", "ViloApp")
        current_mode = settings.value("UI/ChromeMode", False, type=bool)
        print(f"  Chrome mode is currently: {'ENABLED' if current_mode else 'DISABLED'}")
        
        # Test enabling Chrome mode
        print("\nTo enable Chrome mode:")
        print("  1. Run the application: python main.py")
        print("  2. Go to View menu > Enable Chrome-Style Tabs")
        print("  3. Restart the application")
        print("\nOr run: python -c \"from PySide6.QtCore import QSettings; s = QSettings('ViloApp', 'ViloApp'); s.setValue('UI/ChromeMode', True); print('Chrome mode enabled')\"")
        
        return True
        
    except Exception as e:
        print(f"✗ Error during instantiation: {e}")
        return False
    finally:
        app.quit()

if __name__ == "__main__":
    success = test_chrome_components()
    sys.exit(0 if success else 1)