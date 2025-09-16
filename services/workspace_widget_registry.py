#!/usr/bin/env python3
"""
Widget registry for tracking widgets in workspace tabs.

This component manages the mapping between widget IDs and their
tab indices, providing singleton widget support and focus operations.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class WorkspaceWidgetRegistry:
    """
    Registry for tracking widget IDs to tab indices.

    Provides widget registration, lookup, and registry maintenance
    operations for the workspace service.
    """

    def __init__(self):
        """Initialize the widget registry."""
        # Track widget IDs to tab indices for singleton support
        self._widget_registry: Dict[str, int] = {}  # widget_id -> tab_index

    def has_widget(self, widget_id: str) -> bool:
        """
        Check if a widget with the given ID exists.

        Args:
            widget_id: The widget ID to check

        Returns:
            True if the widget exists, False otherwise
        """
        return widget_id in self._widget_registry

    def register_widget(self, widget_id: str, tab_index: int) -> bool:
        """
        Register a widget with its tab index.

        Args:
            widget_id: The widget identifier
            tab_index: The tab index where the widget is located

        Returns:
            True if successfully registered
        """
        self._widget_registry[widget_id] = tab_index
        logger.debug(f"Registered widget {widget_id} at tab index {tab_index}")
        return True

    def unregister_widget(self, widget_id: str) -> bool:
        """
        Unregister a widget from the registry.

        Args:
            widget_id: The widget identifier to remove

        Returns:
            True if widget was found and removed, False otherwise
        """
        if widget_id in self._widget_registry:
            del self._widget_registry[widget_id]
            logger.debug(f"Unregistered widget {widget_id}")
            return True
        logger.warning(f"Widget {widget_id} not found in registry")
        return False

    def update_registry_after_tab_close(self, closed_index: int, widget_id: Optional[str] = None) -> int:
        """
        Update registry indices after a tab is closed.

        Args:
            closed_index: The index of the tab that was closed
            widget_id: Optional widget ID that was closed

        Returns:
            Number of widgets whose indices were updated
        """
        # Remove the closed widget if specified
        if widget_id and widget_id in self._widget_registry:
            del self._widget_registry[widget_id]
            logger.debug(f"Removed widget {widget_id} from registry (tab closed)")

        # Update indices for remaining widgets
        updated_count = 0
        for wid, tab_idx in list(self._widget_registry.items()):
            if tab_idx > closed_index:
                self._widget_registry[wid] = tab_idx - 1
                updated_count += 1
                logger.debug(f"Updated widget {wid} index: {tab_idx} -> {tab_idx - 1}")

        return updated_count

    def get_widget_tab_index(self, widget_id: str) -> Optional[int]:
        """
        Get the tab index for a registered widget.

        Args:
            widget_id: The widget identifier

        Returns:
            Tab index if widget is registered, None otherwise
        """
        return self._widget_registry.get(widget_id)

    def is_widget_registered(self, widget_id: str) -> bool:
        """
        Check if a widget is registered.

        Args:
            widget_id: The widget identifier

        Returns:
            True if widget is registered, False otherwise
        """
        return widget_id in self._widget_registry

    def clear(self):
        """Clear all widget registrations."""
        self._widget_registry.clear()

    def get_all_widgets(self) -> Dict[str, int]:
        """
        Get all registered widgets.

        Returns:
            Copy of the widget registry
        """
        return self._widget_registry.copy()