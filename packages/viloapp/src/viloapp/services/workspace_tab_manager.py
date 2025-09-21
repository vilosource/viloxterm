#!/usr/bin/env python3
"""
Tab management operations for the workspace service.

This component handles tab creation, closing, switching, and related
tab-based operations in the workspace. Works exclusively with model interface.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class WorkspaceTabManager:
    """
    Manager for tab operations in the workspace.

    Handles tab creation, closing, switching, and tab-related
    state management. Works exclusively with model interface.
    """

    def __init__(self, model, widget_registry=None):
        """
        Initialize the tab manager.

        Args:
            model: The workspace model interface (required)
            widget_registry: The widget registry instance
        """
        self._model = model
        self._widget_registry = widget_registry
        self._tab_counter = 0

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
            RuntimeError: If model interface is not available
        """
        # Auto-generate name if not provided
        if not name:
            self._tab_counter += 1
            name = f"Untitled {self._tab_counter}"

        logger.debug(f"Adding editor tab: {name}")

        if self._model:
            result = self._model.add_tab("editor", name)
            if result.success and result.data:
                index = result.data.get("index", -1)
                logger.info(f"Added editor tab '{name}' at index {index} via model")
                return index
            else:
                logger.error(f"Failed to add editor tab via model: {result.error}")
                raise RuntimeError(f"Failed to add editor tab: {result.error}")
        else:
            raise RuntimeError("Model interface is not available")

    def add_terminal_tab(self, name: Optional[str] = None) -> int:
        """
        Add a new terminal tab to the workspace.

        Args:
            name: Optional tab name, auto-generated if not provided

        Returns:
            Index of the created tab

        Raises:
            RuntimeError: If model interface is not available
        """
        # Auto-generate name if not provided
        if not name:
            self._tab_counter += 1
            name = f"Terminal {self._tab_counter}"

        logger.debug(f"Adding terminal tab: {name}")

        if self._model:
            result = self._model.add_tab("terminal", name)
            if result.success and result.data:
                index = result.data.get("index", -1)
                logger.info(f"Added terminal tab '{name}' at index {index} via model")
                return index
            else:
                logger.error(f"Failed to add terminal tab via model: {result.error}")
                raise RuntimeError(f"Failed to add terminal tab: {result.error}")
        else:
            raise RuntimeError("Model interface is not available")

    def add_app_widget_tab(
        self, widget_type: str, widget_id: str, name: Optional[str] = None
    ) -> int:
        """
        Add a generic app widget tab.

        Args:
            widget_type: Type of widget to create
            widget_id: Unique identifier for the widget
            name: Optional tab name

        Returns:
            Index of the created tab
        """
        if not name:
            name = f"{widget_type} Tab"

        logger.debug(f"Adding app widget tab: {name} (type: {widget_type})")

        if self._model:
            result = self._model.add_tab(widget_type, name)
            if result.success and result.data:
                index = result.data.get("index", -1)
                logger.info(f"Added widget tab '{name}' at index {index}")
                return index
            else:
                logger.error(f"Failed to add widget tab: {result.error}")
                return -1
        else:
            logger.error("No model interface available for adding widget tab")
            return -1

    def close_tab(self, index: int) -> bool:
        """
        Close the tab at the given index.

        Args:
            index: The tab index to close

        Returns:
            True if the tab was closed successfully, False otherwise
        """
        logger.debug(f"Closing tab at index: {index}")

        if self._model:
            result = self._model.close_tab(index)
            if result.success:
                logger.info(f"Successfully closed tab at index {index}")
                return True
            else:
                logger.error(f"Failed to close tab: {result.error}")
                return False
        else:
            logger.error("No model interface available for closing tab")
            return False

    def get_current_tab_index(self) -> int:
        """
        Get the index of the currently active tab.

        Returns:
            The index of the active tab, or 0 if no tabs
        """
        if self._model:
            state = self._model.get_state()
            return state.active_tab_index
        else:
            logger.error("No model interface available for getting current tab")
            return 0

    def get_tab_count(self) -> int:
        """
        Get the total number of tabs.

        Returns:
            The number of tabs in the workspace
        """
        if self._model:
            state = self._model.get_state()
            return len(state.tabs)
        else:
            logger.error("No model interface available for getting tab count")
            return 0

    def switch_to_tab(self, index: int) -> bool:
        """
        Switch to a specific tab.
        Args:
            index: Tab index
        Returns:
            True if switched successfully
        """
        if self._model:
            result = self._model.set_active_tab(index)
            return result.success
        else:
            logger.error("No model interface available for tab switching")
            return False

    def focus_widget(self, widget_id: str) -> bool:
        """
        Focus (switch to) a widget by its ID.

        Args:
            widget_id: The widget ID to focus

        Returns:
            True if the widget was focused successfully
        """
        logger.debug(f"Focusing widget: {widget_id}")

        if self._model:
            state = self._model.get_state()
            for i, tab in enumerate(state.tabs):
                # Check if this tab contains the widget
                if tab.id == widget_id:
                    result = self._model.set_active_tab(i)
                    return result.success

            logger.warning(f"Widget {widget_id} not found in tabs")
            return False
        else:
            logger.error("No model interface available for focusing widget")
            return False

    def rename_tab(self, index: int, new_name: str) -> bool:
        """
        Rename a tab at the given index.

        Args:
            index: The tab index to rename
            new_name: The new name for the tab

        Returns:
            True if the tab was renamed successfully
        """
        logger.debug(f"Renaming tab at index {index} to: {new_name}")

        if self._model:
            result = self._model.rename_tab(index, new_name)
            if result.success:
                logger.info(f"Successfully renamed tab at index {index} to '{new_name}'")
                return True
            else:
                logger.error(f"Failed to rename tab: {result.error}")
                return False
        else:
            logger.error("No model interface available for renaming tab")
            return False

    def get_tab_name(self, index: int) -> str:
        """
        Get the name of the tab at the given index.

        Args:
            index: The tab index

        Returns:
            The name of the tab, or empty string if not found
        """
        if self._model:
            state = self._model.get_state()
            if 0 <= index < len(state.tabs):
                return state.tabs[index].name
            else:
                logger.warning(f"Tab index {index} out of range")
                return ""
        else:
            logger.error("No model interface available for getting tab name")
            return ""

    def get_tab_info(self, index: int) -> dict:
        """
        Get information about a tab.

        Args:
            index: The tab index

        Returns:
            Dictionary with tab information
        """
        if self._model:
            state = self._model.get_state()
            if 0 <= index < len(state.tabs):
                tab = state.tabs[index]
                return {
                    "id": tab.id,
                    "name": tab.name,
                    "type": getattr(tab, "widget_type", "unknown"),
                    "is_active": index == state.active_tab_index,
                }
            else:
                logger.warning(f"Tab index {index} out of range")
                return {}
        else:
            logger.error("No model interface available for getting tab info")
            return {}
