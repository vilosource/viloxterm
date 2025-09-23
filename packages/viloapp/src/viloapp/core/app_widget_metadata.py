#!/usr/bin/env python3
"""
AppWidget metadata definitions.

This module contains the metadata classes used to describe AppWidgets,
including their capabilities, requirements, and UI properties.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Optional

from viloapp.core.widget_placement import WidgetPlacement

# Widget IDs are now defined in the widget classes themselves

if TYPE_CHECKING:
    from viloapp.ui.widgets.app_widget import AppWidget


class WidgetCategory(Enum):
    """Categories for organizing widgets in menus and palettes."""

    EDITOR = "editor"
    TERMINAL = "terminal"
    VIEWER = "viewer"
    TOOLS = "tools"
    DEVELOPMENT = "development"
    SYSTEM = "system"
    PLUGIN = "plugin"


@dataclass
class AppWidgetMetadata:
    """
    Complete metadata for an AppWidget.

    This class contains all information needed to register, create,
    and manage an AppWidget throughout its lifecycle.
    """

    # === Identity ===
    widget_id: str  # Unique identifier (e.g., "com.viloapp.terminal")

    # === Display ===
    display_name: str  # Human-readable name
    description: str  # Brief description for tooltips
    icon: str  # Icon name or path
    category: WidgetCategory  # Category for organization

    # === Technical ===
    widget_class: type["AppWidget"]  # The actual widget class
    factory: Optional[Callable[[str], "AppWidget"]] = None  # Optional factory function

    # === Commands ===
    open_command: Optional[str] = None  # Command ID to open this widget
    associated_commands: list[str] = field(default_factory=list)  # Related commands

    # Context-specific commands (for different placement intents)
    commands: dict[str, str] = field(default_factory=dict)
    # Expected keys: "open_new_tab", "replace_pane", "open_smart"

    # === Behavior ===
    singleton: bool = False  # Only allow one instance
    can_split: bool = True  # Can be used in split panes
    show_in_menu: bool = True  # Show in widget type menu
    show_in_palette: bool = True  # Show in command palette
    show_header: bool = True  # Show pane header bar
    preserve_context_menu: bool = False  # Preserve native context menu
    can_suspend: bool = (
        True  # Can be suspended when hidden (False for widgets with background processes)
    )

    # === Default Widget Support ===
    can_be_default: bool = False  # Can this widget be used as a default widget
    default_priority: int = 100  # Priority for default selection (lower = higher priority)
    default_for_contexts: list[str] = field(
        default_factory=list
    )  # Contexts where this can be default

    # === Placement Intent ===
    default_placement: WidgetPlacement = WidgetPlacement.SMART
    supports_replacement: bool = True  # Can replace existing pane content
    supports_new_tab: bool = True  # Can open in new tab

    # === Size constraints ===
    min_width: int = 150
    min_height: int = 100
    default_width: Optional[int] = None
    default_height: Optional[int] = None

    # === Requirements & Capabilities ===
    requires_services: list[str] = field(default_factory=list)  # Required services
    provides_capabilities: list[str] = field(default_factory=list)  # Provided capabilities
    supported_file_types: list[str] = field(default_factory=list)  # File extensions

    # === Plugin preparation ===
    source: str = "builtin"  # "builtin" or "plugin"
    plugin_id: Optional[str] = None  # Plugin that provides this widget
    version: str = "1.0.0"  # Widget version
    min_app_version: Optional[str] = None  # Minimum app version required

    # === Future plugin fields ===
    activation_events: list[str] = field(default_factory=list)  # When to activate
    permissions: list[str] = field(default_factory=list)  # Required permissions
    configuration_schema: Optional[dict[str, Any]] = None  # Settings schema

    # === State management ===
    supports_state_save: bool = True  # Can save/restore state
    state_serializer: Optional[Callable] = None  # Custom state serializer
    state_deserializer: Optional[Callable] = None  # Custom state deserializer

    def __post_init__(self):
        """Validate metadata after initialization."""
        if not self.widget_id:
            raise ValueError("widget_id is required")
        if not self.display_name:
            raise ValueError("display_name is required")
        if not self.widget_class:
            raise ValueError("widget_class is required")

        # Ensure widget_id follows naming convention for builtin widgets only
        # Only prefix simple identifiers (no dots) for builtin widgets
        if self.source == "builtin" and not self.widget_id.startswith("com."):
            # Only add prefix if it's a simple identifier without dots
            if "." not in self.widget_id:
                self.widget_id = f"com.viloapp.{self.widget_id}"

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "widget_id": self.widget_id,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "category": self.category.value,
            "version": self.version,
            "source": self.source,
            "capabilities": self.provides_capabilities,
            "requirements": self.requires_services,
            "singleton": self.singleton,
        }

    def is_available(self) -> bool:
        """Check if this widget is currently available."""
        # In the future, this could check:
        # - If required services are available
        # - If the plugin is loaded
        # - If permissions are granted
        # - If the app version is compatible
        return True

    def matches_capability(self, capability: str) -> bool:
        """Check if widget provides a specific capability."""
        return capability in self.provides_capabilities

    def matches_file_type(self, file_extension: str) -> bool:
        """Check if widget supports a file type."""
        if not self.supported_file_types:
            return False
        # Remove leading dot if present
        ext = file_extension.lstrip(".")
        return ext in self.supported_file_types
