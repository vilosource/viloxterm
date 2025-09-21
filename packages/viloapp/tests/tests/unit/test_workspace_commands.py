#!/usr/bin/env python3
"""
Unit tests for workspace commands.

Tests the new unified workspace.newTab commands and their integration
with the application defaults system.
"""

from unittest.mock import MagicMock, patch

import pytest

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.core.commands.builtin import workspace_commands
from viloapp.services.terminal_service import TerminalService
from viloapp.services.workspace_service import WorkspaceService


class TestNewTabCommand:
    """Test the unified workspace.newTab command."""

    @pytest.fixture
    def context(self):
        """Create a command context with mocked services."""
        context = CommandContext()
        context.main_window = MagicMock()
        context.workspace = MagicMock()
        context.args = {}
        return context

    @pytest.fixture
    def workspace_service(self):
        """Create a mocked WorkspaceService."""
        service = MagicMock(spec=WorkspaceService)
        service.add_terminal_tab.return_value = 0
        service.add_editor_tab.return_value = 0
        return service

    @pytest.fixture
    def terminal_service(self):
        """Create a mocked TerminalService."""
        service = MagicMock(spec=TerminalService)
        service.is_server_running.return_value = True
        return service

    @patch("viloapp.core.commands.builtin.workspace_commands.get_default_widget_type")
    def test_new_tab_uses_default_widget_type(
        self, mock_get_default, context, workspace_service
    ):
        """Test that new_tab_command uses the default widget type from settings."""
        mock_get_default.return_value = "editor"

        with patch.object(context, "get_service") as mock_get_service:
            mock_get_service.return_value = workspace_service

            result = workspace_commands.new_tab_command._original_func(context)

        assert result.success is True
        mock_get_default.assert_called_once()
        workspace_service.add_editor_tab.assert_called_once_with(None)

    def test_new_tab_with_explicit_widget_type(
        self, context, workspace_service, terminal_service
    ):
        """Test new_tab_command with explicit widget_type in args."""
        context.args["widget_type"] = "terminal"

        def get_service_side_effect(service_type):
            if service_type == WorkspaceService:
                return workspace_service
            elif service_type == TerminalService:
                return terminal_service
            return None

        with patch.object(context, "get_service", side_effect=get_service_side_effect):
            result = workspace_commands.new_tab_command._original_func(context)

        assert result.success is True
        workspace_service.add_terminal_tab.assert_called_once_with(None)

    def test_new_tab_starts_terminal_server(
        self, context, workspace_service, terminal_service
    ):
        """Test that terminal server is started when creating terminal tab."""
        context.args["widget_type"] = "terminal"
        terminal_service.is_server_running.return_value = False

        def get_service_side_effect(service_type):
            if service_type == WorkspaceService:
                return workspace_service
            elif service_type == TerminalService:
                return terminal_service
            return None

        with patch.object(context, "get_service", side_effect=get_service_side_effect):
            result = workspace_commands.new_tab_command._original_func(context)

        assert result.success is True
        terminal_service.start_server.assert_called_once()
        workspace_service.add_terminal_tab.assert_called_once()

    def test_new_tab_with_custom_name(self, context, workspace_service):
        """Test creating a new tab with a custom name."""
        context.args = {"widget_type": "editor", "name": "My Custom Editor"}

        with patch.object(context, "get_service", return_value=workspace_service):
            result = workspace_commands.new_tab_command._original_func(context)

        assert result.success is True
        workspace_service.add_editor_tab.assert_called_once_with("My Custom Editor")

    def test_new_tab_no_workspace_service(self, context):
        """Test handling when WorkspaceService is not available."""
        with patch.object(context, "get_service", return_value=None):
            result = workspace_commands.new_tab_command._original_func(context)

        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_new_tab_with_settings_widget(self, context, workspace_service):
        """Test creating a Settings tab."""
        context.args["widget_type"] = "settings"
        workspace_service.add_app_widget.return_value = True
        workspace_service.get_tab_count.return_value = 3

        with patch.object(context, "get_service", return_value=workspace_service):
            result = workspace_commands.new_tab_command._original_func(context)

        assert result.success is True
        assert result.value["index"] == 2  # get_tab_count returns 3, so index is 2
        assert result.value["widget_type"] == "settings"

        # Verify add_app_widget was called with correct parameters
        from viloapp.ui.widgets.widget_registry import WidgetType

        workspace_service.add_app_widget.assert_called_once_with(
            WidgetType.SETTINGS, "com.viloapp.settings", None
        )


class TestNewTabWithTypeCommand:
    """Test the workspace.newTabWithType command."""

    @pytest.fixture
    def context(self):
        """Create a command context."""
        context = CommandContext()
        context.main_window = MagicMock()
        context.args = {}
        return context

    def test_new_tab_with_type_programmatic(self, context):
        """Test programmatic use with widget_type in args."""
        context.args["widget_type"] = "editor"

        with patch.object(
            workspace_commands.new_tab_command, "_original_func"
        ) as mock_new_tab:
            mock_new_tab.return_value = CommandResult(success=True)

            result = workspace_commands.new_tab_with_type_command._original_func(
                context
            )

        assert result.success is True
        mock_new_tab.assert_called_once_with(context)
        assert context.args["widget_type"] == "editor"

    @patch("PySide6.QtWidgets.QInputDialog.getItem")
    def test_new_tab_with_type_dialog(self, mock_dialog, context):
        """Test showing widget type selection dialog."""
        mock_dialog.return_value = ("Terminal", True)

        with patch.object(
            workspace_commands.new_tab_command, "_original_func"
        ) as mock_new_tab:
            mock_new_tab.return_value = CommandResult(success=True)

            result = workspace_commands.new_tab_with_type_command._original_func(
                context
            )

        assert result.success is True
        mock_dialog.assert_called_once()
        assert context.args["widget_type"] == "terminal"
        mock_new_tab.assert_called_once()

    @patch("PySide6.QtWidgets.QInputDialog.getItem")
    def test_new_tab_with_type_dialog_cancelled(self, mock_dialog, context):
        """Test when user cancels the dialog."""
        mock_dialog.return_value = ("", False)  # User cancelled

        result = workspace_commands.new_tab_with_type_command._original_func(context)

        assert result.success is False
        assert "User cancelled" in result.error

    def test_new_tab_with_type_no_widget_no_window(self, context):
        """Test when no widget type provided and no main window."""
        context.main_window = None
        context.args = {}

        result = workspace_commands.new_tab_with_type_command._original_func(context)

        assert result.success is False
        assert "Widget type must be specified" in result.error
        assert "available_types" in result.value

    @patch("PySide6.QtWidgets.QInputDialog.getItem")
    def test_new_tab_with_type_all_widget_types(self, mock_dialog, context):
        """Test that all widget types are available in dialog."""
        mock_dialog.return_value = ("Settings", True)

        with patch.object(
            workspace_commands.new_tab_command, "_original_func"
        ) as mock_new_tab:
            mock_new_tab.return_value = CommandResult(success=True)

            workspace_commands.new_tab_with_type_command._original_func(context)

        # Check that Settings was mapped correctly
        assert context.args["widget_type"] == "settings"

        # Verify dialog was called with all widget types
        call_args = mock_dialog.call_args[0]
        widget_types = call_args[3]  # Fourth argument is the list of items
        assert "Terminal" in widget_types
        assert "Editor" in widget_types
        assert "Theme Editor" in widget_types
        assert "Explorer" in widget_types
        assert "Settings" in widget_types


class TestCommandIntegration:
    """Test integration between commands and services."""

    @patch("viloapp.core.commands.builtin.workspace_commands.get_default_widget_type")
    def test_full_flow_with_defaults(self, mock_get_default):
        """Test the full flow from command to service with defaults."""
        mock_get_default.return_value = "editor"

        context = CommandContext()
        workspace_service = MagicMock(spec=WorkspaceService)
        workspace_service.add_editor_tab.return_value = 2

        with patch.object(context, "get_service", return_value=workspace_service):
            result = workspace_commands.new_tab_command._original_func(context)

        assert result.success is True
        assert result.value["index"] == 2
        assert result.value["widget_type"] == "editor"

    def test_error_handling_in_command(self):
        """Test error handling when service throws exception."""
        context = CommandContext()
        workspace_service = MagicMock(spec=WorkspaceService)
        workspace_service.add_terminal_tab.side_effect = Exception("Test error")
        terminal_service = MagicMock(spec=TerminalService)
        terminal_service.is_server_running.return_value = True

        context.args = {"widget_type": "terminal"}

        def get_service_side_effect(service_type):
            if service_type == WorkspaceService:
                return workspace_service
            elif service_type == TerminalService:
                return terminal_service
            return None

        with patch.object(context, "get_service", side_effect=get_service_side_effect):
            result = workspace_commands.new_tab_command._original_func(context)

        assert result.success is False
        assert "Test error" in result.error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
