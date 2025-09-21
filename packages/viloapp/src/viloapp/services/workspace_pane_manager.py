#!/usr/bin/env python3
"""
Pane management operations for the workspace service.

This component handles pane splitting, closing, navigation, and related
pane-based operations in the workspace. Works exclusively with model interface.
"""

import logging
from typing import Optional

from viloapp.core.events.event_bus import event_bus
from viloapp.core.events.events import EventTypes

logger = logging.getLogger(__name__)


class WorkspacePaneManager:
    """
    Manager for pane operations in the workspace.

    Handles pane splitting, closing, navigation, and pane-related
    state management. Works exclusively with model interface.
    """

    def __init__(self, model):
        """
        Initialize the pane manager.

        Args:
            model: The workspace model interface (required)
        """
        self._model = model
        self._pane_counter = 0

    def split_active_pane(self, orientation: str) -> Optional[str]:
        """
        Split the active pane in the given orientation.

        Args:
            orientation: "horizontal" or "vertical"

        Returns:
            ID of the newly created pane, or None on failure
        """
        logger.debug(f"Splitting active pane {orientation}ly")

        if self._model:
            # Get the current active pane from model
            state = self._model.get_state()
            if not state.tabs:
                logger.warning("No tabs available to split")
                return None

            active_tab = state.tabs[state.active_tab_index]
            active_pane_id = active_tab.active_pane_id

            # Create split pane request
            from viloapp.models.operations import SplitPaneRequest

            request = SplitPaneRequest(pane_id=active_pane_id, orientation=orientation, ratio=0.5)

            # Execute split via model
            result = self._model.split_pane(request)
            if result.success:
                new_pane_id = result.data.get("new_pane_id")
                logger.info(f"Split pane {orientation}ly via model, created pane {new_pane_id}")
                return new_pane_id
            else:
                logger.error(f"Failed to split pane via model: {result.error}")
                return None
        else:
            logger.error("No model interface available for pane splitting")
            return None

    def close_active_pane(self) -> bool:
        """
        Close the currently active pane.

        Returns:
            True if the pane was closed successfully
        """
        logger.debug("Closing active pane")

        if self._model:
            # Get the current active pane from model
            state = self._model.get_state()
            if not state.tabs:
                logger.warning("No tabs available")
                return False

            active_tab = state.tabs[state.active_tab_index]
            active_pane_id = active_tab.active_pane_id

            # Create close pane request
            from viloapp.models.operations import ClosePaneRequest

            request = ClosePaneRequest(pane_id=active_pane_id)

            # Execute close via model
            result = self._model.close_pane(request)
            if result.success:
                logger.info(f"Closed active pane {active_pane_id}")
                return True
            else:
                logger.error(f"Failed to close pane: {result.error}")
                return False
        else:
            logger.error("No model interface available for pane closing")
            return False

    def close_pane(self, pane_id: str) -> bool:
        """
        Close a specific pane by ID.

        Args:
            pane_id: ID of the pane to close

        Returns:
            True if the pane was closed successfully
        """
        logger.debug(f"Closing pane: {pane_id}")

        if self._model:
            # Create close pane request
            from viloapp.models.operations import ClosePaneRequest

            request = ClosePaneRequest(pane_id=pane_id)

            # Execute close via model
            result = self._model.close_pane(request)
            if result.success:
                logger.info(f"Closed pane {pane_id}")
                return True
            else:
                logger.error(f"Failed to close pane {pane_id}: {result.error}")
                return False
        else:
            logger.error("No model interface available for pane closing")
            return False

    def get_active_pane_id(self) -> Optional[str]:
        """
        Get the ID of the currently active pane.

        Returns:
            Active pane ID or None if no active pane
        """
        if self._model:
            state = self._model.get_state()
            if state.tabs and state.active_tab_index < len(state.tabs):
                return state.tabs[state.active_tab_index].active_pane_id
            return None
        else:
            logger.error("No model interface available for getting active pane")
            return None

    def navigate_pane(self, direction: str) -> bool:
        """
        Navigate to the next pane in the given direction.

        Args:
            direction: "up", "down", "left", "right"

        Returns:
            True if navigation was successful
        """
        logger.debug(f"Navigating pane {direction}")

        if self._model:
            # Get current state
            state = self._model.get_state()
            if not state.tabs:
                return False

            active_tab = state.tabs[state.active_tab_index]
            current_pane_id = active_tab.active_pane_id

            # Find pane in direction (this would be implemented in the model)
            # For now, we'll publish an event to request UI navigation
            event_bus.publish(
                EventTypes.PANE_NAVIGATION_REQUESTED,
                {"direction": direction, "current_pane_id": current_pane_id},
            )

            return True
        else:
            logger.error("No model interface available for pane navigation")
            return False

    def toggle_pane_numbers(self) -> bool:
        """
        Toggle the visibility of pane numbers.

        Returns:
            True if pane numbers are now visible, False if hidden
        """
        logger.debug("Toggling pane numbers")

        if self._model:
            # Get current state
            state = self._model.get_state()
            if not state.tabs:
                return False

            # Toggle pane numbers via event bus to avoid UI dependency
            event_bus.publish(EventTypes.PANE_NUMBERS_TOGGLE_REQUESTED, {})

            return True
        else:
            logger.error("No model interface available for toggling pane numbers")
            return False

    def get_pane_count(self) -> int:
        """
        Get the total number of panes in the active tab.

        Returns:
            Number of panes
        """
        if self._model:
            state = self._model.get_state()
            if state.tabs and state.active_tab_index < len(state.tabs):
                active_tab = state.tabs[state.active_tab_index]
                # Count panes in the pane tree
                return self._count_panes_in_tree(active_tab.pane_tree)
            return 0
        else:
            logger.error("No model interface available for getting pane count")
            return 0

    def _count_panes_in_tree(self, pane_tree: dict) -> int:
        """
        Recursively count panes in a pane tree structure.

        Args:
            pane_tree: The pane tree dictionary

        Returns:
            Number of panes in the tree
        """
        if not pane_tree:
            return 0

        if pane_tree.get("type") == "pane":
            return 1
        elif pane_tree.get("type") == "split":
            left_count = self._count_panes_in_tree(pane_tree.get("left", {}))
            right_count = self._count_panes_in_tree(pane_tree.get("right", {}))
            return left_count + right_count
        else:
            return 0

    def change_pane_widget_type(self, pane_id: str, widget_type: str) -> bool:
        """
        Change the widget type of a pane.

        Args:
            pane_id: ID of the pane to change
            widget_type: New widget type

        Returns:
            True if the change was successful
        """
        logger.debug(f"Changing pane {pane_id} to widget type: {widget_type}")

        if self._model:
            # Create widget state update request
            from viloapp.models.operations import WidgetStateUpdateRequest

            request = WidgetStateUpdateRequest(
                pane_id=pane_id, widget_type=widget_type, state_data={}
            )

            # Execute change via model
            result = self._model.update_pane_widget(request)
            if result.success:
                logger.info(f"Changed pane {pane_id} to widget type {widget_type}")
                return True
            else:
                logger.error(f"Failed to change pane widget type: {result.error}")
                return False
        else:
            logger.error("No model interface available for changing pane widget type")
            return False

    def get_pane_info(self, pane_id: str) -> dict:
        """
        Get information about a specific pane.

        Args:
            pane_id: ID of the pane

        Returns:
            Dictionary with pane information
        """
        if self._model:
            state = self._model.get_state()
            for tab in state.tabs:
                pane_info = self._find_pane_in_tree(tab.pane_tree, pane_id)
                if pane_info:
                    return pane_info

            logger.warning(f"Pane {pane_id} not found")
            return {}
        else:
            logger.error("No model interface available for getting pane info")
            return {}

    def _find_pane_in_tree(self, pane_tree: dict, pane_id: str) -> Optional[dict]:
        """
        Recursively find a pane in a pane tree structure.

        Args:
            pane_tree: The pane tree dictionary
            pane_id: ID of the pane to find

        Returns:
            Pane information dictionary or None if not found
        """
        if not pane_tree:
            return None

        if pane_tree.get("type") == "pane" and pane_tree.get("id") == pane_id:
            return pane_tree
        elif pane_tree.get("type") == "split":
            # Search in left and right subtrees
            left_result = self._find_pane_in_tree(pane_tree.get("left", {}), pane_id)
            if left_result:
                return left_result
            return self._find_pane_in_tree(pane_tree.get("right", {}), pane_id)
        else:
            return None
