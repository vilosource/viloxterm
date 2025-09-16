#!/usr/bin/env python3
"""
Tab management operations for the workspace service.

This component handles tab creation, closing, switching, and related
tab-based operations in the workspace.
"""

from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class WorkspaceTabManager:
    """
    Manager for tab operations in the workspace.

    Handles tab creation, closing, switching, and tab-related
    state management.
    """

    def __init__(self, workspace=None, widget_registry=None):
        """
        Initialize the tab manager.

        Args:
            workspace: The workspace instance
            widget_registry: The widget registry instance
        """
        self._workspace = workspace
        self._widget_registry = widget_registry
        self._tab_counter = 0

    def set_workspace(self, workspace):
        """Set the workspace instance."""
        self._workspace = workspace

    def set_widget_registry(self, widget_registry):
        """Set the widget registry instance."""
        self._widget_registry = widget_registry

    def add_editor_tab(self, name: Optional[str] = None) -> int:
        """
        Add a new editor tab to the workspace.

        Args:
            name: Optional tab name, auto-generated if not provided

        Returns:
            Index of the created tab

        Raises:
            RuntimeError: If workspace is not available
        """
        if not self._workspace:
            raise RuntimeError("Workspace not available")

        # Auto-generate name if not provided
        if not name:
            self._tab_counter += 1
            name = f"Editor {self._tab_counter}"

        # Add the tab
        index = self._workspace.add_editor_tab(name)

        logger.info(f"Added editor tab '{name}' at index {index}")
        return index

    def add_terminal_tab(self, name: Optional[str] = None) -> int:
        """
        Add a new terminal tab to the workspace.

        Args:
            name: Optional tab name, auto-generated if not provided

        Returns:
            Index of the created tab

        Raises:
            RuntimeError: If workspace is not available
        """
        if not self._workspace:
            raise RuntimeError("Workspace not available")

        # Auto-generate name if not provided
        if not name:
            self._tab_counter += 1
            name = f"Terminal {self._tab_counter}"

        # Add the tab
        index = self._workspace.add_terminal_tab(name)

        logger.info(f"Added terminal tab '{name}' at index {index}")
        return index

    def add_app_widget(self, widget_type, widget_id: str, name: Optional[str] = None) -> bool:
        """
        Add a generic app widget tab.

        Args:
            widget_type: The WidgetType of the widget to add
            widget_id: Unique ID for the widget
            name: Optional tab name

        Returns:
            bool: True if successfully added, False otherwise
        """
        if not self._workspace:
            logger.error("Cannot add app widget: workspace not available")
            return False

        try:
            # Add the generic app widget tab - returns tab index or -1 on failure
            tab_index = self._workspace.add_app_widget_tab(widget_type, widget_id, name)
            success = tab_index >= 0

            if success and self._widget_registry:
                # Track the widget in our registry
                self._widget_registry.register_widget(widget_id, tab_index)
                logger.info(f"Added app widget '{name}' (type: {widget_type}) with id {widget_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to add app widget: {e}")
            return False

    def close_tab(self, index: Optional[int] = None) -> bool:
        """
        Close a tab.

        Args:
            index: Tab index to close, or None for current tab

        Returns:
            True if tab was closed
        """
        if not self._workspace:
            return False

        # Get current index if not provided
        if index is None:
            index = self._workspace.tab_widget.currentIndex()

        if index < 0:
            return False

        # Get tab name before closing
        tab_name = self._workspace.tab_widget.tabText(index) if self._workspace.tab_widget else None

        # Clean up widget registry if available
        if self._widget_registry:
            # Find and remove any widgets at this tab index, update others
            widgets_to_remove = []
            for widget_id, tab_idx in self._widget_registry.get_all_widgets().items():
                if tab_idx == index:
                    widgets_to_remove.append(widget_id)

            # Remove widgets that were in the closed tab and update indices
            for widget_id in widgets_to_remove:
                self._widget_registry.unregister_widget(widget_id)
                logger.debug(f"Removed widget {widget_id} from registry (tab closed)")

            # Update registry for remaining tabs
            self._widget_registry.update_registry_after_tab_close(index)

        # Close the tab
        self._workspace.close_tab(index)

        logger.info(f"Closed tab '{tab_name}' at index {index}")
        return True

    def get_current_tab_index(self) -> int:
        """
        Get the index of the current tab.

        Returns:
            Current tab index, or -1 if no tabs
        """
        if not self._workspace:
            return -1
        return self._workspace.tab_widget.currentIndex()

    def get_tab_count(self) -> int:
        """
        Get the number of open tabs.

        Returns:
            Number of tabs
        """
        if not self._workspace:
            return 0
        return self._workspace.tab_widget.count()

    def switch_to_tab(self, index: int) -> bool:
        """
        Switch to a specific tab.

        Args:
            index: Tab index

        Returns:
            True if switched successfully
        """
        if not self._workspace:
            return False

        if 0 <= index < self._workspace.tab_widget.count():
            self._workspace.tab_widget.setCurrentIndex(index)
            return True

        return False

    def focus_widget(self, widget_id: str) -> bool:
        """
        Focus (switch to) a widget by its ID.

        Args:
            widget_id: The widget ID to focus

        Returns:
            True if successfully focused, False otherwise
        """
        if not self._widget_registry:
            logger.warning("Cannot focus widget: no widget registry available")
            return False

        if not self._widget_registry.has_widget(widget_id):
            logger.warning(f"Cannot focus widget {widget_id}: not found in registry")
            return False

        tab_index = self._widget_registry.get_widget_tab_index(widget_id)
        if tab_index is None:
            return False

        # Verify the tab index is still valid
        if not self._workspace or tab_index >= self._workspace.tab_widget.count():
            logger.warning(f"Widget {widget_id} has invalid tab index {tab_index}, removing from registry")
            self._widget_registry.unregister_widget(widget_id)
            return False

        return self.switch_to_tab(tab_index)

    def get_tab_info(self) -> Dict[str, Any]:
        """
        Get information about tabs.

        Returns:
            Dictionary with tab information
        """
        if not self._workspace:
            return {
                'count': 0,
                'current': -1,
                'available': False
            }

        return {
            'count': self.get_tab_count(),
            'current': self.get_current_tab_index(),
            'available': True,
            'current_tab_info': self._workspace.get_current_tab_info() if hasattr(self._workspace, 'get_current_tab_info') else None
        }