#!/usr/bin/env python3
"""
Theme service for managing application themes.
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QFile, QTextStream, Signal

from viloapp.core.themes.theme import Theme, ThemeInfo
from viloapp.core.themes.typography import TYPOGRAPHY_PRESETS, ThemeTypography
from viloapp.services.base import Service

logger = logging.getLogger(__name__)


class ThemeService(Service):
    """
    Service for managing themes.

    Handles loading, applying, and managing both built-in and custom themes.
    """

    # Signal emitted when theme changes (emits color dictionary)
    theme_changed = Signal(dict)
    # Signal emitted when typography changes
    typography_changed = Signal(object)

    def __init__(self):
        """Initialize theme service."""
        super().__init__("ThemeService")

        self._themes: dict[str, Theme] = {}
        self._current_theme: Optional[Theme] = None
        self._user_themes_path = Path.home() / ".config/ViloxTerm/themes"
        self._theme_provider = None  # Will be set after initialization

        # Preview mode state
        self._preview_mode = False
        self._preview_backup: Optional[Theme] = None
        self._preview_colors: dict[str, str] = {}

        # Ensure user themes directory exists
        self._user_themes_path.mkdir(parents=True, exist_ok=True)

    def initialize(self, context: dict) -> None:
        """
        Initialize the service.

        Args:
            context: Application context
        """
        super().initialize(context)

        # Load all themes
        self._load_builtin_themes()
        self._load_user_themes()

        # Check if theme reset was requested via command line
        from viloapp.core.app_config import app_config

        if app_config.reset_theme:
            self.reset_to_default_theme()
        # Apply default theme
        elif not self._current_theme:
            self.apply_theme("vscode-dark")

        logger.info(f"ThemeService initialized with {len(self._themes)} themes")

    def _load_builtin_themes(self) -> None:
        """Load built-in themes from resources or filesystem."""
        from viloapp.core.app_config import app_config

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
            ":/themes/builtin/solarized-dark.json",
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

    def get_available_themes(self) -> list[ThemeInfo]:
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

        # Apply theme using internal method
        self._apply_theme_internal(theme, save=True)

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

    def get_colors(self) -> dict[str, str]:
        """
        Get all colors from the current theme.

        Returns:
            Dictionary of color key to value mappings
        """
        if self._current_theme:
            return self._current_theme.colors.copy()
        return {}

    def get_typography(self) -> ThemeTypography:
        """
        Get typography configuration from the current theme.

        Returns:
            ThemeTypography instance
        """
        if self._current_theme:
            return self._current_theme.get_typography()
        return ThemeTypography()

    def get_font_size(self, scale_key: str = "base") -> int:
        """
        Get font size for a specific scale.

        Args:
            scale_key: Size scale key (xs, sm, base, lg, xl, 2xl, 3xl)

        Returns:
            Font size in pixels
        """
        typography = self.get_typography()
        return typography.get_font_size(scale_key)

    def get_font_family(self) -> str:
        """
        Get the font family from current theme.

        Returns:
            Font family string
        """
        typography = self.get_typography()
        return typography.font_family

    def get_component_typography(self, component: str) -> dict[str, any]:
        """
        Get typography style for a specific component.

        Args:
            component: Component identifier (e.g., "editor", "terminal", "sidebar")

        Returns:
            Dictionary of typography properties for the component
        """
        typography = self.get_typography()
        return typography.get_component_style(component)

    def update_typography(self, typography_data: dict) -> None:
        """
        Update typography settings for current theme.

        Args:
            typography_data: Dictionary with typography settings
        """
        if not self._current_theme:
            return

        # Create or update typography
        if self._current_theme.typography:
            # Merge with existing
            current_data = self._current_theme.typography.to_dict()
            current_data.update(typography_data)
            self._current_theme.typography = ThemeTypography.from_dict(current_data)
        else:
            # Create new typography
            self._current_theme.typography = ThemeTypography.from_dict(typography_data)

        # Emit change signal
        self.typography_changed.emit(self._current_theme.typography)

        # If not in preview mode, save the theme
        if not self._preview_mode:
            self.save_custom_theme(self._current_theme)

    def apply_typography_preset(self, preset_name: str) -> bool:
        """
        Apply a typography preset to the current theme.

        Args:
            preset_name: Name of the preset (compact, default, comfortable, large)

        Returns:
            True if preset was applied successfully
        """
        if preset_name not in TYPOGRAPHY_PRESETS:
            logger.error(f"Typography preset not found: {preset_name}")
            return False

        if not self._current_theme:
            return False

        # Apply preset
        self._current_theme.typography = TYPOGRAPHY_PRESETS[preset_name]

        # Emit change signal
        self.typography_changed.emit(self._current_theme.typography)

        # Save if not in preview mode
        if not self._preview_mode:
            self.save_custom_theme(self._current_theme)

        logger.info(f"Applied typography preset: {preset_name}")
        return True

    def apply_theme_preview(
        self, colors: dict[str, str], typography: Optional[ThemeTypography] = None
    ) -> None:
        """
        Apply temporary theme for preview without saving.

        Args:
            colors: Dictionary of color key-value pairs to preview
            typography: Optional typography configuration to preview
        """
        if not self._preview_mode:
            # Backup current theme
            self._preview_backup = self._current_theme
            self._preview_mode = True

        # Merge preview colors with current theme
        preview_theme = Theme(
            id="__preview__",
            name="Preview",
            description="Temporary preview theme",
            version="1.0.0",
            author="Theme Editor",
            colors=({**self._current_theme.colors, **colors} if self._current_theme else colors),
            typography=typography
            or (self._current_theme.typography if self._current_theme else None),
        )

        # Store preview colors for reference
        self._preview_colors = colors

        # Apply without saving to settings
        self._apply_theme_internal(preview_theme, save=False)

    def end_preview(self) -> None:
        """End preview and restore previous theme."""
        if self._preview_mode and self._preview_backup:
            self._apply_theme_internal(self._preview_backup, save=False)
            self._preview_mode = False
            self._preview_backup = None
            self._preview_colors = {}

    def is_preview_mode(self) -> bool:
        """Check if in preview mode."""
        return self._preview_mode

    def get_preview_colors(self) -> dict[str, str]:
        """Get colors being previewed."""
        return self._preview_colors.copy()

    def _apply_theme_internal(self, theme: Theme, save: bool = True) -> None:
        """
        Internal method to apply theme.

        Args:
            theme: Theme to apply
            save: Whether to save to settings
        """
        self._current_theme = theme
        if save and not self._preview_mode and theme.id != "__preview__":
            self._save_theme_preference(theme.id)

        # Emit signals for UI updates
        self.theme_changed.emit(theme.colors)
        self.typography_changed.emit(theme.get_typography())

    def create_custom_theme(
        self, base_theme_id: str, name: str, description: str = ""
    ) -> Optional[Theme]:
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
            colors={},  # Start with empty, will inherit from base
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
            from viloapp.core.settings.config import get_settings

            settings = get_settings("ViloxTerm", "ViloxTerm")
            settings.setValue("theme/current", theme_id)
            settings.sync()
        except Exception as e:
            logger.error(f"Failed to save theme preference: {e}")

    def _load_theme_preference(self) -> Optional[str]:
        """Load theme preference from settings."""
        try:
            from viloapp.core.settings.config import get_settings

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

    def reset_to_default_theme(self) -> bool:
        """
        Reset theme to the default VS Code theme.

        Returns:
            True if reset was successful
        """
        DEFAULT_THEME_ID = "vscode-dark"

        try:
            # Clear theme preference from settings
            from viloapp.core.settings.config import get_settings

            settings = get_settings("ViloxTerm", "ViloxTerm")
            settings.remove("theme/current")
            settings.sync()

            # Apply default theme
            success = self.apply_theme(DEFAULT_THEME_ID)

            if success:
                logger.info(f"Theme reset to default: {DEFAULT_THEME_ID}")
            else:
                logger.error(f"Failed to reset theme to default: {DEFAULT_THEME_ID}")

            return success
        except Exception as e:
            logger.error(f"Failed to reset theme: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up service resources."""
        super().cleanup()
