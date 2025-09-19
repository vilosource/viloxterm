#!/usr/bin/env python3
"""
Unit tests for tab_commands.py

Tests verify that the tab management commands properly delegate to services
and follow the MVC architecture patterns. Focus is on service delegation
rather than complex UI interactions.
"""

from unittest.mock import Mock
import pytest

from core.commands.base import CommandContext
from core.commands.builtin.tab_commands import (
    duplicate_tab_command,
    close_tabs_to_right_command,
    rename_tab_command,
    close_other_tabs_command,
)
from services.workspace_service import WorkspaceService


class TestDuplicateTabCommand:
    """Test duplicate_tab_command delegates properly to WorkspaceService."""

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
        service.get_workspace.return_value = Mock()
        service.get_current_tab_index.return_value = 0
        service.duplicate_tab.return_value = 2
        return service

    def test_duplicate_tab_uses_workspace_service(
        self, mock_context, mock_workspace_service
    ):
        """Test that duplicate_tab_command delegates to WorkspaceService."""
        # Mock the service
        mock_context.get_service.return_value = mock_workspace_service

        # Test with tab_index in args
        mock_context.args = {"tab_index": 1}
        result = duplicate_tab_command(mock_context)

        # Verify service delegation
        assert result.success is True
        mock_workspace_service.duplicate_tab.assert_called_once_with(1)
        assert result.value["duplicated_tab"] == 1
        assert result.value["new_index"] == 2

    def test_duplicate_tab_uses_current_tab_when_no_index(
        self, mock_context, mock_workspace_service
    ):
        """Test duplicate_tab_command uses current tab when no index provided."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_tab_index.return_value = 3

        # No tab_index in args
        result = duplicate_tab_command(mock_context)

        # Should get current tab index then duplicate it
        assert result.success is True
        mock_workspace_service.get_current_tab_index.assert_called_once()
        mock_workspace_service.duplicate_tab.assert_called_once_with(3)
        assert result.value["duplicated_tab"] == 3

    def test_duplicate_tab_handles_service_unavailable(self, mock_context):
        """Test duplicate_tab_command handles WorkspaceService unavailable."""
        mock_context.get_service.return_value = None

        result = duplicate_tab_command(mock_context)

        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_duplicate_tab_handles_no_workspace(
        self, mock_context, mock_workspace_service
    ):
        """Test duplicate_tab_command handles no workspace available."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_workspace.return_value = None

        result = duplicate_tab_command(mock_context)

        assert result.success is False
        assert "No workspace available" in result.error

    def test_duplicate_tab_handles_exception(
        self, mock_context, mock_workspace_service
    ):
        """Test duplicate_tab_command handles exceptions properly."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.duplicate_tab.side_effect = Exception("Test error")
        mock_context.args = {"tab_index": 1}

        result = duplicate_tab_command(mock_context)

        assert result.success is False
        assert "Test error" in result.error


class TestCloseTabsToRightCommand:
    """Test close_tabs_to_right_command delegates properly to WorkspaceService."""

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
        service.get_workspace.return_value = Mock()
        service.get_current_tab_index.return_value = 0
        service.close_tabs_to_right.return_value = 3
        return service

    def test_close_tabs_to_right_uses_workspace_service(
        self, mock_context, mock_workspace_service
    ):
        """Test that close_tabs_to_right_command delegates to WorkspaceService."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {"tab_index": 2}

        result = close_tabs_to_right_command(mock_context)

        assert result.success is True
        mock_workspace_service.close_tabs_to_right.assert_called_once_with(2)
        assert result.value["closed_from_index"] == 3  # tab_index + 1
        assert result.value["closed_count"] == 3

    def test_close_tabs_to_right_uses_current_tab_when_no_index(
        self, mock_context, mock_workspace_service
    ):
        """Test close_tabs_to_right_command uses current tab when no index."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_tab_index.return_value = 1
        mock_workspace_service.close_tabs_to_right.return_value = 2

        result = close_tabs_to_right_command(mock_context)

        assert result.success is True
        mock_workspace_service.get_current_tab_index.assert_called_once()
        mock_workspace_service.close_tabs_to_right.assert_called_once_with(1)
        assert result.value["closed_from_index"] == 2

    def test_close_tabs_to_right_handles_service_unavailable(self, mock_context):
        """Test close_tabs_to_right_command handles WorkspaceService unavailable."""
        mock_context.get_service.return_value = None

        result = close_tabs_to_right_command(mock_context)

        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_close_tabs_to_right_handles_no_workspace(
        self, mock_context, mock_workspace_service
    ):
        """Test close_tabs_to_right_command handles no workspace available."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_workspace.return_value = None

        result = close_tabs_to_right_command(mock_context)

        assert result.success is False
        assert "No workspace available" in result.error

    def test_close_tabs_to_right_handles_exception(
        self, mock_context, mock_workspace_service
    ):
        """Test close_tabs_to_right_command handles exceptions properly."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.close_tabs_to_right.side_effect = Exception("Test error")
        mock_context.args = {"tab_index": 1}

        result = close_tabs_to_right_command(mock_context)

        assert result.success is False
        assert "Test error" in result.error


class TestRenameTabCommand:
    """Test rename_tab_command delegates properly to WorkspaceService."""

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
        service.get_workspace.return_value = Mock()
        service.get_current_tab_index.return_value = 0
        service.rename_tab.return_value = True
        return service

    def test_rename_tab_with_new_name_uses_workspace_service(
        self, mock_context, mock_workspace_service
    ):
        """Test rename_tab_command with new_name delegates to WorkspaceService."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {"tab_index": 1, "new_name": "My Tab"}

        result = rename_tab_command(mock_context)

        assert result.success is True
        mock_workspace_service.rename_tab.assert_called_once_with(1, "My Tab")
        assert result.value["tab_index"] == 1
        assert result.value["new_name"] == "My Tab"

    def test_rename_tab_uses_current_tab_when_no_index(
        self, mock_context, mock_workspace_service
    ):
        """Test rename_tab_command uses current tab when no index provided."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_tab_index.return_value = 2
        mock_context.args = {"new_name": "Custom Name"}

        result = rename_tab_command(mock_context)

        assert result.success is True
        mock_workspace_service.get_current_tab_index.assert_called_once()
        mock_workspace_service.rename_tab.assert_called_once_with(2, "Custom Name")

    def test_rename_tab_interactive_mode_fallback(
        self, mock_context, mock_workspace_service
    ):
        """Test rename_tab_command falls back to interactive mode."""
        mock_workspace = Mock()
        mock_workspace.tab_widget.tabText.return_value = "Current Tab"
        mock_workspace_service.get_workspace.return_value = mock_workspace
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {"tab_index": 1}  # No new_name

        result = rename_tab_command(mock_context)

        assert result.success is True
        assert result.value["tab_index"] == 1
        assert result.value["mode"] == "interactive"
        mock_workspace.start_tab_rename.assert_called_once_with(1, "Current Tab")

    def test_rename_tab_handles_rename_failure(
        self, mock_context, mock_workspace_service
    ):
        """Test rename_tab_command handles rename failure from service."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.rename_tab.return_value = False
        mock_context.args = {"tab_index": 1, "new_name": "My Tab"}

        result = rename_tab_command(mock_context)

        assert result.success is False
        assert "Failed to rename tab" in result.error

    def test_rename_tab_handles_service_unavailable(self, mock_context):
        """Test rename_tab_command handles WorkspaceService unavailable."""
        mock_context.get_service.return_value = None

        result = rename_tab_command(mock_context)

        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_rename_tab_handles_no_workspace(
        self, mock_context, mock_workspace_service
    ):
        """Test rename_tab_command handles no workspace available."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_workspace.return_value = None

        result = rename_tab_command(mock_context)

        assert result.success is False
        assert "No workspace available" in result.error

    def test_rename_tab_handles_exception(
        self, mock_context, mock_workspace_service
    ):
        """Test rename_tab_command handles exceptions properly."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.rename_tab.side_effect = Exception("Test error")
        mock_context.args = {"tab_index": 1, "new_name": "My Tab"}

        result = rename_tab_command(mock_context)

        assert result.success is False
        assert "Test error" in result.error


class TestCloseOtherTabsCommand:
    """Test close_other_tabs_command delegates properly to WorkspaceService."""

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
        service.get_workspace.return_value = Mock()
        service.get_current_tab_index.return_value = 1
        service.close_other_tabs.return_value = 4
        return service

    def test_close_other_tabs_uses_workspace_service(
        self, mock_context, mock_workspace_service
    ):
        """Test that close_other_tabs_command delegates to WorkspaceService."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {"tab_index": 2}

        result = close_other_tabs_command(mock_context)

        assert result.success is True
        mock_workspace_service.close_other_tabs.assert_called_once_with(2)
        assert result.value["kept_tab"] == 2
        assert result.value["closed_count"] == 4

    def test_close_other_tabs_uses_current_tab_when_no_index(
        self, mock_context, mock_workspace_service
    ):
        """Test close_other_tabs_command uses current tab when no index provided."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_current_tab_index.return_value = 3
        mock_workspace_service.close_other_tabs.return_value = 2

        result = close_other_tabs_command(mock_context)

        assert result.success is True
        mock_workspace_service.get_current_tab_index.assert_called_once()
        mock_workspace_service.close_other_tabs.assert_called_once_with(3)
        assert result.value["kept_tab"] == 3
        assert result.value["closed_count"] == 2

    def test_close_other_tabs_handles_service_unavailable(self, mock_context):
        """Test close_other_tabs_command handles WorkspaceService unavailable."""
        mock_context.get_service.return_value = None

        result = close_other_tabs_command(mock_context)

        assert result.success is False
        assert "WorkspaceService not available" in result.error

    def test_close_other_tabs_handles_no_workspace(
        self, mock_context, mock_workspace_service
    ):
        """Test close_other_tabs_command handles no workspace available."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.get_workspace.return_value = None

        result = close_other_tabs_command(mock_context)

        assert result.success is False
        assert "No workspace available" in result.error

    def test_close_other_tabs_handles_exception(
        self, mock_context, mock_workspace_service
    ):
        """Test close_other_tabs_command handles exceptions properly."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.close_other_tabs.side_effect = Exception("Test error")
        mock_context.args = {"tab_index": 1}

        result = close_other_tabs_command(mock_context)

        assert result.success is False
        assert "Test error" in result.error


class TestTabCommandsEdgeCases:
    """Test edge cases and boundary conditions for tab commands."""

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
        service.get_workspace.return_value = Mock()
        return service

    def test_tab_commands_with_negative_index(
        self, mock_context, mock_workspace_service
    ):
        """Test tab commands handle negative tab indices."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {"tab_index": -1}

        # Test with duplicate_tab_command
        mock_workspace_service.duplicate_tab.return_value = 0
        result = duplicate_tab_command(mock_context)
        assert result.success is True
        mock_workspace_service.duplicate_tab.assert_called_with(-1)

    def test_tab_commands_with_zero_index(
        self, mock_context, mock_workspace_service
    ):
        """Test tab commands handle zero tab index."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {"tab_index": 0}

        # Test with close_tabs_to_right_command
        mock_workspace_service.close_tabs_to_right.return_value = 2
        result = close_tabs_to_right_command(mock_context)
        assert result.success is True
        mock_workspace_service.close_tabs_to_right.assert_called_with(0)
        assert result.value["closed_from_index"] == 1  # tab_index + 1

    def test_tab_commands_with_very_large_index(
        self, mock_context, mock_workspace_service
    ):
        """Test tab commands handle very large tab indices."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {"tab_index": 99999}

        # Test with close_other_tabs_command
        mock_workspace_service.close_other_tabs.return_value = 0
        result = close_other_tabs_command(mock_context)
        assert result.success is True
        mock_workspace_service.close_other_tabs.assert_called_with(99999)

    def test_rename_tab_with_empty_name(
        self, mock_context, mock_workspace_service
    ):
        """Test rename_tab_command handles empty name."""
        mock_context.get_service.return_value = mock_workspace_service
        mock_workspace_service.rename_tab.return_value = True
        mock_context.args = {"tab_index": 1, "new_name": ""}

        result = rename_tab_command(mock_context)

        assert result.success is True
        mock_workspace_service.rename_tab.assert_called_once_with(1, "")

    def test_rename_tab_with_none_name(
        self, mock_context, mock_workspace_service
    ):
        """Test rename_tab_command handles None name."""
        mock_workspace = Mock()
        mock_workspace.tab_widget.tabText.return_value = "Current Tab"
        mock_workspace_service.get_workspace.return_value = mock_workspace
        mock_context.get_service.return_value = mock_workspace_service
        mock_context.args = {"tab_index": 1, "new_name": None}

        result = rename_tab_command(mock_context)

        # Should fall back to interactive mode since new_name is None
        assert result.success is True
        assert result.value["mode"] == "interactive"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])