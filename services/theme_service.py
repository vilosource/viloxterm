#!/usr/bin/env python3
"""
Theme service for managing application themes.
"""

from typing import Dict, List, Optional
from pathlib import Path
from PySide6.QtCore import Signal, QFile, QTextStream
import json
import logging

from services.base import Service
from core.themes.theme import Theme, ThemeInfo
from core.themes.schema import ThemeSchema

logger = logging.getLogger(__name__)


class ThemeService(Service):
    """
    Service for managing themes.

    Handles loading, applying, and managing both built-in and custom themes.
    """

    # Signal emitted when theme changes (emits color dictionary)
    theme_changed = Signal(dict)

    def __init__(self):
        """Initialize theme service."""
        super().__init__("ThemeService")

        self._themes: Dict[str, Theme] = {}
        self._current_theme: Optional[Theme] = None
        self._user_themes_path = Path.home() / ".config/ViloxTerm/themes"
        self._theme_provider = None  # Will be set after initialization

        # Ensure user themes directory exists
        self._user_themes_path.mkdir(parents=True, exist_ok=True)

    def initialize(self, context: Dict) -> None:
        """
        Initialize the service.

        Args:
            context: Application context
        """
        super().initialize(context)

        # Load all themes
        self._load_builtin_themes()
        self._load_user_themes()

        # Apply default theme
        if not self._current_theme:
            self.apply_theme("vscode-dark")

        logger.info(f"ThemeService initialized with {len(self._themes)} themes")

    def _load_builtin_themes(self) -> None:
        """Load built-in themes from resources or filesystem."""
        from core.app_config import app_config

        if app_config.production_mode:
            # Load from Qt resources
            self._load_themes_from_resources()
        else:
            # Load from filesystem for development
            themes_dir = Path(__file__).parent.parent / "resources/themes/builtin"
            if themes_dir.exists():
                self._load_themes_from_directory(themes_dir)
            else:
                logger.warning(f"Builtin themes directory not found: {themes_dir}")

    def _load_themes_from_resources(self) -> None:
        """Load themes from Qt resources."""
        theme_files = [
            ":/themes/builtin/vscode-dark.json",
            ":/themes/builtin/vscode-light.json",
            ":/themes/builtin/monokai.json",
            ":/themes/builtin/solarized-dark.json"
        ]

        for resource_path in theme_files:
            try:
                file = QFile(resource_path)
                if file.open(QFile.ReadOnly):
                    stream = QTextStream(file)
                    json_str = stream.readAll()
                    file.close()

                    theme = Theme.from_json(json_str)
                    self._themes[theme.id] = theme
                    logger.debug(f"Loaded theme from resource: {theme.id}")
                else:
                    logger.warning(f"Could not open theme resource: {resource_path}")
            except Exception as e:
                logger.error(f"Failed to load theme from {resource_path}: {e}")

    def _load_themes_from_directory(self, directory: Path) -> None:
        """
        Load themes from a directory.

        Args:
            directory: Directory containing theme JSON files
        """
        if not directory.exists():
            return

        for theme_file in directory.glob("*.json"):
            try:
                theme = Theme.from_json_file(theme_file)

                # Validate theme
                is_valid, errors = theme.validate()
                if not is_valid:
                    logger.warning(f"Theme {theme.id} validation errors: {errors}")
                    continue

                self._themes[theme.id] = theme
                logger.debug(f"Loaded theme: {theme.id} from {theme_file}")
            except Exception as e:
                logger.error(f"Failed to load theme from {theme_file}: {e}")

    def _load_user_themes(self) -> None:
        """Load custom user themes."""
        self._load_themes_from_directory(self._user_themes_path)

    def get_available_themes(self) -> List[ThemeInfo]:
        """
        Get list of available themes.

        Returns:
            List of theme information
        """
        return [theme.get_info() for theme in self._themes.values()]

    def get_theme(self, theme_id: str) -> Optional[Theme]:
        """
        Get a theme by ID.

        Args:
            theme_id: Theme identifier

        Returns:
            Theme instance or None if not found
        """
        return self._themes.get(theme_id)

    def get_current_theme(self) -> Optional[Theme]:
        """
        Get the currently active theme.

        Returns:
            Current theme or None
        """
        return self._current_theme

    def get_current_theme_id(self) -> Optional[str]:
        """
        Get the ID of the current theme.

        Returns:
            Current theme ID or None
        """
        return self._current_theme.id if self._current_theme else None

    def apply_theme(self, theme_id: str) -> bool:
        """
        Apply a theme by ID.

        Args:
            theme_id: Theme identifier

        Returns:
            True if theme was applied successfully
        """
        theme = self._themes.get(theme_id)
        if not theme:
            logger.error(f"Theme not found: {theme_id}")
            return False

        # Handle theme inheritance
        if theme.extends:
            parent_theme = self._themes.get(theme.extends)
            if parent_theme:
                theme.merge_with_parent(parent_theme)
            else:
                logger.warning(f"Parent theme not found: {theme.extends}")

        # Set current theme
        self._current_theme = theme

        # Emit change signal with color dictionary
        self.theme_changed.emit(theme.colors)

        # Save preference
        self._save_theme_preference(theme_id)

        logger.info(f"Applied theme: {theme_id}")
        return True

    def get_color(self, key: str, fallback: str = "#000000") -> str:
        """
        Get a color from the current theme.

        Args:
            key: Color key
            fallback: Fallback color if key not found

        Returns:
            Color value as hex string
        """
        if self._current_theme:
            return self._current_theme.get_color(key, fallback)
        return fallback

    def get_colors(self) -> Dict[str, str]:
        """
        Get all colors from the current theme.

        Returns:
            Dictionary of color key to value mappings
        """
        if self._current_theme:
            return self._current_theme.colors.copy()
        return {}

    def create_custom_theme(self, base_theme_id: str, name: str,
                          description: str = "") -> Optional[Theme]:
        """
        Create a new custom theme based on an existing theme.

        Args:
            base_theme_id: ID of theme to base on
            name: Name for the new theme
            description: Theme description

        Returns:
            New theme instance or None if base not found
        """
        base_theme = self._themes.get(base_theme_id)
        if not base_theme:
            logger.error(f"Base theme not found: {base_theme_id}")
            return None

        # Generate unique ID
        theme_id = name.lower().replace(" ", "-")
        if theme_id in self._themes:
            # Add number suffix if ID exists
            counter = 1
            while f"{theme_id}-{counter}" in self._themes:
                counter += 1
            theme_id = f"{theme_id}-{counter}"

        # Create new theme
        new_theme = Theme(
            id=theme_id,
            name=name,
            description=description or f"Custom theme based on {base_theme.name}",
            version="1.0.0",
            author="User",
            extends=base_theme_id,
            colors={}  # Start with empty, will inherit from base
        )

        # Apply inheritance
        new_theme.merge_with_parent(base_theme)

        # Add to themes
        self._themes[theme_id] = new_theme

        logger.info(f"Created custom theme: {theme_id}")
        return new_theme

    def save_custom_theme(self, theme: Theme) -> bool:
        """
        Save a custom theme to disk.

        Args:
            theme: Theme to save

        Returns:
            True if saved successfully
        """
        try:
            theme_path = self._user_themes_path / f"{theme.id}.json"
            theme.to_json_file(theme_path)
            logger.info(f"Saved custom theme: {theme.id} to {theme_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save theme {theme.id}: {e}")
            return False

    def delete_custom_theme(self, theme_id: str) -> bool:
        """
        Delete a custom theme.

        Args:
            theme_id: Theme identifier

        Returns:
            True if deleted successfully
        """
        # Don't allow deleting built-in themes
        theme_path = self._user_themes_path / f"{theme_id}.json"
        if not theme_path.exists():
            logger.error(f"Cannot delete theme {theme_id}: not a custom theme")
            return False

        try:
            theme_path.unlink()
            if theme_id in self._themes:
                del self._themes[theme_id]
            logger.info(f"Deleted custom theme: {theme_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete theme {theme_id}: {e}")
            return False

    def import_theme(self, file_path: Path) -> Optional[str]:
        """
        Import a theme from a file.

        Args:
            file_path: Path to theme file

        Returns:
            Theme ID if imported successfully, None otherwise
        """
        try:
            theme = Theme.from_json_file(file_path)

            # Validate
            is_valid, errors = theme.validate()
            if not is_valid:
                logger.error(f"Invalid theme: {errors}")
                return None

            # Check for ID conflict
            if theme.id in self._themes:
                # Generate new ID
                base_id = theme.id
                counter = 1
                while f"{base_id}-imported-{counter}" in self._themes:
                    counter += 1
                theme.id = f"{base_id}-imported-{counter}"

            # Save to user themes
            self.save_custom_theme(theme)

            # Add to loaded themes
            self._themes[theme.id] = theme

            logger.info(f"Imported theme: {theme.id}")
            return theme.id
        except Exception as e:
            logger.error(f"Failed to import theme from {file_path}: {e}")
            return None

    def export_theme(self, theme_id: str, file_path: Path) -> bool:
        """
        Export a theme to a file.

        Args:
            theme_id: Theme identifier
            file_path: Path to save theme

        Returns:
            True if exported successfully
        """
        theme = self._themes.get(theme_id)
        if not theme:
            logger.error(f"Theme not found: {theme_id}")
            return False

        try:
            theme.to_json_file(file_path)
            logger.info(f"Exported theme {theme_id} to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export theme {theme_id}: {e}")
            return False

    def _save_theme_preference(self, theme_id: str) -> None:
        """Save theme preference to settings."""
        try:
            from core.settings.config import get_settings
            settings = get_settings("ViloxTerm", "ViloxTerm")
            settings.setValue("theme/current", theme_id)
            settings.sync()
        except Exception as e:
            logger.error(f"Failed to save theme preference: {e}")

    def _load_theme_preference(self) -> Optional[str]:
        """Load theme preference from settings."""
        try:
            from core.settings.config import get_settings
            settings = get_settings("ViloxTerm", "ViloxTerm")
            return settings.value("theme/current", "vscode-dark")
        except Exception as e:
            logger.error(f"Failed to load theme preference: {e}")
            return None

    def set_theme_provider(self, theme_provider) -> None:
        """Set the theme provider reference."""
        self._theme_provider = theme_provider

    def get_theme_provider(self):
        """Get the theme provider."""
        return self._theme_provider

    def cleanup(self) -> None:
        """Clean up service resources."""
        super().cleanup()