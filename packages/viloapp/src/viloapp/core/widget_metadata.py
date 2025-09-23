"""
Widget metadata registry for ViloxTerm.

This module provides a registry for widget metadata including display names,
icons, categories, and capabilities. It replaces the old WidgetType enum
with a flexible, extensible system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class WidgetMetadata:
    """Complete widget identity and capabilities."""

    widget_id: str  # Unique identifier (e.g., "viloapp.terminal")
    display_name: str  # Human-readable name
    icon: Optional[str] = None  # Icon identifier
    category: str = "general"  # For grouping (terminal, editor, tool, etc.)
    capabilities: Set[str] = field(default_factory=set)  # Feature flags
    default_position: str = "main"  # Where widget typically appears
    singleton: bool = False  # Only one instance allowed
    priority: int = 0  # Display order
    description: Optional[str] = None  # Brief description for tooltips


class WidgetMetadataRegistry:
    """Central registry for all widget metadata."""

    _instance = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize registry with built-in widgets."""
        if not hasattr(self, '_initialized'):
            self._metadata: Dict[str, WidgetMetadata] = {}
            self._by_category: Dict[str, List[str]] = {}
            self._by_capability: Dict[str, Set[str]] = {}
            self._register_builtin_widgets()
            self._initialized = True

    def _register_builtin_widgets(self):
        """Register all built-in widget types."""
        # Widget IDs are now defined as strings directly
        # This maintains the registry for backward compatibility

        # Terminal widget
        self.register(WidgetMetadata(
            widget_id="com.viloapp.terminal",
            display_name="Terminal",
            icon="terminal",
            category="terminal",
            capabilities={"shell", "command_execution", "ansi"},
            description="Terminal emulator for running commands"
        ))

        # Editor widget
        self.register(WidgetMetadata(
            widget_id="com.viloapp.editor",
            display_name="Text Editor",
            icon="file-text",
            category="editor",
            capabilities={"text_editing", "syntax_highlighting", "file_operations"},
            description="Text editor with syntax highlighting"
        ))

        # File Explorer widget
        self.register(WidgetMetadata(
            widget_id="com.viloapp.explorer",
            display_name="File Explorer",
            icon="folder",
            category="navigation",
            capabilities={"file_browsing", "file_operations"},
            default_position="sidebar",
            description="Browse and manage files"
        ))

        # Output widget
        self.register(WidgetMetadata(
            widget_id="com.viloapp.output",
            display_name="Output",
            icon="list",
            category="output",
            capabilities={"text_display", "logging"},
            default_position="panel",
            description="Display command output and logs"
        ))

        # Settings widget
        self.register(WidgetMetadata(
            widget_id="com.viloapp.settings",
            display_name="Settings",
            icon="settings",
            category="configuration",
            capabilities={"configuration", "preferences"},
            singleton=True,
            description="Application settings and preferences"
        ))

        # Theme Editor widget
        self.register(WidgetMetadata(
            widget_id="com.viloapp.theme_editor",
            display_name="Theme Editor",
            icon="palette",
            category="configuration",
            capabilities={"theming", "customization"},
            singleton=True,
            description="Customize application appearance"
        ))

        # Shortcut Config widget
        self.register(WidgetMetadata(
            widget_id="com.viloapp.shortcuts",
            display_name="Keyboard Shortcuts",
            icon="keyboard",
            category="configuration",
            capabilities={"shortcuts", "keybindings"},
            singleton=True,
            description="Configure keyboard shortcuts"
        ))

        # Placeholder widget
        self.register(WidgetMetadata(
            widget_id="com.viloapp.placeholder",
            display_name="Placeholder",
            icon="layout",
            category="utility",
            capabilities={"placeholder"},
            description="Placeholder for development"
        ))

    def register(self, metadata: WidgetMetadata) -> None:
        """
        Register widget metadata.

        Args:
            metadata: Widget metadata to register
        """
        self._metadata[metadata.widget_id] = metadata

        # Update category index
        if metadata.category not in self._by_category:
            self._by_category[metadata.category] = []
        if metadata.widget_id not in self._by_category[metadata.category]:
            self._by_category[metadata.category].append(metadata.widget_id)

        # Update capability index
        for capability in metadata.capabilities:
            if capability not in self._by_capability:
                self._by_capability[capability] = set()
            self._by_capability[capability].add(metadata.widget_id)

    def unregister(self, widget_id: str) -> None:
        """
        Unregister widget metadata.

        Args:
            widget_id: Widget ID to unregister
        """
        if widget_id in self._metadata:
            metadata = self._metadata[widget_id]

            # Remove from category index
            if metadata.category in self._by_category:
                self._by_category[metadata.category].remove(widget_id)

            # Remove from capability index
            for capability in metadata.capabilities:
                if capability in self._by_capability:
                    self._by_capability[capability].discard(widget_id)

            del self._metadata[widget_id]

    def get_metadata(self, widget_id: str) -> Optional[WidgetMetadata]:
        """
        Get metadata for a widget.

        Args:
            widget_id: Widget ID

        Returns:
            Widget metadata or None if not found
        """
        return self._metadata.get(widget_id)

    def get_display_name(self, widget_id: str) -> str:
        """
        Get display name for a widget.

        Args:
            widget_id: Widget ID

        Returns:
            Display name or extracted name from ID
        """
        metadata = self.get_metadata(widget_id)
        if metadata:
            return metadata.display_name

        # Fallback: extract from widget ID
        # e.g., "viloapp.terminal" -> "Terminal"
        # e.g., "plugin.markdown_editor" -> "Markdown Editor"
        parts = widget_id.split('.')
        if len(parts) > 1:
            name = parts[-1]
        else:
            name = widget_id

        # Convert snake_case to Title Case
        return name.replace('_', ' ').title()

    def get_icon(self, widget_id: str) -> Optional[str]:
        """
        Get icon for a widget.

        Args:
            widget_id: Widget ID

        Returns:
            Icon identifier or None
        """
        metadata = self.get_metadata(widget_id)
        return metadata.icon if metadata else None

    def get_by_category(self, category: str) -> List[WidgetMetadata]:
        """
        Get all widgets in a category.

        Args:
            category: Category name

        Returns:
            List of widget metadata in the category
        """
        widget_ids = self._by_category.get(category, [])
        return [self._metadata[wid] for wid in widget_ids if wid in self._metadata]

    def get_by_capability(self, capability: str) -> List[WidgetMetadata]:
        """
        Get all widgets with a specific capability.

        Args:
            capability: Capability name

        Returns:
            List of widget metadata with the capability
        """
        widget_ids = self._by_capability.get(capability, set())
        return [self._metadata[wid] for wid in widget_ids if wid in self._metadata]

    def get_all(self) -> List[WidgetMetadata]:
        """
        Get all registered widget metadata.

        Returns:
            List of all widget metadata
        """
        return list(self._metadata.values())

    def get_categories(self) -> List[str]:
        """
        Get all registered categories.

        Returns:
            List of category names
        """
        return list(self._by_category.keys())

    def has_widget(self, widget_id: str) -> bool:
        """
        Check if a widget is registered.

        Args:
            widget_id: Widget ID

        Returns:
            True if widget is registered
        """
        return widget_id in self._metadata


# Global registry instance
widget_metadata_registry = WidgetMetadataRegistry()


# Convenience functions
def register_widget_metadata(metadata: WidgetMetadata) -> None:
    """Register widget metadata."""
    widget_metadata_registry.register(metadata)


def get_widget_display_name(widget_id: str) -> str:
    """Get display name for a widget."""
    return widget_metadata_registry.get_display_name(widget_id)


def get_widget_icon(widget_id: str) -> Optional[str]:
    """Get icon for a widget."""
    return widget_metadata_registry.get_icon(widget_id)


def get_widget_metadata(widget_id: str) -> Optional[WidgetMetadata]:
    """Get complete metadata for a widget."""
    return widget_metadata_registry.get_metadata(widget_id)
