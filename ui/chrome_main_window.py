#!/usr/bin/env python3
"""
Chrome-style main window with frameless design and integrated tab bar in title.
"""

import logging
from enum import Enum
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QApplication
from PySide6.QtCore import Qt, QPoint, QRect, Signal, QEvent, QSettings
from PySide6.QtGui import QMouseEvent, QCursor, QScreen

from ui.widgets.chrome_title_bar import ChromeTitleBar
from ui.main_window import MainWindow

logger = logging.getLogger(__name__)


class ResizeDirection(Enum):
    """Resize directions for frameless window."""
    NONE = 0
    LEFT = 1
    RIGHT = 2
    TOP = 3
    BOTTOM = 4
    TOP_LEFT = 5
    TOP_RIGHT = 6
    BOTTOM_LEFT = 7
    BOTTOM_RIGHT = 8


class ChromeMainWindow(MainWindow):
    """
    Main window with Chrome-style frameless design.
    Inherits from the existing MainWindow to maintain all functionality.
    """
    
    def __init__(self):
        # Store the chrome mode flag before calling parent init
        self.chrome_mode_enabled = self._load_chrome_mode_preference()
        
        # Initialize parent
        super().__init__()
        
        # Apply Chrome-style modifications if enabled
        if self.chrome_mode_enabled:
            self._apply_chrome_style()
    
    def _load_chrome_mode_preference(self) -> bool:
        """Load the Chrome mode preference from settings."""
        settings = QSettings()
        return settings.value("UI/ChromeMode", False, type=bool)
    
    def _apply_chrome_style(self):
        """Apply Chrome-style modifications to the window."""
        logger.info("=" * 60)
        logger.info("APPLYING CHROME-STYLE UI")
        logger.info("=" * 60)
        
        # Set frameless window hint
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint | 
                          Qt.WindowMinMaxButtonsHint)
        
        # Enable mouse tracking for resize detection
        self.setMouseTracking(True)
        
        # Resize handling variables
        self.resize_margin = 8
        self.resize_direction = ResizeDirection.NONE
        self.drag_position = None
        
        # Get the current central widget
        current_central = self.centralWidget()
        
        # Create new container for Chrome layout
        chrome_container = QWidget()
        chrome_layout = QVBoxLayout(chrome_container)
        chrome_layout.setContentsMargins(0, 0, 0, 0)
        chrome_layout.setSpacing(0)
        
        # Create and add Chrome title bar
        self.chrome_title_bar = ChromeTitleBar(self)
        chrome_layout.addWidget(self.chrome_title_bar)
        
        # Connect title bar signals
        self._connect_chrome_signals()
        
        # Transfer tabs from existing workspace to Chrome title bar
        if hasattr(self, 'workspace') and self.workspace:
            self._transfer_tabs_to_chrome()
        
        # Add the original central widget below the title bar
        chrome_layout.addWidget(current_central)
        
        # Set the new container as central widget
        self.setCentralWidget(chrome_container)
        
        # Hide the original menu bar (we'll add a menu button to title bar later)
        if self.menuBar():
            self.menuBar().setVisible(False)
        
        # Apply window shadow/border for definition
        self._apply_window_border()
    
    def _connect_chrome_signals(self):
        """Connect Chrome title bar signals to window actions."""
        logger.info("Connecting Chrome title bar signals...")
        self.chrome_title_bar.minimize_window.connect(self.showMinimized)
        self.chrome_title_bar.maximize_window.connect(self.toggle_maximize)
        self.chrome_title_bar.close_window.connect(self.close)
        # Window dragging uses Qt's native startSystemMove() now
        logger.info("  ✓ Using native system move for window dragging")
        self.chrome_title_bar.new_tab_requested.connect(self.add_new_tab)
        self.chrome_title_bar.tab_changed.connect(self.on_chrome_tab_changed)
        self.chrome_title_bar.tab_close_requested.connect(self.on_chrome_tab_close)
    
    def _transfer_tabs_to_chrome(self):
        """Transfer existing tabs to Chrome title bar."""
        if not hasattr(self.workspace, 'tab_widget'):
            return
        
        # Hide the original tab bar
        self.workspace.tab_widget.tabBar().setVisible(False)
        
        # Sync existing tabs to Chrome title bar
        for i in range(self.workspace.tab_widget.count()):
            tab_text = self.workspace.tab_widget.tabText(i)
            self.chrome_title_bar.add_tab(tab_text)
        
        # Set current tab
        current_index = self.workspace.tab_widget.currentIndex()
        if current_index >= 0:
            self.chrome_title_bar.set_current_tab(current_index)
        
        # Force update of tab bar layout after transferring tabs
        self.chrome_title_bar.update_container_size()
        
        # Re-apply styles after loading tabs to ensure they take effect
        if hasattr(self.chrome_title_bar, 'tab_bar'):
            self.chrome_title_bar.tab_bar.setup_style()
        
        # Set up ongoing tab synchronization
        self._setup_tab_synchronization()
    
    def _setup_tab_synchronization(self):
        """Set up synchronization between workspace tabs and Chrome title bar."""
        if not hasattr(self.workspace, 'tab_added') or not hasattr(self.workspace, 'tab_removed'):
            logger.warning("Workspace does not have required signals for tab synchronization")
            return
        
        # Connect workspace signals to Chrome title bar updates
        self.workspace.tab_added.connect(self.on_workspace_tab_added)
        self.workspace.tab_removed.connect(self.on_workspace_tab_removed)
        
        logger.info("Tab synchronization set up for Chrome mode")
    
    def on_workspace_tab_added(self, name: str):
        """Handle when a new tab is added to the workspace."""
        logger.info(f"Workspace tab added: {name}")
        
        # Add the tab to Chrome title bar
        index = self.chrome_title_bar.add_tab(name)
        
        # Set it as the current tab (workspace automatically switches to new tabs)
        self.chrome_title_bar.set_current_tab(index)
        
        logger.info(f"Added Chrome tab '{name}' at index {index}")
    
    def on_workspace_tab_removed(self, name: str):
        """Handle when a tab is removed from the workspace."""
        logger.info(f"Workspace tab removed: {name}")
        
        # Find the index of the tab by name and remove it
        if hasattr(self.chrome_title_bar, 'remove_tab_by_name'):
            self.chrome_title_bar.remove_tab_by_name(name)
        elif hasattr(self.chrome_title_bar, 'remove_tab'):
            # Try to find index by iterating through tabs
            for i in range(self.chrome_title_bar.tab_count() if hasattr(self.chrome_title_bar, 'tab_count') else 0):
                if hasattr(self.chrome_title_bar, 'tab_text') and self.chrome_title_bar.tab_text(i) == name:
                    self.chrome_title_bar.remove_tab(i)
                    break
        else:
            logger.warning("Chrome title bar does not support tab removal")
    
    def _apply_window_border(self):
        """Apply a subtle border/shadow for window definition."""
        self.setStyleSheet("""
            ChromeMainWindow {
                border: 1px solid #2d2d30;
            }
        """)
    
    def toggle_maximize(self):
        """Toggle between maximized and normal window state."""
        if self.isMaximized():
            self.showNormal()
            self.chrome_title_bar.set_maximized(False)
        else:
            self.showMaximized()
            self.chrome_title_bar.set_maximized(True)
    
    # Note: move_window method removed - using native system move in ChromeTitleBarFixed
    
    def add_new_tab(self):
        """Add a new tab through the workspace."""
        if hasattr(self, 'workspace'):
            # Use the existing workspace method to add a tab
            index = self.workspace.add_editor_tab("New Tab")
            # Sync to Chrome title bar
            self.chrome_title_bar.add_tab("New Tab")
            self.chrome_title_bar.set_current_tab(index)
    
    def on_chrome_tab_changed(self, index: int):
        """Handle tab change from Chrome title bar using command."""
        from core.commands.executor import execute_command
        # Use command to switch tabs (which will also update Chrome via the command)
        execute_command("workbench.action.selectTab", tab_index=index)
    
    def on_chrome_tab_close(self, index: int):
        """Handle tab close request from Chrome title bar."""
        if hasattr(self, 'workspace') and self.workspace:
            # Don't close the last tab
            if self.workspace.tab_widget.count() > 1:
                self.workspace.close_tab(index)
    
    def get_resize_direction(self, pos: QPoint) -> ResizeDirection:
        """Determine resize direction based on mouse position."""
        rect = self.rect()
        margin = self.resize_margin
        
        # Check corners first (they take priority)
        if pos.x() <= margin and pos.y() <= margin:
            return ResizeDirection.TOP_LEFT
        elif pos.x() >= rect.width() - margin and pos.y() <= margin:
            return ResizeDirection.TOP_RIGHT
        elif pos.x() <= margin and pos.y() >= rect.height() - margin:
            return ResizeDirection.BOTTOM_LEFT
        elif pos.x() >= rect.width() - margin and pos.y() >= rect.height() - margin:
            return ResizeDirection.BOTTOM_RIGHT
        # Then check edges
        elif pos.x() <= margin:
            return ResizeDirection.LEFT
        elif pos.x() >= rect.width() - margin:
            return ResizeDirection.RIGHT
        elif pos.y() <= margin:
            return ResizeDirection.TOP
        elif pos.y() >= rect.height() - margin:
            return ResizeDirection.BOTTOM
        
        return ResizeDirection.NONE
    
    def update_cursor(self, direction: ResizeDirection):
        """Update cursor based on resize direction."""
        cursors = {
            ResizeDirection.LEFT: Qt.SizeHorCursor,
            ResizeDirection.RIGHT: Qt.SizeHorCursor,
            ResizeDirection.TOP: Qt.SizeVerCursor,
            ResizeDirection.BOTTOM: Qt.SizeVerCursor,
            ResizeDirection.TOP_LEFT: Qt.SizeFDiagCursor,
            ResizeDirection.BOTTOM_RIGHT: Qt.SizeFDiagCursor,
            ResizeDirection.TOP_RIGHT: Qt.SizeBDiagCursor,
            ResizeDirection.BOTTOM_LEFT: Qt.SizeBDiagCursor,
            ResizeDirection.NONE: Qt.ArrowCursor
        }
        self.setCursor(cursors[direction])
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse press for resize operations."""
        if self.chrome_mode_enabled and event.button() == Qt.LeftButton:
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction != ResizeDirection.NONE:
                self.drag_position = event.globalPos()
                event.accept()
                return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse move for resize cursor and operations."""
        if not self.chrome_mode_enabled:
            super().mouseMoveEvent(event)
            return
        
        if self.drag_position is not None and event.buttons() == Qt.LeftButton:
            # Perform resize
            diff = event.globalPos() - self.drag_position
            self.drag_position = event.globalPos()
            
            rect = self.geometry()
            
            if self.resize_direction == ResizeDirection.LEFT:
                rect.setLeft(rect.left() + diff.x())
            elif self.resize_direction == ResizeDirection.RIGHT:
                rect.setRight(rect.right() + diff.x())
            elif self.resize_direction == ResizeDirection.TOP:
                rect.setTop(rect.top() + diff.y())
            elif self.resize_direction == ResizeDirection.BOTTOM:
                rect.setBottom(rect.bottom() + diff.y())
            elif self.resize_direction == ResizeDirection.TOP_LEFT:
                rect.setTopLeft(rect.topLeft() + diff)
            elif self.resize_direction == ResizeDirection.TOP_RIGHT:
                rect.setTopRight(rect.topRight() + diff)
            elif self.resize_direction == ResizeDirection.BOTTOM_LEFT:
                rect.setBottomLeft(rect.bottomLeft() + diff)
            elif self.resize_direction == ResizeDirection.BOTTOM_RIGHT:
                rect.setBottomRight(rect.bottomRight() + diff)
            
            # Apply minimum size constraints
            if rect.width() >= self.minimumWidth() and rect.height() >= self.minimumHeight():
                self.setGeometry(rect)
        else:
            # Update cursor based on position
            direction = self.get_resize_direction(event.pos())
            self.update_cursor(direction)
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Handle mouse release to stop resize."""
        if self.chrome_mode_enabled:
            self.resize_direction = ResizeDirection.NONE
            self.drag_position = None
            self.update_cursor(ResizeDirection.NONE)
        
        super().mouseReleaseEvent(event)
    
    def changeEvent(self, event: QEvent):
        """Handle window state changes."""
        if event.type() == QEvent.WindowStateChange:
            if hasattr(self, 'chrome_title_bar'):
                self.chrome_title_bar.set_maximized(self.isMaximized())
        
        super().changeEvent(event)
    
    def save_state(self):
        """Save window state including Chrome mode preference."""
        super().save_state()
        
        # Save Chrome mode preference
        settings = QSettings()
        settings.setValue("UI/ChromeMode", self.chrome_mode_enabled)
    
    def toggle_chrome_mode(self):
        """Toggle between Chrome-style and traditional UI."""
        self.chrome_mode_enabled = not self.chrome_mode_enabled
        
        # Save preference
        settings = QSettings()
        settings.setValue("UI/ChromeMode", self.chrome_mode_enabled)
        
        # Notify user that restart is required
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "Restart Required",
            "Please restart the application for the UI change to take effect."
        )