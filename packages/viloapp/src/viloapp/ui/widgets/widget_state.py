"""
Stub for widget_state.

Temporary stub while transitioning to new architecture.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class WidgetState:
    """Stub for widget state."""

    widget_id: str
    widget_type: str
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
    """Stub for widget state manager."""

    def __init__(self):
        self.states = {}

    def get_state(self, widget_id: str) -> Optional[WidgetState]:
        """Get state for a widget."""
        return self.states.get(widget_id)

    def set_state(self, widget_id: str, state: WidgetState):
        """Set state for a widget."""
        self.states[widget_id] = state

    def create_state(self, widget_id: str, widget_type: str) -> WidgetState:
        """Create a new state for a widget."""
        state = WidgetState(widget_id, widget_type)
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
    """Stub for widget state validator."""

    @staticmethod
    def validate(state: WidgetState) -> bool:
        """Validate a widget state."""
        return state is not None and state.widget_id and state.widget_type

    @staticmethod
    def validate_data(data: Dict[str, Any]) -> bool:
        """Validate state data."""
        return isinstance(data, dict)


# Singleton instance
widget_state_manager = WidgetStateManager()
