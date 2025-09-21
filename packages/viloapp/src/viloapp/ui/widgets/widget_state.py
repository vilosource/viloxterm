#!/usr/bin/env python3
"""
Widget lifecycle state management.

Defines the states an AppWidget can be in during its lifecycle
and provides validation for state transitions.
"""

from enum import Enum


class WidgetState(Enum):
    """
    Enumeration of widget lifecycle states.

    States:
        CREATED: Widget instantiated but not initialized
        INITIALIZING: Widget is loading resources/content
        READY: Widget is fully loaded and interactive
        SUSPENDED: Widget is hidden/inactive but preserving state
        ERROR: Widget failed to initialize or encountered error
        DESTROYING: Widget is being cleaned up
        DESTROYED: Widget cleanup is complete
    """

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    SUSPENDED = "suspended"
    ERROR = "error"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"


class WidgetStateValidator:
    """Validates widget state transitions."""

    # Valid state transitions
    VALID_TRANSITIONS = {
        WidgetState.CREATED: [WidgetState.INITIALIZING, WidgetState.DESTROYING],
        WidgetState.INITIALIZING: [
            WidgetState.READY,
            WidgetState.ERROR,
            WidgetState.DESTROYING,
        ],
        WidgetState.READY: [
            WidgetState.SUSPENDED,
            WidgetState.ERROR,
            WidgetState.DESTROYING,
        ],
        WidgetState.SUSPENDED: [WidgetState.READY, WidgetState.DESTROYING],
        WidgetState.ERROR: [
            WidgetState.INITIALIZING,  # Allow retry
            WidgetState.DESTROYING,
        ],
        WidgetState.DESTROYING: [WidgetState.DESTROYED],
        WidgetState.DESTROYED: [],  # Terminal state
    }

    @classmethod
    def is_valid_transition(cls, from_state: WidgetState, to_state: WidgetState) -> bool:
        """
        Check if a state transition is valid.

        Args:
            from_state: Current widget state
            to_state: Desired new state

        Returns:
            True if transition is valid, False otherwise
        """
        valid_states = cls.VALID_TRANSITIONS.get(from_state, [])
        return to_state in valid_states

    @classmethod
    def get_valid_transitions(cls, from_state: WidgetState) -> list[WidgetState]:
        """
        Get list of valid states to transition to.

        Args:
            from_state: Current widget state

        Returns:
            List of valid target states
        """
        return cls.VALID_TRANSITIONS.get(from_state, [])
