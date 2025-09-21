#!/usr/bin/env python3
"""
Tests to detect and verify fixes for Command Pattern violations.

These tests ensure that commands only call service methods and never bypass
the service layer to call UI components directly.
"""

import pytest
from unittest.mock import Mock, patch

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.core.commands.builtin.pane_commands import (
    split_pane_horizontal_command,
    split_pane_vertical_command,
    close_pane_command,
)
from viloapp.services.workspace_service import WorkspaceService


class TestCommandPatternCompliance:
    """Test that commands follow the Command Pattern correctly."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_service = Mock(spec=WorkspaceService)
        self.mock_workspace = Mock()
        self.mock_context = Mock(spec=CommandContext)
        self.mock_context.get_service.return_value = self.mock_service
        self.mock_context.args = {}

    def test_split_horizontal_command_uses_service_not_ui(self):
        """Test that split horizontal command calls service, not UI directly."""
        # Configure mock service
        self.mock_service.get_workspace.return_value = self.mock_workspace
        self.mock_service.split_active_pane.return_value = "new_pane_id"

        # Execute command
        result = split_pane_horizontal_command(self.mock_context)

        # Verify command used service interface
        self.mock_service.split_active_pane.assert_called_once_with("horizontal")

        # Verify command did NOT call UI directly
        assert not hasattr(self.mock_workspace, "split_active_pane_horizontal") or \
               not self.mock_workspace.split_active_pane_horizontal.called, \
               "Command should not call UI method directly"

        assert result.success, f"Command should succeed: {result.error}"

    def test_split_vertical_command_uses_service_not_ui(self):
        """Test that split vertical command calls service, not UI directly."""
        # Configure mock service
        self.mock_service.get_workspace.return_value = self.mock_workspace
        self.mock_service.split_active_pane.return_value = "new_pane_id"

        # Execute command
        result = split_pane_vertical_command(self.mock_context)

        # Verify command used service interface
        self.mock_service.split_active_pane.assert_called_once_with("vertical")

        # Verify command did NOT call UI directly
        assert not hasattr(self.mock_workspace, "split_active_pane_vertical") or \
               not self.mock_workspace.split_active_pane_vertical.called, \
               "Command should not call UI method directly"

        assert result.success, f"Command should succeed: {result.error}"

    def test_close_pane_command_uses_service_not_ui(self):
        """Test that close pane command calls service, not UI directly."""
        # Configure mock service
        self.mock_service.close_active_pane.return_value = True

        # Execute command
        result = close_pane_command(self.mock_context)

        # Verify command used service interface
        self.mock_service.close_active_pane.assert_called_once()

        # Verify command did NOT call UI directly
        assert not hasattr(self.mock_workspace, "close_active_pane") or \
               not self.mock_workspace.close_active_pane.called, \
               "Command should not call UI method directly"

        assert result.success, f"Command should succeed: {result.error}"

    def test_commands_return_operation_result_format(self):
        """Test that commands return proper CommandResult format."""
        # Test horizontal split
        self.mock_service.split_active_pane.return_value = "new_pane_id"
        result = split_pane_horizontal_command(self.mock_context)

        assert isinstance(result, CommandResult), "Should return CommandResult"
        assert result.success, "Should indicate success"
        assert result.value is not None, "Should include result data"

        # Test vertical split
        result = split_pane_vertical_command(self.mock_context)

        assert isinstance(result, CommandResult), "Should return CommandResult"
        assert result.success, "Should indicate success"
        assert result.value is not None, "Should include result data"

        # Test close pane
        self.mock_service.close_active_pane.return_value = True
        result = close_pane_command(self.mock_context)

        assert isinstance(result, CommandResult), "Should return CommandResult"
        assert result.success, "Should indicate success"

    @patch('viloapp.core.commands.builtin.pane_commands.logger')
    def test_commands_handle_service_errors_gracefully(self, mock_logger):
        """Test that commands handle service errors and return proper error results."""
        # Test service not available
        self.mock_context.get_service.return_value = None

        result = split_pane_horizontal_command(self.mock_context)
        assert not result.success, "Should fail when service unavailable"
        assert "WorkspaceService not available" in result.error

        # Test service exception
        self.mock_context.get_service.return_value = self.mock_service
        self.mock_service.split_active_pane.side_effect = Exception("Service error")

        result = split_pane_horizontal_command(self.mock_context)
        assert not result.success, "Should fail when service throws exception"
        assert "Service error" in result.error
        mock_logger.error.assert_called()


class TestViolationDetection:
    """Tests that detect specific violations that need to be fixed."""

    def test_detect_ui_bypass_violations(self):
        """Detect commands that bypass service layer and call UI directly."""
        # This test documents the current violations that need fixing
        violations = []

        # Check pane_commands.py for direct workspace calls
        with open('/home/kuja/GitHub/viloapp/packages/viloapp/src/viloapp/core/commands/builtin/pane_commands.py', 'r') as f:
            content = f.read()

            # These are the violations that need fixing:
            if 'workspace.split_active_pane_horizontal()' in content:
                violations.append("Line 46: workspace.split_active_pane_horizontal() - should call service")

            if 'workspace.split_active_pane_vertical()' in content:
                violations.append("Line 84: workspace.split_active_pane_vertical() - should call service")

            if 'split_widget.model.change_pane_type(' in content:
                violations.append("Line 247: split_widget.model.change_pane_type() - should call service")

        # Document violations for tracking
        if violations:
            pytest.fail(f"Command Pattern violations detected:\n" + "\n".join(violations))