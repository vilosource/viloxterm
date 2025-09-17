#!/usr/bin/env python3
"""
Unit tests for WidgetState and WidgetStateValidator.
"""

from ui.widgets.widget_state import WidgetState, WidgetStateValidator


class TestWidgetState:
    """Test WidgetState enum."""

    def test_widget_states_exist(self):
        """Test that all expected states are defined."""
        assert WidgetState.CREATED
        assert WidgetState.INITIALIZING
        assert WidgetState.READY
        assert WidgetState.SUSPENDED
        assert WidgetState.ERROR
        assert WidgetState.DESTROYING
        assert WidgetState.DESTROYED

    def test_widget_state_values(self):
        """Test that states have expected string values."""
        assert WidgetState.CREATED.value == "created"
        assert WidgetState.INITIALIZING.value == "initializing"
        assert WidgetState.READY.value == "ready"
        assert WidgetState.SUSPENDED.value == "suspended"
        assert WidgetState.ERROR.value == "error"
        assert WidgetState.DESTROYING.value == "destroying"
        assert WidgetState.DESTROYED.value == "destroyed"


class TestWidgetStateValidator:
    """Test WidgetStateValidator transitions."""

    def test_valid_transitions_from_created(self):
        """Test valid transitions from CREATED state."""
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.CREATED, WidgetState.INITIALIZING
        )
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.CREATED, WidgetState.DESTROYING
        )

    def test_invalid_transitions_from_created(self):
        """Test invalid transitions from CREATED state."""
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.CREATED, WidgetState.READY
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.CREATED, WidgetState.SUSPENDED
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.CREATED, WidgetState.ERROR
        )

    def test_valid_transitions_from_initializing(self):
        """Test valid transitions from INITIALIZING state."""
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.INITIALIZING, WidgetState.READY
        )
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.INITIALIZING, WidgetState.ERROR
        )
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.INITIALIZING, WidgetState.DESTROYING
        )

    def test_invalid_transitions_from_initializing(self):
        """Test invalid transitions from INITIALIZING state."""
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.INITIALIZING, WidgetState.CREATED
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.INITIALIZING, WidgetState.SUSPENDED
        )

    def test_valid_transitions_from_ready(self):
        """Test valid transitions from READY state."""
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.READY, WidgetState.SUSPENDED
        )
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.READY, WidgetState.ERROR
        )
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.READY, WidgetState.DESTROYING
        )

    def test_invalid_transitions_from_ready(self):
        """Test invalid transitions from READY state."""
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.READY, WidgetState.CREATED
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.READY, WidgetState.INITIALIZING
        )

    def test_valid_transitions_from_suspended(self):
        """Test valid transitions from SUSPENDED state."""
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.SUSPENDED, WidgetState.READY
        )
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.SUSPENDED, WidgetState.DESTROYING
        )

    def test_invalid_transitions_from_suspended(self):
        """Test invalid transitions from SUSPENDED state."""
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.SUSPENDED, WidgetState.CREATED
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.SUSPENDED, WidgetState.INITIALIZING
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.SUSPENDED, WidgetState.ERROR
        )

    def test_valid_transitions_from_error(self):
        """Test valid transitions from ERROR state."""
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.ERROR, WidgetState.INITIALIZING
        )
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.ERROR, WidgetState.DESTROYING
        )

    def test_invalid_transitions_from_error(self):
        """Test invalid transitions from ERROR state."""
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.ERROR, WidgetState.CREATED
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.ERROR, WidgetState.READY
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.ERROR, WidgetState.SUSPENDED
        )

    def test_valid_transitions_from_destroying(self):
        """Test valid transitions from DESTROYING state."""
        assert WidgetStateValidator.is_valid_transition(
            WidgetState.DESTROYING, WidgetState.DESTROYED
        )

    def test_invalid_transitions_from_destroying(self):
        """Test invalid transitions from DESTROYING state."""
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.DESTROYING, WidgetState.CREATED
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.DESTROYING, WidgetState.INITIALIZING
        )
        assert not WidgetStateValidator.is_valid_transition(
            WidgetState.DESTROYING, WidgetState.READY
        )

    def test_destroyed_is_terminal_state(self):
        """Test that DESTROYED is a terminal state with no valid transitions."""
        for state in WidgetState:
            if state != WidgetState.DESTROYED:
                assert not WidgetStateValidator.is_valid_transition(
                    WidgetState.DESTROYED, state
                )

    def test_self_transitions_invalid(self):
        """Test that self-transitions are not allowed."""
        for state in WidgetState:
            assert not WidgetStateValidator.is_valid_transition(state, state)
