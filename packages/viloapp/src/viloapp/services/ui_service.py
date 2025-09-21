#!/usr/bin/env python3
"""
UI service for managing user interface state and operations.

This service handles theme management, sidebar visibility, menu bar state,
and other UI-related operations.
"""

import logging
from typing import Any

from viloapp.services.base import Service

logger = logging.getLogger(__name__)


class UIService(Service):
    """
    Service for managing UI state and operations.

    Handles theme switching, sidebar management, menu bar visibility,
    status bar messages, and other UI-related functionality.
    """

    def __init__(self, main_window=None):
        """
        Initialize the UI service.

        Args:
            main_window: Optional MainWindow instance
        """
        super().__init__("UIService")
        self._main_window = main_window
        self._sidebar_visible = True
        self._menu_bar_visible = True
        self._current_theme = "dark"
        self._sidebar_view = "explorer"
        # Use the same settings as main.py for consistency
        from viloapp.core.settings.config import get_settings

        self._settings = get_settings("ViloxTerm", "ViloxTerm")

    def initialize(self, context: dict[str, Any]) -> None:
        """Initialize the service with application context."""
        super().initialize(context)

        # Get main window from context if not provided
        if not self._main_window:
            self._main_window = context.get("main_window")

        # Load saved UI state
        self._load_ui_state()

        if not self._main_window:
            logger.warning("UIService initialized without main window reference")

    def cleanup(self) -> None:
        """Cleanup service resources."""
        # Save UI state before cleanup
        self._save_ui_state()
        self._main_window = None
        super().cleanup()

    def get_main_window(self):
        """Get the main window instance."""
        return self._main_window

    def is_frameless_mode_enabled(self) -> bool:
        """Check if frameless mode is enabled."""
        return self._settings.value("UI/FramelessMode", False, type=bool)

    def toggle_frameless_mode(self) -> bool:
        """
        Toggle frameless window mode.
        Note: Requires application restart to take effect.

        Returns:
            True if frameless mode is now enabled, False if disabled
        """
        current = self.is_frameless_mode_enabled()
        new_mode = not current
        self._settings.setValue("UI/FramelessMode", new_mode)
        self._settings.sync()

        # Log for debugging
        logger.info(f"Toggled frameless mode from {current} to {new_mode}")
        logger.info(f"Settings file: {self._settings.fileName()}")
        logger.info(f"Verified setting value: {self._settings.value('UI/FramelessMode')}")

        return new_mode

    def get_window_state(self) -> str:
        """
        Get the current window state.

        Returns:
            'normal', 'minimized', 'maximized', or 'fullscreen'
        """
        if not self._main_window:
            return "normal"

        if self._main_window.isFullScreen():
            return "fullscreen"
        elif self._main_window.isMaximized():
            return "maximized"
        elif self._main_window.isMinimized():
            return "minimized"
        else:
            return "normal"

    # ============= Theme Management =============

    def toggle_theme(self) -> str:
        """
        Toggle between light and dark theme.

        Returns:
            The new theme name ("light" or "dark")
        """
        self.validate_initialized()

        # Import here to avoid circular dependency
        from viloapp.ui.icon_manager import get_icon_manager

        icon_manager = get_icon_manager()
        icon_manager.toggle_theme()

        self._current_theme = icon_manager.theme

        # Update status bar if available
        if self._main_window and hasattr(self._main_window, "status_bar"):
            self._main_window.status_bar.set_message(
                f"Switched to {self._current_theme.capitalize()} theme", 2000
            )

        # Save theme preference
        self._settings.setValue("theme", self._current_theme)

        # Notify observers
        self.notify("theme_changed", {"theme": self._current_theme})

        logger.info(f"Theme toggled to: {self._current_theme}")
        return self._current_theme

    def set_theme(self, theme: str) -> bool:
        """
        Set a specific theme.

        Args:
            theme: "light" or "dark"

        Returns:
            True if theme was set successfully
        """
        self.validate_initialized()

        if theme not in ["light", "dark"]:
            logger.error(f"Invalid theme: {theme}")
            return False

        from viloapp.ui.icon_manager import get_icon_manager

        icon_manager = get_icon_manager()
        icon_manager.theme = theme

        self._current_theme = theme
        self._settings.setValue("theme", theme)

        # Notify observers
        self.notify("theme_changed", {"theme": theme})

        logger.info(f"Theme set to: {theme}")
        return True

    def get_current_theme(self) -> str:
        """
        Get the current theme.

        Returns:
            Current theme name
        """
        return self._current_theme

    # ============= Sidebar Management =============

    def toggle_sidebar(self) -> bool:
        """
        Toggle sidebar visibility.

        Returns:
            New visibility state (True if visible)
        """
        self.validate_initialized()

        if not self._main_window:
            return False

        # Call main window's toggle method
        self._main_window.toggle_sidebar()
        self._sidebar_visible = not self._sidebar_visible

        # Save state
        self._settings.setValue("sidebar_visible", self._sidebar_visible)

        # Notify observers
        self.notify("sidebar_toggled", {"visible": self._sidebar_visible})

        logger.info(f"Sidebar toggled, visible: {self._sidebar_visible}")
        return self._sidebar_visible

    def show_sidebar(self) -> None:
        """Show the sidebar."""
        if not self._sidebar_visible:
            self.toggle_sidebar()

    def hide_sidebar(self) -> None:
        """Hide the sidebar."""
        if self._sidebar_visible:
            self.toggle_sidebar()

    def is_sidebar_visible(self) -> bool:
        """
        Check if sidebar is visible.

        Returns:
            True if sidebar is visible
        """
        return self._sidebar_visible

    def set_sidebar_view(self, view_name: str) -> bool:
        """
        Set the active sidebar view.

        Args:
            view_name: Name of the view ("explorer", "search", "git", "settings")

        Returns:
            True if view was set successfully
        """
        self.validate_initialized()

        valid_views = ["explorer", "search", "git", "settings"]
        if view_name not in valid_views:
            logger.error(f"Invalid sidebar view: {view_name}")
            return False

        if not self._main_window or not hasattr(self._main_window, "sidebar"):
            return False

        # Set the view
        self._main_window.sidebar.set_current_view(view_name)
        self._sidebar_view = view_name

        # Make sure sidebar is visible
        if not self._sidebar_visible:
            self.show_sidebar()

        # Save preference
        self._settings.setValue("sidebar_view", view_name)

        # Notify observers
        self.notify("sidebar_view_changed", {"view": view_name})

        logger.info(f"Sidebar view set to: {view_name}")
        return True

    def toggle_activity_bar(self) -> bool:
        """
        Toggle the activity bar visibility.

        Returns:
            True if activity bar is now visible, False if hidden
        """
        self.validate_initialized()

        if not self._main_window or not hasattr(self._main_window, "toggle_activity_bar"):
            logger.error("Main window doesn't support activity bar toggle")
            return False

        # Toggle and get new state
        visible = self._main_window.toggle_activity_bar()

        # Save preference
        self._settings.setValue("activity_bar_visible", visible)

        # Notify observers
        self.notify("activity_bar_toggled", {"visible": visible})

        logger.info(f"Activity bar toggled to: {'visible' if visible else 'hidden'}")
        return visible

    def get_current_sidebar_view(self) -> str:
        """
        Get the current sidebar view.

        Returns:
            Current sidebar view name
        """
        return self._sidebar_view

    # ============= Menu Bar Management =============

    def toggle_menu_bar(self) -> bool:
        """
        Toggle menu bar visibility.

        Returns:
            New visibility state (True if visible)
        """
        self.validate_initialized()

        if not self._main_window:
            return False

        # Toggle menu bar
        self._main_window.toggle_menu_bar()
        self._menu_bar_visible = not self._menu_bar_visible

        # Save state
        self._settings.setValue("menu_bar_visible", self._menu_bar_visible)

        # Notify observers
        self.notify("menu_bar_toggled", {"visible": self._menu_bar_visible})

        logger.info(f"Menu bar toggled, visible: {self._menu_bar_visible}")
        return self._menu_bar_visible

    def is_menu_bar_visible(self) -> bool:
        """
        Check if menu bar is visible.

        Returns:
            True if menu bar is visible
        """
        return self._menu_bar_visible

    # ============= Status Bar Management =============

    def set_status_message(self, message: str, timeout: int = 0) -> None:
        """
        Set a message in the status bar.

        Args:
            message: Message to display
            timeout: Timeout in milliseconds (0 for permanent)
        """
        if self._main_window and hasattr(self._main_window, "status_bar"):
            self._main_window.status_bar.set_message(message, timeout)

            # Notify observers
            self.notify("status_message", {"message": message, "timeout": timeout})

    def clear_status_message(self) -> None:
        """Clear the status bar message."""
        self.set_status_message("", 0)

    # ============= Window Management =============

    def toggle_fullscreen(self) -> bool:
        """
        Toggle fullscreen mode.

        Returns:
            True if now in fullscreen mode
        """
        self.validate_initialized()

        if not self._main_window:
            return False

        if self._main_window.isFullScreen():
            self._main_window.showNormal()
            is_fullscreen = False
        else:
            self._main_window.showFullScreen()
            is_fullscreen = True

        # Notify observers
        self.notify("fullscreen_toggled", {"fullscreen": is_fullscreen})

        logger.info(f"Fullscreen toggled: {is_fullscreen}")
        return is_fullscreen

    def reset_layout(self) -> None:
        """Reset the UI layout to defaults."""
        self.validate_initialized()

        if not self._main_window:
            return

        # Reset various UI components
        self.set_theme("dark")
        self._sidebar_visible = True
        self._menu_bar_visible = True
        self.set_sidebar_view("explorer")

        # Reset window geometry
        self._main_window.resize(1200, 800)

        # Notify observers
        self.notify("layout_reset", {})

        logger.info("UI layout reset to defaults")

    # ============= State Management =============

    def _load_ui_state(self) -> None:
        """Load saved UI state from settings."""
        try:
            # Load theme
            saved_theme = self._settings.value("theme", "dark")
            if saved_theme in ["light", "dark"]:
                self._current_theme = saved_theme

            # Load sidebar state
            self._sidebar_visible = self._settings.value("sidebar_visible", True, type=bool)
            self._sidebar_view = self._settings.value("sidebar_view", "explorer")

            # Load menu bar state
            self._menu_bar_visible = self._settings.value("menu_bar_visible", True, type=bool)

            logger.info("UI state loaded from settings")

        except Exception as e:
            logger.error(f"Failed to load UI state: {e}")

    def _save_ui_state(self) -> None:
        """Save current UI state to settings."""
        try:
            self._settings.setValue("theme", self._current_theme)
            self._settings.setValue("sidebar_visible", self._sidebar_visible)
            self._settings.setValue("sidebar_view", self._sidebar_view)
            self._settings.setValue("menu_bar_visible", self._menu_bar_visible)

            self._settings.sync()

            logger.info("UI state saved to settings")

        except Exception as e:
            logger.error(f"Failed to save UI state: {e}")

    def get_ui_state(self) -> dict[str, Any]:
        """
        Get the current UI state.

        Returns:
            Dictionary containing UI state
        """
        return {
            "theme": self._current_theme,
            "sidebar_visible": self._sidebar_visible,
            "sidebar_view": self._sidebar_view,
            "menu_bar_visible": self._menu_bar_visible,
            "window_fullscreen": (self._main_window.isFullScreen() if self._main_window else False),
        }

    def restore_ui_state(self, state: dict[str, Any]) -> None:
        """
        Restore UI state from a dictionary.

        Args:
            state: UI state dictionary
        """
        self.validate_initialized()

        # Restore theme
        if "theme" in state:
            self.set_theme(state["theme"])

        # Restore sidebar
        if "sidebar_visible" in state:
            if state["sidebar_visible"] != self._sidebar_visible:
                self.toggle_sidebar()

        if "sidebar_view" in state:
            self.set_sidebar_view(state["sidebar_view"])

        # Restore menu bar
        if "menu_bar_visible" in state:
            if state["menu_bar_visible"] != self._menu_bar_visible:
                self.toggle_menu_bar()

        logger.info("UI state restored")
