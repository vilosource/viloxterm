#!/usr/bin/env python3
"""
Debug script to trace focus management issues.
Creates a detailed log of what happens with active pane tracking.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.widgets.widget_registry import WidgetType
from ui.terminal.terminal_server import terminal_server


class FocusDebugWindow(QMainWindow):
    """Debug window to test focus management."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the debug UI."""
        self.setWindowTitle("Focus Debug Test")
        self.resize(1000, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Status display
        self.status_label = QLabel("Ready to test focus")
        layout.addWidget(self.status_label)
        
        # Control buttons
        controls = QHBoxLayout()
        
        # Split buttons to simulate keyboard shortcuts
        split_h_btn = QPushButton("Keyboard Split Horizontal (Ctrl+\\)")
        split_h_btn.clicked.connect(self.keyboard_split_horizontal)
        controls.addWidget(split_h_btn)
        
        split_v_btn = QPushButton("Keyboard Split Vertical (Ctrl+Shift+\\)")
        split_v_btn.clicked.connect(self.keyboard_split_vertical)
        controls.addWidget(split_v_btn)
        
        # Debug buttons
        debug_btn = QPushButton("Show Active Pane")
        debug_btn.clicked.connect(self.show_active_pane)
        controls.addWidget(debug_btn)
        
        layout.addLayout(controls)
        
        # Split pane widget - start with terminal
        self.split_widget = SplitPaneWidget(initial_widget_type=WidgetType.TERMINAL)
        
        # Connect signals to trace them
        self.split_widget.active_pane_changed.connect(self.on_active_pane_changed)
        self.split_widget.pane_added.connect(self.on_pane_added)
        
        layout.addWidget(self.split_widget)
        
        # Initial status
        self.update_status()
        
    def keyboard_split_horizontal(self):
        """Simulate the keyboard shortcut Ctrl+\ (horizontal split)."""
        logger.info("🖱️ User pressed Ctrl+\\ (horizontal split)")
        
        # This simulates exactly what the main window does
        widget = self.split_widget
        active_pane = widget.active_pane_id
        
        logger.info(f"📍 Active pane before split: {active_pane}")
        logger.info(f"📍 All panes: {widget.get_all_pane_ids()}")
        
        if widget and active_pane:
            logger.info(f"🔄 Calling split_horizontal({active_pane})")
            widget.split_horizontal(active_pane)
            
        self.update_status()
        
    def keyboard_split_vertical(self):
        """Simulate the keyboard shortcut Ctrl+Shift+\ (vertical split)."""
        logger.info("🖱️ User pressed Ctrl+Shift+\\ (vertical split)")
        
        # This simulates exactly what the main window does
        widget = self.split_widget
        active_pane = widget.active_pane_id
        
        logger.info(f"📍 Active pane before split: {active_pane}")
        logger.info(f"📍 All panes: {widget.get_all_pane_ids()}")
        
        if widget and active_pane:
            logger.info(f"🔄 Calling split_vertical({active_pane})")
            widget.split_vertical(active_pane)
            
        self.update_status()
        
    def show_active_pane(self):
        """Show detailed info about the active pane."""
        active_pane = self.split_widget.active_pane_id
        all_panes = self.split_widget.get_all_pane_ids()
        
        logger.info("📊 === PANE STATUS ===")
        logger.info(f"📍 Active pane: {active_pane}")
        logger.info(f"📍 All panes: {all_panes}")
        
        # Check if active pane exists in model
        leaf = self.split_widget.model.find_leaf(active_pane)
        if leaf:
            logger.info(f"✅ Active pane exists in model: {leaf.id}")
            logger.info(f"📱 Widget type: {leaf.widget_type}")
            logger.info(f"🔗 Has AppWidget: {leaf.app_widget is not None}")
        else:
            logger.error(f"❌ Active pane {active_pane} NOT FOUND in model!")
            
        logger.info("📊 ==================")
        
    def on_active_pane_changed(self, pane_id: str):
        """Handle active pane change."""
        logger.info(f"🎯 ACTIVE PANE CHANGED: {pane_id}")
        self.update_status()
        
    def on_pane_added(self, pane_id: str):
        """Handle pane addition."""
        logger.info(f"➕ PANE ADDED: {pane_id}")
        self.update_status()
        
    def update_status(self):
        """Update the status display."""
        active = self.split_widget.active_pane_id
        count = self.split_widget.get_pane_count()
        sessions = len(terminal_server.sessions)
        
        status_text = f"Active: {active} | Panes: {count} | Sessions: {sessions}"
        self.status_label.setText(status_text)
        logger.info(f"📊 Status: {status_text}")


def main():
    """Run the focus debug test."""
    app = QApplication(sys.argv)
    
    window = FocusDebugWindow()
    window.show()
    
    logger.info("🚀 Focus Debug Window started")
    logger.info("📋 Instructions:")
    logger.info("   1. Click on terminal areas to focus them")
    logger.info("   2. Use 'Keyboard Split' buttons to simulate Ctrl+\\ shortcuts")
    logger.info("   3. Use split icons in panes to compare behavior")
    logger.info("   4. Check logs to see what's happening with focus")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()