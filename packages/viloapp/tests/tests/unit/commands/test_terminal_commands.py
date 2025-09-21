#!/usr/bin/env python3
"""
Unit tests for terminal_commands.py

Tests verify that terminal commands properly delegate to services
and follow the MVC architecture patterns. Focus is on service delegation
and proper workspace service usage.
"""

from unittest.mock import Mock, patch
import pytest

from viloapp.core.commands.base import CommandContext
from viloapp.core.commands.builtin.terminal_commands import (
    clear_terminal_handler,
    copy_terminal_handler,
    paste_terminal_handler,
    kill_terminal_handler,
    restart_terminal_handler,
)
from viloapp.services.workspace_service import WorkspaceService


class TestClearTerminalHandler:
    """Test clear_terminal_handler delegates properly to WorkspaceService."""

    @pytest.fixture
    def mock_context(self):
        """Create mock command context."""
        context = Mock(spec=CommandContext)
        context.args = {}
        return context

    @pytest.fixture
    def mock_workspace_service(self):
        """Create mock WorkspaceService."""
        service = Mock(spec=WorkspaceService)
        return service

    def test_clear_terminal_uses_workspace_service(self, mock_context, mock_workspace_service):
        """Test that clear_terminal_handler uses workspace_service.get_current_widget()."""
        # ARRANGE - Setup mocks
        mock_terminal_widget = Mock()
        mock_terminal_widget.clear_terminal = Mock()

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget

        # ACT - Execute command
        result = clear_terminal_handler(mock_context)

        # ASSERT - Verify service delegation
        assert result.success is True
        assert "Terminal cleared" in result.value
        mock_context.get_service.assert_called_once_with(WorkspaceService)
        mock_workspace_service.get_current_widget.assert_called_once()
        mock_terminal_widget.clear_terminal.assert_called_once()

    def test_clear_terminal_handles_no_workspace_service(self, mock_context):
        """Test clear_terminal_handler when WorkspaceService unavailable."""
        # ARRANGE - No workspace service
        mock_context.get_service.return_value = None

        # ACT - Execute command
        result = clear_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_clear_terminal_handles_no_current_widget(self, mock_context, mock_workspace_service):
        """Test clear_terminal_handler when no current widget available."""
        # ARRANGE - Services available but no current widget
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = None

        # ACT - Execute command
        result = clear_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No active terminal to clear" in result.error

    def test_clear_terminal_handles_non_terminal_widget(self, mock_context, mock_workspace_service):
        """Test clear_terminal_handler when current widget is not a terminal."""
        # ARRANGE - Current widget doesn't have clear_terminal method
        mock_non_terminal_widget = Mock(spec=[])  # No clear_terminal method

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_non_terminal_widget

        # ACT - Execute command
        result = clear_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No active terminal to clear" in result.error

    def test_clear_terminal_handles_exception(self, mock_context, mock_workspace_service):
        """Test clear_terminal_handler handles exceptions properly."""
        # ARRANGE - Service throws exception
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.side_effect = RuntimeError("Service error")

        # ACT - Execute command
        result = clear_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Failed to clear terminal" in result.error
        assert "Service error" in result.error


class TestCopyTerminalHandler:
    """Test copy_terminal_handler delegates properly to WorkspaceService."""

    @pytest.fixture
    def mock_context(self):
        """Create mock command context."""
        context = Mock(spec=CommandContext)
        context.args = {}
        return context

    @pytest.fixture
    def mock_workspace_service(self):
        """Create mock WorkspaceService."""
        service = Mock(spec=WorkspaceService)
        return service

    def test_copy_terminal_uses_workspace_service(self, mock_context, mock_workspace_service):
        """Test that copy_terminal_handler uses workspace_service.get_current_widget()."""
        # ARRANGE - Setup mocks
        mock_terminal_widget = Mock()
        mock_terminal_widget.copy_selection = Mock()

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget

        # ACT - Execute command
        result = copy_terminal_handler(mock_context)

        # ASSERT - Verify service delegation
        assert result.success is True
        assert "Copied to clipboard" in result.value
        mock_context.get_service.assert_called_once_with(WorkspaceService)
        mock_workspace_service.get_current_widget.assert_called_once()
        mock_terminal_widget.copy_selection.assert_called_once()

    def test_copy_terminal_handles_no_workspace_service(self, mock_context):
        """Test copy_terminal_handler when WorkspaceService unavailable."""
        # ARRANGE - No workspace service
        mock_context.get_service.return_value = None

        # ACT - Execute command
        result = copy_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_copy_terminal_handles_no_terminal_widget(self, mock_context, mock_workspace_service):
        """Test copy_terminal_handler when no terminal widget available."""
        # ARRANGE - No terminal widget
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = None

        # ACT - Execute command
        result = copy_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No active terminal to copy from" in result.error


class TestPasteTerminalHandler:
    """Test paste_terminal_handler delegates properly to WorkspaceService."""

    @pytest.fixture
    def mock_context(self):
        """Create mock command context."""
        context = Mock(spec=CommandContext)
        context.args = {}
        return context

    @pytest.fixture
    def mock_workspace_service(self):
        """Create mock WorkspaceService."""
        service = Mock(spec=WorkspaceService)
        return service

    @patch('PySide6.QtWidgets.QApplication.clipboard')
    def test_paste_terminal_uses_workspace_service(self, mock_clipboard, mock_context, mock_workspace_service):
        """Test that paste_terminal_handler uses workspace_service.get_current_widget()."""
        # ARRANGE - Setup mocks
        mock_terminal_widget = Mock()
        mock_terminal_widget.paste_to_terminal = Mock()
        mock_clipboard_obj = Mock()
        mock_clipboard_obj.text.return_value = "test clipboard text"
        mock_clipboard.return_value = mock_clipboard_obj

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget

        # ACT - Execute command
        result = paste_terminal_handler(mock_context)

        # ASSERT - Verify service delegation
        assert result.success is True
        assert "Pasted to terminal" in result.value
        mock_context.get_service.assert_called_once_with(WorkspaceService)
        mock_workspace_service.get_current_widget.assert_called_once()
        mock_terminal_widget.paste_to_terminal.assert_called_once_with("test clipboard text")

    @patch('PySide6.QtWidgets.QApplication.clipboard')
    def test_paste_terminal_handles_empty_clipboard(self, mock_clipboard, mock_context, mock_workspace_service):
        """Test paste_terminal_handler when clipboard is empty."""
        # ARRANGE - Empty clipboard
        mock_terminal_widget = Mock()
        mock_clipboard_obj = Mock()
        mock_clipboard_obj.text.return_value = ""  # Empty clipboard
        mock_clipboard.return_value = mock_clipboard_obj

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget

        # ACT - Execute command
        result = paste_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Clipboard is empty" in result.error

    def test_paste_terminal_handles_no_workspace_service(self, mock_context):
        """Test paste_terminal_handler when WorkspaceService unavailable."""
        # ARRANGE - No workspace service
        mock_context.get_service.return_value = None

        # ACT - Execute command
        result = paste_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_paste_terminal_handles_no_terminal_widget(self, mock_context, mock_workspace_service):
        """Test paste_terminal_handler when no terminal widget available."""
        # ARRANGE - No terminal widget
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = None

        # ACT - Execute command
        result = paste_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No active terminal to paste to" in result.error


class TestKillTerminalHandler:
    """Test kill_terminal_handler delegates properly to WorkspaceService."""

    @pytest.fixture
    def mock_context(self):
        """Create mock command context."""
        context = Mock(spec=CommandContext)
        context.args = {}
        return context

    @pytest.fixture
    def mock_workspace_service(self):
        """Create mock WorkspaceService."""
        service = Mock(spec=WorkspaceService)
        return service

    def test_kill_terminal_uses_workspace_service(self, mock_context, mock_workspace_service):
        """Test that kill_terminal_handler uses workspace_service.get_current_widget()."""
        # ARRANGE - Setup mocks
        mock_terminal_widget = Mock()
        mock_terminal_widget.close_terminal = Mock()

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget
        mock_workspace_service.close_tab.return_value = True

        # ACT - Execute command
        result = kill_terminal_handler(mock_context)

        # ASSERT - Verify service delegation
        assert result.success is True
        assert "Terminal closed" in result.value
        mock_context.get_service.assert_called_once_with(WorkspaceService)
        mock_workspace_service.get_current_widget.assert_called_once()
        mock_workspace_service.close_tab.assert_called_once()

    def test_kill_terminal_handles_no_workspace_service(self, mock_context):
        """Test kill_terminal_handler when WorkspaceService unavailable."""
        # ARRANGE - No workspace service
        mock_context.get_service.return_value = None

        # ACT - Execute command
        result = kill_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_kill_terminal_handles_no_terminal_widget(self, mock_context, mock_workspace_service):
        """Test kill_terminal_handler when no terminal widget available."""
        # ARRANGE - No terminal widget
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = None

        # ACT - Execute command
        result = kill_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No active terminal to close" in result.error

    def test_kill_terminal_handles_close_tab_failure(self, mock_context, mock_workspace_service):
        """Test kill_terminal_handler when close_tab fails."""
        # ARRANGE - Terminal widget but close_tab fails
        mock_terminal_widget = Mock()
        mock_terminal_widget.close_terminal = Mock()

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget
        mock_workspace_service.close_tab.return_value = False

        # ACT - Execute command
        result = kill_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No active terminal to close" in result.error


class TestRestartTerminalHandler:
    """Test restart_terminal_handler delegates properly to WorkspaceService."""

    @pytest.fixture
    def mock_context(self):
        """Create mock command context."""
        context = Mock(spec=CommandContext)
        context.args = {}
        return context

    @pytest.fixture
    def mock_workspace_service(self):
        """Create mock WorkspaceService."""
        service = Mock(spec=WorkspaceService)
        return service

    def test_restart_terminal_uses_workspace_service(self, mock_context, mock_workspace_service):
        """Test that restart_terminal_handler uses workspace_service.get_current_widget()."""
        # ARRANGE - Setup mocks
        mock_terminal_widget = Mock()
        mock_terminal_widget.restart_terminal = Mock()

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget

        # ACT - Execute command
        result = restart_terminal_handler(mock_context)

        # ASSERT - Verify service delegation
        assert result.success is True
        assert "Terminal restarted" in result.value
        mock_context.get_service.assert_called_once_with(WorkspaceService)
        mock_workspace_service.get_current_widget.assert_called_once()
        mock_terminal_widget.restart_terminal.assert_called_once()

    def test_restart_terminal_handles_no_workspace_service(self, mock_context):
        """Test restart_terminal_handler when WorkspaceService unavailable."""
        # ARRANGE - No workspace service
        mock_context.get_service.return_value = None

        # ACT - Execute command
        result = restart_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_restart_terminal_handles_no_terminal_widget(self, mock_context, mock_workspace_service):
        """Test restart_terminal_handler when no terminal widget available."""
        # ARRANGE - No terminal widget
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = None

        # ACT - Execute command
        result = restart_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No active terminal to restart" in result.error

    def test_restart_terminal_handles_non_terminal_widget(self, mock_context, mock_workspace_service):
        """Test restart_terminal_handler when current widget is not a terminal."""
        # ARRANGE - Current widget doesn't have restart_terminal method
        mock_non_terminal_widget = Mock(spec=[])  # No restart_terminal method

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_non_terminal_widget

        # ACT - Execute command
        result = restart_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No active terminal to restart" in result.error


class TestTerminalCommandsMVCCompliance:
    """Test that terminal commands follow MVC architecture patterns."""

    def test_commands_use_workspace_service_not_direct_ui(self):
        """Test that all terminal commands use WorkspaceService instead of direct UI access."""
        # ARRANGE - Setup common mocks
        mock_context = Mock(spec=CommandContext)
        mock_workspace_service = Mock(spec=WorkspaceService)
        mock_terminal_widget = Mock()
        mock_terminal_widget.clear_terminal = Mock()
        mock_terminal_widget.copy_selection = Mock()
        mock_terminal_widget.restart_terminal = Mock()

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget
        mock_workspace_service.close_tab.return_value = True

        # Test each command uses WorkspaceService
        commands_to_test = [
            clear_terminal_handler,
            copy_terminal_handler,
            restart_terminal_handler,
            kill_terminal_handler,
        ]

        for command_func in commands_to_test:
            mock_context.get_service.reset_mock()
            mock_workspace_service.reset_mock()

            result = command_func(mock_context)

            # Verify service was requested (MVC compliance)
            assert result.success is True
            mock_context.get_service.assert_called_once_with(WorkspaceService)
            mock_workspace_service.get_current_widget.assert_called_once()

    def test_commands_return_proper_command_results(self):
        """Test that all terminal commands return proper CommandResult objects."""
        mock_context = Mock(spec=CommandContext)
        mock_context.get_service.return_value = None  # Force error path

        commands = [
            clear_terminal_handler,
            copy_terminal_handler,
            paste_terminal_handler,
            kill_terminal_handler,
            restart_terminal_handler,
        ]

        for command_func in commands:
            result = command_func(mock_context)

            # Verify proper CommandResult structure
            assert hasattr(result, 'success')
            assert hasattr(result, 'error')
            assert isinstance(result.success, bool)
            assert result.success is False  # All should fail without service
            assert isinstance(result.error, str)
            assert len(result.error) > 0

    def test_commands_handle_service_unavailable(self):
        """Test all terminal commands gracefully handle unavailable services."""
        mock_context = Mock(spec=CommandContext)
        mock_context.get_service.return_value = None  # No services available

        commands = [
            clear_terminal_handler,
            copy_terminal_handler,
            paste_terminal_handler,
            kill_terminal_handler,
            restart_terminal_handler,
        ]

        for command_func in commands:
            result = command_func(mock_context)

            assert result.success is False
            assert "not available" in result.error


class TestTerminalCommandsEdgeCases:
    """Test edge cases and boundary conditions for terminal commands."""

    def test_terminal_commands_with_widget_exceptions(self):
        """Test terminal commands handle widget method exceptions."""
        # ARRANGE - Terminal widget methods throw exceptions
        mock_context = Mock(spec=CommandContext)
        mock_workspace_service = Mock(spec=WorkspaceService)
        mock_terminal_widget = Mock()
        mock_terminal_widget.clear_terminal.side_effect = RuntimeError("Clear failed")
        mock_terminal_widget.copy_selection.side_effect = RuntimeError("Copy failed")
        mock_terminal_widget.restart_terminal.side_effect = RuntimeError("Restart failed")

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget

        # Test each command handles widget exceptions
        test_cases = [
            (clear_terminal_handler, "Failed to clear terminal"),
            (copy_terminal_handler, "Failed to copy"),
            (restart_terminal_handler, "Failed to restart terminal"),
        ]

        for command_func, expected_error in test_cases:
            result = command_func(mock_context)
            assert result.success is False
            assert expected_error in result.error

    @patch('PySide6.QtWidgets.QApplication.clipboard')
    def test_paste_terminal_handles_clipboard_exception(self, mock_clipboard):
        """Test paste_terminal_handler handles clipboard access exceptions."""
        # ARRANGE - Clipboard throws exception
        mock_context = Mock(spec=CommandContext)
        mock_workspace_service = Mock(spec=WorkspaceService)
        mock_terminal_widget = Mock()
        mock_clipboard.side_effect = RuntimeError("Clipboard error")

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_widget.return_value = mock_terminal_widget

        # ACT - Execute command
        result = paste_terminal_handler(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Failed to paste" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])