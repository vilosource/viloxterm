#!/usr/bin/env python3
"""
Simple test script to verify terminal widget functionality.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from ui.terminal.terminal_widget import TerminalWidget
from ui.terminal.terminal_factory import register_terminal_widget


def main():
    """Test terminal widget in a simple window."""
    app = QApplication(sys.argv)
    
    # Register terminal widget
    register_terminal_widget()
    
    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Terminal Widget Test")
    window.resize(800, 600)
    
    # Create terminal widget
    terminal = TerminalWidget()
    window.setCentralWidget(terminal)
    
    # Show window
    window.show()
    
    # Run app
    sys.exit(app.exec())


if __name__ == "__main__":
    main()