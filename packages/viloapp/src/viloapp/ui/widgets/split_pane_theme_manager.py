#!/usr/bin/env python3
"""
Split pane theme management - handles theming for split pane widgets.

This module provides theme management functionality for split pane widgets,
including splitter styling and theme application.
"""

import logging

from viloapp.core.commands.executor import execute_command

logger = logging.getLogger(__name__)


class SplitPaneThemeManager:
    """
    Manages theming for split pane widgets.

    Handles:
    - Splitter stylesheet generation
    - Theme application
    - Color scheme management
    """

    def __init__(self):
        """Initialize the theme manager."""
        self._cached_stylesheet = None
        self._current_theme_id = None

    def get_splitter_stylesheet(self) -> str:
        """
        Get splitter stylesheet from current theme.

        Returns:
            CSS stylesheet string for QSplitter
        """
        # Get current theme through command execution
        result = execute_command("theme.getCurrentTheme")
        if result and result.success and result.value:
            theme_provider = result.value
            if hasattr(theme_provider, "get_stylesheet"):
                stylesheet = theme_provider.get_stylesheet("splitter")
                if stylesheet:
                    self._cached_stylesheet = stylesheet
                    return stylesheet

        # Fallback style
        fallback_style = """
            QSplitter::handle {
                background-color: #3e3e42;
            }
            QSplitter::handle:horizontal {
                width: 1px;
            }
            QSplitter::handle:vertical {
                height: 1px;
            }
            QSplitter::handle:hover {
                background-color: #007ACC;
            }
        """
        self._cached_stylesheet = fallback_style
        return fallback_style

    def apply_theme_to_widget(self, widget) -> bool:
        """
        Apply current theme to a split pane widget.

        Args:
            widget: The widget to apply theme to

        Returns:
            True if theme was applied successfully, False otherwise
        """
        try:
            # Get current theme through command execution
            result = execute_command("theme.getCurrentTheme")
            if result and result.success and result.value:
                theme_provider = result.value
                if hasattr(theme_provider, "_theme_service") and theme_provider._theme_service:
                    colors = theme_provider._theme_service.get_colors()
                    background_color = colors.get("editor.background", "#1e1e1e")
                    widget.setStyleSheet(
                        f"""
                        SplitPaneWidget {{
                            background-color: {background_color};
                        }}
                    """
                    )
                    logger.debug(f"Applied theme to widget with background: {background_color}")
                    return True

            # Fallback styling
            self._apply_fallback_theme(widget)
            return True

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")
            self._apply_fallback_theme(widget)
            return False

    def _apply_fallback_theme(self, widget):
        """Apply fallback theme styling."""
        widget.setStyleSheet(
            """
            SplitPaneWidget {
                background-color: #1e1e1e;
            }
        """
        )
        logger.debug("Applied fallback theme to widget")

    def get_theme_colors(self) -> dict[str, str]:
        """
        Get current theme colors.

        Returns:
            Dictionary of theme colors
        """
        try:
            result = execute_command("theme.getCurrentTheme")
            if result and result.success and result.value:
                theme_provider = result.value
                if hasattr(theme_provider, "_theme_service") and theme_provider._theme_service:
                    return theme_provider._theme_service.get_colors()
        except Exception as e:
            logger.error(f"Failed to get theme colors: {e}")

        # Return fallback colors
        return {
            "editor.background": "#1e1e1e",
            "splitter.handle": "#3e3e42",
            "splitter.handle.hover": "#007ACC",
            "pane.border.active": "#007ACC",
            "pane.border.inactive": "#3c3c3c",
        }

    def clear_cache(self):
        """Clear cached theme data."""
        self._cached_stylesheet = None
        self._current_theme_id = None
        logger.debug("Theme cache cleared")


# Global theme manager instance
_theme_manager_instance = None


def get_theme_manager() -> SplitPaneThemeManager:
    """
    Get the global theme manager instance.

    Returns:
        Global SplitPaneThemeManager instance
    """
    global _theme_manager_instance
    if _theme_manager_instance is None:
        _theme_manager_instance = SplitPaneThemeManager()
    return _theme_manager_instance
