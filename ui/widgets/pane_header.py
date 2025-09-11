#!/usr/bin/env python3
"""
Pane header bar component for split operations.
Provides a minimal, unobtrusive header with split/close controls.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, 
    QToolButton, QMenu, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QFont, QPalette, QColor, QPainter, QBrush
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ui.vscode_theme import *


class PaneHeaderBar(QWidget):
    """
    Minimal header bar for pane operations.
    Appears at the top of each pane with split/close controls.
    """
    
    # Signals
    split_horizontal_requested = Signal()
    split_vertical_requested = Signal()
    close_requested = Signal()
    type_menu_requested = Signal()
    
    def __init__(self, pane_id: str = "", show_type_menu: bool = True, parent=None):
        super().__init__(parent)
        self.pane_id = pane_id
        self.show_type_menu = show_type_menu
        self.is_active = False
        self.background_color = QColor(PANE_HEADER_BACKGROUND)
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the header UI."""
        # Set fixed height for minimal footprint
        self.setFixedHeight(18)  # Ultra-minimal height to save screen space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Don't use palette or stylesheet for background - we'll paint it ourselves
        self.setAttribute(Qt.WA_StyledBackground, False)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 0, 2, 0)  # Minimal margins
        layout.setSpacing(1)  # Minimal spacing
        
        # Pane number label (shows 1-9 when enabled)
        self.number_label = QLabel()
        self.number_label.setStyleSheet(f"""
            QLabel {{
                background-color: {ACCENT_COLOR};
                color: white;
                border-radius: 2px;
                padding: 0px 4px;
                font-weight: bold;
                font-size: 10px;
                min-width: 12px;
                max-width: 12px;
            }}
        """)
        self.number_label.setAlignment(Qt.AlignCenter)
        self.number_label.hide()  # Hidden by default
        layout.addWidget(self.number_label)
        
        # Pane ID label (optional, for debugging)
        self.id_label = QLabel(self.pane_id)
        self.id_label.setStyleSheet(f"""
            QLabel {{
                color: {TAB_INACTIVE_FOREGROUND};
                font-size: 10px;
                padding: 0 2px;
            }}
        """)
        layout.addWidget(self.id_label)
        
        # Stretch to push buttons to the right
        layout.addStretch()
        
        # Type menu button (optional)
        if self.show_type_menu:
            self.type_button = self.create_tool_button("≡", "Change widget type")
            self.type_button.clicked.connect(self.type_menu_requested.emit)
            layout.addWidget(self.type_button)
        
        # Split horizontal button
        self.split_h_button = self.create_tool_button("↔", "Split horizontal (new pane on right)")
        self.split_h_button.clicked.connect(self.split_horizontal_requested.emit)
        layout.addWidget(self.split_h_button)
        
        # Split vertical button
        self.split_v_button = self.create_tool_button("↕", "Split vertical (new pane below)")
        self.split_v_button.clicked.connect(self.split_vertical_requested.emit)
        layout.addWidget(self.split_v_button)
        
        # Close button
        self.close_button = self.create_tool_button("×", "Close this pane")
        self.close_button.clicked.connect(self.close_requested.emit)
        self.close_button.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {PANE_HEADER_FOREGROUND};
                border: none;
                padding: 0px 2px;
                font-size: 12px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: {PANE_HEADER_CLOSE_HOVER};
                color: white;
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self.close_button)
    
    def create_tool_button(self, text: str, tooltip: str) -> QToolButton:
        """Create a styled tool button."""
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.setFixedSize(16, 16)  # Smaller buttons
        
        # Style the button with VSCode theme
        button.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {PANE_HEADER_FOREGROUND};
                border: none;
                padding: 0px;
                font-size: 12px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: {PANE_HEADER_BUTTON_HOVER};
                border: 1px solid {ACCENT_COLOR};
                border-radius: 2px;
            }}
            QToolButton:pressed {{
                background-color: {ACCENT_COLOR};
            }}
        """)
        
        return button
    
    def set_pane_id(self, pane_id: str):
        """Update the pane ID display."""
        self.pane_id = pane_id
        self.id_label.setText(pane_id)
    
    def set_pane_number(self, number: int = None, visible: bool = False):
        """
        Set the pane number display.
        
        Args:
            number: Pane number (1-9) or None
            visible: Whether to show the number
        """
        if number is not None:
            self.number_label.setText(str(number))
        self.number_label.setVisible(visible and number is not None)
    
    def paintEvent(self, event):
        """Custom paint event to draw the background."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QBrush(self.background_color))
        super().paintEvent(event)
    
    def set_active(self, active: bool):
        """Update visual state for active pane."""
        self.is_active = active
        
        if active:
            # Set active background color
            self.background_color = QColor(PANE_HEADER_ACTIVE_BACKGROUND)
            self.update()  # Force repaint
            
            self.id_label.setStyleSheet(f"""
                QLabel {{
                    color: {PANE_HEADER_ACTIVE_FOREGROUND};
                    font-size: 10px;
                    padding: 0 2px;
                    font-weight: bold;
                }}
            """)
            # Highlight number label for active pane
            if self.number_label.isVisible():
                self.number_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {ACCENT_COLOR};
                        color: white;
                        border-radius: 2px;
                        padding: 0px 4px;
                        font-weight: bold;
                        font-size: 10px;
                        min-width: 12px;
                        max-width: 12px;
                        border: 1px solid white;
                    }}
                """)
        else:
            # Set inactive background color
            self.background_color = QColor(PANE_HEADER_BACKGROUND)
            self.update()  # Force repaint
            
            self.id_label.setStyleSheet(f"""
                QLabel {{
                    color: {TAB_INACTIVE_FOREGROUND};
                    font-size: 10px;
                    padding: 0 2px;
                }}
            """)
            # Normal number label for inactive pane
            if self.number_label.isVisible():
                self.number_label.setStyleSheet(f"""
                    QLabel {{
                        background-color: {PANE_HEADER_BUTTON_HOVER};
                        color: {TAB_INACTIVE_FOREGROUND};
                        border-radius: 2px;
                        padding: 0px 4px;
                        font-weight: bold;
                        font-size: 10px;
                        min-width: 12px;
                        max-width: 12px;
                    }}
                """)


class CompactPaneHeader(QWidget):
    """
    Even more minimal header - appears only on hover.
    """
    
    split_horizontal_requested = Signal()
    split_vertical_requested = Signal()
    close_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Auto-hide behavior
        self.setMouseTracking(True)
        self.hide_on_mouse_leave = True
        
    def setup_ui(self):
        """Initialize compact header."""
        self.setFixedHeight(18)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Semi-transparent by default
        self.setStyleSheet("""
            CompactPaneHeader {
                background-color: rgba(45, 45, 48, 180);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        layout.addStretch()
        
        # Mini buttons
        for text, signal, tooltip in [
            ("↔", self.split_horizontal_requested, "Split H"),
            ("↕", self.split_vertical_requested, "Split V"),
            ("×", self.close_requested, "Close"),
        ]:
            btn = QToolButton()
            btn.setText(text)
            btn.setToolTip(tooltip)
            btn.setFixedSize(18, 18)
            btn.clicked.connect(signal.emit)
            btn.setStyleSheet("""
                QToolButton {
                    background: transparent;
                    color: #969696;
                    border: none;
                    font-size: 12px;
                }
                QToolButton:hover {
                    background: #3c3c3c;
                    color: white;
                }
            """)
            layout.addWidget(btn)
    
    def enterEvent(self, event):
        """Show fully on mouse enter."""
        self.setStyleSheet("""
            CompactPaneHeader {
                background-color: rgba(45, 45, 48, 255);
            }
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Fade on mouse leave."""
        if self.hide_on_mouse_leave:
            self.setStyleSheet("""
                CompactPaneHeader {
                    background-color: rgba(45, 45, 48, 180);
                }
            """)
        super().leaveEvent(event)