"""
Widget metadata registry for ViloxTerm.

This module provides a registry for widget metadata including display names,
icons, categories, and capabilities. It replaces the old WidgetType enum
with a flexible, extensible system.

ARCHITECTURE COMPLIANCE:
- This registry starts EMPTY
- Widgets register themselves at runtime
- No hardcoded widget IDs or metadata in core
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class WidgetMetadata:
    """Complete widget identity and capabilities."""

    widget_id: str  # Unique identifier (e.g., "com.viloapp.terminal")
    display_name: str  # Human-readable name
    icon: Optional[str] = None  # Icon identifier
    category: str = "general"  # For grouping (terminal, editor, tool, etc.)
    capabilities: Set[str] = field(default_factory=set)  # Feature flags
    default_position: str = "main"  # Where widget typically appears
    singleton: bool = False  # Only one instance allowed
    priority: int = 0  # Display order
    description: Optional[str] = None  # Brief description for tooltips


class WidgetMetadataRegistry:
    """Central registry for all widget metadata.

    This registry is populated at RUNTIME by widgets registering themselves.
    It contains NO hardcoded widget information - true platform architecture.
    """

    _instance = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize EMPTY registry - widgets register themselves."""
        if not hasattr(self, '_initialized'):
            self._metadata: Dict[str, WidgetMetadata] = {}
            self._by_category: Dict[str, List[str]] = {}
            self._by_capability: Dict[str, Set[str]] = {}
            # NO HARDCODED WIDGETS - registry starts empty
            # Widgets register themselves when loaded
            self._initialized = True

    def register(self, metadata: WidgetMetadata) -> None:
        """Register widget metadata.

        This is called by widgets themselves at load time.
        Core never calls this with hardcoded data.

        Args:
            metadata: Widget metadata to register
        """
        widget_id = metadata.widget_id

        # Store metadata
        self._metadata[widget_id] = metadata

        # Update category index
        if metadata.category not in self._by_category:
            self._by_category[metadata.category] = []
        if widget_id not in self._by_category[metadata.category]:
            self._by_category[metadata.category].append(widget_id)

        # Update capability index
        for cap in metadata.capabilities:
            if cap not in self._by_capability:
                self._by_capability[cap] = set()
            self._by_capability[cap].add(widget_id)

    def unregister(self, widget_id: str) -> None:
        """Remove widget metadata from registry.

        Args:
            widget_id: Widget to unregister
        """
        if widget_id not in self._metadata:
            return

        metadata = self._metadata[widget_id]

        # Remove from category index
        if metadata.category in self._by_category:
            self._by_category[metadata.category].remove(widget_id)
            if not self._by_category[metadata.category]:
                del self._by_category[metadata.category]

        # Remove from capability index
        for cap in metadata.capabilities:
            if cap in self._by_capability:
                self._by_capability[cap].discard(widget_id)
                if not self._by_capability[cap]:
                    del self._by_capability[cap]

        # Remove metadata
        del self._metadata[widget_id]

    def get(self, widget_id: str) -> Optional[WidgetMetadata]:
        """Get widget metadata by ID.

        Args:
            widget_id: Widget ID to look up

        Returns:
            Widget metadata or None if not found
        """
        return self._metadata.get(widget_id)

    def get_by_category(self, category: str) -> List[WidgetMetadata]:
        """Get all widgets in a category.

        Args:
            category: Category name

        Returns:
            List of widget metadata in the category
        """
        widget_ids = self._by_category.get(category, [])
        return [self._metadata[wid] for wid in widget_ids]

    def get_by_capability(self, capability: str) -> List[WidgetMetadata]:
        """Get all widgets with a specific capability.

        Args:
            capability: Capability name

        Returns:
            List of widget metadata with the capability
        """
        widget_ids = self._by_capability.get(capability, set())
        return [self._metadata[wid] for wid in widget_ids]

    def get_all(self) -> List[WidgetMetadata]:
        """Get all registered widget metadata.

        Returns:
            List of all widget metadata
        """
        return list(self._metadata.values())

    def get_display_name(self, widget_id: str) -> str:
        """Get display name for widget.

        Args:
            widget_id: Widget ID

        Returns:
            Display name or widget ID if not found
        """
        metadata = self.get(widget_id)
        return metadata.display_name if metadata else widget_id

    def get_icon(self, widget_id: str) -> Optional[str]:
        """Get icon for widget.

        Args:
            widget_id: Widget ID

        Returns:
            Icon name or None
        """
        metadata = self.get(widget_id)
        return metadata.icon if metadata else None

    def has_capability(self, widget_id: str, capability: str) -> bool:
        """Check if widget has a specific capability.

        Args:
            widget_id: Widget ID
            capability: Capability to check

        Returns:
            True if widget has the capability
        """
        metadata = self.get(widget_id)
        return capability in metadata.capabilities if metadata else False

    def is_singleton(self, widget_id: str) -> bool:
        """Check if widget is a singleton.

        Args:
            widget_id: Widget ID

        Returns:
            True if widget is a singleton
        """
        metadata = self.get(widget_id)
        return metadata.singleton if metadata else False


# Global registry instance
widget_metadata_registry = WidgetMetadataRegistry()


def register_widget_metadata(metadata: WidgetMetadata) -> None:
    """Convenience function to register widget metadata.

    This is called by widgets themselves, not by core code.

    Args:
        metadata: Widget metadata to register
    """
    widget_metadata_registry.register(metadata)


def get_widget_metadata(widget_id: str) -> Optional[WidgetMetadata]:
    """Convenience function to get widget metadata.

    Args:
        widget_id: Widget ID to look up

    Returns:
        Widget metadata or None if not found
    """
    return widget_metadata_registry.get(widget_id)


# NO HARDCODED WIDGET REGISTRATIONS HERE
# Widgets register themselves when they load
# This maintains true platform architecture
