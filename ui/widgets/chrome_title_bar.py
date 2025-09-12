#!/usr/bin/env python3
"""
Chrome-style title bar widget that integrates tabs with window controls.
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTabBar, 
    QToolButton, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QPoint, QRect, QTimer, QSize
from PySide6.QtGui import QMouseEvent, QPalette, QColor
from ui.widgets.window_controls import WindowControls
from ui import vscode_theme
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
        # Allow tabs to expand to fill available space
        self.setExpanding(True)
        # Don't use document mode - it creates a full-width baseline
        self.setDocumentMode(False)
        
        # Set shape for Chrome-like appearance
        self.setShape(QTabBar.RoundedNorth)
        
        # Allow tab bar to expand to fill available width
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Disable scrolling - tabs will shrink instead
        self.setUsesScrollButtons(False)
        
        # Override cursor to use default arrow instead of move cursor
        self.setCursor(Qt.ArrowCursor)
        
        # Configure appearance
        self.setup_style()
    
    def setup_style(self):
        """Apply Chrome-like styling to the tab bar."""
        logger.debug("Applying Chrome tab bar styles")
        self.setStyleSheet(f"""
            QTabBar {{
                background: transparent;
                border: none;
            }}
            QTabBar::tab {{
                background: {vscode_theme.CHROME_TAB_INACTIVE_BACKGROUND};
                color: {vscode_theme.TAB_INACTIVE_FOREGROUND};
                padding: 4px 10px 4px 10px;
                margin: 0;
                margin-right: 2px;
                margin-top: 3px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-left: 1px solid rgba(255, 255, 255, 0.15);
                border-top: 1px solid rgba(255, 255, 255, 0.15);
                border-right: 1px solid rgba(0, 0, 0, 0.3);
                border-bottom: none;
                min-width: 50px;
                max-width: 240px;
                height: 22px;
                line-height: 14px;
            }}
            QTabBar::tab:selected {{
                background: {vscode_theme.PANE_HEADER_BACKGROUND};
                color: #ffffff;
                margin: 0;
                margin-right: 2px;
                margin-top: 1px;
                padding: 5px 10px 5px 10px;
                border-left: 1px solid rgba(255, 255, 255, 0.2);
                border-top: 1px solid rgba(255, 255, 255, 0.2);
                border-right: 1px solid rgba(255, 255, 255, 0.2);
                border-bottom: none;
                height: 24px;
                line-height: 14px;
            }}
            QTabBar::tab:hover:!selected {{
                background: {vscode_theme.LIST_HOVER_BACKGROUND};
                border-left: 1px solid rgba(255, 255, 255, 0.18);
                border-top: 1px solid rgba(255, 255, 255, 0.18);
                border-right: 1px solid rgba(0, 0, 0, 0.3);
                border-bottom: none;
            }}
            QTabBar::close-button {{
                image: none;
                width: 16px;
                height: 16px;
                background: transparent;
                border-radius: 8px;
            }}
            QTabBar::close-button:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
        """)
    
    
    def enterEvent(self, event):
        """Override enter event to set arrow cursor."""
        self.setCursor(Qt.ArrowCursor)
        super().enterEvent(event)
    
    def mouseMoveEvent(self, event):
        """Override mouse move to maintain arrow cursor."""
        # Keep arrow cursor instead of move cursor
        self.setCursor(Qt.ArrowCursor)
        super().mouseMoveEvent(event)
    
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_maximized = False
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the title bar UI."""
        # Set fixed height like Chrome
        self.setFixedHeight(28)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(vscode_theme.CHROME_TITLE_BAR_BACKGROUND))
        self.setPalette(palette)
        
        # Remove any focus outline/border and ensure no margins
        self.setStyleSheet("""
            ChromeTitleBar {
                outline: none;
                border: none;
                margin: 0;
                padding: 0;
            }
            ChromeTitleBar:focus {
                outline: none;
                border: none;
            }
        """)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create a wrapper widget for tabs and button - NO LAYOUT
        self.tabs_wrapper = QWidget()
        self.tabs_wrapper.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.tabs_wrapper.setFixedHeight(28)
        self.tabs_wrapper.setObjectName("tabsWrapper")  # For identification
        
        # Tab bar as child of wrapper (no layout - manual positioning)
        self.tab_bar = ChromeTabBar(self.tabs_wrapper)
        self.tab_bar.currentChanged.connect(self.tab_changed.emit)
        self.tab_bar.tabCloseRequested.connect(self.tab_close_requested.emit)
        self.tab_bar.new_tab_requested.connect(self.new_tab_requested.emit)
        self.tab_bar.move(0, 0)  # Position at top-left of wrapper
        
        # Add new tab button as child of wrapper (no layout)
        self.new_tab_btn = QToolButton(self.tabs_wrapper)
        self.new_tab_btn.setText("+")
        self.new_tab_btn.setFixedSize(22, 22)
        self.new_tab_btn.clicked.connect(self.new_tab_requested.emit)
        self.new_tab_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                border: none;
                color: #888888;
                font-size: 14px;
                border-radius: 11px;
            }
            QToolButton:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #cccccc;
            }
        """)
        # Position will be set in update_container_size
        
        # Add wrapper to main layout
        main_layout.addWidget(self.tabs_wrapper)
        
        # Add draggable spacing between tabs and window controls
        # This will expand to fill all available space
        spacer = QWidget()
        spacer.setMinimumWidth(80)  # Minimum space for dragging
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        spacer.setObjectName("dragSpacer")  # For identification
        main_layout.addWidget(spacer, 1)  # Stretch factor 1 to take remaining space
        
        # Right side: Window controls
        self.window_controls = WindowControls(self)
        self.window_controls.minimize_clicked.connect(self.minimize_window.emit)
        self.window_controls.maximize_clicked.connect(self.maximize_window.emit)
        self.window_controls.close_clicked.connect(self.close_window.emit)
        main_layout.addWidget(self.window_controls)
        
        # Enable mouse tracking for drag detection
        self.setMouseTracking(True)
        
        # Set initial container size
        self.update_container_size()
        
        # Also update after a delay to handle initial layout
        QTimer.singleShot(100, self.update_container_size)
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for window dragging."""
        if event.button() == Qt.LeftButton:
            # Get the widget at the click position
            child = self.childAt(event.pos())
            
            # Check if we're clicking on a draggable widget
            if self._is_draggable_widget(child):
                # Use Qt's native system move (cross-platform)
                window = self.window()
                if hasattr(window, 'windowHandle') and window.windowHandle():
                    window.windowHandle().startSystemMove()
                    logger.debug("Started native system move")
                else:
                    logger.warning("Window handle not available for system move")
                event.accept()
        
        super().mousePressEvent(event)
    
    def _is_draggable_widget(self, widget):
        """Check if a widget should allow window dragging."""
        if widget is None:
            return True  # Empty space is draggable
        
        # Check if it's the title bar itself
        if widget == self:
            return True
        
        # Check if it's our tabs wrapper - check if we're on empty space
        if hasattr(self, 'tabs_wrapper') and widget == self.tabs_wrapper:
            # The wrapper itself is draggable (empty areas between/around tabs)
            return True
            
        # Check for spacer widgets (they have no specific type but are QWidget)
        if widget.__class__.__name__ == 'QWidget':
            # Check if it's the drag spacer specifically
            if widget.objectName() == "dragSpacer":
                return True
            # Other generic QWidgets might not be draggable
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
        index = self.tab_bar.addTab(text)
        self.update_container_size()
        return index
    
    def remove_tab(self, index: int):
        """Remove a tab from the tab bar."""
        self.tab_bar.removeTab(index)
        self.update_container_size()
    
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
    
    def showEvent(self, event):
        """Handle show event to update layout after window is visible."""
        super().showEvent(event)
        # Update container size once window is shown and has valid geometry
        QTimer.singleShot(50, self.update_container_size)
    
    def resizeEvent(self, event):
        """Handle resize event to update tab layout."""
        super().resizeEvent(event)
        # Update container size when window is resized
        self.update_container_size()
    
    def update_container_size(self):
        """Update the wrapper widget and manually position children."""
        if not hasattr(self, 'tabs_wrapper') or not hasattr(self, 'tab_bar'):
            return
            
        # Ensure tab bar has valid geometry
        if not self.tab_bar.isVisible():
            return
        
        # Get the total width available in the title bar
        title_bar_width = self.width()
        
        # Reserve space for:
        # - Left spacer (8px)
        # - Window controls (approximately 120px)
        # - Minimum drag area (100px)
        # - New tab button (30px including gap)
        reserved_space = 8 + 120 + 100 + 30
        
        # Calculate maximum width available for tab bar
        max_tab_bar_width = title_bar_width - reserved_space
        
        # Since setExpanding(True), tab bar will use all available width
        # Just constrain it to the maximum
        if max_tab_bar_width > 0:
            tab_bar_width = max_tab_bar_width
            tab_bar_height = 28  # Full height of the container
            
            # Size the tab bar to use full available width and height
            self.tab_bar.resize(tab_bar_width, tab_bar_height)
            
            # Position the + button right after the tab bar
            self.new_tab_btn.move(tab_bar_width + 2, 2)
            
            # Calculate total wrapper width
            total_width = tab_bar_width + 2 + 22  # tab bar + gap + button
            
            # Update wrapper to use the calculated width
            self.tabs_wrapper.setFixedWidth(total_width)
            
            # Debug output
            logger.debug(f"Title bar width: {title_bar_width}, tab bar width: {tab_bar_width}")
            logger.debug(f"Wrapper width: {total_width}, drag space: {title_bar_width - total_width - 120}")