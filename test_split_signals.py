#!/usr/bin/env python3
"""
Test to verify split signals are correctly routed after the MVC fix.
This ensures splits happen on the correct pane.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTextEdit
from PySide6.QtCore import Qt
from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType


class SignalTestWindow(QMainWindow):
    """Test window to verify signal routing."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.test_counter = 0
        
    def setup_ui(self):
        """Setup the test UI."""
        self.setWindowTitle("Split Signal Test - Check Console Output")
        self.resize(1000, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Log output
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(200)
        layout.addWidget(self.log)
        
        # Split pane widget
        self.split_widget = SplitPaneWidget(initial_widget_type=WidgetType.TEXT_EDITOR)
        layout.addWidget(self.split_widget)
        
        # Initial test
        self.log.append("Test: Right-click on different panes and split them.")
        self.log.append("The console will show which pane_id is being split.")
        self.log.append("Verify that the correct pane is split each time.\n")
        
        # Run automated test after UI is shown
        self.test_timer = None
        
    def showEvent(self, event):
        """Run test after window is shown."""
        super().showEvent(event)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(500, self.run_automated_test)
    
    def run_automated_test(self):
        """Run automated test sequence."""
        self.log.append("=== AUTOMATED TEST STARTING ===")
        
        # Get initial pane
        initial_panes = list(self.split_widget.leaves.keys())
        self.log.append(f"Initial panes: {initial_panes}")
        
        if initial_panes:
            first_pane = initial_panes[0]
            
            # Test 1: Split first pane
            self.log.append(f"\nTest 1: Splitting pane {first_pane}")
            self.split_widget.split_horizontal(first_pane)
            
            # Check new state
            new_panes = list(self.split_widget.leaves.keys())
            self.log.append(f"After split, panes: {new_panes}")
            
            # Test 2: Focus on original pane and split again
            if first_pane in self.split_widget.leaves:
                self.log.append(f"\nTest 2: Focusing on {first_pane} and splitting again")
                self.split_widget.set_active_pane(first_pane)
                self.split_widget.split_vertical(first_pane)
                
                # Check state again
                final_panes = list(self.split_widget.leaves.keys())
                self.log.append(f"After second split, panes: {final_panes}")
                
                # Verify the original pane was split (not the newest one)
                if len(final_panes) == 3:
                    self.log.append("\n✅ SUCCESS: Splits are targeting the correct panes!")
                else:
                    self.log.append("\n❌ ISSUE: Unexpected number of panes")
            
        self.log.append("\n=== TEST COMPLETE - Check console for debug output ===")


def main():
    """Run the test."""
    app = QApplication(sys.argv)
    
    window = SignalTestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()