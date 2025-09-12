#!/usr/bin/env python3
"""
Test script for Chrome mode window dragging.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QSettings, QPoint
from ui.chrome_main_window import ChromeMainWindow

def test_chrome_dragging():
    """Test Chrome window dragging functionality."""
    app = QApplication(sys.argv)
    
    # Enable Chrome mode
    settings = QSettings("ViloApp", "ViloApp") 
    settings.setValue("UI/ChromeMode", True)
    
    # Create Chrome window
    window = ChromeMainWindow()
    window.resize(800, 600)
    window.show()
    
    # Make sure it's not maximized for testing
    if window.isMaximized():
        window.showNormal()
    
    print("Chrome Window Dragging Test")
    print("=" * 40)
    print("✓ Chrome window created")
    print(f"✓ Chrome mode enabled: {window.chrome_mode_enabled}")
    print(f"✓ Has Chrome title bar: {hasattr(window, 'chrome_title_bar')}")
    
    if hasattr(window, 'chrome_title_bar'):
        title_bar = window.chrome_title_bar
        
        # Check draggable areas
        print("\nDraggable Areas Test:")
        
        # Test various points
        test_points = [
            (100, 15, "Empty space in title bar"),
            (400, 15, "Middle of title bar"),
            (title_bar.width() - 200, 15, "Before window controls"),
        ]
        
        for x, y, description in test_points:
            point = QPoint(x, y)
            child = title_bar.childAt(point)
            is_draggable = title_bar._is_draggable_widget(child)
            
            widget_type = "None" if child is None else child.__class__.__name__
            status = "✓ Draggable" if is_draggable else "✗ Not draggable"
            
            print(f"  {status}: {description} (widget: {widget_type})")
        
        # Test window movement
        print("\nWindow Movement Test:")
        initial_pos = window.pos()
        print(f"  Initial position: ({initial_pos.x()}, {initial_pos.y()})")
        
        # Simulate a drag
        diff = QPoint(50, 30)
        window.move_window(diff)
        
        new_pos = window.pos()
        print(f"  After move by (50, 30): ({new_pos.x()}, {new_pos.y()})")
        
        if new_pos != initial_pos:
            print("  ✓ Window movement works!")
        else:
            print("  ✗ Window didn't move")
        
        print("\nInstructions for Manual Testing:")
        print("1. Click and drag on empty areas of the title bar")
        print("2. The window should move with your mouse")
        print("3. Double-click empty title bar area to maximize/restore")
        print("4. Tabs and buttons should NOT trigger dragging")
        print("\nWindow will close automatically in 10 seconds...")
    
    # Close after 10 seconds
    QTimer.singleShot(10000, app.quit)
    
    app.exec()

if __name__ == "__main__":
    test_chrome_dragging()