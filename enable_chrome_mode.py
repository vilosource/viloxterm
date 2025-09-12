#!/usr/bin/env python3
"""
Script to enable Chrome mode for testing.
"""

from PySide6.QtCore import QSettings
import sys

def enable_chrome_mode():
    """Enable Chrome mode in settings."""
    settings = QSettings("ViloApp", "ViloApp")
    settings.setValue("UI/ChromeMode", True)
    settings.sync()
    print("✓ Chrome mode ENABLED")
    print("\nNow run the application with: python main.py")
    print("The app will start with Chrome-style tabs in the title bar.")

def disable_chrome_mode():
    """Disable Chrome mode in settings."""
    settings = QSettings("ViloApp", "ViloApp")
    settings.setValue("UI/ChromeMode", False)
    settings.sync()
    print("✓ Chrome mode DISABLED")
    print("\nNow run the application with: python main.py")
    print("The app will start with traditional UI.")

def check_chrome_mode():
    """Check current Chrome mode status."""
    settings = QSettings("ViloApp", "ViloApp")
    current = settings.value("UI/ChromeMode", False, type=bool)
    if current:
        print("Chrome mode is currently: ENABLED ✓")
    else:
        print("Chrome mode is currently: DISABLED")
    return current

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "enable":
            enable_chrome_mode()
        elif sys.argv[1] == "disable":
            disable_chrome_mode()
        elif sys.argv[1] == "check":
            check_chrome_mode()
        else:
            print("Usage: python enable_chrome_mode.py [enable|disable|check]")
    else:
        # Default: check status
        current = check_chrome_mode()
        print("\nTo change Chrome mode:")
        print("  Enable:  python enable_chrome_mode.py enable")
        print("  Disable: python enable_chrome_mode.py disable")