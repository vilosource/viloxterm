#!/usr/bin/env python3
"""
Capability manager for ViloxTerm.

This module manages widget capabilities, enabling the platform to
discover and interact with widgets based on their capabilities rather
than their types.

ARCHITECTURE COMPLIANCE:
- Singleton pattern for global capability management
- Dynamic discovery - no hardcoded widget knowledge
- Runtime registration and querying
"""

import logging
from typing import Any, Dict, List, Optional, Set

from viloapp.core.capabilities import WidgetCapability
from viloapp.core.capability_provider import (
    CapabilityExecutionError,
    CapabilityNotSupportedError,
    ICapabilityProvider,
)

logger = logging.getLogger(__name__)


class CapabilityManager:
    """
    Central manager for widget capabilities.

    This manager tracks which widgets support which capabilities,
    enabling capability-based interactions without type checking.
    """

    _instance: Optional["CapabilityManager"] = None

    def __new__(cls) -> "CapabilityManager":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the manager (only once)."""
        if self._initialized:
            return

        # Widget registry: widget_id -> ICapabilityProvider
        self._widgets: Dict[str, ICapabilityProvider] = {}

        # Capability index: capability -> set of widget_ids
        self._capability_index: Dict[WidgetCapability, Set[str]] = {}

        # Cache of widget capabilities for performance
        self._capability_cache: Dict[str, Set[WidgetCapability]] = {}

        self._initialized = True
        logger.info("CapabilityManager initialized")

    def register_widget(self, widget_id: str, widget: ICapabilityProvider) -> None:
        """
        Register a widget and its capabilities.

        This is called when a widget is created or when its
        capabilities change.

        Args:
            widget_id: Unique identifier for the widget instance
            widget: The widget implementing ICapabilityProvider
        """
        # Get widget's capabilities
        try:
            capabilities = widget.get_capabilities()
        except Exception as e:
            logger.error(f"Failed to get capabilities for widget {widget_id}: {e}")
            capabilities = set()

        # Store widget reference
        self._widgets[widget_id] = widget

        # Cache capabilities
        self._capability_cache[widget_id] = capabilities

        # Update capability index
        for capability in capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = set()
            self._capability_index[capability].add(widget_id)

        logger.debug(f"Registered widget {widget_id} with {len(capabilities)} capabilities")

    def unregister_widget(self, widget_id: str) -> None:
        """
        Unregister a widget and its capabilities.

        This is called when a widget is destroyed.

        Args:
            widget_id: The widget to unregister
        """
        if widget_id not in self._widgets:
            return

        # Get cached capabilities
        capabilities = self._capability_cache.get(widget_id, set())

        # Remove from capability index
        for capability in capabilities:
            if capability in self._capability_index:
                self._capability_index[capability].discard(widget_id)
                if not self._capability_index[capability]:
                    del self._capability_index[capability]

        # Remove from registries
        del self._widgets[widget_id]
        if widget_id in self._capability_cache:
            del self._capability_cache[widget_id]

        logger.debug(f"Unregistered widget {widget_id}")

    def find_widgets_with_capability(self, capability: WidgetCapability) -> List[str]:
        """
        Find all widgets that support a specific capability.

        Args:
            capability: The capability to search for

        Returns:
            List of widget IDs that support the capability
        """
        return list(self._capability_index.get(capability, set()))

    def get_widget_capabilities(self, widget_id: str) -> Set[WidgetCapability]:
        """
        Get all capabilities for a specific widget.

        Args:
            widget_id: The widget to query

        Returns:
            Set of capabilities the widget supports
        """
        return self._capability_cache.get(widget_id, set())

    def widget_has_capability(self, widget_id: str, capability: WidgetCapability) -> bool:
        """
        Check if a widget supports a specific capability.

        Args:
            widget_id: The widget to check
            capability: The capability to check for

        Returns:
            True if the widget supports the capability
        """
        return capability in self._capability_cache.get(widget_id, set())

    def execute_capability(
        self, widget_id: str, capability: WidgetCapability, **kwargs: Any
    ) -> Any:
        """
        Execute a capability on a widget.

        This is the main interface for the platform to interact with
        widgets in a type-agnostic manner.

        Args:
            widget_id: The widget to execute on
            capability: The capability to execute
            **kwargs: Capability-specific arguments

        Returns:
            Capability-specific return value

        Raises:
            CapabilityNotSupportedError: Widget doesn't support capability
            CapabilityExecutionError: Execution failed
        """
        # Get the widget
        widget = self._widgets.get(widget_id)
        if not widget:
            raise CapabilityExecutionError(widget_id, capability, "Widget not registered")

        # Check if widget supports the capability
        if not self.widget_has_capability(widget_id, capability):
            raise CapabilityNotSupportedError(widget_id, capability)

        # Execute the capability
        try:
            return widget.execute_capability(capability, **kwargs)
        except CapabilityNotSupportedError:
            raise
        except CapabilityExecutionError:
            raise
        except Exception as e:
            raise CapabilityExecutionError(widget_id, capability, str(e)) from e

    def get_first_widget_with_capability(self, capability: WidgetCapability) -> Optional[str]:
        """
        Get the first widget that supports a capability.

        Useful for finding any widget that can perform an action.

        Args:
            capability: The capability to search for

        Returns:
            Widget ID or None if no widgets support the capability
        """
        widgets = self.find_widgets_with_capability(capability)
        return widgets[0] if widgets else None

    def get_active_widget_with_capability(
        self, capability: WidgetCapability, active_widget_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a widget with a capability, preferring the active widget.

        Args:
            capability: The capability to search for
            active_widget_id: The currently active widget (if any)

        Returns:
            Widget ID or None if no widgets support the capability
        """
        # Check if active widget has the capability
        if active_widget_id and self.widget_has_capability(active_widget_id, capability):
            return active_widget_id

        # Otherwise, find any widget with the capability
        return self.get_first_widget_with_capability(capability)

    def refresh_widget_capabilities(self, widget_id: str) -> None:
        """
        Refresh the cached capabilities for a widget.

        Call this if a widget's capabilities change at runtime.

        Args:
            widget_id: The widget to refresh
        """
        widget = self._widgets.get(widget_id)
        if not widget:
            return

        # Get old capabilities
        old_capabilities = self._capability_cache.get(widget_id, set())

        # Get new capabilities
        try:
            new_capabilities = widget.get_capabilities()
        except Exception as e:
            logger.error(f"Failed to refresh capabilities for widget {widget_id}: {e}")
            return

        # Update cache
        self._capability_cache[widget_id] = new_capabilities

        # Update index - remove old
        for capability in old_capabilities - new_capabilities:
            if capability in self._capability_index:
                self._capability_index[capability].discard(widget_id)
                if not self._capability_index[capability]:
                    del self._capability_index[capability]

        # Update index - add new
        for capability in new_capabilities - old_capabilities:
            if capability not in self._capability_index:
                self._capability_index[capability] = set()
            self._capability_index[capability].add(widget_id)

        logger.debug(f"Refreshed capabilities for widget {widget_id}")

    def clear(self) -> None:
        """
        Clear all registered widgets and capabilities.

        Mainly for testing or shutdown.
        """
        self._widgets.clear()
        self._capability_index.clear()
        self._capability_cache.clear()
        logger.info("CapabilityManager cleared")

    def get_capability_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about registered capabilities.

        Returns:
            Dictionary with capability statistics
        """
        return {
            "total_widgets": len(self._widgets),
            "total_capabilities": len(self._capability_index),
            "capabilities_by_count": {
                capability.value: len(widgets)
                for capability, widgets in self._capability_index.items()
            },
            "widgets_by_capability_count": {
                widget_id: len(caps) for widget_id, caps in self._capability_cache.items()
            },
        }


# Global singleton instance
capability_manager = CapabilityManager()


def register_widget_capabilities(widget_id: str, widget: ICapabilityProvider) -> None:
    """
    Convenience function to register widget capabilities.

    Args:
        widget_id: Unique identifier for the widget
        widget: The widget implementing ICapabilityProvider
    """
    capability_manager.register_widget(widget_id, widget)


def unregister_widget_capabilities(widget_id: str) -> None:
    """
    Convenience function to unregister widget capabilities.

    Args:
        widget_id: The widget to unregister
    """
    capability_manager.unregister_widget(widget_id)


def find_capable_widgets(capability: WidgetCapability) -> List[str]:
    """
    Convenience function to find widgets with a capability.

    Args:
        capability: The capability to search for

    Returns:
        List of widget IDs that support the capability
    """
    return capability_manager.find_widgets_with_capability(capability)
