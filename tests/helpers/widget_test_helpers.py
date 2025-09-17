#!/usr/bin/env python3
"""
Test helpers for widget lifecycle testing.

This module provides reusable mock widgets, utilities, and fixtures
for testing widget lifecycle behavior.
"""

import time
from typing import Callable
from unittest.mock import Mock

from PySide6.QtCore import QTimer
from PySide6.QtTest import QSignalSpy

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
from ui.widgets.widget_state import WidgetState


class MockSyncWidget(AppWidget):
    """Mock synchronous widget that's ready immediately."""

    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.TEXT_EDITOR, parent)
        self.focus_count = 0
        self.on_suspend_called = False
        self.on_resume_called = False
        self.on_cleanup_called = False
        self.initialize()
        self.set_ready()

    def focus_widget(self):
        """Track focus calls."""
        self.focus_count += 1
        return super().focus_widget()

    def on_suspend(self):
        """Track suspend calls."""
        self.on_suspend_called = True

    def on_resume(self):
        """Track resume calls."""
        self.on_resume_called = True

    def on_cleanup(self):
        """Track cleanup calls."""
        self.on_cleanup_called = True


class MockAsyncWidget(AppWidget):
    """Mock asynchronous widget with configurable initialization delay."""

    def __init__(self, widget_id: str, init_delay: int = 50, parent=None):
        super().__init__(widget_id, WidgetType.TERMINAL, parent)
        self.init_delay = init_delay
        self.focus_count = 0
        self.load_complete_called = False
        self.on_suspend_called = False
        self.on_resume_called = False
        self.on_cleanup_called = False
        self.retry_count = 0
        self._init_timer = None

    def start_initialization(self):
        """Start async initialization."""
        self.initialize()
        self._init_timer = QTimer.singleShot(self.init_delay, self.complete_initialization)

    def complete_initialization(self):
        """Complete initialization and become ready."""
        self.load_complete_called = True
        self.set_ready()

    def focus_widget(self):
        """Track focus calls."""
        self.focus_count += 1
        return super().focus_widget()

    def on_suspend(self):
        """Track suspend calls."""
        self.on_suspend_called = True

    def on_resume(self):
        """Track resume calls."""
        self.on_resume_called = True

    def on_cleanup(self):
        """Track cleanup calls."""
        self.on_cleanup_called = True
        # Cancel init timer if still running
        if self._init_timer:
            self._init_timer = None

    def retry_initialization(self):
        """Track retry calls."""
        self.retry_count += 1
        super().retry_initialization()


class MockErrorWidget(AppWidget):
    """Mock widget that simulates errors."""

    def __init__(self, widget_id: str, error_on_attempt: int = 1, parent=None):
        super().__init__(widget_id, WidgetType.CUSTOM, parent)
        self.error_on_attempt = error_on_attempt
        self.attempt_count = 0
        self.retry_count = 0

    def start_initialization(self):
        """Start initialization that may error."""
        self.initialize()
        self.attempt_count += 1

        if self.attempt_count < self.error_on_attempt:
            QTimer.singleShot(10, lambda: self.set_error(f"Error on attempt {self.attempt_count}"))
        else:
            QTimer.singleShot(10, self.set_ready)

    def retry_initialization(self):
        """Track and perform retry."""
        self.retry_count += 1
        self.start_initialization()


class WidgetTestHelper:
    """Helper class for widget testing."""

    @staticmethod
    def wait_for_state(widget: AppWidget, state: WidgetState, timeout_ms: int = 1000) -> bool:
        """
        Wait for widget to reach a specific state.

        Args:
            widget: The widget to monitor
            state: The desired state
            timeout_ms: Maximum time to wait in milliseconds

        Returns:
            True if state was reached, False if timeout
        """
        start_time = time.time()
        while widget.widget_state != state:
            if (time.time() - start_time) * 1000 > timeout_ms:
                return False
            QTimer.processEvents()
        return True

    @staticmethod
    def assert_state_transition(widget: AppWidget, from_state: WidgetState,
                               to_state: WidgetState, action: Callable):
        """
        Assert that an action causes a specific state transition.

        Args:
            widget: The widget to test
            from_state: Expected initial state
            to_state: Expected final state
            action: Callable that triggers the transition
        """
        assert widget.widget_state == from_state, \
            f"Widget not in expected initial state {from_state.value}, got {widget.widget_state.value}"

        action()

        assert widget.widget_state == to_state, \
            f"Widget not in expected final state {to_state.value}, got {widget.widget_state.value}"

    @staticmethod
    def create_signal_spy(signal, process_events: bool = False) -> QSignalSpy:
        """
        Create a QSignalSpy with helper methods.

        Args:
            signal: The signal to spy on
            process_events: Whether to process events after signal

        Returns:
            Enhanced QSignalSpy
        """
        spy = QSignalSpy(signal)

        # Add helper to get last emission
        def get_last_emission():
            if spy.count() > 0:
                return spy.at(spy.count() - 1)
            return None

        spy.get_last_emission = get_last_emission
        return spy

    @staticmethod
    def verify_focus_behavior(widget: AppWidget, qtbot):
        """
        Verify standard focus behavior for a widget.

        Args:
            widget: The widget to test
            qtbot: pytest-qt fixture
        """
        # Test focus when ready
        if widget.widget_state == WidgetState.READY:
            result = widget.focus_widget()
            assert result
            assert widget.has_focus

        # Test focus when not ready
        elif widget.widget_state in [WidgetState.CREATED, WidgetState.INITIALIZING]:
            result = widget.focus_widget()
            assert not result
            assert widget._pending_focus
            assert not widget.has_focus

        # Test focus in error state
        elif widget.widget_state == WidgetState.ERROR:
            result = widget.focus_widget()
            assert not result
            assert not widget._pending_focus
            assert not widget.has_focus

    @staticmethod
    def verify_signal_cleanup(widget: AppWidget):
        """
        Verify that signals are properly cleaned up.

        Args:
            widget: The widget to test
        """
        widget._signal_manager.get_connection_count()

        # Perform cleanup
        widget.cleanup()

        # Verify all connections removed
        assert widget._signal_manager.get_connection_count() == 0, \
            f"Signal connections not cleaned up: {widget._signal_manager.get_connection_count()} remaining"

        # Verify state
        assert widget.widget_state == WidgetState.DESTROYED

    @staticmethod
    def simulate_error_recovery(widget: AppWidget, qtbot, max_wait_ms: int = 5000):
        """
        Simulate and verify error recovery behavior.

        Args:
            widget: The widget to test
            qtbot: pytest-qt fixture
            max_wait_ms: Maximum time to wait for recovery
        """
        # Trigger error
        widget.set_error("Test error")
        assert widget.widget_state == WidgetState.ERROR

        # Wait for retry if configured
        if widget._max_retries > widget._error_count:
            # Should retry
            spy = QSignalSpy(widget.widget_state_changed)
            qtbot.wait(widget._retry_base_delay + 100)  # Wait for retry delay

            # Check if retry was attempted
            if spy.count() > 0:
                last_state = spy.at(spy.count() - 1)[0]
                assert last_state in ["initializing", "ready"], \
                    f"Expected retry to initializing or ready, got {last_state}"

    @staticmethod
    def mock_timer_singleshot():
        """
        Create a mock for QTimer.singleShot that captures calls.

        Returns:
            Mock object with call tracking
        """
        calls = []

        def mock_singleshot(delay, callback):
            calls.append({'delay': delay, 'callback': callback})
            # Optionally execute callback immediately for testing
            # callback()

        mock = Mock(side_effect=mock_singleshot)
        mock.calls = calls
        return mock


class WidgetTestFixtures:
    """Reusable fixtures for widget testing."""

    @staticmethod
    def create_widget_set(qtbot) -> dict:
        """
        Create a standard set of test widgets.

        Args:
            qtbot: pytest-qt fixture

        Returns:
            Dictionary of test widgets
        """
        widgets = {
            'sync': MockSyncWidget("sync-test"),
            'async_fast': MockAsyncWidget("async-fast", init_delay=10),
            'async_slow': MockAsyncWidget("async-slow", init_delay=100),
            'error': MockErrorWidget("error-test", error_on_attempt=2)
        }

        for widget in widgets.values():
            qtbot.addWidget(widget)

        return widgets

    @staticmethod
    def setup_widget_with_spy(widget: AppWidget, qtbot) -> dict:
        """
        Set up a widget with signal spies on all lifecycle signals.

        Args:
            widget: The widget to set up
            qtbot: pytest-qt fixture

        Returns:
            Dictionary of signal spies
        """
        qtbot.addWidget(widget)

        spies = {
            'ready': QSignalSpy(widget.widget_ready),
            'error': QSignalSpy(widget.widget_error),
            'state_changed': QSignalSpy(widget.widget_state_changed),
            'destroying': QSignalSpy(widget.widget_destroying),
            'focus_requested': QSignalSpy(widget.focus_requested)
        }

        return spies


# Pytest fixtures that can be imported
def pytest_fixtures():
    """Define pytest fixtures for use in test files."""
    import pytest

    @pytest.fixture
    def mock_sync_widget(qtbot):
        """Provide a mock synchronous widget."""
        widget = MockSyncWidget("test-sync")
        qtbot.addWidget(widget)
        return widget

    @pytest.fixture
    def mock_async_widget(qtbot):
        """Provide a mock asynchronous widget."""
        widget = MockAsyncWidget("test-async")
        qtbot.addWidget(widget)
        return widget

    @pytest.fixture
    def mock_error_widget(qtbot):
        """Provide a mock error widget."""
        widget = MockErrorWidget("test-error")
        qtbot.addWidget(widget)
        return widget

    @pytest.fixture
    def widget_helper():
        """Provide widget test helper."""
        return WidgetTestHelper()

    return {
        'mock_sync_widget': mock_sync_widget,
        'mock_async_widget': mock_async_widget,
        'mock_error_widget': mock_error_widget,
        'widget_helper': widget_helper
    }
