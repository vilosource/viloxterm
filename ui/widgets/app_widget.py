#!/usr/bin/env python3
"""
AppWidget base class for all application content widgets.

This is the foundation of our content widget architecture. All content widgets
(terminal, editor, browser, etc.) extend this base class.
"""

import logging
import time
from typing import Any, Optional

from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QWidget

from ui.widgets.signal_manager import SignalManager
from ui.widgets.widget_registry import WidgetType
from ui.widgets.widget_state import WidgetState, WidgetStateValidator

logger = logging.getLogger(__name__)


class AppWidget(QWidget):
    """
    Base class for all application content widgets.

    AppWidgets are the actual content (terminals, editors, etc.) that users interact with.
    They are owned by the model (stored in LeafNodes) and wrapped by the view (PaneContent).

    Key principles:
    - AppWidgets don't know their position in the tree
    - They communicate through signals that bubble up the tree
    - They manage their own resources and cleanup
    - They can be moved between panes without recreation
    """

    # Lifecycle signals
    widget_ready = Signal()  # Emitted when widget is fully initialized and ready
    widget_error = Signal(str)  # Emitted on initialization or runtime error
    widget_state_changed = Signal(str)  # Emitted when lifecycle state changes
    widget_destroying = Signal()  # Emitted before widget cleanup begins

    # Existing signals
    action_requested = Signal(str, dict)  # action_type, params
    state_changed = Signal(dict)  # state_data
    focus_requested = Signal()  # Request focus on this widget

    def __init__(self, widget_id: str, widget_type: WidgetType, parent=None):
        """
        Initialize the AppWidget.

        Args:
            widget_id: Unique identifier for this widget
            widget_type: Type of widget (TERMINAL, TEXT_EDITOR, etc.)
            parent: Parent QWidget
        """
        super().__init__(parent)
        self.widget_id = widget_id
        self.widget_type = widget_type
        self.leaf_node = None  # Back-reference to tree node (set by model)
        self._metadata = None  # Will be set by AppWidgetManager during creation

        # Lifecycle state management
        self.widget_state = WidgetState.CREATED
        self._pending_focus = False
        self._has_focus = False  # Explicit focus tracking
        self._initialization_time = None
        self._error_count = 0

        # Retry configuration
        self._max_retries = 3  # Maximum number of retry attempts
        self._retry_base_delay = 1000  # Base delay in milliseconds
        self._retry_backoff_factor = 1.5  # Exponential backoff factor

        # State transition callbacks
        self._state_callbacks = {}  # Dict[Tuple[WidgetState, WidgetState], List[Callable]]
        self._any_state_callbacks = []  # Callbacks for any state transition

        # Signal management
        self._signal_manager = SignalManager(self)

    def initialize(self):
        """
        Start widget initialization (may be async).

        Subclasses should call this at the start of their initialization.
        """
        self._set_state(WidgetState.INITIALIZING)
        self._initialization_time = time.time()

    def set_ready(self):
        """
        Mark widget as ready and handle pending operations.

        Call this when async initialization completes successfully.
        """
        if self._initialization_time:
            init_duration = time.time() - self._initialization_time
            logger.info(f"Widget {self.widget_id} ready in {init_duration:.2f}s")

        self._set_state(WidgetState.READY)
        self.widget_ready.emit()

        # Handle pending focus request
        if self._pending_focus:
            self._pending_focus = False
            # Use timer to ensure event loop processes the ready signal first
            QTimer.singleShot(0, self.focus_widget)

    def set_error(self, error_msg: str):
        """
        Mark widget as failed to initialize.

        Args:
            error_msg: Description of the error
        """
        self._error_count += 1
        logger.error(f"Widget {self.widget_id} error (attempt {self._error_count}/{self._max_retries}): {error_msg}")

        self._set_state(WidgetState.ERROR)
        self.widget_error.emit(error_msg)

        # Attempt recovery if not too many errors
        if self._error_count < self._max_retries:
            # Calculate retry delay with exponential backoff
            retry_delay = int(self._retry_base_delay * (self._retry_backoff_factor ** (self._error_count - 1)))
            logger.info(f"Retrying widget {self.widget_id} initialization in {retry_delay}ms (attempt {self._error_count + 1}/{self._max_retries})")
            QTimer.singleShot(retry_delay, self.retry_initialization)
        else:
            logger.error(f"Widget {self.widget_id} exceeded max retries ({self._max_retries}), giving up")

    def suspend(self):
        """Suspend widget when hidden/inactive."""
        # Check if widget can be suspended
        if not self.can_suspend:
            logger.debug(f"Widget {self.widget_id} cannot be suspended (can_suspend=False)")
            return

        if self.widget_state == WidgetState.READY:
            self._set_state(WidgetState.SUSPENDED)
            self.on_suspend()

    def resume(self):
        """Resume widget when shown/active."""
        # If widget can't be suspended, it was never suspended
        if not self.can_suspend:
            return

        if self.widget_state == WidgetState.SUSPENDED:
            self._set_state(WidgetState.READY)
            self.on_resume()

    def cleanup(self):
        """
        Clean up resources when widget is being destroyed.

        Calls lifecycle hooks and disconnects signals.
        """
        self._set_state(WidgetState.DESTROYING)
        self.widget_destroying.emit()

        # Disconnect all signals
        self._signal_manager.disconnect_all()

        # Call subclass cleanup
        self.on_cleanup()

        self._set_state(WidgetState.DESTROYED)

    def get_state(self) -> dict[str, Any]:
        """
        Get widget state for persistence.

        Returns:
            Dictionary containing widget state that can be serialized
        """
        return {
            "type": self.widget_type.value,
            "widget_id": self.widget_id
        }

    def set_state(self, state: dict[str, Any]):
        """
        Restore widget state from persisted data.

        Args:
            state: Dictionary containing widget state to restore
        """
        pass  # Base implementation does nothing

    def can_close(self) -> bool:
        """
        Check if widget can be closed safely.

        Returns:
            True if widget can be closed, False if there are unsaved changes, etc.
        """
        return True

    def request_action(self, action: str, params: Optional[dict[str, Any]] = None):
        """
        Request an action through the tree structure.

        This is the primary way AppWidgets communicate with the system.
        Actions bubble up through the tree to be handled by the model/view.

        Args:
            action: Action type (e.g., 'split', 'close', 'focus')
            params: Optional parameters for the action
        """
        self.action_requested.emit(action, params or {})

    def notify_state_change(self, state_data: Optional[dict[str, Any]] = None):
        """
        Notify that widget state has changed.

        Args:
            state_data: Optional data about what changed
        """
        self.state_changed.emit(state_data or {})

    def request_focus(self):
        """Request focus on this widget."""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"AppWidget.request_focus() called for widget {self.widget_id}")
        self.focus_requested.emit()
        logger.debug(f"focus_requested signal emitted for widget {self.widget_id}")

    def focus_widget(self):
        """
        Set keyboard focus on the actual content widget.

        Respects widget state - queues focus if not ready.

        Returns:
            True if focus was set, False if queued or failed
        """
        if self.widget_state == WidgetState.READY:
            # Widget is ready, set focus now
            self.setFocus()
            self._has_focus = True
            logger.debug(f"Focus set on widget {self.widget_id}")
            return True
        elif self.widget_state in [WidgetState.CREATED, WidgetState.INITIALIZING]:
            # Widget not ready, queue focus request
            self._pending_focus = True
            logger.debug(f"Focus pending for widget {self.widget_id} (state: {self.widget_state.value})")
            return False
        else:
            # Widget in error/destroying state, cannot focus
            logger.warning(f"Cannot focus widget {self.widget_id} in state {self.widget_state.value}")
            return False

    def get_title(self) -> str:
        """
        Get title/label for this widget.

        Returns:
            String to display in tabs, headers, etc.
        """
        return f"{self.widget_type.value.replace('_', ' ').title()}"

    def get_icon_name(self) -> Optional[str]:
        """
        Get icon name for this widget type.

        Returns:
            Icon name or None if no icon
        """
        # Map widget types to icons
        icon_map = {
            WidgetType.TERMINAL: "terminal",
            WidgetType.TEXT_EDITOR: "file-text",
            WidgetType.FILE_EXPLORER: "folder",
            WidgetType.SEARCH: "search",
            WidgetType.GIT: "git-branch",
            WidgetType.SETTINGS: "settings",
            WidgetType.PLACEHOLDER: "layout"
        }
        return icon_map.get(self.widget_type)

    @property
    def has_focus(self) -> bool:
        """
        Check if widget currently has focus.

        Returns:
            True if widget has keyboard focus
        """
        return self._has_focus

    @property
    def can_suspend(self) -> bool:
        """
        Check if widget can be suspended when hidden.

        Widgets with background processes (like Terminal) should not be suspended.

        Returns:
            True if widget can be suspended, False otherwise
        """
        # If metadata is available, use its can_suspend setting
        if self._metadata:
            return self._metadata.can_suspend
        # Default to allowing suspension if no metadata
        return True

    def set_metadata(self, metadata):
        """
        Set the widget's metadata.

        This is typically called by AppWidgetManager during widget creation.

        Args:
            metadata: AppWidgetMetadata instance
        """
        self._metadata = metadata

    def configure_retry_strategy(self, max_retries: int = None, base_delay: int = None, backoff_factor: float = None):
        """
        Configure the retry strategy for error recovery.

        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in milliseconds (default: 1000)
            backoff_factor: Exponential backoff factor (default: 1.5)
        """
        if max_retries is not None:
            self._max_retries = max(0, max_retries)
        if base_delay is not None:
            self._retry_base_delay = max(0, base_delay)
        if backoff_factor is not None:
            self._retry_backoff_factor = max(1.0, backoff_factor)

    def on_state_transition(self, from_state: WidgetState = None, to_state: WidgetState = None, callback: callable = None):
        """
        Register a callback for state transitions.

        Args:
            from_state: Source state (None for any)
            to_state: Target state (None for any)
            callback: Function to call on transition (receives widget, from_state, to_state)

        Returns:
            Callback function for disconnection
        """
        if callback is None:
            raise ValueError("Callback function is required")

        if from_state is None and to_state is None:
            # Register for any state transition
            self._any_state_callbacks.append(callback)
        else:
            # Register for specific transition
            key = (from_state, to_state)
            if key not in self._state_callbacks:
                self._state_callbacks[key] = []
            self._state_callbacks[key].append(callback)

        return callback

    def remove_state_callback(self, callback: callable, from_state: WidgetState = None, to_state: WidgetState = None):
        """
        Remove a state transition callback.

        Args:
            callback: The callback to remove
            from_state: Source state (None for any)
            to_state: Target state (None for any)
        """
        if from_state is None and to_state is None:
            if callback in self._any_state_callbacks:
                self._any_state_callbacks.remove(callback)
        else:
            key = (from_state, to_state)
            if key in self._state_callbacks and callback in self._state_callbacks[key]:
                self._state_callbacks[key].remove(callback)
                if not self._state_callbacks[key]:
                    del self._state_callbacks[key]

    # Qt event overrides for lifecycle management
    def showEvent(self, event):
        """Handle widget becoming visible."""
        super().showEvent(event)
        if self.widget_state == WidgetState.SUSPENDED:
            self.resume()
        # Process pending focus if widget is now ready and visible
        if self._pending_focus and self.widget_state == WidgetState.READY:
            QTimer.singleShot(0, self.focus_widget)

    def hideEvent(self, event):
        """Handle widget becoming hidden."""
        super().hideEvent(event)
        if self.widget_state == WidgetState.READY:
            self.suspend()

    def focusInEvent(self, event):
        """Handle widget gaining focus."""
        super().focusInEvent(event)
        self._has_focus = True
        logger.debug(f"Widget {self.widget_id} gained focus")

    def focusOutEvent(self, event):
        """Handle widget losing focus."""
        super().focusOutEvent(event)
        self._has_focus = False
        logger.debug(f"Widget {self.widget_id} lost focus")

    # Protected lifecycle methods
    def _set_state(self, new_state: WidgetState):
        """
        Set widget state with validation.

        Args:
            new_state: The new state to transition to
        """
        old_state = self.widget_state
        if WidgetStateValidator.is_valid_transition(old_state, new_state):
            self.widget_state = new_state
            self.widget_state_changed.emit(new_state.value)
            logger.debug(f"Widget {self.widget_id}: {old_state.value} → {new_state.value}")

            # Trigger state transition callbacks
            self._trigger_state_callbacks(old_state, new_state)
        else:
            logger.error(f"Invalid state transition for widget {self.widget_id}: "
                        f"{old_state.value} → {new_state.value}")

    def _trigger_state_callbacks(self, from_state: WidgetState, to_state: WidgetState):
        """
        Trigger registered callbacks for a state transition.

        Args:
            from_state: The previous state
            to_state: The new state
        """
        # Trigger specific transition callbacks
        specific_key = (from_state, to_state)
        if specific_key in self._state_callbacks:
            for callback in self._state_callbacks[specific_key][:]:  # Copy list to allow modification during iteration
                try:
                    callback(self, from_state, to_state)
                except Exception as e:
                    logger.error(f"Error in state transition callback: {e}")

        # Trigger wildcard callbacks (from any state to specific state)
        to_any_key = (None, to_state)
        if to_any_key in self._state_callbacks:
            for callback in self._state_callbacks[to_any_key][:]:
                try:
                    callback(self, from_state, to_state)
                except Exception as e:
                    logger.error(f"Error in state transition callback: {e}")

        # Trigger wildcard callbacks (from specific state to any state)
        from_any_key = (from_state, None)
        if from_any_key in self._state_callbacks:
            for callback in self._state_callbacks[from_any_key][:]:
                try:
                    callback(self, from_state, to_state)
                except Exception as e:
                    logger.error(f"Error in state transition callback: {e}")

        # Trigger any-state callbacks
        for callback in self._any_state_callbacks[:]:
            try:
                callback(self, from_state, to_state)
            except Exception as e:
                logger.error(f"Error in state transition callback: {e}")

    # Lifecycle hooks for subclasses to override
    def on_suspend(self):
        """
        Called when widget is suspended.

        Override in subclasses to pause expensive operations.
        """
        pass

    def on_resume(self):
        """
        Called when widget is resumed from suspension.

        Override in subclasses to resume operations.
        """
        pass

    def on_cleanup(self):
        """
        Called during widget cleanup.

        Override in subclasses to clean up specific resources.
        """
        pass

    def retry_initialization(self):
        """
        Retry initialization after error.

        Override in subclasses for custom retry logic.
        """
        logger.info(f"Widget {self.widget_id}: Retrying initialization (attempt #{self._error_count})")
        self.initialize()
