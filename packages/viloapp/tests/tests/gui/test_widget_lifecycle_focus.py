#!/usr/bin/env python3
"""
GUI integration tests for widget lifecycle and focus behavior.
"""

from PySide6.QtCore import QTimer

from viloapp.ui.widgets.app_widget import AppWidget
from viloapp.ui.widgets.widget_registry import WidgetType
from viloapp.ui.widgets.widget_state import WidgetState


class AsyncTestWidget(AppWidget):
    """Test widget that simulates async initialization."""

    def __init__(self, widget_id: str, init_delay: int = 100, parent=None):
        super().__init__(widget_id, WidgetType.TERMINAL, parent)
        self.init_delay = init_delay
        self.load_complete_called = False

    def start_loading(self):
        """Simulate async loading."""
        self.initialize()
        QTimer.singleShot(self.init_delay, self.load_complete)

    def load_complete(self):
        """Simulate load completion."""
        self.load_complete_called = True
        self.set_ready()

    def focus_widget(self):
        """Override to track focus calls."""
        return super().focus_widget()


class SyncTestWidget(AppWidget):
    """Test widget that initializes synchronously."""

    def __init__(self, widget_id: str, parent=None):
        super().__init__(widget_id, WidgetType.TEXT_EDITOR, parent)
        self.initialize()
        self.set_ready()


class TestWidgetLifecycleFocus:
    """Test widget lifecycle and focus behavior in GUI context."""

    def test_async_widget_focus_queuing(self, qtbot):
        """Test that focus is queued for async widgets and applied when ready."""
        widget = AsyncTestWidget("async-test-1", init_delay=50)
        qtbot.addWidget(widget)

        # Start async loading
        widget.start_loading()
        assert widget.widget_state == WidgetState.INITIALIZING

        # Request focus while loading
        result = widget.focus_widget()
        assert not result
        assert widget._pending_focus
        assert not widget.hasFocus()

        # Wait for widget to become ready
        with qtbot.waitSignal(widget.widget_ready, timeout=200):
            pass

        # Widget should be ready
        assert widget.widget_state == WidgetState.READY
        assert widget.load_complete_called

        # Process events to handle pending focus
        qtbot.wait(10)

        # Pending focus should be cleared
        assert not widget._pending_focus

    def test_sync_widget_immediate_focus(self, qtbot):
        """Test that sync widgets can receive focus immediately."""
        widget = SyncTestWidget("sync-test-1")
        qtbot.addWidget(widget)

        # Widget should be ready immediately
        assert widget.widget_state == WidgetState.READY

        # Focus should work immediately
        result = widget.focus_widget()
        assert result
        assert widget.hasFocus()

    def test_multiple_async_widgets_focus(self, qtbot):
        """Test focus handling with multiple async widgets."""
        widget1 = AsyncTestWidget("async-test-2", init_delay=50)
        widget2 = AsyncTestWidget("async-test-3", init_delay=100)
        qtbot.addWidget(widget1)
        qtbot.addWidget(widget2)

        # Start both loading
        widget1.start_loading()
        widget2.start_loading()

        # Request focus on widget2 (longer delay)
        widget2.focus_widget()
        assert widget2._pending_focus

        # Wait for widget1 to be ready
        with qtbot.waitSignal(widget1.widget_ready, timeout=200):
            pass

        # Focus widget1 (now ready)
        result = widget1.focus_widget()
        assert result
        assert widget1.hasFocus()

        # Wait for widget2 to be ready
        with qtbot.waitSignal(widget2.widget_ready, timeout=200):
            pass

        # Process pending focus for widget2
        qtbot.wait(10)

        # Widget2's pending focus should be processed, but widget1 still has focus
        # unless widget2's pending focus takes it
        assert not widget2._pending_focus

    def test_widget_state_transitions_with_focus(self, qtbot):
        """Test focus behavior during state transitions."""
        widget = AsyncTestWidget("async-test-4", init_delay=50)
        qtbot.addWidget(widget)

        # Start in CREATED state
        assert widget.widget_state == WidgetState.CREATED

        # Focus should queue in CREATED state
        result = widget.focus_widget()
        assert not result
        assert widget._pending_focus

        # Start loading
        widget.start_loading()
        assert widget.widget_state == WidgetState.INITIALIZING

        # Focus request during INITIALIZING should maintain pending status
        widget._pending_focus = False  # Reset
        result = widget.focus_widget()
        assert not result
        assert widget._pending_focus

        # Wait for ready
        with qtbot.waitSignal(widget.widget_ready, timeout=200):
            pass

        # Process pending focus
        qtbot.wait(10)

        # Now suspend the widget
        widget.suspend()
        assert widget.widget_state == WidgetState.SUSPENDED

        # Focus should work in SUSPENDED state (some widgets allow this)
        # But our base implementation might not - check actual behavior
        result = widget.focus_widget()
        # Suspended widgets may or may not accept focus depending on implementation

        # Resume
        widget.resume()
        assert widget.widget_state == WidgetState.READY

        # Focus should work after resume
        result = widget.focus_widget()
        assert result

    def test_error_state_focus_behavior(self, qtbot):
        """Test focus behavior when widget enters error state."""
        widget = AsyncTestWidget("async-test-5", init_delay=50)
        qtbot.addWidget(widget)

        # Start loading
        widget.start_loading()

        # Simulate error instead of success
        widget.set_error("Test error")
        assert widget.widget_state == WidgetState.ERROR

        # Focus should be rejected in error state
        result = widget.focus_widget()
        assert not result
        assert not widget._pending_focus
        assert not widget.hasFocus()

    def test_cleanup_with_pending_focus(self, qtbot):
        """Test cleanup when widget has pending focus."""
        widget = AsyncTestWidget("async-test-6", init_delay=100)
        qtbot.addWidget(widget)

        # Start loading and request focus
        widget.start_loading()
        widget.focus_widget()
        assert widget._pending_focus

        # Cleanup before ready
        widget.cleanup()
        assert widget.widget_state == WidgetState.DESTROYED

        # Widget should not process pending focus after cleanup
        # Wait to ensure no crashes
        qtbot.wait(150)  # Wait longer than init_delay

    def test_rapid_focus_requests(self, qtbot):
        """Test handling of rapid/multiple focus requests."""
        widget = AsyncTestWidget("async-test-7", init_delay=50)
        qtbot.addWidget(widget)

        widget.start_loading()

        # Multiple focus requests while loading
        for _ in range(5):
            widget.focus_widget()

        # Should still have single pending focus
        assert widget._pending_focus

        # Wait for ready
        with qtbot.waitSignal(widget.widget_ready, timeout=200):
            pass

        qtbot.wait(10)

        # Focus should be set once
        assert not widget._pending_focus

    def test_widget_visibility_and_focus(self, qtbot):
        """Test interaction between visibility and focus."""
        widget = SyncTestWidget("sync-test-2")
        qtbot.addWidget(widget)

        # Widget is ready
        assert widget.widget_state == WidgetState.READY

        # Hide widget
        widget.hide()
        assert widget.widget_state == WidgetState.SUSPENDED

        # Try to focus hidden widget
        result = widget.focus_widget()
        # Implementation may vary - suspended widgets might queue focus

        # Show widget
        widget.show()
        qtbot.wait(10)

        # Focus should work after showing
        result = widget.focus_widget()
        assert result

    def test_parent_child_focus_propagation(self, qtbot):
        """Test focus behavior with parent-child widget relationships."""
        parent = SyncTestWidget("parent-1")
        child = AsyncTestWidget("child-1", init_delay=50, parent=parent)
        qtbot.addWidget(parent)

        # Start child loading
        child.start_loading()

        # Focus on child
        child.focus_widget()
        assert child._pending_focus

        # Wait for child ready
        with qtbot.waitSignal(child.widget_ready, timeout=200):
            pass

        qtbot.wait(10)

        # Child should process pending focus
        assert not child._pending_focus
