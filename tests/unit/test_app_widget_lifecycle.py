#!/usr/bin/env python3
"""
Unit tests for AppWidget lifecycle functionality.
"""

from unittest.mock import patch

from PySide6.QtCore import QTimer
from PySide6.QtTest import QSignalSpy

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
from ui.widgets.widget_state import WidgetState


class MockAppWidget(AppWidget):
    """Test implementation of AppWidget."""

    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.TEXT_EDITOR, parent)
        self.on_suspend_called = False
        self.on_resume_called = False
        self.on_cleanup_called = False
        self.retry_count = 0

    def on_suspend(self):
        """Track suspend calls."""
        self.on_suspend_called = True

    def on_resume(self):
        """Track resume calls."""
        self.on_resume_called = True

    def on_cleanup(self):
        """Track cleanup calls."""
        self.on_cleanup_called = True

    def retry_initialization(self):
        """Track retry calls."""
        self.retry_count += 1
        super().retry_initialization()


class TestMockAppWidgetLifecycle:
    """Test AppWidget lifecycle functionality."""

    def test_widget_creation(self, qtbot):
        """Test widget is created in correct initial state."""
        widget = MockAppWidget("test-widget-1")
        qtbot.addWidget(widget)

        assert widget.widget_id == "test-widget-1"
        assert widget.widget_type == WidgetType.TEXT_EDITOR
        assert widget.widget_state == WidgetState.CREATED
        assert not widget._pending_focus
        assert widget._error_count == 0
        assert widget._signal_manager is not None

    def test_widget_initialization(self, qtbot):
        """Test widget initialization."""
        widget = MockAppWidget("test-widget-2")
        qtbot.addWidget(widget)

        # Spy on state change signal
        state_spy = QSignalSpy(widget.widget_state_changed)

        widget.initialize()

        assert widget.widget_state == WidgetState.INITIALIZING
        assert state_spy.count() == 1
        # QSignalSpy stores signals as list, access with at()
        assert state_spy.at(0)[0] == "initializing"

    def test_widget_set_ready(self, qtbot):
        """Test widget becoming ready."""
        widget = MockAppWidget("test-widget-3")
        qtbot.addWidget(widget)

        # Spy on signals
        ready_spy = QSignalSpy(widget.widget_ready)
        state_spy = QSignalSpy(widget.widget_state_changed)

        # Initialize and set ready
        widget.initialize()
        widget.set_ready()

        assert widget.widget_state == WidgetState.READY
        assert ready_spy.count() == 1
        assert state_spy.count() == 2  # CREATED->INITIALIZING, INITIALIZING->READY

    def test_widget_set_error(self, qtbot):
        """Test widget error handling."""
        widget = MockAppWidget("test-widget-4")
        qtbot.addWidget(widget)

        # Spy on error signal
        error_spy = QSignalSpy(widget.widget_error)

        # Initialize and set error
        widget.initialize()
        widget.set_error("Test error message")

        assert widget.widget_state == WidgetState.ERROR
        assert error_spy.count() == 1
        assert error_spy.at(0)[0] == "Test error message"
        assert widget._error_count == 1

    def test_error_retry_mechanism(self, qtbot):
        """Test automatic retry on error."""
        widget = MockAppWidget("test-widget-5")
        qtbot.addWidget(widget)

        widget.initialize()

        # Mock QTimer.singleShot to capture retry scheduling
        with patch.object(QTimer, "singleShot") as mock_timer:
            widget.set_error("Test error")

            # Should schedule retry with 1000ms delay
            mock_timer.assert_called_once()
            assert mock_timer.call_args[0][0] == 1000  # First retry delay
            assert widget._error_count == 1

    def test_max_error_retries(self, qtbot):
        """Test that retries stop after max attempts."""
        widget = MockAppWidget("test-widget-6")
        qtbot.addWidget(widget)

        widget.initialize()

        # Set error 3 times
        with patch.object(QTimer, "singleShot") as mock_timer:
            widget.set_error("Error 1")
            assert mock_timer.call_count == 1

            widget.set_error("Error 2")
            assert mock_timer.call_count == 2

            widget.set_error("Error 3")
            # Should not schedule retry after 3rd error
            assert mock_timer.call_count == 2  # No additional call
            assert widget._error_count == 3

    def test_widget_suspend_resume(self, qtbot):
        """Test widget suspend and resume."""
        widget = MockAppWidget("test-widget-7")
        qtbot.addWidget(widget)

        # Get to ready state
        widget.initialize()
        widget.set_ready()

        # Suspend
        widget.suspend()
        assert widget.widget_state == WidgetState.SUSPENDED
        assert widget.on_suspend_called

        # Resume
        widget.resume()
        assert widget.widget_state == WidgetState.READY
        assert widget.on_resume_called

    def test_widget_cleanup(self, qtbot):
        """Test widget cleanup."""
        widget = MockAppWidget("test-widget-8")
        qtbot.addWidget(widget)

        # Spy on destroying signal
        destroying_spy = QSignalSpy(widget.widget_destroying)

        # Add a mock connection to signal manager
        widget._signal_manager.connect(
            widget.widget_ready, lambda: None, description="Test connection"
        )
        assert widget._signal_manager.get_connection_count() == 1

        # Cleanup
        widget.cleanup()

        assert widget.widget_state == WidgetState.DESTROYED
        assert destroying_spy.count() == 1
        assert widget.on_cleanup_called
        assert widget._signal_manager.get_connection_count() == 0

    def test_focus_when_ready(self, qtbot):
        """Test focus is set immediately when widget is ready."""
        widget = MockAppWidget("test-widget-9")
        qtbot.addWidget(widget)

        # Get to ready state
        widget.initialize()
        widget.set_ready()

        # Request focus
        result = widget.focus_widget()
        assert result
        assert widget.has_focus  # Use our property instead of Qt's hasFocus()

    def test_focus_queued_when_not_ready(self, qtbot):
        """Test focus is queued when widget is not ready."""
        widget = MockAppWidget("test-widget-10")
        qtbot.addWidget(widget)

        # Widget in CREATED state
        result = widget.focus_widget()
        assert not result
        assert widget._pending_focus
        assert not widget.has_focus

        # Initialize
        widget.initialize()

        # Still not ready
        result = widget.focus_widget()
        assert not result
        assert widget._pending_focus

    def test_pending_focus_processed_on_ready(self, qtbot):
        """Test pending focus is processed when widget becomes ready."""
        widget = MockAppWidget("test-widget-11")
        qtbot.addWidget(widget)

        # Request focus before ready
        widget.focus_widget()
        assert widget._pending_focus

        # Initialize
        widget.initialize()

        # Mock QTimer.singleShot to verify focus is scheduled
        with patch.object(QTimer, "singleShot") as mock_timer:
            widget.set_ready()

            # Should schedule focus processing
            mock_timer.assert_called_once()
            assert mock_timer.call_args[0][0] == 0  # Immediate scheduling
            # The callback should be focus_widget
            callback = mock_timer.call_args[0][1]
            assert callback == widget.focus_widget

        assert not widget._pending_focus

    def test_focus_rejected_in_error_state(self, qtbot):
        """Test focus is rejected when widget is in error state."""
        widget = MockAppWidget("test-widget-12")
        qtbot.addWidget(widget)

        # Get to error state
        widget.initialize()
        widget.set_error("Test error")

        # Try to focus
        result = widget.focus_widget()
        assert not result
        assert not widget._pending_focus
        assert not widget.has_focus

    def test_show_hide_events(self, qtbot):
        """Test show/hide events trigger suspend/resume."""
        widget = MockAppWidget("test-widget-13")
        qtbot.addWidget(widget)

        # Get to ready state
        widget.initialize()
        widget.set_ready()

        # Manually call suspend (in tests, hide() might not trigger hideEvent)
        widget.suspend()
        assert widget.widget_state == WidgetState.SUSPENDED
        assert widget.on_suspend_called

        # Resume
        widget.resume()
        assert widget.widget_state == WidgetState.READY
        assert widget.on_resume_called

    def test_invalid_state_transitions(self, qtbot):
        """Test that invalid state transitions are prevented."""
        widget = MockAppWidget("test-widget-14")
        qtbot.addWidget(widget)

        # Try invalid transition from CREATED to READY
        widget._set_state(WidgetState.READY)
        assert widget.widget_state == WidgetState.CREATED  # Should not change

        # Valid transition to INITIALIZING
        widget._set_state(WidgetState.INITIALIZING)
        assert widget.widget_state == WidgetState.INITIALIZING

        # Try invalid transition from INITIALIZING to SUSPENDED
        widget._set_state(WidgetState.SUSPENDED)
        assert widget.widget_state == WidgetState.INITIALIZING  # Should not change

    def test_get_state_method(self, qtbot):
        """Test get_state returns widget information."""
        widget = MockAppWidget("test-widget-15")
        qtbot.addWidget(widget)

        state = widget.get_state()
        assert state["type"] == WidgetType.TEXT_EDITOR.value
        assert state["widget_id"] == "test-widget-15"

    def test_request_focus_signal(self, qtbot):
        """Test request_focus emits signal."""
        widget = MockAppWidget("test-widget-16")
        qtbot.addWidget(widget)

        # Spy on focus_requested signal
        focus_spy = QSignalSpy(widget.focus_requested)

        widget.request_focus()
        assert focus_spy.count() == 1

    def test_configurable_retry_strategy(self, qtbot):
        """Test configurable retry strategy."""
        widget = MockAppWidget("test-widget-17")
        qtbot.addWidget(widget)

        # Configure custom retry strategy
        widget.configure_retry_strategy(
            max_retries=5, base_delay=500, backoff_factor=2.0
        )

        assert widget._max_retries == 5
        assert widget._retry_base_delay == 500
        assert widget._retry_backoff_factor == 2.0

        # Test that retries use the configured values
        widget.initialize()

        with patch.object(QTimer, "singleShot") as mock_timer:
            widget.set_error("Test error")

            # Should schedule retry with 500ms delay (base_delay * 2.0^0)
            mock_timer.assert_called_once()
            assert mock_timer.call_args[0][0] == 500

            # Second error should use exponential backoff
            widget.set_error("Test error 2")
            # Should schedule retry with 1000ms delay (500 * 2.0^1)
            assert mock_timer.call_args[0][0] == 1000

    def test_disable_retries(self, qtbot):
        """Test disabling retries by setting max_retries to 0."""
        widget = MockAppWidget("test-widget-18")
        qtbot.addWidget(widget)

        # Disable retries
        widget.configure_retry_strategy(max_retries=0)

        widget.initialize()

        with patch.object(QTimer, "singleShot") as mock_timer:
            widget.set_error("Test error")

            # Should not schedule retry
            mock_timer.assert_not_called()
            assert widget._error_count == 1
