#!/usr/bin/env python3
"""
Centralized AppWidget management system.

This module provides a singleton manager for registering, creating,
and querying AppWidgets. It serves as the single source of truth
for all widget metadata and factories.
"""

import logging
import warnings
from typing import Dict, List, Optional, Callable, Type
from core.app_widget_metadata import AppWidgetMetadata, WidgetCategory
from ui.widgets.widget_registry import WidgetType
from ui.widgets.app_widget import AppWidget

logger = logging.getLogger(__name__)


class AppWidgetManager:
    """
    Singleton manager for all AppWidget metadata and factories.

    This class provides centralized management of widget registration,
    creation, and discovery. It replaces the fragmented widget
    registration patterns throughout the codebase.
    """

    _instance: Optional['AppWidgetManager'] = None

    def __new__(cls) -> 'AppWidgetManager':
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the manager (only runs once due to singleton)."""
        if not self._initialized:
            self._widgets: Dict[str, AppWidgetMetadata] = {}
            self._type_mapping: Dict[WidgetType, str] = {}  # For backward compatibility
            self._factories: Dict[str, Callable] = {}
            self._category_cache: Dict[WidgetCategory, List[str]] = {}
            self._initialized = True
            logger.info("AppWidgetManager initialized")

    @classmethod
    def get_instance(cls) -> 'AppWidgetManager':
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
        self._type_mapping[metadata.widget_type] = metadata.widget_id

        # Cache by category
        if metadata.category not in self._category_cache:
            self._category_cache[metadata.category] = []
        if metadata.widget_id not in self._category_cache[metadata.category]:
            self._category_cache[metadata.category].append(metadata.widget_id)

        # Register factory if provided
        if metadata.factory:
            self._factories[metadata.widget_id] = metadata.factory

        logger.debug(f"Registered widget: {metadata.widget_id} ({metadata.display_name})")

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
        if metadata.widget_type in self._type_mapping:
            if self._type_mapping[metadata.widget_type] == widget_id:
                del self._type_mapping[metadata.widget_type]

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

            logger.debug(f"Created widget instance: {widget_id} (instance: {instance_id})")
            return widget

        except Exception as e:
            logger.error(f"Failed to create widget {widget_id}: {e}")
            return None

    def create_widget_by_type(self, widget_type: WidgetType, instance_id: str) -> Optional[AppWidget]:
        """
        Create a widget by WidgetType enum (backward compatibility).

        Args:
            widget_type: WidgetType enum value
            instance_id: Unique instance identifier

        Returns:
            New AppWidget instance or None if type not found
        """
        widget_id = self._type_mapping.get(widget_type)
        if not widget_id:
            logger.error(f"No widget registered for type {widget_type}")
            return None

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

    def get_widget_by_type(self, widget_type: WidgetType) -> Optional[AppWidgetMetadata]:
        """
        Get widget metadata by WidgetType enum.

        Args:
            widget_type: WidgetType enum value

        Returns:
            Widget metadata or None if not found
        """
        widget_id = self._type_mapping.get(widget_type)
        if widget_id:
            return self._widgets.get(widget_id)
        return None

    def get_all_widgets(self) -> List[AppWidgetMetadata]:
        """
        Get all registered widgets.

        Returns:
            List of all widget metadata
        """
        return list(self._widgets.values())

    def get_widgets_by_category(self, category: WidgetCategory) -> List[AppWidgetMetadata]:
        """
        Get widgets in a specific category.

        Args:
            category: Widget category

        Returns:
            List of widgets in the category
        """
        widget_ids = self._category_cache.get(category, [])
        return [self._widgets[wid] for wid in widget_ids if wid in self._widgets]

    def get_widgets_by_source(self, source: str) -> List[AppWidgetMetadata]:
        """
        Get widgets by source (builtin/plugin).

        Args:
            source: Source type ("builtin" or "plugin")

        Returns:
            List of widgets from the source
        """
        return [w for w in self._widgets.values() if w.source == source]

    def get_widgets_with_capability(self, capability: str) -> List[AppWidgetMetadata]:
        """
        Get widgets that provide a specific capability.

        Args:
            capability: Capability name

        Returns:
            List of widgets with the capability
        """
        return [w for w in self._widgets.values() if capability in w.provides_capabilities]

    def get_widgets_for_file_type(self, file_extension: str) -> List[AppWidgetMetadata]:
        """
        Get widgets that support a file type.

        Args:
            file_extension: File extension (with or without dot)

        Returns:
            List of widgets supporting the file type
        """
        ext = file_extension.lstrip('.')
        return [w for w in self._widgets.values() if ext in w.supported_file_types]

    def get_available_widgets(self) -> List[AppWidgetMetadata]:
        """
        Get all currently available widgets.

        Returns:
            List of available widgets
        """
        return [w for w in self._widgets.values() if w.is_available()]

    def get_menu_widgets(self) -> List[AppWidgetMetadata]:
        """
        Get widgets that should appear in menus.

        Returns:
            List of widgets for menu display
        """
        return [w for w in self._widgets.values() if w.show_in_menu and w.is_available()]

    def register_factory_compat(self, widget_type: WidgetType, factory: Callable) -> None:
        """
        Register a factory using old WidgetType pattern (backward compatibility).

        This method is deprecated and provided only for backward compatibility
        with existing code that uses widget_registry.register_factory().

        Args:
            widget_type: WidgetType enum value
            factory: Factory function
        """
        warnings.warn(
            "register_factory_compat is deprecated. "
            "Use register_widget() with full metadata instead.",
            DeprecationWarning,
            stacklevel=2
        )

        # Find widget with this type
        widget_id = self._type_mapping.get(widget_type)
        if widget_id and widget_id in self._widgets:
            self._widgets[widget_id].factory = factory
            self._factories[widget_id] = factory
            logger.debug(f"Updated factory for {widget_id} via compatibility method")
        else:
            logger.warning(f"Cannot register factory for unknown widget type {widget_type}")

    def clear(self) -> None:
        """Clear all registered widgets (mainly for testing)."""
        self._widgets.clear()
        self._type_mapping.clear()
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