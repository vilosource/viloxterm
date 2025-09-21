"""Backward compatibility layer for ViloxTerm plugin architecture."""

import logging
from typing import Dict, Any, Optional, Callable
import warnings

logger = logging.getLogger(__name__)


class DeprecationWarning(UserWarning):
    """Custom deprecation warning for ViloxTerm."""
    pass


def deprecated(reason: str, version: str = "3.0"):
    """Decorator to mark functions as deprecated."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated and will be removed in version {version}. {reason}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


class LegacyAPIWrapper:
    """Wrapper for legacy API methods to maintain backward compatibility."""

    def __init__(self, new_api):
        self.new_api = new_api

    @deprecated("Use new_api.get_terminal_instance() instead")
    def get_terminal(self):
        """Legacy method to get terminal instance."""
        return self.new_api.get_terminal_instance()

    @deprecated("Use new_api.execute_command() instead")
    def run_command(self, command: str):
        """Legacy method to run commands."""
        return self.new_api.execute_command(command)

    @deprecated("Use new_api.get_editor_instance() instead")
    def get_editor(self):
        """Legacy method to get editor instance."""
        return self.new_api.get_editor_instance()

    @deprecated("Use new_api.open_file() instead")
    def open_editor_file(self, file_path: str):
        """Legacy method to open files in editor."""
        return self.new_api.open_file(file_path)


class ConfigurationMigrator:
    """Handles migration of old configuration format to new plugin system."""

    def __init__(self):
        self.migration_map = {
            # Old key -> New plugin.setting format
            "terminal_font": "viloxterm.font_family",
            "terminal_font_size": "viloxterm.font_size",
            "terminal_bg": "viloxterm.colors.background",
            "terminal_fg": "viloxterm.colors.foreground",
            "editor_font": "viloedit.font_family",
            "editor_font_size": "viloedit.font_size",
            "tab_width": "viloedit.tab_width",
            "word_wrap": "viloedit.word_wrap",
            "show_line_numbers": "viloedit.line_numbers",
        }

    def migrate_config_key(self, old_key: str, value: Any) -> Optional[tuple]:
        """Migrate a single configuration key from old to new format."""
        if old_key in self.migration_map:
            new_key = self.migration_map[old_key]
            return (new_key, value)
        return None

    def migrate_all_config(self, old_config: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate entire configuration from old to new format."""
        new_config = {}

        for old_key, value in old_config.items():
            migration_result = self.migrate_config_key(old_key, value)
            if migration_result:
                new_key, new_value = migration_result
                self._set_nested_key(new_config, new_key, new_value)
            else:
                # Keep unmapped keys as-is with warning
                logger.warning(f"Configuration key '{old_key}' has no migration path")
                new_config[old_key] = value

        return new_config

    def _set_nested_key(self, config: Dict[str, Any], key_path: str, value: Any):
        """Set a value in nested dictionary using dot notation."""
        keys = key_path.split('.')
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value


class PluginCompatibilityShim:
    """Provides compatibility shim for old plugin interfaces."""

    def __init__(self, plugin_manager):
        self.plugin_manager = plugin_manager

    @deprecated("Use plugin_manager.get_plugin() instead")
    def get_plugin_by_name(self, name: str):
        """Legacy method to get plugin by name."""
        return self.plugin_manager.get_plugin(name)

    @deprecated("Use plugin_manager.list_plugins() instead")
    def get_all_plugins(self):
        """Legacy method to get all plugins."""
        return self.plugin_manager.list_plugins()

    @deprecated("Use plugin_manager.enable_plugin() instead")
    def activate_plugin(self, name: str):
        """Legacy method to activate plugin."""
        return self.plugin_manager.enable_plugin(name)

    @deprecated("Use plugin_manager.disable_plugin() instead")
    def deactivate_plugin(self, name: str):
        """Legacy method to deactivate plugin."""
        return self.plugin_manager.disable_plugin(name)


def ensure_backward_compatibility():
    """Set up backward compatibility features."""
    # Configure deprecation warnings to be shown
    warnings.filterwarnings("default", category=DeprecationWarning)

    logger.info("Backward compatibility layer initialized")


def check_legacy_usage(func_name: str, args: tuple, kwargs: dict) -> bool:
    """Check if function call uses legacy patterns and warn user."""
    legacy_patterns = {
        "create_widget": "Use create_instance(instance_id) instead",
        "get_metadata": "Use individual get_* methods instead",
        "run_command": "Use execute_command() instead",
    }

    if func_name in legacy_patterns:
        warnings.warn(
            f"Legacy function '{func_name}' used. {legacy_patterns[func_name]}",
            DeprecationWarning,
            stacklevel=3
        )
        return True

    return False