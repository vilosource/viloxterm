#!/usr/bin/env python3
"""
Main entry point for the VSCode-style PySide6 application.
"""

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication
from ui.main_window import MainWindow

# Import compiled resources
try:
    import resources.resources_rc
except ImportError:
    print("Warning: Resources not compiled. Run 'make resources' to compile icons.")
    pass


def main():
    """Initialize and run the application."""
    # Set application metadata
    QCoreApplication.setApplicationName("ViloApp")
    QCoreApplication.setOrganizationName("ViloApp")
    QCoreApplication.setOrganizationDomain("viloapp.local")
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()