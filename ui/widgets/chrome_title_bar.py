#!/usr/bin/env python3
"""
Chrome-style title bar widget that integrates tabs with window controls.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTabBar, 
    QToolButton, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QTimer
from PySide6.QtGui import QMouseEvent, QPalette, QColor
from ui.widgets.window_controls import WindowControls
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure debug logging is enabled


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


class ChromeTitleBar(QWidget):
    """Chrome-style title bar with integrated tabs and window controls."""
    
    # Signals
    minimize_window = Signal()
    maximize_window = Signal()
    close_window = Signal()
    new_tab_requested = Signal()
    tab_changed = Signal(int)
    tab_close_requested = Signal(int)
    window_move_requested = Signal(QPoint)  # For window dragging
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_maximized = False
        self.drag_start_position = None
        self.window_start_position = None
        self.setup_ui()
        
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
        
        # Left side: Optional app menu button (can be added later)
        # For now, just add some padding
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
        spacer.setMinimumWidth(80)  # Minimum space for dragging
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)  # Allow it to expand
        spacer.setObjectName("dragSpacer")  # For identification
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
        logger.debug(f"ChromeTitleBar.mousePressEvent: button={event.button()}, pos={event.pos()}, globalPos={event.globalPos()}")
        
        # Check if we're clicking on a draggable area (not on tabs or buttons)
        if event.button() == Qt.LeftButton:
            # Get the widget at the click position
            child = self.childAt(event.pos())
            
            widget_info = "None" if child is None else f"{child.__class__.__name__} (objectName={child.objectName() or 'unnamed'})"
            logger.debug(f"  Widget at click position: {widget_info}")
            
            # Check if we're clicking on a draggable widget
            is_draggable = self._is_draggable_widget(child)
            logger.debug(f"  Is draggable: {is_draggable}")
            
            if is_draggable:
                # Store the initial click position relative to the window
                self.drag_start_position = event.globalPos()
                # Get the top-level window position
                top_window = self.window()
                self.window_start_position = top_window.pos()
                logger.info(f"DRAG STARTED at global position: {self.drag_start_position}, window at: {self.window_start_position}")
                logger.debug(f"  Window type: {top_window.__class__.__name__}, frameless: {bool(top_window.windowFlags() & Qt.FramelessWindowHint)}")
                event.accept()  # Accept the event to prevent propagation
            else:
                self.drag_start_position = None
                self.window_start_position = None
                logger.debug("  Not draggable - drag not started")
        
        super().mousePressEvent(event)
    
    def _is_draggable_widget(self, widget):
        """Check if a widget should allow window dragging."""
        if widget is None:
            return True  # Empty space is draggable
        
        # Check if it's the title bar itself
        if widget == self:
            return True
            
        # Check for spacer widgets (they have no specific type but are QWidget)
        if widget.__class__.__name__ == 'QWidget':
            # Check if it's not one of our interactive widgets
            if not isinstance(widget, (WindowControls, QToolButton)):
                return True
        
        # Labels are draggable
        if isinstance(widget, QLabel):
            return True
        
        # Tab bar itself is NOT draggable (to allow tab interactions)
        # But empty space on the tab bar IS draggable
        if isinstance(widget, QTabBar):
            return False
        
        # Buttons and controls are not draggable
        if isinstance(widget, (QToolButton, WindowControls)):
            return False
        
        # Check parent hierarchy - if parent is tab bar, not draggable
        parent = widget.parent()
        while parent and parent != self:
            if isinstance(parent, QTabBar):
                return False
            parent = parent.parent()
        
        return True  # Default to draggable for unknown widgets
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for window dragging and cursor updates."""
        if hasattr(self, 'drag_start_position') and self.drag_start_position is not None and event.buttons() == Qt.LeftButton:
            # Calculate the new window position based on mouse movement
            mouse_delta = event.globalPos() - self.drag_start_position
            new_window_pos = self.window_start_position + mouse_delta
            
            logger.debug(f"DRAGGING: Mouse moved by {mouse_delta}, moving window to {new_window_pos}")
            
            # Emit signal to move window to the new absolute position
            self.window_move_requested.emit(new_window_pos)
            logger.debug(f"  Emitted window_move_requested signal with new position: {new_window_pos}")
        elif event.buttons() == Qt.NoButton:
            # Not dragging - update cursor based on what we're hovering over
            child = self.childAt(event.pos())
            if self._is_draggable_widget(child):
                self.setCursor(Qt.ArrowCursor)  # Normal cursor for draggable areas
            else:
                self.setCursor(Qt.ArrowCursor)  # Keep arrow for non-draggable too
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to stop dragging."""
        if hasattr(self, 'drag_start_position') and self.drag_start_position is not None:
            logger.info(f"DRAG ENDED at position: {event.globalPos()}")
        self.drag_start_position = None
        self.window_start_position = None
        super().mouseReleaseEvent(event)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click to maximize/restore window."""
        # Only maximize if double-clicking on draggable area
        child = self.childAt(event.pos())
        if self._is_draggable_widget(child):
            self.maximize_window.emit()
            event.accept()
        
        super().mouseDoubleClickEvent(event)
    
    def set_maximized(self, maximized: bool):
        """Update the maximize button state."""
        self.is_maximized = maximized
        self.window_controls.set_maximized(maximized)
    
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