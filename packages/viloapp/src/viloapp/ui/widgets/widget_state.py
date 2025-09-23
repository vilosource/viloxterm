"""
Widget state management for lifecycle and state tracking.

This module provides the WidgetState enum and related functionality
for managing widget lifecycle states.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Set


class WidgetState(Enum):
    """
    Widget lifecycle states.

    These states represent the lifecycle of a widget from creation
    to destruction.
    """

    CREATED = "created"  # Widget instance created but not initialized
    INITIALIZING = "initializing"  # Widget is being initialized
    READY = "ready"  # Widget is ready for use
    SUSPENDED = "suspended"  # Widget is temporarily suspended
    ERROR = "error"  # Widget is in error state
    DESTROYING = "destroying"  # Widget is being destroyed
    DESTROYED = "destroyed"  # Widget has been destroyed


@dataclass
class WidgetStateData:
    """Container for widget state data (separate from lifecycle state)."""

    widget_id: str
    instance_id: str
    state: WidgetState = WidgetState.CREATED
    state_data: Dict[str, Any] = None

    def __post_init__(self):
        if self.state_data is None:
            self.state_data = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a state value."""
        return self.state_data.get(key, default)

    def set(self, key: str, value: Any):
        """Set a state value."""
        self.state_data[key] = value

    def update(self, data: Dict[str, Any]):
        """Update state with dictionary."""
        self.state_data.update(data)

    def clear(self):
        """Clear all state."""
        self.state_data.clear()


class WidgetStateManager:
    """Manager for widget states."""

    def __init__(self):
        self.states = {}

    def get_state(self, widget_id: str) -> Optional[WidgetStateData]:
        """Get state for a widget."""
        return self.states.get(widget_id)

    def set_state(self, widget_id: str, state: WidgetStateData):
        """Set state for a widget."""
        self.states[widget_id] = state

    def create_state(self, widget_id: str, instance_id: str) -> WidgetStateData:
        """Create a new state for a widget."""
        state = WidgetStateData(widget_id, instance_id)
        self.states[widget_id] = state
        return state

    def remove_state(self, widget_id: str):
        """Remove state for a widget."""
        if widget_id in self.states:
            del self.states[widget_id]

    def clear_all(self):
        """Clear all states."""
        self.states.clear()


class WidgetStateValidator:
    """Validator for widget state transitions."""

    # Define valid state transitions
    VALID_TRANSITIONS: Dict[WidgetState, Set[WidgetState]] = {
        WidgetState.CREATED: {WidgetState.INITIALIZING, WidgetState.DESTROYING},
        WidgetState.INITIALIZING: {WidgetState.READY, WidgetState.ERROR, WidgetState.DESTROYING},
        WidgetState.READY: {WidgetState.SUSPENDED, WidgetState.ERROR, WidgetState.DESTROYING},
        WidgetState.SUSPENDED: {WidgetState.READY, WidgetState.ERROR, WidgetState.DESTROYING},
        WidgetState.ERROR: {WidgetState.INITIALIZING, WidgetState.DESTROYING},
        WidgetState.DESTROYING: {WidgetState.DESTROYED},
        WidgetState.DESTROYED: set(),  # Terminal state
    }

    @classmethod
    def is_valid_transition(cls, from_state: WidgetState, to_state: WidgetState) -> bool:
        """Check if a state transition is valid."""
        valid_states = cls.VALID_TRANSITIONS.get(from_state, set())
        return to_state in valid_states

    @staticmethod
    def validate(state: WidgetStateData) -> bool:
        """Validate a widget state data object."""
        return state is not None and state.widget_id and state.widget_id

    @staticmethod
    def validate_data(data: Dict[str, Any]) -> bool:
        """Validate state data."""
        return isinstance(data, dict)


# Singleton instance
widget_state_manager = WidgetStateManager()
