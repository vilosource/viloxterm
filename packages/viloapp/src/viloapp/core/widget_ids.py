"""
Widget ID conventions and utilities for ViloxTerm.

This module defines PATTERNS and CONVENTIONS for widget IDs.
It does NOT contain specific widget IDs - those belong to the widgets themselves.

Widget ID Conventions:
- Built-in widgets: "com.viloapp.<name>"
- Plugin widgets: "plugin.<plugin_id>.<widget_name>"

IMPORTANT: This module should NEVER need modification when adding new widgets.
"""

from typing import Optional

# Widget ID pattern constants (for documentation and validation)
BUILTIN_WIDGET_PREFIX = "com.viloapp."
PLUGIN_WIDGET_PREFIX = "plugin."

# No hardcoded defaults - everything comes from the registry
# Defaults are discovered at runtime, not declared at compile time


def is_builtin_widget(widget_id: str) -> bool:
    """
    Check if a widget ID represents a built-in widget.

    Args:
        widget_id: The widget ID to check

    Returns:
        True if this is a built-in widget ID
    """
    return widget_id.startswith(BUILTIN_WIDGET_PREFIX)


def is_plugin_widget(widget_id: str) -> bool:
    """
    Check if a widget ID represents a plugin widget.

    Args:
        widget_id: The widget ID to check

    Returns:
        True if this is a plugin widget ID
    """
    return widget_id.startswith(PLUGIN_WIDGET_PREFIX)


def get_widget_namespace(widget_id: str) -> str:
    """
    Extract the namespace from a widget ID.

    Examples:
        "com.viloapp.terminal" -> "com.viloapp"
        "plugin.markdown.editor" -> "plugin.markdown"

    Args:
        widget_id: The widget ID

    Returns:
        The namespace portion of the ID
    """
    parts = widget_id.rsplit(".", 1)
    return parts[0] if len(parts) > 1 else widget_id


def get_widget_name(widget_id: str) -> str:
    """
    Extract the widget name from a widget ID.

    Examples:
        "com.viloapp.terminal" -> "terminal"
        "plugin.markdown.editor" -> "editor"

    Args:
        widget_id: The widget ID

    Returns:
        The name portion of the ID
    """
    return widget_id.rsplit(".", 1)[-1]


def create_plugin_widget_id(plugin_id: str, widget_name: str) -> str:
    """
    Create a properly formatted plugin widget ID.

    Args:
        plugin_id: The plugin identifier
        widget_name: The widget name within the plugin

    Returns:
        Formatted plugin widget ID
    """
    return f"{PLUGIN_WIDGET_PREFIX}{plugin_id}.{widget_name}"


def validate_widget_id(widget_id: str) -> bool:
    """
    Validate that a widget ID follows conventions.

    Args:
        widget_id: The widget ID to validate

    Returns:
        True if the widget ID is valid
    """
    if not widget_id:
        return False

    # Must be either built-in or plugin
    if not (is_builtin_widget(widget_id) or is_plugin_widget(widget_id)):
        return False

    # Must have at least namespace.name structure
    parts = widget_id.split(".")
    if is_builtin_widget(widget_id) and len(parts) < 3:  # com.viloapp.name
        return False
    if is_plugin_widget(widget_id) and len(parts) < 3:  # plugin.id.name
        return False

    return True


# Legacy migration support
# This mapping exists ONLY for backward compatibility with old saves
# New code should NEVER use these old names
LEGACY_WIDGET_MAP = {
    # Terminal and Editor removed - now provided by plugins
    # Plugins should register with their own IDs (e.g., plugin.viloxterm.terminal)
    "output": "com.viloapp.output",
    "OUTPUT": "com.viloapp.output",  # Old enum value
    "settings": "com.viloapp.settings",
    "SETTINGS": "com.viloapp.settings",  # Old enum value
    "file_explorer": "com.viloapp.explorer",
    "explorer": "com.viloapp.explorer",  # Alias
    "theme_editor": "com.viloapp.theme_editor",
    "shortcut_config": "com.viloapp.shortcuts",
    "placeholder": "com.viloapp.placeholder",
    "PLACEHOLDER": "com.viloapp.placeholder",  # Old enum value
    "custom": "plugin.unknown",  # Generic plugin widget
}


def migrate_widget_type(old_type: str) -> str:
    """
    Migrate old widget type strings to new widget IDs.

    This function exists ONLY for backward compatibility with old saved states.
    New code should use proper widget IDs directly.

    Args:
        old_type: Old widget type string (e.g., "terminal", "editor")

    Returns:
        New widget ID following current conventions
    """
    # Check if it's already a valid widget ID
    if validate_widget_id(old_type):
        return old_type

    # Try to migrate from legacy map
    if old_type in LEGACY_WIDGET_MAP:
        return LEGACY_WIDGET_MAP[old_type]

    # If not in map and contains a dot, assume it's already a widget ID
    if "." in old_type:
        return old_type

    # Otherwise, assume it's a plugin widget with unknown format
    return f"{PLUGIN_WIDGET_PREFIX}unknown.{old_type}"


def get_default_widget_id() -> Optional[str]:
    """
    Get the default widget ID for new panes.

    This now properly queries the registry for defaults rather than
    using hardcoded values.

    Returns:
        Default widget ID from registry or None if no widgets available
    """
    try:
        from viloapp.core.app_widget_manager import app_widget_manager
        return app_widget_manager.get_default_widget_id()
    except ImportError:
        # During early initialization, registry might not be available yet
        # Return None to let caller handle this case
        return None


# DO NOT ADD SPECIFIC WIDGET IDS HERE
# Widget IDs belong in the widgets themselves or in the registry
# This file should NEVER need modification when adding new widgets
