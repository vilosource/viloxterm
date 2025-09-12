#!/usr/bin/env python3
"""
Window control buttons for Chrome-style title bar.
Provides minimize, maximize/restore, and close buttons.
"""

from PySide6.QtWidgets import QWidget, QHBoxLayout, QToolButton
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QPen, QColor, QIcon, QPainterPath
import sys


class WindowControlButton(QToolButton):
    """Custom window control button with hover effects."""
    
    def __init__(self, button_type: str, parent=None):
        super().__init__(parent)
        self.button_type = button_type  # 'minimize', 'maximize', 'close'
        self.is_maximized = False
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the button appearance."""
        self.setFixedSize(46, 30)
        self.setCursor(Qt.PointingHandCursor)
        self.setAutoRaise(True)
        
        # Base style for all buttons
        base_style = """
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 0px;
            }
        """
        
        if self.button_type == 'close':
            # Close button has red hover
            self.setStyleSheet(base_style + """
                QToolButton:hover {
                    background-color: #e81123;
                }
                QToolButton:pressed {
                    background-color: #f1707a;
                }
            """)
        else:
            # Minimize and maximize have gray hover
            self.setStyleSheet(base_style + """
                QToolButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                QToolButton:pressed {
                    background-color: rgba(255, 255, 255, 0.2);
                }
            """)
    
    def paintEvent(self, event):
        """Custom paint for the button icons."""
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        # Set pen color based on hover state and button type
        if self.underMouse():
            if self.button_type == 'close':
                pen_color = QColor(255, 255, 255)
            else:
                pen_color = QColor(255, 255, 255)
        else:
            pen_color = QColor(200, 200, 200)
        
        pen = QPen(pen_color, 1.5)
        painter.setPen(pen)
        
        # Center point for drawing
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        if self.button_type == 'minimize':
            # Draw minimize line
            painter.drawLine(center_x - 5, center_y, center_x + 5, center_y)
            
        elif self.button_type == 'maximize':
            # Draw maximize/restore icon
            if self.is_maximized:
                # Draw restore icon (two overlapping squares)
                # Back square
                painter.drawRect(center_x - 3, center_y - 5, 8, 8)
                # Front square with fill to hide overlap
                painter.fillRect(center_x - 5, center_y - 3, 8, 8, QColor(30, 30, 30))
                painter.drawRect(center_x - 5, center_y - 3, 8, 8)
            else:
                # Draw maximize icon (single square)
                painter.drawRect(center_x - 5, center_y - 5, 10, 10)
                
        elif self.button_type == 'close':
            # Draw X
            painter.drawLine(center_x - 5, center_y - 5, center_x + 5, center_y + 5)
            painter.drawLine(center_x + 5, center_y - 5, center_x - 5, center_y + 5)
    
    def set_maximized(self, maximized: bool):
        """Update the maximize button state."""
        if self.button_type == 'maximize':
            self.is_maximized = maximized
            self.update()  # Trigger repaint


class WindowControls(QWidget):
    """Container for window control buttons."""
    
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the window controls layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create buttons
        self.minimize_btn = WindowControlButton('minimize', self)
        self.maximize_btn = WindowControlButton('maximize', self)
        self.close_btn = WindowControlButton('close', self)
        
        # Connect signals
        self.minimize_btn.clicked.connect(self.minimize_clicked.emit)
        self.maximize_btn.clicked.connect(self.maximize_clicked.emit)
        self.close_btn.clicked.connect(self.close_clicked.emit)
        
        # Add to layout
        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.maximize_btn)
        layout.addWidget(self.close_btn)
        
        # Set fixed width for the control group
        self.setFixedWidth(138)  # 46 * 3
        self.setFixedHeight(30)
    
    def set_maximized(self, maximized: bool):
        """Update maximize button state."""
        self.maximize_btn.set_maximized(maximized)
    
    def set_dark_theme(self, dark: bool):
        """Update colors for dark/light theme."""
        # For now, we're using a dark theme by default
        # This can be extended to support light themes
        pass


def get_platform_button_order():
    """Get the button order based on the platform."""
    if sys.platform == 'darwin':
        # macOS has close, minimize, maximize on the left
        return ['close', 'minimize', 'maximize'], Qt.AlignLeft
    else:
        # Windows and Linux have minimize, maximize, close on the right
        return ['minimize', 'maximize', 'close'], Qt.AlignRight