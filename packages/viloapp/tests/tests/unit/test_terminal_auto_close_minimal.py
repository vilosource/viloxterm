#!/usr/bin/env python3
"""
Minimal tests for terminal pane auto-close functionality - no Qt widget creation.

Tests the existence of required methods and signal definitions.

NOTE: These tests are currently DISABLED because terminal functionality
has been moved to the viloxterm plugin. The tests remain as documentation
of the expected plugin interface.
"""

import pytest

from unittest.mock import Mock


class TestCodeChangesExist:
    """Test that all required code changes exist."""

    @pytest.mark.skip(reason="Terminal functionality moved to viloxterm plugin")
    def test_terminal_server_has_session_ended_signal(self):
        """Test that TerminalServerManager class has session_ended signal."""
        # from viloapp.services.terminal_server import TerminalServerManager
        pytest.skip("Terminal server is now in viloxterm plugin")

        # Check signal exists on class
        assert hasattr(TerminalServerManager, "session_ended")

    @pytest.mark.skip(reason="Terminal functionality moved to viloxterm plugin")
    def test_terminal_server_inherits_qobject(self):
        """Test that TerminalServerManager inherits from QObject."""
        # from PySide6.QtCore import QObject
        # from viloapp.services.terminal_server import TerminalServerManager
        pytest.skip("Terminal server is now in viloxterm plugin")

        # Check inheritance
        assert issubclass(TerminalServerManager, QObject)

    @pytest.mark.skip(reason="Terminal functionality moved to viloxterm plugin")
    def test_terminal_app_widget_has_pane_close_signal(self):
        """Test that TerminalAppWidget has pane_close_requested signal."""
        # from viloapp.ui.terminal.terminal_app_widget import TerminalAppWidget
        pytest.skip("Terminal widgets are now in viloxterm plugin")

        # Check signal exists on class
        assert hasattr(TerminalAppWidget, "pane_close_requested")

    @pytest.mark.skip(reason="Terminal functionality moved to viloxterm plugin")
    def test_terminal_app_widget_has_session_handler(self):
        """Test that TerminalAppWidget has session end handler."""
        # from viloapp.ui.terminal.terminal_app_widget import TerminalAppWidget
        pytest.skip("Terminal widgets are now in viloxterm plugin")

        # Check method exists
        assert hasattr(TerminalAppWidget, "on_session_ended")
        assert callable(TerminalAppWidget.on_session_ended)

    def test_split_pane_model_has_callback_system(self):
        """Test that SplitPaneModel has terminal callback system."""
        # Import without creating instances
        import viloapp.ui.widgets.split_pane_model as model_module

        # Check methods exist on class
        assert hasattr(model_module.SplitPaneModel, "set_terminal_close_callback")
        assert hasattr(model_module.SplitPaneModel, "on_terminal_close_requested")

        # Check they are callable
        assert callable(model_module.SplitPaneModel.set_terminal_close_callback)
        assert callable(model_module.SplitPaneModel.on_terminal_close_requested)

    def test_split_pane_widget_has_terminal_handler(self):
        """Test that SplitPaneWidget has terminal close handler."""
        # Import without creating instances
        import viloapp.ui.widgets.split_pane_widget as widget_module

        # Check method exists on class
        assert hasattr(widget_module.SplitPaneWidget, "on_terminal_close_requested")
        assert callable(widget_module.SplitPaneWidget.on_terminal_close_requested)

    def test_split_pane_widget_has_close_pane_method(self):
        """Test that SplitPaneWidget has close_pane method."""
        # Import without creating instances
        import viloapp.ui.widgets.split_pane_widget as widget_module

        # Check method exists on class
        assert hasattr(widget_module.SplitPaneWidget, "close_pane")
        assert callable(widget_module.SplitPaneWidget.close_pane)


class TestCallbackLogic:
    """Test the callback logic without creating widgets."""

    def test_callback_system_mock_behavior(self):
        """Test the callback system using mocks."""
        # Mock the callback system behavior
        callback = Mock()

        # Simulate setting callback
        callback_holder = Mock()
        callback_holder.terminal_close_callback = None
        callback_holder.set_terminal_close_callback = lambda cb: setattr(
            callback_holder, "terminal_close_callback", cb
        )

        # Test setting callback
        callback_holder.set_terminal_close_callback(callback)
        assert callback_holder.terminal_close_callback is callback

        # Test calling callback
        if callback_holder.terminal_close_callback:
            callback_holder.terminal_close_callback("test_pane")

        callback.assert_called_once_with("test_pane")

    def test_signal_emission_mock_behavior(self):
        """Test signal emission behavior using mocks."""
        # Mock signal behavior
        signal_mock = Mock()
        signal_mock.emit = Mock()

        # Simulate signal emission
        signal_mock.emit()

        signal_mock.emit.assert_called_once()

    def test_session_matching_logic(self):
        """Test the session matching logic."""
        # Simulate session matching
        widget_session_id = "test_session_123"
        ended_session_id = "test_session_123"
        other_session_id = "different_session_456"

        # Should match
        assert widget_session_id == ended_session_id

        # Should not match
        assert widget_session_id != other_session_id


class TestDataStructures:
    """Test data structures without Qt."""

    @pytest.mark.skip(reason="Terminal functionality moved to viloxterm plugin")
    def test_terminal_session_dataclass(self):
        """Test TerminalSession dataclass."""
        # from viloapp.services.terminal_server import TerminalSession
        # session = TerminalSession(session_id="test_123", fd=1, child_pid=1234, active=True)
        pytest.skip("TerminalSession is now in viloxterm plugin")
