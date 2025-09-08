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
from PySide6.QtGui import QAction, QFont
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
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the header UI."""
        # Set fixed height for minimal footprint
        self.setFixedHeight(24)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Style the header with VSCode theme
        self.setStyleSheet(f"""
            PaneHeaderBar {{
                background-color: {PANE_HEADER_BACKGROUND};
                border-bottom: 1px solid {PANE_HEADER_BORDER};
            }}
        """)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(2)
        
        # Pane ID label (optional, for debugging)
        self.id_label = QLabel(self.pane_id)
        self.id_label.setStyleSheet(f"""
            QLabel {{
                color: {TAB_INACTIVE_FOREGROUND};
                font-size: 11px;
                padding: 0 4px;
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
                padding: 2px 4px;
                font-size: 14px;
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
        button.setFixedSize(20, 20)
        
        # Style the button with VSCode theme
        button.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                color: {PANE_HEADER_FOREGROUND};
                border: none;
                padding: 2px;
                font-size: 14px;
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
    
    def set_active(self, active: bool):
        """Update visual state for active pane."""
        if active:
            self.setStyleSheet(f"""
                PaneHeaderBar {{
                    background-color: {PANE_HEADER_ACTIVE_BACKGROUND};
                    border-bottom: 1px solid {PANE_HEADER_ACTIVE_BACKGROUND};
                }}
            """)
            self.id_label.setStyleSheet(f"""
                QLabel {{
                    color: {PANE_HEADER_ACTIVE_FOREGROUND};
                    font-size: 11px;
                    padding: 0 4px;
                    font-weight: bold;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                PaneHeaderBar {{
                    background-color: {PANE_HEADER_BACKGROUND};
                    border-bottom: 1px solid {PANE_HEADER_BORDER};
                }}
            """)
            self.id_label.setStyleSheet(f"""
                QLabel {{
                    color: {TAB_INACTIVE_FOREGROUND};
                    font-size: 11px;
                    padding: 0 4px;
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