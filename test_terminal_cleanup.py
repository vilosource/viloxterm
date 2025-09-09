#!/usr/bin/env python3
"""
Test script to verify terminal session cleanup works properly.
"""

import sys
import time
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import Qt
from ui.terminal.terminal_widget import TerminalWidget
from ui.terminal.terminal_server import terminal_server
from ui.terminal.terminal_factory import register_terminal_widget


class TestWindow(QMainWindow):
    """Test window for terminal cleanup."""
    
    def __init__(self):
        super().__init__()
        self.terminals = []
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the test UI."""
        self.setWindowTitle("Terminal Cleanup Test")
        self.resize(800, 600)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Status label
        self.status_label = QLabel("Sessions: 0")
        layout.addWidget(self.status_label)
        
        # Buttons
        create_btn = QPushButton("Create Terminal")
        create_btn.clicked.connect(self.create_terminal)
        layout.addWidget(create_btn)
        
        close_btn = QPushButton("Close Last Terminal")
        close_btn.clicked.connect(self.close_last_terminal)
        layout.addWidget(close_btn)
        
        close_all_btn = QPushButton("Close All Terminals")
        close_all_btn.clicked.connect(self.close_all_terminals)
        layout.addWidget(close_all_btn)
        
        # Terminal container
        self.terminal_container = QWidget()
        self.terminal_layout = QVBoxLayout(self.terminal_container)
        layout.addWidget(self.terminal_container)
        
        self.update_status()
    
    def update_status(self):
        """Update session count display."""
        count = len(terminal_server.sessions)
        self.status_label.setText(f"Active Sessions: {count} / {terminal_server.max_sessions}")
        
    def create_terminal(self):
        """Create a new terminal widget."""
        try:
            terminal = TerminalWidget()
            self.terminals.append(terminal)
            self.terminal_layout.addWidget(terminal)
            self.update_status()
            print(f"Created terminal, session: {terminal.session_id}")
        except Exception as e:
            print(f"Error creating terminal: {e}")
            self.update_status()
    
    def close_last_terminal(self):
        """Close the last created terminal."""
        if self.terminals:
            terminal = self.terminals.pop()
            session_id = terminal.session_id
            terminal.close_terminal()
            self.terminal_layout.removeWidget(terminal)
            terminal.deleteLater()
            self.update_status()
            print(f"Closed terminal, session: {session_id}")
    
    def close_all_terminals(self):
        """Close all terminals."""
        while self.terminals:
            self.close_last_terminal()
    
    def closeEvent(self, event):
        """Clean up on window close."""
        self.close_all_terminals()
        super().closeEvent(event)


def main():
    """Run the test."""
    app = QApplication(sys.argv)
    
    # Register terminal widget
    register_terminal_widget()
    
    # Create test window
    window = TestWindow()
    window.show()
    
    # Print initial status
    print(f"Terminal server max sessions: {terminal_server.max_sessions}")
    
    # Run app
    sys.exit(app.exec())


if __name__ == "__main__":
    main()