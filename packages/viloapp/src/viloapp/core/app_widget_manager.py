#!/usr/bin/env python3
"""
Centralized AppWidget management system.

This module provides a singleton manager for registering, creating,
and querying AppWidgets. It serves as the single source of truth
for all widget metadata and factories.
"""

import logging
from typing import Callable, Optional

from viloapp.core.app_widget_metadata import AppWidgetMetadata, WidgetCategory
from viloapp.ui.widgets.app_widget import AppWidget

# WidgetType removed - now using string widget_ids

logger = logging.getLogger(__name__)


class AppWidgetManager:
    """
    Singleton manager for all AppWidget metadata and factories.

    This class provides centralized management of widget registration,
    creation, and discovery. It replaces the fragmented widget
    registration patterns throughout the codebase.
    """

    _instance: Optional["AppWidgetManager"] = None

    def __new__(cls) -> "AppWidgetManager":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the manager (only runs once due to singleton)."""
        if not self._initialized:
            self._widgets: dict[str, AppWidgetMetadata] = {}
            # Type mapping removed - now using widget IDs directly
            self._factories: dict[str, Callable] = {}
            self._category_cache: dict[WidgetCategory, list[str]] = {}
            self._initialized = True
            logger.info("AppWidgetManager initialized")

    @classmethod
    def get_instance(cls) -> "AppWidgetManager":
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_widget(self, metadata: AppWidgetMetadata) -> None:
        """
        Register a widget with its metadata.

        Args:
            metadata: Complete widget metadata

        Raises:
            ValueError: If widget_id already registered
        """
        if metadata.widget_id in self._widgets:
            logger.warning(f"Widget {metadata.widget_id} already registered, updating")

        self._widgets[metadata.widget_id] = metadata
        # Type mapping removed - no longer needed

        # Cache by category
        if metadata.category not in self._category_cache:
            self._category_cache[metadata.category] = []
        if metadata.widget_id not in self._category_cache[metadata.category]:
            self._category_cache[metadata.category].append(metadata.widget_id)

        # Register factory if provided
        if metadata.factory:
            self._factories[metadata.widget_id] = metadata.factory

        logger.debug(f"Registered widget: {metadata.widget_id} ({metadata.display_name})")

    def get_widget(self, widget_id: str) -> Optional[AppWidgetMetadata]:
        """
        Get widget metadata by ID.

        Args:
            widget_id: Widget ID to look up

        Returns:
            Widget metadata or None if not found
        """
        return self._widgets.get(widget_id)

    def is_widget_available(self, widget_id: str) -> bool:
        """
        Check if a widget is available.

        Args:
            widget_id: Widget ID to check

        Returns:
            True if widget exists and is available
        """
        widget = self.get_widget(widget_id)
        return widget is not None and widget.is_available()

    def unregister_widget(self, widget_id: str) -> bool:
        """
        Unregister a widget.

        Args:
            widget_id: Widget identifier

        Returns:
            True if widget was unregistered, False if not found
        """
        if widget_id not in self._widgets:
            return False

        metadata = self._widgets[widget_id]

        # Remove from main registry
        del self._widgets[widget_id]

        # Remove from type mapping
        # Type mapping cleanup removed - no longer needed

        # Remove from category cache
        if metadata.category in self._category_cache:
            if widget_id in self._category_cache[metadata.category]:
                self._category_cache[metadata.category].remove(widget_id)

        # Remove factory
        if widget_id in self._factories:
            del self._factories[widget_id]

        logger.debug(f"Unregistered widget: {widget_id}")
        return True

    def create_widget(self, widget_id: str, instance_id: str) -> Optional[AppWidget]:
        """
        Create a widget instance.

        Args:
            widget_id: Widget type identifier
            instance_id: Unique instance identifier

        Returns:
            New AppWidget instance or None if widget not found
        """
        metadata = self._widgets.get(widget_id)
        if not metadata:
            logger.error(f"Widget {widget_id} not registered")
            return None

        if not metadata.is_available():
            logger.error(f"Widget {widget_id} is not available")
            return None

        try:
            # Use factory if available
            if metadata.factory:
                widget = metadata.factory(instance_id)
            else:
                # Direct instantiation - only pass instance_id
                # Widget classes handle their own widget_type internally
                widget = metadata.widget_class(instance_id)

            # Set the metadata on the widget so it knows its configuration
            if hasattr(widget, "set_metadata"):
                widget.set_metadata(metadata)

            logger.debug(f"Created widget instance: {widget_id} (instance: {instance_id})")
            return widget

        except Exception as e:
            logger.error(f"Failed to create widget {widget_id}: {e}")
            return None

    def create_widget_by_id(
        self, widget_id: str, instance_id: str
    ) -> Optional[AppWidget]:
        """
        Create a widget by widget ID.

        Args:
            widget_id: Widget ID string (e.g., 'viloapp.terminal')
            instance_id: Unique instance identifier

        Returns:
            New AppWidget instance or None if not found
        """
        return self.create_widget(widget_id, instance_id)

    def get_widget_metadata(self, widget_id: str) -> Optional[AppWidgetMetadata]:
        """
        Get metadata for a widget.

        Args:
            widget_id: Widget identifier

        Returns:
            Widget metadata or None if not found
        """
        return self._widgets.get(widget_id)

    # Method removed - use get_widget_metadata with widget ID instead

    def get_all_widgets(self) -> list[AppWidgetMetadata]:
        """
        Get all registered widgets.

        Returns:
            List of all widget metadata
        """
        return list(self._widgets.values())

    def get_widgets_by_category(self, category: WidgetCategory) -> list[AppWidgetMetadata]:
        """
        Get widgets in a specific category.

        Args:
            category: Widget category

        Returns:
            List of widgets in the category
        """
        widget_ids = self._category_cache.get(category, [])
        return [self._widgets[wid] for wid in widget_ids if wid in self._widgets]

    def widget_has_category(self, widget_id: str, category: WidgetCategory) -> bool:
        """
        Check if a widget belongs to a specific category.

        Args:
            widget_id: Widget identifier
            category: Category to check

        Returns:
            True if widget belongs to the category
        """
        metadata = self.get_widget_metadata(widget_id)
        return metadata.category == category if metadata else False

    def get_default_widget_for_category(self, category: WidgetCategory) -> Optional[str]:
        """
        Get the default widget ID for a category.

        Args:
            category: Widget category

        Returns:
            Widget ID of the default widget for the category, or None
        """
        widgets = self.get_widgets_by_category(category)
        if not widgets:
            return None

        # Sort by default priority (lower is better) and return the first
        default_widgets = [w for w in widgets if w.can_be_default]
        if default_widgets:
            default_widgets.sort(key=lambda w: w.default_priority)
            return default_widgets[0].widget_id

        # If no default widgets, return the first available
        return widgets[0].widget_id if widgets else None

    def get_widgets_by_source(self, source: str) -> list[AppWidgetMetadata]:
        """
        Get widgets by source (builtin/plugin).

        Args:
            source: Source type ("builtin" or "plugin")

        Returns:
            List of widgets from the source
        """
        return [w for w in self._widgets.values() if w.source == source]

    def get_widgets_with_capability(self, capability: str) -> list[AppWidgetMetadata]:
        """
        Get widgets that provide a specific capability.

        Args:
            capability: Capability name

        Returns:
            List of widgets with the capability
        """
        return [w for w in self._widgets.values() if capability in w.provides_capabilities]

    def get_widgets_for_file_type(self, file_extension: str) -> list[AppWidgetMetadata]:
        """
        Get widgets that support a file type.

        Args:
            file_extension: File extension (with or without dot)

        Returns:
            List of widgets supporting the file type
        """
        ext = file_extension.lstrip(".")
        return [w for w in self._widgets.values() if ext in w.supported_file_types]

    def get_available_widgets(self) -> list[AppWidgetMetadata]:
        """
        Get all currently available widgets.

        Returns:
            List of available widgets
        """
        return [w for w in self._widgets.values() if w.is_available()]

    def get_menu_widgets(self) -> list[AppWidgetMetadata]:
        """
        Get widgets that should appear in menus.

        Returns:
            List of widgets for menu display
        """
        return [w for w in self._widgets.values() if w.show_in_menu and w.is_available()]

    def get_default_widget_id(self, context: Optional[str] = None) -> Optional[str]:
        """
        Get the default widget ID based on registry and preferences.

        Uses a multi-level fallback system:
        1. User preference for the specific context (if provided)
        2. User general preference
        3. Widgets that declare themselves as defaults (sorted by priority)
        4. First available widget in the context category
        5. Any available widget

        Args:
            context: Optional context like "terminal", "editor", "shell"

        Returns:
            Default widget ID or None if no widgets are available
        """
        # Step 1: Check user preference for specific context
        if context:
            from viloapp.core.settings.app_defaults import get_default_widget_for_context
            pref = get_default_widget_for_context(context)
            if pref and self.is_widget_available(pref):
                return pref

        # Step 2: Check user's general preference
        from viloapp.core.settings.app_defaults import get_default_widget_preference
        general_pref = get_default_widget_preference()
        if general_pref and self.is_widget_available(general_pref):
            return general_pref

        # Step 3: Find widgets that can be defaults
        candidates = [
            w for w in self._widgets.values()
            if w.can_be_default and w.is_available()
        ]

        # If context provided, prefer widgets that support that context
        if context and candidates:
            context_widgets = [
                w for w in candidates
                if context in w.default_for_contexts
            ]
            if context_widgets:
                candidates = context_widgets

        # Sort by priority (lower number = higher priority)
        if candidates:
            candidates.sort(key=lambda w: w.default_priority)
            return candidates[0].widget_id

        # Step 4: Fall back to any available widget
        available = self.get_available_widgets()
        if available:
            return available[0].widget_id

        # Step 5: No widgets available
        return None

    def get_widgets_for_context(self, context: str) -> list[str]:
        """
        Get all widget IDs that support a specific context.

        Args:
            context: Context like "terminal", "editor", "shell"

        Returns:
            List of widget IDs that support the context
        """
        widgets = [
            w.widget_id for w in self._widgets.values()
            if context in w.default_for_contexts and w.is_available()
        ]
        return widgets

    def get_available_widget_ids(self) -> list[str]:
        """
        Get list of all available widget IDs.

        Returns:
            List of widget IDs that are currently available
        """
        return [w.widget_id for w in self.get_available_widgets()]

    def is_terminal_widget(self, widget_id: str) -> bool:
        """
        Check if a widget ID represents a terminal widget.

        Args:
            widget_id: Widget ID to check

        Returns:
            True if this is a terminal widget
        """
        metadata = self.get_widget(widget_id)
        if metadata:
            return "terminal" in metadata.default_for_contexts or "shell" in metadata.default_for_contexts
        return False

    def is_editor_widget(self, widget_id: str) -> bool:
        """
        Check if a widget ID represents an editor widget.

        Args:
            widget_id: Widget ID to check

        Returns:
            True if this is an editor widget
        """
        metadata = self.get_widget(widget_id)
        if metadata:
            return "editor" in metadata.default_for_contexts or "text" in metadata.default_for_contexts
        return False

    def is_settings_widget(self, widget_id: str) -> bool:
        """
        Check if a widget ID represents a settings widget.

        Args:
            widget_id: Widget ID to check

        Returns:
            True if this is a settings widget
        """
        # Check if widget has settings category
        metadata = self.get_widget_metadata(widget_id)
        if metadata and "settings" in metadata.categories:
            return True
        # Fallback to ID-based check for plugins
        return widget_id.endswith(".settings")

    def clear(self) -> None:
        """Clear all registered widgets (mainly for testing)."""
        self._widgets.clear()
        # Type mapping clear removed - no longer needed
        self._factories.clear()
        self._category_cache.clear()
        logger.debug("Cleared all registered widgets")

    def __len__(self) -> int:
        """Get number of registered widgets."""
        return len(self._widgets)

    def __contains__(self, widget_id: str) -> bool:
        """Check if a widget is registered."""
        return widget_id in self._widgets

    def __repr__(self) -> str:
        """String representation."""
        return f"AppWidgetManager({len(self._widgets)} widgets registered)"


# Create and export singleton instance
app_widget_manager = AppWidgetManager.get_instance()
