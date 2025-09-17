#!/usr/bin/env python3
"""
Application defaults configuration with validation and fallback system.

This module defines user-configurable application defaults that control
the behavior of various features throughout the application. All settings
are validated and have safe fallbacks to prevent crashes.
"""

import logging
from typing import Any, Callable

from PySide6.QtCore import QSettings

logger = logging.getLogger(__name__)


# ============= Hard-coded Ultimate Fallbacks =============
# These are the last line of defense, used when everything else fails
HARD_CODED_FALLBACKS = {
    "workspace.default_new_tab_widget": "terminal",
    "workspace.tab_auto_naming_pattern": "{type} {index}",
    "workspace.max_tabs": 20,
    "workspace.close_last_tab_behavior": "create_default",
    "workspace.restore_tabs_on_startup": True,
    "workspace.confirm_close_unsaved_tab": True,
    "pane.default_split_direction": "horizontal",
    "pane.default_split_ratio": 0.5,
    "pane.minimum_width": 200,
    "pane.minimum_height": 100,
    "pane.focus_new_on_split": True,
    "pane.default_widget": "same",
    "terminal.default_shell": "auto",
    "terminal.starting_directory": "home",
    "terminal.inherit_environment": True,
    "terminal.close_on_exit": "always",
    "editor.default_file_type": "text",
    "editor.default_encoding": "utf-8",
    "editor.create_untitled": True,
    "editor.auto_detect_language": True,
    "ui.default_window_width": 1200,
    "ui.default_window_height": 800,
    "ui.window_position": "center",
    "ui.start_maximized": False,
    "ui.start_fullscreen": False,
    "ui.sidebar_visible_on_start": True,
    "ui.default_sidebar_width": 300,
    "ui.show_status_bar": True,
    "ux.confirm_app_exit": True,
    "ux.confirm_reload_window": True,
    "ux.show_notifications": True,
    "ux.notification_duration": 5000,
    "ux.animation_speed": 1.0,
    "ux.enable_animations": True,
}


class AppDefaultsValidator:
    """Validates and sanitizes application settings."""

    @staticmethod
    def get_available_widget_types() -> list[str]:
        """Get list of valid widget types."""
        return [
            "terminal",
            "editor",
            "theme_editor",
            "explorer",
            "output",
            "placeholder",
            "settings",
            "shortcuts",
        ]

    @staticmethod
    def validate_widget_type(value: str) -> tuple[bool, str]:
        """Validate widget type setting."""
        valid_types = AppDefaultsValidator.get_available_widget_types()
        if value in valid_types:
            return (True, value)
        logger.warning(f"Invalid widget type '{value}', falling back to 'terminal'")
        return (False, "terminal")

    @staticmethod
    def validate_split_ratio(value: Any) -> tuple[bool, float]:
        """Validate split ratio (must be between 0.1 and 0.9)."""
        try:
            ratio = float(value)
            if 0.1 <= ratio <= 0.9:
                return (True, ratio)
            logger.warning(f"Split ratio {ratio} out of range, using 0.5")
            return (False, 0.5)
        except (TypeError, ValueError):
            logger.warning(f"Invalid split ratio '{value}', using 0.5")
            return (False, 0.5)

    @staticmethod
    def validate_positive_int(
        value: Any, max_val: int = 100, default: int = 20
    ) -> tuple[bool, int]:
        """Validate positive integer setting."""
        try:
            num = int(value)
            if 0 <= num <= max_val:
                return (True, num)
            logger.warning(f"Value {num} out of range [0, {max_val}], using {default}")
            return (False, default)
        except (TypeError, ValueError):
            logger.warning(f"Invalid integer '{value}', using {default}")
            return (False, default)

    @staticmethod
    def validate_close_behavior(value: str) -> tuple[bool, str]:
        """Validate close last tab behavior."""
        valid_behaviors = ["create_default", "close_window", "do_nothing"]
        if value in valid_behaviors:
            return (True, value)
        logger.warning(f"Invalid close behavior '{value}', using 'create_default'")
        return (False, "create_default")

    @staticmethod
    def validate_bool(value: Any, default: bool = True) -> tuple[bool, bool]:
        """Validate boolean setting."""
        if isinstance(value, bool):
            return (True, value)
        if isinstance(value, str):
            if value.lower() in ("true", "1", "yes", "on"):
                return (True, True)
            elif value.lower() in ("false", "0", "no", "off"):
                return (True, False)
        logger.warning(f"Invalid boolean '{value}', using {default}")
        return (False, default)

    @staticmethod
    def validate_and_sanitize(key: str, value: Any) -> tuple[bool, Any]:
        """
        Validate a setting value and return sanitized version.

        Args:
            key: Setting key
            value: Value to validate

        Returns:
            Tuple of (is_valid, safe_value)
        """
        validators = {
            # Workspace settings
            "workspace.default_new_tab_widget": AppDefaultsValidator.validate_widget_type,
            "workspace.max_tabs": lambda v: AppDefaultsValidator.validate_positive_int(
                v, 100, 20
            ),
            "workspace.close_last_tab_behavior": AppDefaultsValidator.validate_close_behavior,
            "workspace.restore_tabs_on_startup": lambda v: AppDefaultsValidator.validate_bool(
                v, True
            ),
            "workspace.confirm_close_unsaved_tab": lambda v: AppDefaultsValidator.validate_bool(
                v, True
            ),
            # Pane settings
            "pane.default_split_ratio": AppDefaultsValidator.validate_split_ratio,
            "pane.minimum_width": lambda v: AppDefaultsValidator.validate_positive_int(
                v, 1000, 200
            ),
            "pane.minimum_height": lambda v: AppDefaultsValidator.validate_positive_int(
                v, 1000, 100
            ),
            "pane.focus_new_on_split": lambda v: AppDefaultsValidator.validate_bool(
                v, True
            ),
            # UI settings
            "ui.default_window_width": lambda v: AppDefaultsValidator.validate_positive_int(
                v, 4000, 1200
            ),
            "ui.default_window_height": lambda v: AppDefaultsValidator.validate_positive_int(
                v, 2000, 800
            ),
            "ui.sidebar_visible_on_start": lambda v: AppDefaultsValidator.validate_bool(
                v, True
            ),
            "ui.default_sidebar_width": lambda v: AppDefaultsValidator.validate_positive_int(
                v, 800, 300
            ),
            "ui.show_status_bar": lambda v: AppDefaultsValidator.validate_bool(v, True),
            "ui.start_maximized": lambda v: AppDefaultsValidator.validate_bool(
                v, False
            ),
            "ui.start_fullscreen": lambda v: AppDefaultsValidator.validate_bool(
                v, False
            ),
            # UX settings
            "ux.confirm_app_exit": lambda v: AppDefaultsValidator.validate_bool(
                v, True
            ),
            "ux.confirm_reload_window": lambda v: AppDefaultsValidator.validate_bool(
                v, True
            ),
            "ux.show_notifications": lambda v: AppDefaultsValidator.validate_bool(
                v, True
            ),
            "ux.enable_animations": lambda v: AppDefaultsValidator.validate_bool(
                v, True
            ),
        }

        # Use specific validator if available
        if key in validators:
            return validators[key](value)

        # Pass through unknown keys
        return (True, value)


class AppDefaults:
    """Application defaults manager with validation and fallback support."""

    def __init__(self):
        """Initialize app defaults manager."""
        self._settings = QSettings()
        self._cache: dict[str, Any] = {}
        self._validators: dict[str, Callable] = {}

    def get(self, key: str, fallback: Any = None) -> Any:
        """
        Get a setting value with validation and fallback.

        Args:
            key: Setting key
            fallback: Fallback value if not found or invalid

        Returns:
            Valid setting value
        """
        # Check cache first
        if key in self._cache:
            return self._cache[key]

        # Try to get from QSettings
        settings_key = f"app_defaults/{key}"
        if self._settings.contains(settings_key):
            value = self._settings.value(settings_key)

            # Validate the value
            is_valid, safe_value = AppDefaultsValidator.validate_and_sanitize(
                key, value
            )

            if is_valid:
                self._cache[key] = safe_value
                return safe_value
            else:
                # Invalid value, use fallback
                logger.warning(f"Invalid setting {key}={value}, using fallback")

        # Use provided fallback or hard-coded fallback
        if fallback is not None:
            self._cache[key] = fallback
            return fallback

        if key in HARD_CODED_FALLBACKS:
            self._cache[key] = HARD_CODED_FALLBACKS[key]
            return HARD_CODED_FALLBACKS[key]

        # No fallback available
        logger.warning(f"No fallback for setting {key}")
        return None

    def set(self, key: str, value: Any) -> bool:
        """
        Set a setting value with validation.

        Args:
            key: Setting key
            value: Value to set

        Returns:
            True if value was set successfully
        """
        # Validate before setting
        is_valid, safe_value = AppDefaultsValidator.validate_and_sanitize(key, value)

        if not is_valid:
            logger.warning(f"Rejecting invalid value for {key}: {value}")
            return False

        # Save to QSettings
        settings_key = f"app_defaults/{key}"
        self._settings.setValue(settings_key, safe_value)

        # Update cache
        self._cache[key] = safe_value

        return True

    def reset(self, key: str) -> None:
        """
        Reset a setting to its default value.

        Args:
            key: Setting key to reset
        """
        settings_key = f"app_defaults/{key}"
        self._settings.remove(settings_key)

        # Clear from cache
        if key in self._cache:
            del self._cache[key]

    def reset_all(self) -> None:
        """Reset all settings to defaults."""
        # Remove all app_defaults keys
        self._settings.beginGroup("app_defaults")
        self._settings.remove("")  # Removes all keys in group
        self._settings.endGroup()

        # Clear cache
        self._cache.clear()

    def export_settings(self) -> dict[str, Any]:
        """
        Export all current settings.

        Returns:
            Dictionary of all settings
        """
        settings = {}

        self._settings.beginGroup("app_defaults")
        for key in self._settings.allKeys():
            value = self._settings.value(key)
            settings[key] = value
        self._settings.endGroup()

        return settings

    def import_settings(self, settings: dict[str, Any]) -> int:
        """
        Import settings from dictionary.

        Args:
            settings: Dictionary of settings to import

        Returns:
            Number of settings successfully imported
        """
        imported = 0

        for key, value in settings.items():
            if self.set(key, value):
                imported += 1
            else:
                logger.warning(f"Failed to import setting {key}={value}")

        return imported

    def migrate_legacy_settings(self) -> int:
        """
        Migrate settings from old format to new format.

        Returns:
            Number of settings migrated
        """
        # Check if migration already done
        if self._settings.value("app_defaults_migrated", False):
            logger.info("Settings already migrated")
            return 0

        migration_map = {
            # UI settings
            "UI/ShowSidebar": "ui.sidebar_visible_on_start",
            "UI/ShowActivityBar": "ui.show_activity_bar",
            "UI/SidebarWidth": "ui.default_sidebar_width",
            "UI/ShowStatusBar": "ui.show_status_bar",
            "UI/ShowMenuBar": "ui.show_menu_bar",
            "UI/FramelessMode": "ui.frameless_mode",
            # Theme settings
            "Theme/Current": "appearance.theme",
            "Theme/FontFamily": "appearance.font_family",
            "Theme/FontSize": "appearance.font_size",
            # Workspace settings
            "Workspace/RestoreOnStartup": "workspace.restore_tabs_on_startup",
            # Terminal settings
            "Terminal/Shell": "terminal.default_shell",
            "Terminal/FontSize": "terminal.font_size",
        }

        migrated = 0
        for old_key, new_key in migration_map.items():
            if self._settings.contains(old_key):
                value = self._settings.value(old_key)
                if self.set(new_key, value):
                    migrated += 1
                    logger.info(f"Migrated {old_key} -> {new_key}")

        # Mark migration complete
        self._settings.setValue("app_defaults_migrated", True)

        logger.info(f"Migrated {migrated} settings")
        return migrated


# Global instance
_app_defaults = None


def get_app_defaults() -> AppDefaults:
    """Get the global AppDefaults instance."""
    global _app_defaults
    if _app_defaults is None:
        _app_defaults = AppDefaults()
        # Run migration on first access
        _app_defaults.migrate_legacy_settings()
    return _app_defaults


# Convenience functions
def get_app_default(key: str, fallback: Any = None) -> Any:
    """
    Get an application default setting.

    Args:
        key: Setting key
        fallback: Fallback value if not found

    Returns:
        Setting value
    """
    return get_app_defaults().get(key, fallback)


def set_app_default(key: str, value: Any) -> bool:
    """
    Set an application default setting.

    Args:
        key: Setting key
        value: Value to set

    Returns:
        True if successful
    """
    return get_app_defaults().set(key, value)


def get_default_widget_type() -> str:
    """Get the default widget type for new tabs."""
    return get_app_default("workspace.default_new_tab_widget", "terminal")


def get_default_split_direction() -> str:
    """Get the default split direction."""
    direction = get_app_default("pane.default_split_direction", "horizontal")
    return direction if direction in ["horizontal", "vertical"] else "horizontal"


def get_default_split_ratio() -> float:
    """Get the default split ratio."""
    return get_app_default("pane.default_split_ratio", 0.5)


def should_restore_tabs() -> bool:
    """Check if tabs should be restored on startup."""
    return get_app_default("workspace.restore_tabs_on_startup", True)


def should_confirm_app_exit() -> bool:
    """Check if app exit confirmation is required."""
    return get_app_default("ux.confirm_app_exit", True)


def get_close_last_tab_behavior() -> str:
    """Get the behavior when closing the last tab."""
    return get_app_default("workspace.close_last_tab_behavior", "create_default")


def get_startup_window_state() -> dict[str, Any]:
    """Get the default window state for startup."""
    return {
        "width": get_app_default("ui.default_window_width", 1200),
        "height": get_app_default("ui.default_window_height", 800),
        "maximized": get_app_default("ui.start_maximized", False),
        "fullscreen": get_app_default("ui.start_fullscreen", False),
        "position": get_app_default("ui.window_position", "center"),
    }


if __name__ == "__main__":
    # Test the module
    defaults = get_app_defaults()

    print("Application Defaults Test")
    print("=" * 40)

    # Test getting defaults
    print(f"Default widget type: {get_default_widget_type()}")
    print(f"Default split direction: {get_default_split_direction()}")
    print(f"Default split ratio: {get_default_split_ratio()}")
    print(f"Restore tabs: {should_restore_tabs()}")
    print(f"Confirm exit: {should_confirm_app_exit()}")

    # Test validation
    print("\nValidation tests:")
    print(
        f"Set invalid widget type: {set_app_default('workspace.default_new_tab_widget', 'invalid')}"
    )
    print(
        f"Set valid widget type: {set_app_default('workspace.default_new_tab_widget', 'editor')}"
    )
    print(f"New default: {get_default_widget_type()}")

    # Test window state
    print("\nWindow state:")
    for key, value in get_startup_window_state().items():
        print(f"  {key}: {value}")
