#!/usr/bin/env python3
"""
Split pane controller - business logic for split pane operations.

This module handles the business logic for split pane operations,
including split/close actions, widget type changes, and model interactions.
"""

import logging
from typing import Callable, Optional

from PySide6.QtCore import QObject, QTimer, Signal

from viloapp.ui.widgets.split_pane_model import LeafNode, SplitPaneModel
from viloapp.ui.widgets.widget_registry import WidgetType
from viloapp.ui.widgets.widget_state import WidgetState

logger = logging.getLogger(__name__)


class SplitPaneController(QObject):
    """
    Controller for split pane business logic.

    Handles:
    - Split and close operations
    - Widget action processing
    - Model interaction coordination
    - State management
    """

    # Signals
    pane_added = Signal(str)  # pane_id
    pane_removed = Signal(str)  # pane_id
    active_pane_changed = Signal(str)  # pane_id
    layout_changed = Signal()
    pane_split = Signal(str, str)  # original_pane_id, new_pane_id
    widget_ready_for_focus = Signal(str)  # pane_id

    def __init__(self, model: SplitPaneModel, parent=None):
        """
        Initialize the controller.

        Args:
            model: The split pane model to control
            parent: Parent QObject
        """
        super().__init__(parent)
        self.model = model
        self._focus_callbacks: dict[str, Callable] = {}
        self._terminal_close_callback: Optional[Callable] = None

        # Set up terminal close callback
        self.model.set_terminal_close_callback(self._handle_terminal_close)

    def handle_widget_action(self, leaf_id: str, action: str, params: dict) -> bool:
        """
        Handle action from an AppWidget.

        Args:
            leaf_id: ID of leaf that initiated the action
            action: Action type
            params: Action parameters

        Returns:
            True if action was handled successfully
        """
        logger.info(f"Handling action from {leaf_id}: {action} with params {params}")

        try:
            if action == "split":
                return self._handle_split_action(leaf_id, params)
            elif action == "close":
                return self._handle_close_action(leaf_id, params)
            elif action == "change_type":
                return self._handle_change_type_action(leaf_id, params)
            elif action == "focus":
                return self._handle_focus_action(leaf_id, params)
            else:
                logger.warning(f"Unknown action: {action}")
                return False

        except Exception as e:
            logger.error(f"Error handling action {action} from {leaf_id}: {e}")
            return False

    def _handle_split_action(self, leaf_id: str, params: dict) -> bool:
        """Handle split action - maintains backward compatibility by returning bool."""
        new_id = self._split_pane_internal(leaf_id, params)
        return new_id is not None

    def _split_pane_internal(self, leaf_id: str, params: dict) -> Optional[str]:
        """Core split logic - single source of truth for all split operations."""
        orientation = params.get("orientation", "horizontal")
        target_id = params.get("leaf_id", leaf_id)

        new_id = self.model.split_pane(target_id, orientation)
        if new_id:
            self.pane_added.emit(new_id)
            # Use specific split signal instead of generic layout_changed
            # This allows for incremental updates instead of nuclear refresh
            self.pane_split.emit(target_id, new_id)

            # Set the new pane as active and prepare for focus
            self._prepare_new_pane_for_focus(new_id)

        return new_id

    def _handle_close_action(self, leaf_id: str, params: dict) -> bool:
        """Handle close action."""
        target_id = params.get("leaf_id", leaf_id)

        if self.model.close_pane(target_id):
            self.pane_removed.emit(target_id)
            self.layout_changed.emit()
            return True

        return False

    def _handle_change_type_action(self, leaf_id: str, params: dict) -> bool:
        """Handle widget type change action."""
        target_id = params.get("leaf_id", leaf_id)
        new_type = params.get("new_type")

        if new_type and self.model.change_pane_type(target_id, new_type):
            self.layout_changed.emit()
            return True

        return False

    def _handle_focus_action(self, leaf_id: str, params: dict) -> bool:
        """Handle focus action."""
        target_id = params.get("leaf_id", leaf_id)
        return self.set_active_pane(target_id)

    def _prepare_new_pane_for_focus(self, pane_id: str):
        """
        Prepare a newly created pane for focus.

        Args:
            pane_id: ID of the new pane
        """
        # Set as active first
        self.set_active_pane(pane_id, emit_signal=False)

        # Check widget readiness and handle focus accordingly
        leaf = self.model.find_leaf(pane_id)
        if leaf and leaf.app_widget:
            if leaf.app_widget.widget_state == WidgetState.READY:
                # Widget is synchronously ready
                QTimer.singleShot(10, lambda: self._emit_focus_ready(pane_id))
            else:
                # Widget needs async initialization
                logger.debug(
                    f"Widget {pane_id} not ready, connecting to widget_ready signal"
                )
                leaf.app_widget.widget_ready.connect(
                    lambda: self._emit_focus_ready(pane_id),
                    # Qt.SingleShotConnection  # Auto-disconnect after firing
                )

    def _emit_focus_ready(self, pane_id: str):
        """Emit signal that widget is ready for focus."""
        self.widget_ready_for_focus.emit(pane_id)

    def split_horizontal(self, pane_id: str) -> Optional[str]:
        """
        Split pane horizontally.

        Args:
            pane_id: ID of the pane to split

        Returns:
            ID of the new pane if successful, None otherwise
        """
        # Delegate to core split logic for consistency and proper MVC pattern
        return self._split_pane_internal(pane_id, {"orientation": "horizontal", "leaf_id": pane_id})

    def split_vertical(self, pane_id: str) -> Optional[str]:
        """
        Split pane vertically.

        Args:
            pane_id: ID of the pane to split

        Returns:
            ID of the new pane if successful, None otherwise
        """
        # Delegate to core split logic for consistency and proper MVC pattern
        return self._split_pane_internal(pane_id, {"orientation": "vertical", "leaf_id": pane_id})

    def close_pane(self, pane_id: str) -> bool:
        """
        Close a pane.

        Args:
            pane_id: ID of the pane to close

        Returns:
            True if pane was closed successfully
        """
        if self.model.close_pane(pane_id):
            self.pane_removed.emit(pane_id)
            # Don't emit layout_changed here - pane_removed will handle incremental update
            return True

        return False

    def set_active_pane(self, pane_id: str, emit_signal: bool = True) -> bool:
        """
        Set the active pane.

        Args:
            pane_id: ID of the pane to activate
            emit_signal: Whether to emit the active_pane_changed signal

        Returns:
            True if pane was set as active successfully
        """
        old_active = self.model.get_active_pane_id()
        logger.debug(f"set_active_pane called: {old_active} → {pane_id}")

        if self.model.set_active_pane(pane_id):
            logger.debug(f"Active pane successfully changed to: {pane_id}")
            if emit_signal:
                self.active_pane_changed.emit(pane_id)
            return True
        else:
            logger.warning(f"Failed to set active pane to: {pane_id}")
            return False

    def toggle_pane_numbers(self) -> bool:
        """
        Toggle pane number visibility.

        Returns:
            New visibility state
        """
        return self.model.toggle_pane_numbers()

    def change_pane_type(self, pane_id: str, new_type: WidgetType) -> bool:
        """
        Change the type of a pane's widget.

        Args:
            pane_id: ID of the pane to change
            new_type: New widget type

        Returns:
            True if type was changed successfully
        """
        if self.model.change_pane_type(pane_id, new_type):
            self.layout_changed.emit()
            return True
        return False

    def register_focus_callback(self, pane_id: str, callback: Callable):
        """
        Register a callback for when a pane should be focused.

        Args:
            pane_id: ID of the pane
            callback: Function to call when pane should be focused
        """
        self._focus_callbacks[pane_id] = callback

    def unregister_focus_callback(self, pane_id: str):
        """
        Unregister focus callback for a pane.

        Args:
            pane_id: ID of the pane
        """
        if pane_id in self._focus_callbacks:
            del self._focus_callbacks[pane_id]

    def set_terminal_close_callback(self, callback: Callable[[str], None]):
        """
        Set callback for terminal close events.

        Args:
            callback: Function to call when terminal closes (receives pane_id)
        """
        self._terminal_close_callback = callback

    def _handle_terminal_close(self, pane_id: str):
        """
        Handle terminal close request from model.

        Args:
            pane_id: ID of the pane containing the terminal that exited
        """
        logger.info(f"Terminal in pane {pane_id} exited - handling close")

        if self._terminal_close_callback:
            self._terminal_close_callback(pane_id)
        else:
            # Default behavior: close the pane
            self.close_pane(pane_id)

    def connect_model_signals(self, signal_connector: Callable):
        """
        Connect AppWidget signals in the model to handlers.

        Args:
            signal_connector: Function that connects widget signals
        """

        def connect_widget(leaf: LeafNode):
            if leaf.app_widget:
                signal_connector(leaf)

        # Connect all widgets in tree
        self.model.traverse_tree(callback=connect_widget)

    def get_state(self) -> dict:
        """Get controller state for persistence."""
        return {
            "model_state": self.model.to_dict(),
            "active_pane": self.model.get_active_pane_id(),
        }

    def set_state(self, state: dict) -> bool:
        """
        Restore controller state from persistence.

        Args:
            state: State dictionary

        Returns:
            True if state was restored successfully
        """
        try:
            if "model_state" in state:
                self.model.from_dict(state["model_state"])

            if "active_pane" in state:
                self.set_active_pane(state["active_pane"])

            self.layout_changed.emit()
            return True

        except Exception as e:
            logger.error(f"Failed to restore controller state: {e}")
            return False

    def cleanup(self):
        """Clean up controller resources."""
        self._focus_callbacks.clear()
        self._terminal_close_callback = None
        logger.debug("Controller cleanup complete")
