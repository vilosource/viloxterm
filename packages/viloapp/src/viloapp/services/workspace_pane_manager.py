#!/usr/bin/env python3
"""
Pane management operations for the workspace service.

This component handles pane splitting, closing, navigation, and related
pane-based operations in the workspace.
"""

import logging
from typing import Any, Optional

from viloapp.core.settings.app_defaults import (
    get_default_split_direction,
)

logger = logging.getLogger(__name__)


class WorkspacePaneManager:
    """
    Manager for pane operations in the workspace.

    Handles pane splitting, closing, navigation, and pane-related
    state management.
    """

    def __init__(self, workspace=None):
        """
        Initialize the pane manager.

        Args:
            workspace: The workspace instance
        """
        self._workspace = workspace
        self._pane_counter = 0

    def set_workspace(self, workspace):
        """Set the workspace instance."""
        self._workspace = workspace

    def split_active_pane(self, orientation: Optional[str] = None) -> Optional[str]:
        """
        Split the active pane in the current tab.

        Args:
            orientation: "horizontal" or "vertical"

        Returns:
            ID of the new pane, or None if split failed
        """
        if not self._workspace:
            return None

        # Use default orientation if not specified
        if orientation is None:
            orientation = get_default_split_direction()

        # Get current split widget
        widget = self._workspace.get_current_split_widget()
        if not widget or not widget.active_pane_id:
            logger.warning("No active pane to split")
            return None

        # Perform the split with default ratio
        # Note: Current split methods don't support ratio parameter yet
        # This will need to be added to SplitPaneWidget
        if orientation == "horizontal":
            new_id = widget.split_horizontal(widget.active_pane_id)
        elif orientation == "vertical":
            new_id = widget.split_vertical(widget.active_pane_id)
        else:
            logger.error(f"Invalid split orientation: {orientation}")
            return None

        if new_id:
            self._pane_counter += 1
            logger.info(f"Split pane {orientation}ly, created pane {new_id}")

        return new_id

    def close_active_pane(self) -> bool:
        """
        Close the active pane in the current tab.

        Returns:
            True if pane was closed
        """
        if not self._workspace:
            return False

        # Get current split widget
        widget = self._workspace.get_current_split_widget()
        if not widget or not widget.active_pane_id:
            logger.warning("No active pane to close")
            return False

        # Can't close if it's the only pane
        if widget.get_pane_count() <= 1:
            logger.info("Cannot close the last pane")
            return False

        pane_id = widget.active_pane_id

        # Close the pane
        widget.close_pane(pane_id)

        logger.info(f"Closed pane {pane_id}")
        return True

    def close_pane(self, pane_id: str) -> bool:
        """
        Close a specific pane by its ID.

        Args:
            pane_id: ID of the pane to close

        Returns:
            True if pane was closed
        """
        if not self._workspace:
            return False

        # Get current split widget
        widget = self._workspace.get_current_split_widget()
        if not widget:
            logger.warning("No split widget available")
            return False

        # Can't close if it's the only pane
        if widget.get_pane_count() <= 1:
            logger.info("Cannot close the last pane in tab")
            return False

        # Close the specific pane
        result = widget.close_pane(pane_id)

        if result:
            logger.info(f"Closed pane {pane_id}")
        else:
            logger.warning(f"Failed to close pane {pane_id}")

        return result

    def focus_pane(self, pane_id: str) -> bool:
        """
        Focus a specific pane.

        Args:
            pane_id: ID of the pane to focus

        Returns:
            True if pane was focused
        """
        if not self._workspace:
            return False

        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False

        # Set the active pane AND request keyboard focus
        widget.set_active_pane(pane_id, focus=True)

        return True

    def toggle_pane_numbers(self) -> bool:
        """
        Toggle the visibility of pane identification numbers.

        Returns:
            New visibility state (True if now visible, False if hidden)
        """
        if not self._workspace:
            logger.warning("Cannot toggle pane numbers: workspace not available")
            return False

        widget = self._workspace.get_current_split_widget()
        if not widget:
            logger.warning("Cannot toggle pane numbers: no current split widget")
            return False

        # Toggle the numbers
        visible = widget.toggle_pane_numbers()

        logger.info(f"Pane numbers {'shown' if visible else 'hidden'}")
        return visible

    def show_pane_numbers(self) -> bool:
        """
        Show pane identification numbers.

        Returns:
            True if numbers are now visible
        """
        if not self._workspace:
            return False

        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False

        # Show the numbers if not already visible
        if hasattr(widget, "model") and not widget.model.show_pane_numbers:
            widget.toggle_pane_numbers()
            logger.info("Pane numbers shown")
            return True

        return False

    def hide_pane_numbers(self) -> bool:
        """
        Hide pane identification numbers.

        Returns:
            True if numbers are now hidden
        """
        if not self._workspace:
            return False

        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False

        # Hide the numbers if currently visible
        if hasattr(widget, "model") and widget.model.show_pane_numbers:
            widget.toggle_pane_numbers()
            logger.info("Pane numbers hidden")
            return True

        return False

    def switch_to_pane_by_number(self, number: int) -> bool:
        """
        Switch to a pane by its displayed number.

        Args:
            number: The pane number (1-9)

        Returns:
            True if successfully switched to the pane
        """
        if not self._workspace:
            logger.warning("Cannot switch pane: workspace not available")
            return False

        widget = self._workspace.get_current_split_widget()
        if not widget:
            logger.warning("Cannot switch pane: no current split widget")
            return False

        # Find the pane ID for the given number
        if hasattr(widget, "model") and hasattr(widget.model, "pane_indices"):
            # Reverse lookup: find pane_id for the given number
            for pane_id, pane_number in widget.model.pane_indices.items():
                if pane_number == number:
                    # Focus the pane
                    if self.focus_pane(pane_id):
                        logger.info(f"Switched to pane {number} (id: {pane_id})")
                        return True
                    break

        logger.warning(f"Could not find pane with number {number}")
        return False

    def enter_pane_command_mode(self) -> bool:
        """
        Enter command mode for pane navigation.
        Shows pane numbers and prepares for digit input.

        Returns:
            True if command mode was entered successfully
        """
        # Show pane numbers
        if not self.show_pane_numbers():
            logger.warning("Could not enter pane command mode: no panes to show")
            return False

        # Get main window and activate focus sink
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            for window in app.topLevelWidgets():
                if hasattr(window, "focus_sink"):
                    # Get currently focused widget to restore later
                    current_focus = app.focusWidget()

                    # Enter command mode with focus sink
                    window.focus_sink.enter_command_mode(current_focus)
                    logger.info("Entered pane command mode")
                    return True

        logger.warning("Could not find main window with focus sink")
        return False

    def get_pane_count(self) -> int:
        """
        Get the number of panes in the current tab.

        Returns:
            Number of panes
        """
        if not self._workspace:
            return 0

        widget = self._workspace.get_current_split_widget()
        return widget.get_pane_count() if widget else 0

    def get_active_pane_id(self) -> Optional[str]:
        """
        Get the ID of the active pane.

        Returns:
            Active pane ID or None
        """
        if not self._workspace:
            return None

        widget = self._workspace.get_current_split_widget()
        return widget.active_pane_id if widget else None

    def navigate_in_direction(self, direction: str) -> bool:
        """
        Navigate to a pane in the specified direction.

        Uses tree structure and position overlap to find the most intuitive target.

        Args:
            direction: One of "left", "right", "up", "down"

        Returns:
            True if successfully navigated to a pane
        """
        if not self._workspace:
            return False

        widget = self._workspace.get_current_split_widget()
        if not widget or not widget.active_pane_id:
            logger.warning("No active pane to navigate from")
            return False

        # Use the model's directional navigation
        target_id = widget.model.find_pane_in_direction(
            widget.active_pane_id, direction
        )

        if target_id:
            widget.focus_specific_pane(target_id)
            success = True  # focus_specific_pane doesn't return a value
            if success:
                logger.info(
                    f"Navigated {direction} from {widget.active_pane_id} to {target_id}"
                )
            return success
        else:
            logger.debug(f"No pane found in direction: {direction}")
            return False

    def navigate_to_next_pane(self) -> bool:
        """
        Navigate to the next pane in the current tab.

        Returns:
            True if navigation succeeded
        """
        if not self._workspace:
            return False

        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False

        # Get all pane IDs
        panes = widget.get_all_pane_ids()
        if len(panes) <= 1:
            return False

        # Find current pane index
        current_id = widget.active_pane_id
        if current_id not in panes:
            return False

        current_index = panes.index(current_id)
        next_index = (current_index + 1) % len(panes)

        return self.focus_pane(panes[next_index])

    def navigate_to_previous_pane(self) -> bool:
        """
        Navigate to the previous pane in the current tab.

        Returns:
            True if navigation succeeded
        """
        if not self._workspace:
            return False

        widget = self._workspace.get_current_split_widget()
        if not widget:
            return False

        # Get all pane IDs
        panes = widget.get_all_pane_ids()
        if len(panes) <= 1:
            return False

        # Find current pane index
        current_id = widget.active_pane_id
        if current_id not in panes:
            return False

        current_index = panes.index(current_id)
        prev_index = (current_index - 1) % len(panes)

        return self.focus_pane(panes[prev_index])

    def get_pane_info(self) -> dict[str, Any]:
        """
        Get information about panes in the current tab.

        Returns:
            Dictionary with pane information
        """
        if not self._workspace:
            return {"count": 0, "active": None, "available": False}

        widget = self._workspace.get_current_split_widget()
        if not widget:
            return {"count": 0, "active": None, "available": False}

        return {
            "count": widget.get_pane_count(),
            "active": widget.active_pane_id,
            "available": True,
            "all_panes": (
                widget.get_all_pane_ids() if hasattr(widget, "get_all_pane_ids") else []
            ),
        }
