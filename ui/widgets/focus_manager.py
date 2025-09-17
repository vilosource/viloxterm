#!/usr/bin/env python3
"""
Advanced focus management for widgets.

This module provides a FocusManager class that handles focus history,
priorities, and complex focus scenarios in the widget system.
"""

import logging
from collections import deque
from enum import Enum
from typing import Any, Callable, Optional

from PySide6.QtCore import QObject, Qt, QTime, Signal

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_state import WidgetState

logger = logging.getLogger(__name__)


class FocusPriority(Enum):
    """Focus priority levels."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class FocusRequest:
    """Represents a focus request with metadata."""

    def __init__(
        self,
        widget_id: str,
        priority: FocusPriority = FocusPriority.NORMAL,
        callback: Optional[Callable] = None,
        reason: str = "",
    ):
        """
        Initialize a focus request.

        Args:
            widget_id: ID of the widget requesting focus
            priority: Priority level of the request
            callback: Optional callback when focus is set
            reason: Reason for the focus request
        """
        self.widget_id = widget_id
        self.priority = priority
        self.callback = callback
        self.reason = reason
        self.timestamp = QTime.currentTime()


class FocusManager(QObject):
    """
    Advanced focus management system for widgets.

    Features:
    - Focus history tracking
    - Priority-based focus queue
    - Focus restoration
    - Focus cycling
    - Focus policies
    """

    # Signals
    focus_changed = Signal(str, str)  # old_widget_id, new_widget_id
    focus_restored = Signal(str)  # widget_id
    focus_lost = Signal(str)  # widget_id

    def __init__(self, parent=None):
        """
        Initialize the FocusManager.

        Args:
            parent: Parent QObject
        """
        super().__init__(parent)

        # Current focus
        self._current_focus = None  # widget_id

        # Focus history (most recent last)
        self._focus_history = deque(maxlen=50)

        # Focus queue for pending requests
        self._focus_queue = []  # List of FocusRequest

        # Widget registry
        self._widgets = {}  # widget_id -> AppWidget

        # Focus policies
        self._focus_policies = {}  # widget_id -> policy dict

        # Focus groups for cycling
        self._focus_groups = {}  # group_name -> List[widget_id]

        # Statistics
        self._stats = {
            "focus_changes": 0,
            "focus_requests": 0,
            "focus_restored": 0,
            "focus_denied": 0,
        }

    def register_widget(
        self,
        widget: AppWidget,
        group: Optional[str] = None,
        policy: Optional[dict[str, Any]] = None,
    ):
        """
        Register a widget with the focus manager.

        Args:
            widget: The widget to register
            group: Optional focus group name
            policy: Optional focus policy for the widget
        """
        widget_id = widget.widget_id
        self._widgets[widget_id] = widget

        # Set up focus tracking
        widget.focus_requested.connect(lambda: self._on_focus_requested(widget_id))

        # Add to group if specified
        if group:
            if group not in self._focus_groups:
                self._focus_groups[group] = []
            self._focus_groups[group].append(widget_id)

        # Set policy if provided
        if policy:
            self._focus_policies[widget_id] = policy

        logger.debug(f"Registered widget {widget_id} with FocusManager")

    def unregister_widget(self, widget: AppWidget):
        """
        Unregister a widget from the focus manager.

        Args:
            widget: The widget to unregister
        """
        widget_id = widget.widget_id

        # Remove from registry
        if widget_id in self._widgets:
            del self._widgets[widget_id]

        # Remove from groups
        for group_widgets in self._focus_groups.values():
            if widget_id in group_widgets:
                group_widgets.remove(widget_id)

        # Remove from history
        self._focus_history = deque(
            [wid for wid in self._focus_history if wid != widget_id], maxlen=50
        )

        # Remove from queue
        self._focus_queue = [
            req for req in self._focus_queue if req.widget_id != widget_id
        ]

        # Clear current focus if it was this widget
        if self._current_focus == widget_id:
            self._current_focus = None
            self.focus_lost.emit(widget_id)

        logger.debug(f"Unregistered widget {widget_id} from FocusManager")

    def request_focus(
        self,
        widget_id: str,
        priority: FocusPriority = FocusPriority.NORMAL,
        callback: Optional[Callable] = None,
        reason: str = "",
    ) -> bool:
        """
        Request focus for a widget.

        Args:
            widget_id: ID of the widget requesting focus
            priority: Priority level of the request
            callback: Optional callback when focus is set
            reason: Reason for the focus request

        Returns:
            True if focus was set or queued, False if denied
        """
        self._stats["focus_requests"] += 1

        # Check if widget exists
        if widget_id not in self._widgets:
            logger.warning(f"Unknown widget {widget_id} requesting focus")
            self._stats["focus_denied"] += 1
            return False

        widget = self._widgets[widget_id]

        # Check focus policy
        if not self._check_focus_policy(widget_id):
            logger.debug(f"Focus denied for {widget_id} by policy")
            self._stats["focus_denied"] += 1
            return False

        # Check widget state
        if widget.widget_state == WidgetState.READY:
            # Can focus immediately
            return self._set_focus(widget_id, reason)
        elif widget.widget_state in [WidgetState.CREATED, WidgetState.INITIALIZING]:
            # Queue the request
            request = FocusRequest(widget_id, priority, callback, reason)
            self._queue_focus_request(request)
            return True
        else:
            # Cannot focus (ERROR, DESTROYING, DESTROYED)
            logger.debug(
                f"Cannot focus widget {widget_id} in state {widget.widget_state.value}"
            )
            self._stats["focus_denied"] += 1
            return False

    def _set_focus(self, widget_id: str, reason: str = "") -> bool:
        """
        Actually set focus on a widget.

        Args:
            widget_id: ID of the widget to focus
            reason: Reason for the focus change

        Returns:
            True if focus was set, False otherwise
        """
        if widget_id not in self._widgets:
            return False

        widget = self._widgets[widget_id]

        # Store old focus
        old_focus = self._current_focus

        # Set new focus
        if widget.focus_widget():
            self._current_focus = widget_id
            self._stats["focus_changes"] += 1

            # Update history
            if old_focus and old_focus != widget_id:
                self._focus_history.append(old_focus)

            # Emit signal
            self.focus_changed.emit(old_focus or "", widget_id)

            logger.info(
                f"Focus changed from {old_focus} to {widget_id} (reason: {reason})"
            )
            return True

        return False

    def _queue_focus_request(self, request: FocusRequest):
        """
        Queue a focus request.

        Args:
            request: The focus request to queue
        """
        # Insert based on priority
        inserted = False
        for i, existing in enumerate(self._focus_queue):
            if request.priority.value > existing.priority.value:
                self._focus_queue.insert(i, request)
                inserted = True
                break

        if not inserted:
            self._focus_queue.append(request)

        # Set up callback for when widget is ready
        widget = self._widgets[request.widget_id]
        widget.widget_ready.connect(
            lambda: self._process_queued_request(request.widget_id),
            type=Qt.SingleShotConnection,
        )

        logger.debug(
            f"Queued focus request for {request.widget_id} with priority {request.priority.value}"
        )

    def _process_queued_request(self, widget_id: str):
        """
        Process a queued focus request when widget becomes ready.

        Args:
            widget_id: ID of the widget that became ready
        """
        # Find and remove the request
        request = None
        for req in self._focus_queue:
            if req.widget_id == widget_id:
                request = req
                self._focus_queue.remove(req)
                break

        if request:
            # Try to set focus
            if self._set_focus(widget_id, request.reason):
                # Call callback if provided
                if request.callback:
                    try:
                        request.callback()
                    except Exception as e:
                        logger.error(f"Error in focus callback: {e}")

    def _check_focus_policy(self, widget_id: str) -> bool:
        """
        Check if widget can receive focus based on policy.

        Args:
            widget_id: ID of the widget to check

        Returns:
            True if widget can receive focus, False otherwise
        """
        if widget_id not in self._focus_policies:
            return True  # No policy means allowed

        policy = self._focus_policies[widget_id]

        # Check various policy conditions
        if "enabled" in policy and not policy["enabled"]:
            return False

        if "max_focus_count" in policy:
            # Count how many times this widget has had focus
            focus_count = self._focus_history.count(widget_id)
            if self._current_focus == widget_id:
                focus_count += 1
            if focus_count >= policy["max_focus_count"]:
                return False

        if "requires_permission" in policy and policy["requires_permission"]:
            # Would need to implement permission check
            pass

        return True

    def restore_previous_focus(self) -> bool:
        """
        Restore focus to the previous widget.

        Returns:
            True if focus was restored, False otherwise
        """
        if not self._focus_history:
            logger.debug("No focus history to restore")
            return False

        # Get previous widget
        prev_widget_id = self._focus_history.pop()

        # Check if widget still exists and can receive focus
        if prev_widget_id in self._widgets:
            widget = self._widgets[prev_widget_id]
            if widget.widget_state == WidgetState.READY:
                if self._set_focus(prev_widget_id, "restore"):
                    self._stats["focus_restored"] += 1
                    self.focus_restored.emit(prev_widget_id)
                    return True

        return False

    def cycle_focus(self, group: Optional[str] = None, forward: bool = True) -> bool:
        """
        Cycle focus to the next/previous widget.

        Args:
            group: Optional group to cycle within
            forward: True for next, False for previous

        Returns:
            True if focus was cycled, False otherwise
        """
        # Get widget list
        if group and group in self._focus_groups:
            widget_ids = self._focus_groups[group]
        else:
            # All ready widgets
            widget_ids = [
                wid
                for wid, w in self._widgets.items()
                if w.widget_state == WidgetState.READY
            ]

        if not widget_ids:
            return False

        # Find current index
        current_idx = -1
        if self._current_focus in widget_ids:
            current_idx = widget_ids.index(self._current_focus)

        # Calculate next index
        if forward:
            next_idx = (current_idx + 1) % len(widget_ids)
        else:
            next_idx = (current_idx - 1) % len(widget_ids)

        # Set focus
        return self._set_focus(widget_ids[next_idx], "cycle")

    def clear_focus(self):
        """Clear focus from all widgets."""
        if self._current_focus:
            old_focus = self._current_focus
            self._current_focus = None
            self.focus_lost.emit(old_focus)
            logger.debug(f"Cleared focus from {old_focus}")

    def get_current_focus(self) -> Optional[str]:
        """
        Get the currently focused widget ID.

        Returns:
            Widget ID or None if no focus
        """
        return self._current_focus

    def get_focus_history(self, limit: int = 10) -> list[str]:
        """
        Get focus history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of widget IDs in focus history (most recent last)
        """
        history = list(self._focus_history)
        if limit:
            history = history[-limit:]
        return history

    def get_statistics(self) -> dict[str, int]:
        """
        Get focus management statistics.

        Returns:
            Dictionary of statistics
        """
        return self._stats.copy()

    def set_focus_policy(self, widget_id: str, policy: dict[str, Any]):
        """
        Set focus policy for a widget.

        Args:
            widget_id: ID of the widget
            policy: Policy dictionary
        """
        self._focus_policies[widget_id] = policy
        logger.debug(f"Set focus policy for {widget_id}: {policy}")

    def create_focus_group(self, group_name: str, widget_ids: list[str]):
        """
        Create a focus group for cycling.

        Args:
            group_name: Name of the group
            widget_ids: List of widget IDs in the group
        """
        self._focus_groups[group_name] = widget_ids
        logger.debug(
            f"Created focus group '{group_name}' with {len(widget_ids)} widgets"
        )

    def _on_focus_requested(self, widget_id: str):
        """
        Handle focus request from a widget.

        Args:
            widget_id: ID of the widget requesting focus
        """
        self.request_focus(widget_id, reason="widget_request")


# Global focus manager instance
_global_focus_manager = None


def get_focus_manager() -> FocusManager:
    """
    Get the global focus manager instance.

    Returns:
        The global FocusManager instance
    """
    global _global_focus_manager
    if _global_focus_manager is None:
        _global_focus_manager = FocusManager()
    return _global_focus_manager
