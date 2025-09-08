"""Status bar implementation."""

from PySide6.QtWidgets import QStatusBar, QLabel
from PySide6.QtCore import Qt


class AppStatusBar(QStatusBar):
    """Application status bar."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the status bar UI."""
        self.setObjectName("appStatusBar")
        
        # Create status widgets
        self.status_label = QLabel("Ready")
        self.addWidget(self.status_label)
        
        # Add permanent widgets on the right
        self.position_label = QLabel("Ln 1, Col 1")
        self.addPermanentWidget(self.position_label)
        
        self.encoding_label = QLabel("UTF-8")
        self.addPermanentWidget(self.encoding_label)
        
    def set_message(self, message: str, timeout: int = 0):
        """Set status message."""
        if timeout > 0:
            self.showMessage(message, timeout)
        else:
            self.status_label.setText(message)
            
    def set_position(self, line: int, column: int):
        """Update cursor position display."""
        self.position_label.setText(f"Ln {line}, Col {column}")
        
    def set_encoding(self, encoding: str):
        """Update encoding display."""
        self.encoding_label.setText(encoding)