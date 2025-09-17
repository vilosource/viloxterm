#!/usr/bin/env python3
"""
Theme provider for UI components.

This module provides the bridge between the ThemeService and UI components,
managing stylesheet generation and caching.
"""

import logging
from typing import Optional

from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


class ThemeProvider(QObject):
    """
    Provides theme data and stylesheets to UI components.

    Acts as a bridge between the business logic (ThemeService) and
    the UI layer, handling stylesheet caching and updates.
    """

    # Signal emitted when theme changes
    style_changed = Signal()

    def __init__(self, theme_service):
        """
        Initialize theme provider.

        Args:
            theme_service: ThemeService instance
        """
        super().__init__()
        self._theme_service = theme_service
        self._stylesheet_cache: dict[str, str] = {}
        self._stylesheet_generator = None

        # Connect to theme changes
        theme_service.theme_changed.connect(self._on_theme_changed)
        # Connect to typography changes
        theme_service.typography_changed.connect(self._on_typography_changed)

        # Initialize stylesheet generator
        from ui.themes.stylesheet_generator import StylesheetGenerator
        self._stylesheet_generator = StylesheetGenerator(theme_service)

    def _on_theme_changed(self, colors: dict[str, str]) -> None:
        """
        Handle theme change from service.

        Args:
            colors: New theme colors
        """
        # Clear stylesheet cache
        self._stylesheet_cache.clear()

        # Notify all widgets to update
        self.style_changed.emit()

        logger.debug("Theme changed, cache cleared and widgets notified")

    def _on_typography_changed(self, typography) -> None:
        """
        Handle typography change from service.

        Args:
            typography: New typography configuration
        """
        # Clear stylesheet cache (fonts affect all stylesheets)
        self._stylesheet_cache.clear()

        # Notify all widgets to update
        self.style_changed.emit()

        logger.debug("Typography changed, cache cleared and widgets notified")

    def get_color(self, key: str, fallback: str = "#000000") -> str:
        """
        Get a color from the current theme.

        Args:
            key: Color key
            fallback: Fallback color if key not found

        Returns:
            Color value as hex string
        """
        return self._theme_service.get_color(key, fallback)

    def get_colors(self) -> dict[str, str]:
        """
        Get all colors from the current theme.

        Returns:
            Dictionary of color mappings
        """
        return self._theme_service.get_colors()

    def get_typography(self):
        """
        Get typography configuration from the current theme.

        Returns:
            ThemeTypography instance
        """
        return self._theme_service.get_typography()

    def get_font_size(self, scale: str = "base") -> int:
        """
        Get font size for a specific scale.

        Args:
            scale: Size scale key (xs, sm, base, lg, xl, 2xl, 3xl)

        Returns:
            Font size in pixels
        """
        return self._theme_service.get_font_size(scale)

    def get_font_family(self) -> str:
        """
        Get the font family from current theme.

        Returns:
            Font family string
        """
        return self._theme_service.get_font_family()

    def get_stylesheet(self, component: str) -> str:
        """
        Get stylesheet for a specific component.

        Uses caching for performance.

        Args:
            component: Component name (e.g., "main_window", "editor")

        Returns:
            Stylesheet string
        """
        # Check cache first
        if component in self._stylesheet_cache:
            return self._stylesheet_cache[component]

        # Generate stylesheet
        if self._stylesheet_generator:
            stylesheet = self._stylesheet_generator.generate(component)
            self._stylesheet_cache[component] = stylesheet
            return stylesheet

        logger.warning(f"No stylesheet generator available for {component}")
        return ""

    def get_theme_id(self) -> Optional[str]:
        """
        Get the current theme ID.

        Returns:
            Current theme ID or None
        """
        return self._theme_service.get_current_theme_id()

    def get_theme_name(self) -> str:
        """
        Get the current theme name.

        Returns:
            Current theme name or "Unknown"
        """
        theme = self._theme_service.get_current_theme()
        return theme.name if theme else "Unknown"

    def apply_theme_to_widget(self, widget, component: str) -> None:
        """
        Apply theme to a specific widget.

        Args:
            widget: QWidget to apply theme to
            component: Component name for stylesheet
        """
        try:
            stylesheet = self.get_stylesheet(component)
            if stylesheet:
                widget.setStyleSheet(stylesheet)
            else:
                logger.warning(f"No stylesheet available for component: {component}")
        except Exception as e:
            logger.error(f"Failed to apply theme to widget {component}: {e}")

    def clear_cache(self) -> None:
        """Clear the stylesheet cache."""
        self._stylesheet_cache.clear()
        logger.debug("Stylesheet cache cleared")

    def invalidate_component(self, component: str) -> None:
        """
        Invalidate cache for a specific component.

        Args:
            component: Component name to invalidate
        """
        if component in self._stylesheet_cache:
            del self._stylesheet_cache[component]
            logger.debug(f"Invalidated cache for component: {component}")
