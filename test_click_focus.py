#!/usr/bin/env python3
"""
Test that clicking on AppWidget content properly updates focus.
This tests the core issue: web view consuming mouse events.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QTimer
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType


class ClickFocusTest(QMainWindow):
    """Test clicking to focus panes."""
    
    def __init__(self):
        super().__init__()
        self.test_sequence = []
        self.current_step = 0
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the test UI."""
        self.setWindowTitle("Click Focus Test")
        self.resize(1000, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Status and instructions
        self.status_label = QLabel("Click Focus Test - Follow instructions below")
        layout.addWidget(self.status_label)
        
        self.instruction_label = QLabel("Loading...")
        layout.addWidget(self.instruction_label)
        
        # Control buttons
        controls = QHBoxLayout()
        
        next_btn = QPushButton("Next Step")
        next_btn.clicked.connect(self.next_step)
        controls.addWidget(next_btn)
        
        test_split_btn = QPushButton("Test Keyboard Split (Ctrl+\\)")
        test_split_btn.clicked.connect(self.test_keyboard_split)
        controls.addWidget(test_split_btn)
        
        layout.addLayout(controls)
        
        # Split pane widget with terminals
        self.split_widget = SplitPaneWidget(WidgetType.TERMINAL)
        self.split_widget.active_pane_changed.connect(self.on_active_changed)
        
        layout.addWidget(self.split_widget)
        
        # Set up test sequence
        self.setup_test_sequence()
        self.show_current_step()
        
    def setup_test_sequence(self):
        """Set up the test sequence."""
        self.test_sequence = [
            "Step 1: Starting with single terminal pane",
            "Step 2: Click 'Next Step' to split horizontally", 
            "Step 3: Now you should see LEFT and RIGHT terminal panes",
            "Step 4: Click INSIDE the RIGHT terminal (the web content area)",
            "Step 5: Click 'Test Keyboard Split' - it should split the RIGHT pane",
            "Step 6: Test complete! Check if the split happened on the correct pane"
        ]
        
    def show_current_step(self):
        """Show the current test step."""
        if self.current_step < len(self.test_sequence):
            instruction = self.test_sequence[self.current_step]
            self.instruction_label.setText(instruction)
            
            active_pane = self.split_widget.active_pane_id
            pane_count = self.split_widget.get_pane_count()
            
            status = f"Active Pane: {active_pane} | Total Panes: {pane_count} | Step: {self.current_step + 1}/{len(self.test_sequence)}"
            self.status_label.setText(status)
            
    def next_step(self):
        """Move to next test step."""
        self.current_step += 1
        
        # Perform actions for specific steps
        if self.current_step == 2:  # Step 2: Split horizontally
            print("🔄 Creating horizontal split")
            initial_pane = self.split_widget.active_pane_id
            self.split_widget.split_horizontal(initial_pane)
            print(f"✅ Split created. Active pane: {self.split_widget.active_pane_id}")
            print(f"📋 All panes: {self.split_widget.get_all_pane_ids()}")
            
        self.show_current_step()
        
    def test_keyboard_split(self):
        """Test the keyboard split functionality."""
        active_before = self.split_widget.active_pane_id
        panes_before = self.split_widget.get_all_pane_ids()
        
        print(f"\n🧪 TESTING KEYBOARD SPLIT")
        print(f"📍 Active pane before: {active_before}")
        print(f"📋 All panes before: {panes_before}")
        
        # Simulate keyboard shortcut (vertical split)
        if self.split_widget and active_before:
            self.split_widget.split_vertical(active_before)
            
        active_after = self.split_widget.active_pane_id  
        panes_after = self.split_widget.get_all_pane_ids()
        
        print(f"📍 Active pane after: {active_after}")
        print(f"📋 All panes after: {panes_after}")
        
        # Check if the correct pane was split
        if len(panes_after) == len(panes_before) + 1:
            print(f"✅ Split successful! New pane created.")
            
            # Find which pane was split (should be active_before)
            new_panes = [p for p in panes_after if p not in panes_before]
            if new_panes:
                print(f"🆕 New pane ID: {new_panes[0]}")
                if len(panes_before) == 2:
                    # If we had LEFT and RIGHT, and split RIGHT, we should have LEFT, RIGHT_TOP, RIGHT_BOTTOM
                    print("🎯 Check visually: Did the RIGHT pane split into TOP/BOTTOM?")
        else:
            print(f"❌ Split failed or unexpected result")
            
        self.show_current_step()
        
    def on_active_changed(self, pane_id):
        """Handle active pane changes."""
        print(f"🎯 ACTIVE PANE CHANGED TO: {pane_id}")
        self.show_current_step()


def main():
    """Run the click focus test."""
    app = QApplication(sys.argv)
    
    test_window = ClickFocusTest()
    test_window.show()
    
    print("🧪 Click Focus Test Started")
    print("📋 This test verifies that clicking on terminal content updates the active pane")
    print("🎯 The key test: After clicking inside RIGHT terminal, keyboard split should split the RIGHT pane")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()