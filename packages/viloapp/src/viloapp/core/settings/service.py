#!/usr/bin/env python3
"""
Settings service for centralized application configuration management.

This service provides a high-level interface for managing application settings
with type safety, validation, and integration with the existing StateService.
"""

import copy
import logging
from typing import Any, Callable, Optional

from PySide6.QtCore import Signal

from viloapp.services.base import Service

from .defaults import DEFAULT_SETTINGS, get_default_keyboard_shortcuts
from .schema import SettingsSchema, validate_keyboard_shortcut, validate_settings

logger = logging.getLogger(__name__)


class SettingsService(Service):
    """
    Centralized settings service with validation and persistence.

    Provides a high-level interface for managing application settings
    with type safety, validation, and change notifications.
    """

    # Signals for settings changes
    setting_changed = Signal(str, str, object)  # category, key, new_value
    category_changed = Signal(str, dict)  # category, new_settings
    settings_reset = Signal()  # all settings reset

    def __init__(self):
        """Initialize the settings service."""
        super().__init__("SettingsService")

        self._settings = {}
        self._state_service = None
        self._schema_validator = SettingsSchema()
        self._change_listeners: dict[str, list[Callable]] = {}

        # Load default settings
        self._settings = copy.deepcopy(DEFAULT_SETTINGS)

    def initialize(self, context: dict[str, Any]) -> None:
        """Initialize the service with application context."""
        super().initialize(context)

        # Get StateService for persistence
        from viloapp.services.service_locator import ServiceLocator
        from viloapp.services.state_service import StateService

        locator = ServiceLocator.get_instance()
        self._state_service = locator.get(StateService)

        if not self._state_service:
            logger.warning("StateService not available - settings will not persist")

        # Load saved settings
        self._load_settings()

        logger.info("SettingsService initialized")

    def cleanup(self) -> None:
        """Cleanup service resources."""
        # Save current settings
        self._save_settings()

        self._settings.clear()
        self._change_listeners.clear()
        self._state_service = None

        super().cleanup()

    # ============= Settings Access =============

    def get(self, category: str, key: str, default: Any = None) -> Any:
        """
        Get a specific setting value.

        Args:
            category: Settings category (e.g., 'theme', 'ui')
            key: Setting key within category
            default: Default value if not found

        Returns:
            Setting value or default
        """
        if category not in self._settings:
            return default

        category_settings = self._settings[category]
        if isinstance(category_settings, dict):
            return category_settings.get(key, default)

        return default

    def set(self, category: str, key: str, value: Any, validate: bool = True) -> bool:
        """
        Set a specific setting value.

        Args:
            category: Settings category
            key: Setting key within category
            value: New value
            validate: Whether to validate the setting

        Returns:
            True if setting was updated successfully
        """
        try:
            # Ensure category exists
            if category not in self._settings:
                self._settings[category] = {}

            # Validate if requested
            if validate:
                # Create temporary settings for validation
                temp_settings = copy.deepcopy(self._settings)
                temp_settings[category][key] = value

                is_valid, errors = self._schema_validator.validate_category(
                    category, temp_settings[category]
                )
                if not is_valid:
                    logger.warning(f"Invalid setting {category}.{key}: {errors}")
                    return False

            # Special validation for keyboard shortcuts
            if category == "keyboard_shortcuts" and not validate_keyboard_shortcut(value):
                logger.warning(f"Invalid keyboard shortcut: {value}")
                return False

            # Store old value for comparison
            old_value = self._settings[category].get(key)

            # Update setting
            self._settings[category][key] = value

            # Notify if changed
            if old_value != value:
                self.setting_changed.emit(category, key, value)
                self._notify_listeners(category, key, value)

                # Auto-save if available
                self._auto_save()

                logger.debug(f"Setting updated: {category}.{key} = {value}")

            return True

        except Exception as e:
            logger.error(f"Failed to set {category}.{key}: {e}")
            return False

    def get_category(self, category: str) -> dict[str, Any]:
        """
        Get all settings for a category.

        Args:
            category: Category name

        Returns:
            Dictionary of category settings
        """
        return self._settings.get(category, {}).copy()

    def set_category(self, category: str, settings: dict[str, Any], validate: bool = True) -> bool:
        """
        Set all settings for a category.

        Args:
            category: Category name
            settings: New settings for category
            validate: Whether to validate settings

        Returns:
            True if category was updated successfully
        """
        try:
            # Validate if requested
            if validate:
                is_valid, errors = self._schema_validator.validate_category(category, settings)
                if not is_valid:
                    logger.warning(f"Invalid settings for {category}: {errors}")
                    return False

            # Update category
            old_settings = self._settings.get(category, {})
            self._settings[category] = settings.copy()

            # Notify if changed
            if old_settings != settings:
                self.category_changed.emit(category, settings)

                # Notify individual setting changes
                for key, value in settings.items():
                    if old_settings.get(key) != value:
                        self._notify_listeners(category, key, value)

                # Auto-save if available
                self._auto_save()

                logger.debug(f"Category updated: {category}")

            return True

        except Exception as e:
            logger.error(f"Failed to set category {category}: {e}")
            return False

    def get_all(self) -> dict[str, Any]:
        """
        Get all application settings.

        Returns:
            Complete settings dictionary
        """
        return copy.deepcopy(self._settings)

    def set_all(self, settings: dict[str, Any], validate: bool = True) -> bool:
        """
        Set all application settings.

        Args:
            settings: New settings dictionary
            validate: Whether to validate settings

        Returns:
            True if settings were updated successfully
        """
        try:
            # Validate if requested
            if validate:
                is_valid, errors = validate_settings(settings)
                if not is_valid:
                    logger.warning(f"Invalid settings: {errors}")
                    return False

            # Update all settings
            old_settings = copy.deepcopy(self._settings)
            self._settings = copy.deepcopy(settings)

            # Notify of changes
            for category, category_settings in settings.items():
                if old_settings.get(category) != category_settings:
                    self.category_changed.emit(category, category_settings)

                    if isinstance(category_settings, dict):
                        for key, value in category_settings.items():
                            if old_settings.get(category, {}).get(key) != value:
                                self._notify_listeners(category, key, value)

            # Auto-save if available
            self._auto_save()

            logger.info("All settings updated")
            return True

        except Exception as e:
            logger.error(f"Failed to set all settings: {e}")
            return False

    # ============= Keyboard Shortcuts =============

    def get_keyboard_shortcuts(self) -> dict[str, str]:
        """
        Get all keyboard shortcuts.

        Returns:
            Dictionary of command_id -> shortcut mappings
        """
        return self.get_category("keyboard_shortcuts")

    def get_keyboard_shortcut(self, command_id: str) -> str:
        """
        Get keyboard shortcut for a command.

        Args:
            command_id: Command identifier

        Returns:
            Keyboard shortcut or empty string if none
        """
        return self.get("keyboard_shortcuts", command_id, "")

    def set_keyboard_shortcut(self, command_id: str, shortcut: str) -> bool:
        """
        Set keyboard shortcut for a command.

        Args:
            command_id: Command identifier
            shortcut: New keyboard shortcut

        Returns:
            True if shortcut was updated successfully
        """
        return self.set("keyboard_shortcuts", command_id, shortcut)

    def update_keyboard_shortcuts(self, shortcuts: dict[str, str]) -> bool:
        """
        Update multiple keyboard shortcuts.

        Args:
            shortcuts: Dictionary of command_id -> shortcut mappings

        Returns:
            True if shortcuts were updated successfully
        """
        current_shortcuts = self.get_keyboard_shortcuts()
        current_shortcuts.update(shortcuts)
        return self.set_category("keyboard_shortcuts", current_shortcuts)

    def reset_keyboard_shortcuts(self) -> bool:
        """
        Reset keyboard shortcuts to defaults.

        Returns:
            True if shortcuts were reset successfully
        """
        defaults = get_default_keyboard_shortcuts()
        return self.set_category("keyboard_shortcuts", defaults)

    # ============= Theme Settings =============

    def get_theme(self) -> str:
        """Get current theme."""
        return self.get("theme", "theme", "dark")

    def set_theme(self, theme: str) -> bool:
        """Set current theme."""
        return self.set("theme", "theme", theme)

    def get_font_family(self) -> str:
        """Get font family."""
        return self.get("theme", "font_family", "Consolas, Monaco, monospace")

    def get_font_size(self) -> int:
        """Get font size."""
        return self.get("theme", "font_size", 12)

    # ============= Change Listeners =============

    def add_change_listener(self, category: str, key: str, callback: Callable[[Any], None]) -> None:
        """
        Add a listener for setting changes.

        Args:
            category: Settings category
            key: Setting key (or "*" for all keys in category)
            callback: Function to call when setting changes
        """
        listener_key = f"{category}.{key}"
        if listener_key not in self._change_listeners:
            self._change_listeners[listener_key] = []

        self._change_listeners[listener_key].append(callback)

    def remove_change_listener(
        self, category: str, key: str, callback: Callable[[Any], None]
    ) -> None:
        """
        Remove a setting change listener.

        Args:
            category: Settings category
            key: Setting key
            callback: Callback function to remove
        """
        listener_key = f"{category}.{key}"
        if listener_key in self._change_listeners:
            try:
                self._change_listeners[listener_key].remove(callback)
                if not self._change_listeners[listener_key]:
                    del self._change_listeners[listener_key]
            except ValueError:
                pass  # Callback not found

    def _notify_listeners(self, category: str, key: str, value: Any) -> None:
        """Notify change listeners."""
        # Specific key listeners
        listener_key = f"{category}.{key}"
        if listener_key in self._change_listeners:
            for callback in self._change_listeners[listener_key]:
                try:
                    callback(value)
                except Exception as e:
                    logger.error(f"Error in change listener: {e}")

        # Wildcard listeners for category
        wildcard_key = f"{category}.*"
        if wildcard_key in self._change_listeners:
            for callback in self._change_listeners[wildcard_key]:
                try:
                    callback(value)
                except Exception as e:
                    logger.error(f"Error in wildcard listener: {e}")

    # ============= Persistence =============

    def save(self) -> bool:
        """
        Manually save settings to persistent storage.

        Returns:
            True if save was successful
        """
        return self._save_settings()

    def load(self) -> bool:
        """
        Manually load settings from persistent storage.

        Returns:
            True if load was successful
        """
        return self._load_settings()

    def reset(self, categories: Optional[list[str]] = None) -> bool:
        """
        Reset settings to defaults.

        Args:
            categories: Specific categories to reset, or None for all

        Returns:
            True if reset was successful
        """
        try:
            if categories:
                # Reset specific categories
                for category in categories:
                    if category in DEFAULT_SETTINGS:
                        self._settings[category] = copy.deepcopy(DEFAULT_SETTINGS[category])
                        self.category_changed.emit(category, self._settings[category])
            else:
                # Reset all settings
                self._settings = copy.deepcopy(DEFAULT_SETTINGS)
                self.settings_reset.emit()

            # Auto-save
            self._auto_save()

            logger.info(f"Settings reset: {categories or 'all'}")
            return True

        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False

    def _save_settings(self) -> bool:
        """Save settings using StateService."""
        if not self._state_service:
            return False

        try:
            # Save each category as a preference
            for category, settings in self._settings.items():
                self._state_service.save_preference(f"settings.{category}", settings)

            logger.debug("Settings saved")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def _load_settings(self) -> bool:
        """Load settings using StateService."""
        if not self._state_service:
            return False

        try:
            loaded_any = False

            # Load each category
            for category in DEFAULT_SETTINGS.keys():
                saved_settings = self._state_service.get_preference(f"settings.{category}")

                if saved_settings:
                    # Validate loaded settings
                    is_valid, errors = self._schema_validator.validate_category(
                        category, saved_settings
                    )

                    if is_valid:
                        self._settings[category] = saved_settings
                        loaded_any = True
                    else:
                        logger.warning(
                            f"Invalid saved settings for {category}, using defaults: {errors}"
                        )

            if loaded_any:
                logger.info("Settings loaded from storage")
            else:
                logger.info("No saved settings found, using defaults")

            return loaded_any

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return False

    def _auto_save(self) -> None:
        """Auto-save settings if enabled."""
        # For now, always auto-save
        # In the future, this could be controlled by a setting
        self._save_settings()

    # ============= Service Info =============

    def get_service_info(self) -> dict[str, Any]:
        """Get service information for debugging."""
        return {
            "categories": list(self._settings.keys()),
            "total_settings": sum(
                len(s) if isinstance(s, dict) else 1 for s in self._settings.values()
            ),
            "change_listeners": len(self._change_listeners),
            "has_state_service": self._state_service is not None,
            "validation_available": self._schema_validator._jsonschema_available,
        }
