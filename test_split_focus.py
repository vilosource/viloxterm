#!/usr/bin/env python3
"""
Test script to verify split pane focus behavior.
Tests that splits happen on the focused pane, not always the last one.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType
from ui.terminal.terminal_factory import register_terminal_widget


class TestWindow(QMainWindow):
    """Test window for split focus behavior."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the test UI."""
        self.setWindowTitle("Split Focus Test")
        self.resize(1000, 700)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Instructions
        instructions = QLabel(
            "Instructions:\n"
            "1. Right-click on any pane and split it\n"
            "2. Click on a different pane to focus it (border turns blue)\n"
            "3. Split the focused pane\n"
            "4. Verify the split happens on the focused pane, not the last created one\n"
            "\nEach pane shows its ID. The focused pane has a blue border."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        split_h_btn = QPushButton("Split Active Horizontally")
        split_h_btn.clicked.connect(self.split_active_horizontal)
        button_layout.addWidget(split_h_btn)
        
        split_v_btn = QPushButton("Split Active Vertically")
        split_v_btn.clicked.connect(self.split_active_vertical)
        button_layout.addWidget(split_v_btn)
        
        status_btn = QPushButton("Show Active Pane")
        status_btn.clicked.connect(self.show_active_pane)
        button_layout.addWidget(status_btn)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Active pane: none")
        layout.addWidget(self.status_label)
        
        # Split pane widget
        self.split_widget = SplitPaneWidget(initial_widget_type=WidgetType.TEXT_EDITOR)
        self.split_widget.active_pane_changed.connect(self.on_active_pane_changed)
        layout.addWidget(self.split_widget)
        
    def on_active_pane_changed(self, pane_id: str):
        """Handle active pane change."""
        self.status_label.setText(f"Active pane: {pane_id}")
        print(f"Active pane changed to: {pane_id}")
    
    def split_active_horizontal(self):
        """Split the active pane horizontally."""
        if self.split_widget.active_pane_id:
            print(f"Splitting active pane {self.split_widget.active_pane_id} horizontally")
            self.split_widget.split_horizontal(self.split_widget.active_pane_id)
    
    def split_active_vertical(self):
        """Split the active pane vertically."""
        if self.split_widget.active_pane_id:
            print(f"Splitting active pane {self.split_widget.active_pane_id} vertically")
            self.split_widget.split_vertical(self.split_widget.active_pane_id)
    
    def show_active_pane(self):
        """Show which pane is active."""
        active = self.split_widget.active_pane_id
        print(f"Currently active pane: {active}")
        self.status_label.setText(f"Active pane: {active}")


def main():
    """Run the test."""
    app = QApplication(sys.argv)
    
    # Register terminal widget (in case we want to test with terminals)
    try:
        register_terminal_widget()
    except:
        pass
    
    # Create test window
    window = TestWindow()
    window.show()
    
    # Run app
    sys.exit(app.exec())


if __name__ == "__main__":
    main()