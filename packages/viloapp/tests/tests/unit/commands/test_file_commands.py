#!/usr/bin/env python3
"""
Unit tests for file_commands.py

Tests verify that file commands properly delegate to services
and follow the MVC architecture patterns. Focus is on service delegation
and proper UI service usage for status messages.
"""

from unittest.mock import Mock

import pytest

from viloapp.core.commands.base import CommandContext
from viloapp.core.commands.builtin.file_commands import (
    replace_with_editor_command,
    replace_with_terminal_command,
    restore_state_command,
    save_state_command,
)
from viloapp.services.state_service import StateService
from viloapp.services.ui_service import UIService
from viloapp.services.workspace_service import WorkspaceService


class TestSaveStateCommand:
    """Test save_state_command delegates properly to StateService and UIService."""

    @pytest.fixture
    def mock_context(self):
        """Create mock command context."""
        context = Mock(spec=CommandContext)
        context.args = {}
        return context

    @pytest.fixture
    def mock_state_service(self):
        """Create mock StateService."""
        service = Mock(spec=StateService)
        service.save_all_state = Mock()
        return service

    @pytest.fixture
    def mock_ui_service(self):
        """Create mock UIService."""
        service = Mock(spec=UIService)
        service.set_status_message = Mock()
        return service

    def test_save_state_uses_services(self, mock_context, mock_state_service, mock_ui_service):
        """Test that save_state_command uses StateService.save_all_state() and UIService.set_status_message()."""

        # ARRANGE - Setup service delegation
        def get_service_side_effect(service_type):
            if service_type == StateService:
                return mock_state_service
            elif service_type == UIService:
                return mock_ui_service
            return None

        mock_context.get_service.side_effect = get_service_side_effect

        # ACT - Execute command
        result = save_state_command(mock_context)

        # ASSERT - Verify service delegation
        assert result.success is True
        mock_context.get_service.assert_any_call(StateService)
        mock_context.get_service.assert_any_call(UIService)
        mock_state_service.save_all_state.assert_called_once()
        mock_ui_service.set_status_message.assert_called_once_with("State saved", 2000)

    def test_save_state_handles_no_state_service(self, mock_context):
        """Test save_state_command handles StateService unavailable."""
        # ARRANGE - No StateService
        mock_context.get_service.return_value = None

        # ACT - Execute command
        result = save_state_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "StateService not available" in result.error

    def test_save_state_works_without_ui_service(self, mock_context, mock_state_service):
        """Test save_state_command works even when UIService unavailable."""

        # ARRANGE - StateService available but no UIService
        def get_service_side_effect(service_type):
            if service_type == StateService:
                return mock_state_service
            elif service_type == UIService:
                return None  # No UI service
            return None

        mock_context.get_service.side_effect = get_service_side_effect

        # ACT - Execute command
        result = save_state_command(mock_context)

        # ASSERT - Should still succeed without UI service
        assert result.success is True
        mock_state_service.save_all_state.assert_called_once()

    def test_save_state_handles_exception(self, mock_context, mock_state_service):
        """Test save_state_command handles exceptions from StateService."""

        # ARRANGE - StateService throws exception
        def get_service_side_effect(service_type):
            if service_type == StateService:
                return mock_state_service
            return None

        mock_context.get_service.side_effect = get_service_side_effect
        mock_state_service.save_all_state.side_effect = RuntimeError("Save failed")

        # ACT - Execute command
        result = save_state_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Save failed" in result.error


class TestRestoreStateCommand:
    """Test restore_state_command delegates properly to StateService and UIService."""

    @pytest.fixture
    def mock_context(self):
        """Create mock command context."""
        context = Mock(spec=CommandContext)
        context.args = {}
        return context

    @pytest.fixture
    def mock_state_service(self):
        """Create mock StateService."""
        service = Mock(spec=StateService)
        service.restore_all_state = Mock(return_value=True)
        return service

    @pytest.fixture
    def mock_ui_service(self):
        """Create mock UIService."""
        service = Mock(spec=UIService)
        service.set_status_message = Mock()
        return service

    def test_restore_state_uses_services(self, mock_context, mock_state_service, mock_ui_service):
        """Test that restore_state_command uses StateService.restore_all_state() and UIService.set_status_message()."""

        # ARRANGE - Setup service delegation
        def get_service_side_effect(service_type):
            if service_type == StateService:
                return mock_state_service
            elif service_type == UIService:
                return mock_ui_service
            return None

        mock_context.get_service.side_effect = get_service_side_effect

        # ACT - Execute command
        result = restore_state_command(mock_context)

        # ASSERT - Verify service delegation
        assert result.success is True
        mock_context.get_service.assert_any_call(StateService)
        mock_context.get_service.assert_any_call(UIService)
        mock_state_service.restore_all_state.assert_called_once()
        mock_ui_service.set_status_message.assert_called_once_with("State restored", 2000)

    def test_restore_state_handles_no_saved_state(
        self, mock_context, mock_state_service, mock_ui_service
    ):
        """Test restore_state_command handles when no saved state found."""

        # ARRANGE - StateService returns False (no saved state)
        def get_service_side_effect(service_type):
            if service_type == StateService:
                return mock_state_service
            elif service_type == UIService:
                return mock_ui_service
            return None

        mock_context.get_service.side_effect = get_service_side_effect
        mock_state_service.restore_all_state.return_value = False

        # ACT - Execute command
        result = restore_state_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No saved state found" in result.error

    def test_restore_state_handles_no_state_service(self, mock_context):
        """Test restore_state_command handles StateService unavailable."""
        # ARRANGE - No StateService
        mock_context.get_service.return_value = None

        # ACT - Execute command
        result = restore_state_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "StateService not available" in result.error

    def test_restore_state_works_without_ui_service(self, mock_context, mock_state_service):
        """Test restore_state_command works even when UIService unavailable."""

        # ARRANGE - StateService available but no UIService
        def get_service_side_effect(service_type):
            if service_type == StateService:
                return mock_state_service
            elif service_type == UIService:
                return None  # No UI service
            return None

        mock_context.get_service.side_effect = get_service_side_effect

        # ACT - Execute command
        result = restore_state_command(mock_context)

        # ASSERT - Should still succeed without UI service
        assert result.success is True
        mock_state_service.restore_all_state.assert_called_once()

    def test_restore_state_handles_exception(self, mock_context, mock_state_service):
        """Test restore_state_command handles exceptions from StateService."""

        # ARRANGE - StateService throws exception
        def get_service_side_effect(service_type):
            if service_type == StateService:
                return mock_state_service
            return None

        mock_context.get_service.side_effect = get_service_side_effect
        mock_state_service.restore_all_state.side_effect = RuntimeError("Restore failed")

        # ACT - Execute command
        result = restore_state_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Restore failed" in result.error


class TestReplaceWithTerminalCommand:
    """Test replace_with_terminal_command delegates properly to WorkspaceService."""

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

    @pytest.fixture
    def mock_split_widget(self):
        """Create mock split widget."""
        split_widget = Mock()
        split_widget.model = Mock()
        split_widget.model.change_pane_type = Mock(return_value=True)
        split_widget.refresh_view = Mock()
        return split_widget

    def test_replace_with_terminal_uses_workspace_service(
        self, mock_context, mock_workspace_service, mock_split_widget
    ):
        """Test that replace_with_terminal_command uses workspace_service.get_current_split_widget()."""
        # ARRANGE - Setup service delegation
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget
        mock_context.args = {"pane_id": "pane123"}

        # ACT - Execute command
        result = replace_with_terminal_command(mock_context)

        # ASSERT - Verify service delegation
        assert result.success is True
        mock_context.get_service.assert_called_once_with(WorkspaceService)
        mock_workspace_service.get_current_split_widget.assert_called_once()
        mock_split_widget.model.change_pane_type.assert_called_once()
        mock_split_widget.refresh_view.assert_called_once()

    def test_replace_with_terminal_handles_no_workspace_service(self, mock_context):
        """Test replace_with_terminal_command handles WorkspaceService unavailable."""
        # ARRANGE - No WorkspaceService
        mock_context.get_service.return_value = None

        # ACT - Execute command
        result = replace_with_terminal_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_replace_with_terminal_handles_no_split_widget(
        self, mock_context, mock_workspace_service
    ):
        """Test replace_with_terminal_command when no split widget available."""
        # ARRANGE - No split widget
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = None

        # ACT - Execute command
        result = replace_with_terminal_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No split widget available" in result.error

    def test_replace_with_terminal_handles_split_widget_no_model(
        self, mock_context, mock_workspace_service
    ):
        """Test replace_with_terminal_command when split widget has no model."""
        # ARRANGE - Split widget without model
        mock_split_widget = Mock()
        # Don't add model attribute
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget

        # ACT - Execute command
        result = replace_with_terminal_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No split widget available" in result.error

    def test_replace_with_terminal_extracts_pane_id_from_pane(
        self, mock_context, mock_workspace_service, mock_split_widget
    ):
        """Test replace_with_terminal_command extracts pane_id from pane object."""
        # ARRANGE - Setup pane object with leaf_node.id
        mock_pane = Mock()
        mock_pane.leaf_node = Mock()
        mock_pane.leaf_node.id = "extracted_pane_id"

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget
        mock_context.args = {"pane": mock_pane}  # No pane_id, but has pane

        # ACT - Execute command
        result = replace_with_terminal_command(mock_context)

        # ASSERT - Should extract pane_id from pane and succeed
        assert result.success is True
        mock_split_widget.model.change_pane_type.assert_called_once()

    def test_replace_with_terminal_handles_no_pane_id(
        self, mock_context, mock_workspace_service, mock_split_widget
    ):
        """Test replace_with_terminal_command when no pane_id can be determined."""
        # ARRANGE - No pane_id or pane in args
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget
        # mock_context.args = {}  # No pane_id or pane

        # ACT - Execute command
        result = replace_with_terminal_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Could not identify pane for replacement" in result.error

    def test_replace_with_terminal_handles_change_pane_type_failure(
        self, mock_context, mock_workspace_service, mock_split_widget
    ):
        """Test replace_with_terminal_command when change_pane_type fails."""
        # ARRANGE - change_pane_type returns False
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget
        mock_split_widget.model.change_pane_type.return_value = False
        mock_context.args = {"pane_id": "pane123"}

        # ACT - Execute command
        result = replace_with_terminal_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Could not identify pane for replacement" in result.error

    def test_replace_with_terminal_handles_exception(self, mock_context, mock_workspace_service):
        """Test replace_with_terminal_command handles exceptions."""
        # ARRANGE - Exception from service
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.side_effect = RuntimeError("Widget error")

        # ACT - Execute command
        result = replace_with_terminal_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Widget error" in result.error


class TestReplaceWithEditorCommand:
    """Test replace_with_editor_command delegates properly to WorkspaceService."""

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

    @pytest.fixture
    def mock_split_widget(self):
        """Create mock split widget."""
        split_widget = Mock()
        split_widget.model = Mock()
        split_widget.model.change_pane_type = Mock(return_value=True)
        split_widget.refresh_view = Mock()
        return split_widget

    def test_replace_with_editor_uses_workspace_service(
        self, mock_context, mock_workspace_service, mock_split_widget
    ):
        """Test that replace_with_editor_command uses workspace_service.get_current_split_widget()."""
        # ARRANGE - Setup service delegation
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget
        mock_context.args = {"pane_id": "pane123"}

        # ACT - Execute command
        result = replace_with_editor_command(mock_context)

        # ASSERT - Verify service delegation
        assert result.success is True
        mock_context.get_service.assert_called_once_with(WorkspaceService)
        mock_workspace_service.get_current_split_widget.assert_called_once()
        mock_split_widget.model.change_pane_type.assert_called_once()
        mock_split_widget.refresh_view.assert_called_once()

    def test_replace_with_editor_handles_no_workspace_service(self, mock_context):
        """Test replace_with_editor_command handles WorkspaceService unavailable."""
        # ARRANGE - No WorkspaceService
        mock_context.get_service.return_value = None

        # ACT - Execute command
        result = replace_with_editor_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_replace_with_editor_handles_no_split_widget(
        self, mock_context, mock_workspace_service
    ):
        """Test replace_with_editor_command when no split widget available."""
        # ARRANGE - No split widget
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = None

        # ACT - Execute command
        result = replace_with_editor_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "No split widget available" in result.error

    def test_replace_with_editor_extracts_pane_id_from_pane(
        self, mock_context, mock_workspace_service, mock_split_widget
    ):
        """Test replace_with_editor_command extracts pane_id from pane object."""
        # ARRANGE - Setup pane object with leaf_node.id
        mock_pane = Mock()
        mock_pane.leaf_node = Mock()
        mock_pane.leaf_node.id = "extracted_pane_id"

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget
        mock_context.args = {"pane": mock_pane}  # No pane_id, but has pane

        # ACT - Execute command
        result = replace_with_editor_command(mock_context)

        # ASSERT - Should extract pane_id from pane and succeed
        assert result.success is True
        mock_split_widget.model.change_pane_type.assert_called_once()

    def test_replace_with_editor_handles_no_pane_id(
        self, mock_context, mock_workspace_service, mock_split_widget
    ):
        """Test replace_with_editor_command when no pane_id can be determined."""
        # ARRANGE - No pane_id or pane in args
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget
        # mock_context.args = {}  # No pane_id or pane

        # ACT - Execute command
        result = replace_with_editor_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Could not identify pane for replacement" in result.error

    def test_replace_with_editor_handles_change_pane_type_failure(
        self, mock_context, mock_workspace_service, mock_split_widget
    ):
        """Test replace_with_editor_command when change_pane_type fails."""
        # ARRANGE - change_pane_type returns False
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget
        mock_split_widget.model.change_pane_type.return_value = False
        mock_context.args = {"pane_id": "pane123"}

        # ACT - Execute command
        result = replace_with_editor_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Could not identify pane for replacement" in result.error

    def test_replace_with_editor_handles_exception(self, mock_context, mock_workspace_service):
        """Test replace_with_editor_command handles exceptions."""
        # ARRANGE - Exception from service
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.side_effect = RuntimeError("Widget error")

        # ACT - Execute command
        result = replace_with_editor_command(mock_context)

        # ASSERT - Verify error handling
        assert result.success is False
        assert "Widget error" in result.error


class TestFileCommandsMVCCompliance:
    """Test that file commands follow MVC architecture patterns."""

    def test_commands_use_services_not_direct_ui(self):
        """Test that all file commands use services instead of direct UI access."""
        mock_context = Mock(spec=CommandContext)
        mock_context.args = {}

        # Mock services
        mock_state_service = Mock(spec=StateService)
        mock_ui_service = Mock(spec=UIService)
        mock_workspace_service = Mock(spec=WorkspaceService)

        def get_service_side_effect(service_type):
            if service_type == StateService:
                return mock_state_service
            elif service_type == UIService:
                return mock_ui_service
            elif service_type == WorkspaceService:
                return mock_workspace_service
            return None

        mock_context.get_service.side_effect = get_service_side_effect

        # Test each command uses appropriate services
        commands_to_test = [
            (save_state_command, StateService),
            (restore_state_command, StateService),
            (replace_with_terminal_command, WorkspaceService),
            (replace_with_editor_command, WorkspaceService),
        ]

        for command_func, expected_service in commands_to_test:
            mock_context.get_service.reset_mock()

            # Setup specific mocks based on command
            if command_func in [replace_with_terminal_command, replace_with_editor_command]:
                mock_context.args = {"pane_id": "test_pane"}
                mock_split_widget = Mock()
                mock_split_widget.model = Mock()
                mock_split_widget.model.change_pane_type = Mock(return_value=True)
                mock_split_widget.refresh_view = Mock()
                mock_workspace_service.get_current_split_widget.return_value = mock_split_widget
            else:
                mock_context.args = {}
                mock_state_service.save_all_state = Mock()
                mock_state_service.restore_all_state = Mock(return_value=True)
                mock_ui_service.set_status_message = Mock()

            result = command_func(mock_context)

            # Verify service was requested (MVC compliance)
            assert result.success is True
            mock_context.get_service.assert_any_call(expected_service)

    def test_commands_return_proper_command_results(self):
        """Test that all file commands return proper CommandResult objects."""
        mock_context = Mock(spec=CommandContext)
        mock_context.get_service.return_value = None  # Force error path
        mock_context.args = {}

        commands = [
            save_state_command,
            restore_state_command,
            replace_with_terminal_command,
            replace_with_editor_command,
        ]

        for command_func in commands:
            result = command_func(mock_context)

            # Verify proper CommandResult structure
            assert hasattr(result, "success")
            assert hasattr(result, "error")
            assert isinstance(result.success, bool)
            assert result.success is False  # All should fail without service
            assert isinstance(result.error, str)
            assert len(result.error) > 0

    def test_commands_handle_service_unavailable(self):
        """Test all file commands gracefully handle unavailable services."""
        mock_context = Mock(spec=CommandContext)
        mock_context.get_service.return_value = None
        mock_context.args = {}

        commands = [
            save_state_command,
            restore_state_command,
            replace_with_terminal_command,
            replace_with_editor_command,
        ]

        for command_func in commands:
            result = command_func(mock_context)

            assert result.success is False
            assert "not available" in result.error


class TestFileCommandsEdgeCases:
    """Test edge cases and boundary conditions for file commands."""

    def test_state_commands_with_service_exceptions(self):
        """Test state commands handle service method exceptions."""
        mock_context = Mock(spec=CommandContext)
        mock_context.args = {}

        # Test save_state_command with exception
        mock_state_service = Mock(spec=StateService)
        mock_state_service.save_all_state.side_effect = RuntimeError("Save exception")
        mock_context.get_service.return_value = mock_state_service

        result = save_state_command(mock_context)
        assert result.success is False
        assert "Save exception" in result.error

        # Test restore_state_command with exception
        mock_state_service.save_all_state.side_effect = None  # Reset
        mock_state_service.restore_all_state.side_effect = RuntimeError("Restore exception")

        result = restore_state_command(mock_context)
        assert result.success is False
        assert "Restore exception" in result.error

    def test_replace_commands_with_invalid_pane_objects(self):
        """Test replace commands handle invalid pane objects."""
        mock_context = Mock(spec=CommandContext)
        mock_workspace_service = Mock(spec=WorkspaceService)
        mock_split_widget = Mock()
        mock_split_widget.model = Mock()
        mock_split_widget.model.change_pane_type = Mock(return_value=True)
        mock_split_widget.refresh_view = Mock()

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget

        # Test with pane that doesn't have leaf_node
        mock_pane_no_leaf = Mock()
        # Don't add leaf_node attribute
        mock_context.args = {"pane": mock_pane_no_leaf}

        result = replace_with_terminal_command(mock_context)
        assert result.success is False
        assert "Could not identify pane for replacement" in result.error

        # Test with pane that has leaf_node but no id
        mock_pane_no_id = Mock()
        mock_pane_no_id.leaf_node = Mock()
        # Don't add id attribute
        mock_context.args = {"pane": mock_pane_no_id}

        result = replace_with_editor_command(mock_context)
        assert result.success is False
        assert "Could not identify pane for replacement" in result.error

    def test_replace_commands_with_various_pane_id_types(self):
        """Test replace commands handle different pane_id types."""
        mock_context = Mock(spec=CommandContext)
        mock_workspace_service = Mock(spec=WorkspaceService)
        mock_split_widget = Mock()
        mock_split_widget.model = Mock()
        mock_split_widget.model.change_pane_type = Mock(return_value=True)
        mock_split_widget.refresh_view = Mock()

        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_split_widget.return_value = mock_split_widget

        # Test various pane_id types
        test_cases = [
            "string_pane_id",
            123,  # Integer pane_id
            None,  # None pane_id (should fail)
            "",  # Empty string pane_id
        ]

        for pane_id in test_cases:
            mock_context.args = {"pane_id": pane_id}
            mock_split_widget.model.change_pane_type.reset_mock()

            result = replace_with_terminal_command(mock_context)

            if pane_id is None or pane_id == "":
                # Should fail for None or empty string
                if pane_id == "":
                    # Empty string is still a valid pane_id
                    assert result.success is True
                else:
                    # None should fail
                    assert result.success is False
            else:
                # Should succeed for valid pane_ids
                assert result.success is True
                mock_split_widget.model.change_pane_type.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
