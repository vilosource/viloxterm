#!/usr/bin/env python3
"""
Diagnostic test for Chrome dragging to find the root issue.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QMouseEvent
import logging

logging.basicConfig(level=logging.DEBUG, format='%(message)s')
logger = logging.getLogger(__name__)

class TestTitleBar(QWidget):
    """Simple test title bar."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(35)
        self.setStyleSheet("background-color: #333;")
        
        layout = QVBoxLayout(self)
        label = QLabel("Click and drag here to move window")
        label.setStyleSheet("color: white;")
        layout.addWidget(label)
        
        self.drag_start_pos = None
        self.window_start_pos = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.globalPos()
            self.window_start_pos = self.window().pos()
            logger.info(f"DRAG START - Mouse: {self.drag_start_pos}, Window: {self.window_start_pos}")
    
    def mouseMoveEvent(self, event):
        if self.drag_start_pos and event.buttons() == Qt.LeftButton:
            # Calculate new position
            delta = event.globalPos() - self.drag_start_pos
            new_pos = self.window_start_pos + delta
            
            # Move window
            old_pos = self.window().pos()
            self.window().move(new_pos)
            actual_pos = self.window().pos()
            
            logger.debug(f"MOVE - Target: {new_pos}, Actual: {actual_pos}, Delta: {delta}")
            
            if actual_pos != new_pos:
                logger.warning(f"⚠️ Window didn't move to target! Expected {new_pos}, got {actual_pos}")
    
    def mouseReleaseEvent(self, event):
        if self.drag_start_pos:
            logger.info(f"DRAG END - Final position: {self.window().pos()}")
        self.drag_start_pos = None
        self.window_start_pos = None


class TestWindow(QMainWindow):
    """Test window with frameless style."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag Test")
        
        # Make frameless
        self.setWindowFlags(Qt.FramelessWindowHint)
        
        # Create central widget with title bar
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Add custom title bar
        self.title_bar = TestTitleBar(self)
        layout.addWidget(self.title_bar)
        
        # Add content
        content = QWidget()
        content.setStyleSheet("background-color: white;")
        content.setMinimumSize(400, 300)
        
        content_layout = QVBoxLayout(content)
        info_label = QLabel(
            "DIAGNOSTIC TEST\n\n"
            "1. Try dragging the dark title bar\n"
            "2. Watch console for position info\n"
            "3. Check if window actually moves\n\n"
            "Press 'Test Move' to test programmatic movement"
        )
        content_layout.addWidget(info_label)
        
        # Test button
        test_btn = QPushButton("Test Move (should move right by 100px)")
        test_btn.clicked.connect(self.test_move)
        content_layout.addWidget(test_btn)
        
        layout.addWidget(content)
        
        self.resize(500, 400)
        
    def test_move(self):
        """Test programmatic window movement."""
        old_pos = self.pos()
        new_pos = old_pos + QPoint(100, 0)
        self.move(new_pos)
        actual_pos = self.pos()
        
        logger.info(f"TEST MOVE - Old: {old_pos}, Target: {new_pos}, Actual: {actual_pos}")
        
        if actual_pos == new_pos:
            logger.info("✅ Programmatic move works!")
        else:
            logger.error(f"❌ Programmatic move failed! Window at {actual_pos} instead of {new_pos}")


def main():
    app = QApplication(sys.argv)
    
    print("=" * 60)
    print("DIAGNOSTIC TEST FOR WINDOW DRAGGING")
    print("=" * 60)
    print("This tests basic frameless window dragging")
    print("=" * 60)
    
    window = TestWindow()
    window.show()
    
    # Log initial info
    QTimer.singleShot(100, lambda: logger.info(f"Window flags: {window.windowFlags()}"))
    QTimer.singleShot(100, lambda: logger.info(f"Initial position: {window.pos()}"))
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()