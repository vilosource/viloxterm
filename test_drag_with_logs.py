#!/usr/bin/env python3
"""
Test Chrome dragging with detailed logging.
Run this and try to drag the window to see debug logs.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Ensure Chrome mode is enabled
settings = QSettings("ViloApp", "ViloApp")
settings.setValue("UI/ChromeMode", True)
print("=" * 60)
print("Chrome Mode Dragging Test")
print("=" * 60)
print("✓ Chrome mode enabled")
print("\nTry to drag the window by:")
print("1. Click and hold in the empty space to the right of tabs")
print("2. Click and hold in the space before the window controls")
print("3. Watch the console for debug logs")
print("\nLogs will show:")
print("  - What widget you clicked on")
print("  - Whether it's draggable")
print("  - When dragging starts/moves/ends")
print("=" * 60)
print("\nStarting application...\n")

# Import after logging is set up
from ui.chrome_main_window import ChromeMainWindow

def main():
    app = QApplication(sys.argv)
    
    # Create Chrome window
    window = ChromeMainWindow()
    window.setWindowTitle("Chrome Dragging Test - Try dragging the title bar!")
    window.resize(900, 600)
    window.show()
    
    # Make sure it's not maximized
    if window.isMaximized():
        window.showNormal()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()