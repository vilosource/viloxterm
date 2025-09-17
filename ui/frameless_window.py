#!/usr/bin/env python3
"""
Frameless window implementation for maximizing screen real estate.
Inherits from MainWindow to preserve all functionality.
"""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui.main_window import MainWindow
from ui.widgets.custom_title_bar import CustomTitleBar

logger = logging.getLogger(__name__)


class FramelessWindow(MainWindow):
    """
    Frameless window with custom title bar.
    Preserves all MainWindow functionality while maximizing screen space.
    """

    RESIZE_BORDER = 6  # Pixels for resize hit-test area

    def __init__(self):
        """Initialize frameless window."""
        # Set frameless flag before parent init
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowSystemMenuHint |
                          Qt.WindowMinMaxButtonsHint)

        # Enable mouse tracking for resize detection
        self.setMouseTracking(True)

        # Set minimum window size
        self.setMinimumSize(400, 300)

        # Create and integrate custom title bar
        self.setup_custom_title_bar()

        # Store original geometry for maximize/restore
        self.normal_geometry = None

    def setup_custom_title_bar(self):
        """Create and integrate the custom title bar."""
        # Create custom title bar
        self.custom_title_bar = CustomTitleBar(self)

        # Connect title bar signals
        self.custom_title_bar.minimize_requested.connect(self.showMinimized)
        self.custom_title_bar.maximize_requested.connect(self.toggle_maximize)
        self.custom_title_bar.close_requested.connect(self.close)
        self.custom_title_bar.menu_requested.connect(self.show_title_bar_menu)

        # Get the current central widget
        current_central = self.centralWidget()

        # Create new container for frameless layout
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Add custom title bar at the top
        layout.addWidget(self.custom_title_bar)

        # Integrate menu bar into hamburger menu and hide native menu bar
        if self.menuBar():
            self.integrate_menu_bar()

        # Add the original central widget below
        layout.addWidget(current_central)

        # Set the new container as central widget
        self.setCentralWidget(container)

        # Update title
        self.custom_title_bar.set_title(self.windowTitle())

    def integrate_menu_bar(self):
        """Integrate the menu bar into the custom title bar."""
        menu_bar = self.menuBar()
        if menu_bar:
            # Create a consolidated menu for the hamburger button
            main_menu = self.create_consolidated_menu(menu_bar)
            self.custom_title_bar.attach_menu(main_menu)

            # Hide the original menu bar completely
            menu_bar.hide()
            menu_bar.setMaximumHeight(0)

    def create_consolidated_menu(self, menu_bar):
        """Create a consolidated menu from the menu bar."""
        from PySide6.QtWidgets import QMenu

        main_menu = QMenu(self)

        # Copy all menus from menu bar to the consolidated menu
        for action in menu_bar.actions():
            if action.menu():
                # It's a menu, add it as submenu
                submenu = main_menu.addMenu(action.text())
                for sub_action in action.menu().actions():
                    if sub_action.isSeparator():
                        submenu.addSeparator()
                    else:
                        submenu.addAction(sub_action)
            else:
                # It's a direct action
                main_menu.addAction(action)

        return main_menu

    def show_title_bar_menu(self):
        """Show the title bar menu."""
        # This is called when menu button is clicked without an attached menu
        # Could implement a custom menu here if needed
        pass

    def toggle_maximize(self):
        """Toggle between maximized and normal window state."""
        if self.isMaximized():
            self.showNormal()
            self.custom_title_bar.update_maximize_button(False)
        else:
            self.showMaximized()
            self.custom_title_bar.update_maximize_button(True)

    def setWindowTitle(self, title):
        """Override to update custom title bar."""
        super().setWindowTitle(title)
        if hasattr(self, 'custom_title_bar'):
            self.custom_title_bar.set_title(title)

    def get_resize_direction(self, pos):
        """Determine resize direction based on mouse position."""
        rect = self.rect()
        x = pos.x()
        y = pos.y()

        # Check corners first (for diagonal resizing)
        # Return combined edges for corners
        if x <= self.RESIZE_BORDER and y <= self.RESIZE_BORDER:
            return Qt.Edge.TopEdge | Qt.Edge.LeftEdge
        elif x >= rect.width() - self.RESIZE_BORDER and y <= self.RESIZE_BORDER:
            return Qt.Edge.TopEdge | Qt.Edge.RightEdge
        elif x <= self.RESIZE_BORDER and y >= rect.height() - self.RESIZE_BORDER:
            return Qt.Edge.BottomEdge | Qt.Edge.LeftEdge
        elif x >= rect.width() - self.RESIZE_BORDER and y >= rect.height() - self.RESIZE_BORDER:
            return Qt.Edge.BottomEdge | Qt.Edge.RightEdge

        # Check edges
        elif x <= self.RESIZE_BORDER:
            return Qt.Edge.LeftEdge
        elif x >= rect.width() - self.RESIZE_BORDER:
            return Qt.Edge.RightEdge
        elif y <= self.RESIZE_BORDER:
            return Qt.Edge.TopEdge
        elif y >= rect.height() - self.RESIZE_BORDER:
            return Qt.Edge.BottomEdge

        return None

    def update_cursor(self, pos):
        """Update cursor based on resize direction."""
        direction = self.get_resize_direction(pos)

        if direction == Qt.Edge.LeftEdge or direction == Qt.Edge.RightEdge:
            self.setCursor(Qt.SizeHorCursor)
        elif direction == Qt.Edge.TopEdge or direction == Qt.Edge.BottomEdge:
            self.setCursor(Qt.SizeVerCursor)
        elif direction == (Qt.Edge.TopEdge | Qt.Edge.LeftEdge) or direction == (Qt.Edge.BottomEdge | Qt.Edge.RightEdge):
            self.setCursor(Qt.SizeFDiagCursor)
        elif direction == (Qt.Edge.TopEdge | Qt.Edge.RightEdge) or direction == (Qt.Edge.BottomEdge | Qt.Edge.LeftEdge):
            self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        """Handle mouse press for resize operations."""
        if event.button() == Qt.LeftButton and not self.isMaximized():
            direction = self.get_resize_direction(event.position().toPoint())
            if direction is not None:
                # Use Wayland-compatible resize
                window_handle = self.windowHandle()
                if window_handle:
                    try:
                        window_handle.startSystemResize(direction)
                        event.accept()
                        return
                    except Exception as e:
                        logger.warning(f"startSystemResize not available: {e}")
                        # Could implement fallback resize here if needed
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for cursor updates."""
        if not self.isMaximized() and not event.buttons():
            self.update_cursor(event.position().toPoint())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        """Reset cursor when leaving window."""
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def showMaximized(self):
        """Override to update title bar button."""
        super().showMaximized()
        if hasattr(self, 'custom_title_bar'):
            self.custom_title_bar.update_maximize_button(True)

    def showNormal(self):
        """Override to update title bar button."""
        super().showNormal()
        if hasattr(self, 'custom_title_bar'):
            self.custom_title_bar.update_maximize_button(False)
