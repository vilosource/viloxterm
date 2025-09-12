#!/usr/bin/env python3
"""
Test Chrome dragging after fix - the window should now follow your mouse properly.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication, QLabel
from PySide6.QtCore import QSettings, QTimer

# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,  # Changed to INFO to reduce noise
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Ensure Chrome mode is enabled
settings = QSettings("ViloApp", "ViloApp")
settings.setValue("UI/ChromeMode", True)

print("=" * 60)
print("Chrome Window Dragging Test - FIXED VERSION")
print("=" * 60)
print("✓ Chrome mode enabled")
print("\n🎯 HOW TO TEST DRAGGING:")
print("-" * 40)
print("1. Click and hold in the SPACER AREA between:")
print("   • The '+' button and the minimize button")
print("   • Or any empty gray space in the title bar")
print("\n2. While holding, MOVE YOUR MOUSE")
print("   • The window should follow your mouse smoothly")
print("\n3. Release to stop dragging")
print("\n📝 WHAT TO EXPECT:")
print("-" * 40)
print("• The window should move WITH your mouse")
print("• Movement should be smooth and responsive")
print("• The window stays where you drop it")
print("\n⚠️ NOTES:")
print("-" * 40)
print("• Window must NOT be maximized (click restore first)")
print("• Clicking on tabs or buttons won't drag")
print("• Look for 'DRAG STARTED' and 'WINDOW MOVED' in logs")
print("=" * 60)
print("\nStarting application...\n")

# Import after logging is set up
from ui.chrome_main_window import ChromeMainWindow

def main():
    app = QApplication(sys.argv)
    
    # Create Chrome window
    window = ChromeMainWindow()
    window.setWindowTitle("Chrome Dragging Test - FIXED - Drag the title bar!")
    window.resize(900, 600)
    window.show()
    
    # Make sure it's not maximized
    if window.isMaximized():
        window.showNormal()
        print("ℹ️ Window was maximized - restored to normal state for testing")
    
    # Add a helpful label to the window
    if hasattr(window, 'workspace'):
        try:
            current_widget = window.workspace.get_current_split_widget()
            if current_widget:
                # Get the first widget in the workspace
                panes = current_widget.get_all_pane_ids()
                if panes:
                    widget = current_widget.get_pane_widget(panes[0])
                    if hasattr(widget, 'setPlainText'):
                        widget.setPlainText(
                            "🎯 DRAGGING TEST\n\n"
                            "Try dragging the window by:\n"
                            "1. Click and hold in the empty space before the window controls\n"
                            "2. Move your mouse - the window should follow!\n"
                            "3. Release to stop dragging\n\n"
                            "The spacer area (gray space) before the minimize button is the best spot to test."
                        )
        except:
            pass
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()