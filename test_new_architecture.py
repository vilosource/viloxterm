#!/usr/bin/env python3
"""
Test script for the new split pane architecture.
Tests the key requirements:
1. Splits target the correct pane
2. Terminal sessions are properly cleaned up
3. No flashing on refresh
4. Proper MVC separation
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import Qt

from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType
from ui.terminal.terminal_server import terminal_server


class TestWindow(QMainWindow):
    """Test window for the new architecture."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the test UI."""
        self.setWindowTitle("New Architecture Test")
        self.resize(1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Status display
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)
        
        # Control buttons
        controls = QHBoxLayout()
        
        # Split buttons
        split_h_btn = QPushButton("Split Active Horizontal")
        split_h_btn.clicked.connect(self.split_horizontal)
        controls.addWidget(split_h_btn)
        
        split_v_btn = QPushButton("Split Active Vertical")
        split_v_btn.clicked.connect(self.split_vertical)
        controls.addWidget(split_v_btn)
        
        # Close button
        close_btn = QPushButton("Close Active Pane")
        close_btn.clicked.connect(self.close_pane)
        controls.addWidget(close_btn)
        
        # Type change buttons
        terminal_btn = QPushButton("Change to Terminal")
        terminal_btn.clicked.connect(lambda: self.change_type(WidgetType.TERMINAL))
        controls.addWidget(terminal_btn)
        
        editor_btn = QPushButton("Change to Editor")
        editor_btn.clicked.connect(lambda: self.change_type(WidgetType.TEXT_EDITOR))
        controls.addWidget(editor_btn)
        
        # Info button
        info_btn = QPushButton("Show Info")
        info_btn.clicked.connect(self.show_info)
        controls.addWidget(info_btn)
        
        layout.addLayout(controls)
        
        # Split pane widget - start with editor
        self.split_widget = SplitPaneWidget(initial_widget_type=WidgetType.TEXT_EDITOR)
        
        # Connect signals
        self.split_widget.active_pane_changed.connect(self.on_active_pane_changed)
        self.split_widget.pane_added.connect(self.on_pane_added)
        self.split_widget.pane_removed.connect(self.on_pane_removed)
        
        layout.addWidget(self.split_widget)
        
        self.update_status()
        
    def split_horizontal(self):
        """Split the active pane horizontally."""
        pane_id = self.split_widget.active_pane_id
        print(f"Splitting pane {pane_id} horizontally")
        self.split_widget.split_horizontal(pane_id)
        self.update_status()
        
    def split_vertical(self):
        """Split the active pane vertically."""
        pane_id = self.split_widget.active_pane_id
        print(f"Splitting pane {pane_id} vertically")
        self.split_widget.split_vertical(pane_id)
        self.update_status()
        
    def close_pane(self):
        """Close the active pane."""
        if self.split_widget.get_pane_count() > 1:
            pane_id = self.split_widget.active_pane_id
            print(f"Closing pane {pane_id}")
            self.split_widget.close_pane(pane_id)
            self.update_status()
        else:
            self.status_label.setText("Cannot close last pane")
            
    def change_type(self, widget_type: WidgetType):
        """Change the type of the active pane."""
        pane_id = self.split_widget.active_pane_id
        print(f"Changing pane {pane_id} to {widget_type}")
        
        # Get the active leaf from model
        leaf = self.split_widget.model.get_active_leaf()
        if leaf:
            self.split_widget.model.change_pane_type(pane_id, widget_type)
            self.split_widget.refresh_view()
            self.update_status()
            
    def show_info(self):
        """Show information about current state."""
        print("\n=== Current State ===")
        print(f"Active pane: {self.split_widget.active_pane_id}")
        print(f"Total panes: {self.split_widget.get_pane_count()}")
        print(f"Pane IDs: {self.split_widget.get_all_pane_ids()}")
        print(f"Terminal sessions: {len(terminal_server.sessions)}")
        print(f"Session IDs: {list(terminal_server.sessions.keys())}")
        
        # Print tree structure
        print("\nTree structure:")
        self.print_tree(self.split_widget.model.root, 0)
        print("==================\n")
        
    def print_tree(self, node, indent):
        """Print the tree structure."""
        from ui.widgets.split_pane_model import LeafNode, SplitNode
        
        if isinstance(node, LeafNode):
            active = " [ACTIVE]" if node.id == self.split_widget.active_pane_id else ""
            widget_info = f"{node.widget_type.value}" if node.app_widget else "NO WIDGET"
            print("  " * indent + f"Leaf {node.id}: {widget_info}{active}")
        elif isinstance(node, SplitNode):
            print("  " * indent + f"Split ({node.orientation}, ratio={node.ratio:.2f})")
            if node.first:
                self.print_tree(node.first, indent + 1)
            if node.second:
                self.print_tree(node.second, indent + 1)
                
    def on_active_pane_changed(self, pane_id: str):
        """Handle active pane change."""
        print(f"Active pane changed to: {pane_id}")
        self.update_status()
        
    def on_pane_added(self, pane_id: str):
        """Handle pane addition."""
        print(f"Pane added: {pane_id}")
        self.update_status()
        
    def on_pane_removed(self, pane_id: str):
        """Handle pane removal."""
        print(f"Pane removed: {pane_id}")
        self.update_status()
        
    def update_status(self):
        """Update the status display."""
        active = self.split_widget.active_pane_id
        count = self.split_widget.get_pane_count()
        sessions = len(terminal_server.sessions)
        self.status_label.setText(
            f"Active: {active} | Panes: {count} | Terminal Sessions: {sessions}"
        )
        
    def closeEvent(self, event):
        """Clean up on close."""
        print("Cleaning up...")
        self.split_widget.cleanup()
        print(f"Terminal sessions after cleanup: {len(terminal_server.sessions)}")
        super().closeEvent(event)


def main():
    """Run the test."""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    # Show initial info
    window.show_info()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()