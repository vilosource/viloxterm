#!/usr/bin/env python3
"""
Test script to verify Chrome mode command works.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QSettings
from ui.main_window import MainWindow

def test_chrome_command():
    """Test that Chrome mode command can be executed."""
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainWindow()
    window.show()
    
    # Wait a moment for window to initialize
    QTimer.singleShot(500, lambda: execute_command(window))
    
    # Auto-close after 2 seconds
    QTimer.singleShot(2000, app.quit)
    
    app.exec()

def execute_command(window):
    """Execute the Chrome mode command."""
    print("Testing Chrome mode command...")
    
    # Check current state
    settings = QSettings("ViloApp", "ViloApp")
    before = settings.value("UI/ChromeMode", False, type=bool)
    print(f"Chrome mode before: {before}")
    
    # Try to execute command
    result = window.execute_command("ui.toggleChromeMode")
    
    if result.success:
        print(f"✓ Command executed successfully: {result.value}")
        
        # Check new state
        after = settings.value("UI/ChromeMode", False, type=bool)
        print(f"Chrome mode after: {after}")
        
        if after != before:
            print("✓ Chrome mode was toggled successfully!")
        else:
            print("✗ Chrome mode state didn't change")
    else:
        print(f"✗ Command failed: {result.error}")
    
    # Close the app
    QApplication.quit()

if __name__ == "__main__":
    test_chrome_command()