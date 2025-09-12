#!/usr/bin/env python3
"""
Chrome-style title bar with proper cross-platform dragging support.
Uses Qt's startSystemMove() for native window manager integration.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTabBar, 
    QToolButton, QLabel, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, Signal, QPoint, QTimer
from PySide6.QtGui import QMouseEvent, QPalette, QColor
from ui.widgets.window_controls import WindowControls
import logging
import sys

logger = logging.getLogger(__name__)


class ChromeTabBar(QTabBar):
    """Custom tab bar styled like Chrome."""
    
    # Signal for new tab button
    new_tab_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setTabsClosable(True)
        self.setElideMode(Qt.ElideRight)
        self.setExpanding(False)
        self.setDocumentMode(True)
        
        # Set shape for Chrome-like appearance
        self.setShape(QTabBar.RoundedNorth)
        
        # Configure appearance
        self.setup_style()
    
    def setup_style(self):
        """Apply Chrome-like styling to the tab bar."""
        self.setStyleSheet("""
            QTabBar {
                background: transparent;
                border: none;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.05);
                color: #cccccc;
                padding: 8px 12px;
                margin-right: 1px;
                margin-top: 5px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 100px;
                max-width: 240px;
            }
            QTabBar::tab:selected {
                background: #1e1e1e;
                color: #ffffff;
                margin-top: 2px;
                padding-top: 11px;
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.08);
            }
            QTabBar::close-button {
                image: none;
                width: 16px;
                height: 16px;
                background: transparent;
                border-radius: 8px;
            }
            QTabBar::close-button:hover {
                background: rgba(255, 255, 255, 0.2);
            }
        """)
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click on empty area to create new tab."""
        if self.tabAt(event.pos()) == -1:
            # Clicked on empty area
            self.new_tab_requested.emit()
        else:
            super().mouseDoubleClickEvent(event)


class ChromeTitleBarFixed(QWidget):
    """Chrome-style title bar with cross-platform dragging support."""
    
    # Signals
    minimize_window = Signal()
    maximize_window = Signal()
    close_window = Signal()
    new_tab_requested = Signal()
    tab_changed = Signal(int)
    tab_close_requested = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_maximized = False
        self.use_native_move = self._should_use_native_move()
        self.fallback_drag_pos = None
        self.setup_ui()
        
    def _should_use_native_move(self):
        """Determine if we should use native system move."""
        # Check if we're on Wayland
        platform = QApplication.instance().platformName()
        logger.info(f"Platform detected: {platform}")
        
        # Use native move on Wayland, X11, Windows, and macOS
        # This is the most reliable cross-platform approach
        return True
    
    def setup_ui(self):
        """Set up the title bar UI."""
        # Set fixed height like Chrome
        self.setFixedHeight(35)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(50, 50, 50))  # Dark gray like Chrome
        self.setPalette(palette)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Left side: Optional app menu button
        left_spacer = QWidget()
        left_spacer.setFixedWidth(8)
        main_layout.addWidget(left_spacer)
        
        # Center: Tab bar
        self.tab_bar = ChromeTabBar(self)
        self.tab_bar.currentChanged.connect(self.tab_changed.emit)
        self.tab_bar.tabCloseRequested.connect(self.tab_close_requested.emit)
        self.tab_bar.new_tab_requested.connect(self.new_tab_requested.emit)
        main_layout.addWidget(self.tab_bar, 1)  # Stretch factor 1
        
        # Add new tab button
        self.new_tab_btn = QToolButton(self)
        self.new_tab_btn.setText("+")
        self.new_tab_btn.setFixedSize(28, 28)
        self.new_tab_btn.clicked.connect(self.new_tab_requested.emit)
        self.new_tab_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #888888;
                font-size: 18px;
                border-radius: 14px;
            }
            QToolButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #cccccc;
            }
        """)
        main_layout.addWidget(self.new_tab_btn)
        
        # Add draggable spacing before window controls
        spacer = QWidget()
        spacer.setMinimumWidth(80)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer.setObjectName("dragSpacer")
        main_layout.addWidget(spacer)
        
        # Right side: Window controls
        self.window_controls = WindowControls(self)
        self.window_controls.minimize_clicked.connect(self.minimize_window.emit)
        self.window_controls.maximize_clicked.connect(self.maximize_window.emit)
        self.window_controls.close_clicked.connect(self.close_window.emit)
        main_layout.addWidget(self.window_controls)
        
        # Enable mouse tracking for drag detection
        self.setMouseTracking(True)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.LeftButton:
            # Get the widget at the click position
            child = self.childAt(event.pos())
            
            # Check if we're clicking on a draggable widget
            if self._is_draggable_widget(child):
                if self.use_native_move:
                    # Use Qt's native system move (works on all platforms)
                    self._start_system_move()
                else:
                    # Fallback to manual dragging (shouldn't be needed)
                    self.fallback_drag_pos = event.globalPos()
        
        super().mousePressEvent(event)
    
    def _start_system_move(self):
        """Start native system window move."""
        window = self.window()
        if hasattr(window, 'windowHandle') and window.windowHandle():
            # This is the cross-platform way to drag a frameless window
            window.windowHandle().startSystemMove()
            logger.info("Started native system move")
        else:
            logger.warning("Window handle not available for system move")
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for fallback dragging."""
        if not self.use_native_move and self.fallback_drag_pos is not None:
            if event.buttons() == Qt.LeftButton:
                # Fallback manual dragging (only for platforms that don't support startSystemMove)
                diff = event.globalPos() - self.fallback_drag_pos
                window = self.window()
                window.move(window.pos() + diff)
                self.fallback_drag_pos = event.globalPos()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release."""
        self.fallback_drag_pos = None
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click to maximize/restore window."""
        child = self.childAt(event.pos())
        if self._is_draggable_widget(child):
            self.maximize_window.emit()
            event.accept()
        
        super().mouseDoubleClickEvent(event)
    
    def _is_draggable_widget(self, widget):
        """Check if a widget should allow window dragging."""
        if widget is None:
            return True  # Empty space is draggable
        
        # Check if it's the title bar itself
        if widget == self:
            return True
            
        # Check for spacer widgets
        if widget.__class__.__name__ == 'QWidget':
            if not isinstance(widget, (WindowControls, QToolButton)):
                return True
        
        # Labels are draggable
        if isinstance(widget, QLabel):
            return True
        
        # Tab bar and buttons are not draggable
        if isinstance(widget, (QTabBar, QToolButton, WindowControls)):
            return False
        
        # Check parent hierarchy
        parent = widget.parent()
        while parent and parent != self:
            if isinstance(parent, QTabBar):
                return False
            parent = parent.parent()
        
        return True
    
    def set_maximized(self, maximized: bool):
        """Update the maximize button state."""
        self.is_maximized = maximized
        self.window_controls.set_maximized(maximized)
    
    # Tab management methods
    def add_tab(self, text: str) -> int:
        """Add a new tab to the tab bar."""
        return self.tab_bar.addTab(text)
    
    def remove_tab(self, index: int):
        """Remove a tab from the tab bar."""
        self.tab_bar.removeTab(index)
    
    def set_current_tab(self, index: int):
        """Set the current tab."""
        self.tab_bar.setCurrentIndex(index)
    
    def current_tab(self) -> int:
        """Get the current tab index."""
        return self.tab_bar.currentIndex()
    
    def tab_count(self) -> int:
        """Get the number of tabs."""
        return self.tab_bar.count()
    
    def set_tab_text(self, index: int, text: str):
        """Set the text of a tab."""
        self.tab_bar.setTabText(index, text)
    
    def tab_text(self, index: int) -> str:
        """Get the text of a tab."""
        return self.tab_bar.tabText(index)


# For compatibility - use the fixed version
ChromeTitleBar = ChromeTitleBarFixed