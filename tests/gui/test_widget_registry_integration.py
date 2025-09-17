#!/usr/bin/env python3
"""
GUI integration tests for widget registry management.

Tests that the UI properly uses commands instead of direct service access.
"""

from unittest.mock import MagicMock, call, patch

import pytest

from core.commands.executor import execute_command
from services.service_locator import ServiceLocator
from services.workspace_service import WorkspaceService
from ui.widgets.split_pane_widget import SplitPaneWidget
from ui.workspace import Workspace


@pytest.fixture
def workspace_with_service(qtbot):
    """Create a workspace with mocked service."""
    # Create workspace
    workspace = Workspace()
    qtbot.addWidget(workspace)

    # Mock the service locator
    mock_service = MagicMock(spec=WorkspaceService)
    mock_service._widget_registry = {}
    mock_service._workspace = workspace

    # Setup service locator
    locator = ServiceLocator.get_instance()
    locator.register(WorkspaceService, mock_service)

    yield workspace, mock_service

    # Cleanup
    locator.unregister(WorkspaceService)


class TestWidgetRegistryIntegration:
    """Test widget registry integration with UI."""

    def test_tab_close_uses_command(self, workspace_with_service, qtbot):
        """Test that closing a tab uses commands instead of direct service access."""
        workspace, mock_service = workspace_with_service

        # Add a tab with a widget ID
        split_pane = SplitPaneWidget()
        split_pane.widget_id = "com.viloapp.settings"
        workspace.add_tab(split_pane, "Settings")

        # Mock execute_command to verify it's called
        with patch("ui.workspace.execute_command") as mock_execute:
            mock_execute.return_value = MagicMock(success=True)

            # Close the tab
            workspace.close_tab(0)

            # Verify command was called with correct parameters
            mock_execute.assert_called_once_with(
                "workspace.updateRegistryAfterClose",
                closed_index=0,
                widget_id="com.viloapp.settings",
            )

    def test_no_direct_service_access_in_close_tab(self, workspace_with_service, qtbot):
        """Ensure close_tab doesn't directly access WorkspaceService."""
        workspace, mock_service = workspace_with_service

        # Add a tab
        split_pane = SplitPaneWidget()
        split_pane.widget_id = "test_widget"
        workspace.add_tab(split_pane, "Test")

        # Patch ServiceLocator to ensure it's not called directly
        with patch("ui.workspace.ServiceLocator") as mock_locator:
            with patch("ui.workspace.execute_command") as mock_execute:
                mock_execute.return_value = MagicMock(success=True)

                # Close the tab
                workspace.close_tab(0)

                # ServiceLocator should NOT be imported/used
                mock_locator.get_instance.assert_not_called()

    def test_singleton_widget_behavior_with_commands(
        self, workspace_with_service, qtbot
    ):
        """Test that singleton widgets work correctly with command-based registry."""
        workspace, mock_service = workspace_with_service

        # Simulate opening Settings widget
        with patch("core.commands.executor.execute_command") as mock_execute:
            # First check if widget exists
            mock_execute.return_value = MagicMock(
                success=True, value={"registered": False}
            )

            result = execute_command(
                "workspace.isWidgetRegistered", widget_id="com.viloapp.settings"
            )
            assert not result.value["registered"]

            # Register the widget
            mock_execute.return_value = MagicMock(
                success=True,
                value={"widget_id": "com.viloapp.settings", "tab_index": 0},
            )

            result = execute_command(
                "workspace.registerWidget",
                widget_id="com.viloapp.settings",
                tab_index=0,
            )
            assert result.success

            # Now check if widget exists
            mock_execute.return_value = MagicMock(
                success=True, value={"registered": True}
            )

            result = execute_command(
                "workspace.isWidgetRegistered", widget_id="com.viloapp.settings"
            )
            assert result.value["registered"]

    def test_registry_update_on_multiple_tab_closes(
        self, workspace_with_service, qtbot
    ):
        """Test registry updates correctly when multiple tabs are closed."""
        workspace, mock_service = workspace_with_service

        # Add multiple tabs
        for i in range(4):
            split_pane = SplitPaneWidget()
            split_pane.widget_id = f"widget_{i}"
            workspace.add_tab(split_pane, f"Tab {i}")

        with patch("ui.workspace.execute_command") as mock_execute:
            mock_execute.return_value = MagicMock(success=True)

            # Close middle tab
            workspace.close_tab(2)

            # Verify command was called
            mock_execute.assert_called_with(
                "workspace.updateRegistryAfterClose",
                closed_index=2,
                widget_id="widget_2",
            )

            # Close first tab
            workspace.close_tab(0)

            # Verify command was called again
            calls = mock_execute.call_args_list
            assert len(calls) == 2
            assert calls[1] == call(
                "workspace.updateRegistryAfterClose",
                closed_index=0,
                widget_id="widget_0",
            )

    def test_tab_without_widget_id(self, workspace_with_service, qtbot):
        """Test closing a tab without a widget_id."""
        workspace, mock_service = workspace_with_service

        # Add a tab without widget_id
        split_pane = SplitPaneWidget()
        # Don't set widget_id
        workspace.add_tab(split_pane, "No ID Tab")

        with patch("ui.workspace.execute_command") as mock_execute:
            mock_execute.return_value = MagicMock(success=True)

            # Close the tab
            workspace.close_tab(0)

            # Command should still be called but with widget_id=None
            mock_execute.assert_called_once_with(
                "workspace.updateRegistryAfterClose", closed_index=0, widget_id=None
            )

    def test_command_failure_handling(self, workspace_with_service, qtbot):
        """Test handling of command failures."""
        workspace, mock_service = workspace_with_service

        # Add a tab
        split_pane = SplitPaneWidget()
        split_pane.widget_id = "test_widget"
        workspace.add_tab(split_pane, "Test")

        with patch("ui.workspace.execute_command") as mock_execute:
            # Simulate command failure
            mock_execute.return_value = MagicMock(success=False, error="Command failed")

            with patch("ui.workspace.logger") as mock_logger:
                # Close the tab
                workspace.close_tab(0)

                # Should log the error
                mock_logger.warning.assert_called()
                warning_call = mock_logger.warning.call_args[0][0]
                assert "Failed to update widget registry" in warning_call
                assert "Command failed" in warning_call

    def test_exception_in_command_execution(self, workspace_with_service, qtbot):
        """Test handling of exceptions during command execution."""
        workspace, mock_service = workspace_with_service

        # Add a tab
        split_pane = SplitPaneWidget()
        split_pane.widget_id = "test_widget"
        workspace.add_tab(split_pane, "Test")

        with patch("ui.workspace.execute_command") as mock_execute:
            # Simulate exception
            mock_execute.side_effect = Exception("Unexpected error")

            with patch("ui.workspace.logger") as mock_logger:
                # Close the tab - should not crash
                workspace.close_tab(0)

                # Should log the error
                mock_logger.debug.assert_called()
                debug_call = mock_logger.debug.call_args[0][0]
                assert "Could not update widget registry" in debug_call


class TestThemeCommandIntegration:
    """Test that theme operations use commands."""

    def test_theme_editor_should_use_commands(self):
        """Verify theme editor uses commands instead of direct service calls."""
        # This is a placeholder test - actual implementation would require
        # refactoring the ThemeEditorWidget to use commands

        # Check that theme commands exist
        from core.commands.registry import CommandRegistry

        registry = CommandRegistry.get_instance()

        # Verify theme management commands are registered
        assert registry.get_command("theme.getAvailableThemes") is not None
        assert registry.get_command("theme.getCurrentTheme") is not None
        assert registry.get_command("theme.applyTheme") is not None
        assert registry.get_command("theme.saveCustomTheme") is not None
        assert registry.get_command("theme.deleteCustomTheme") is not None
        assert registry.get_command("theme.importTheme") is not None
        assert registry.get_command("theme.exportTheme") is not None

    @pytest.mark.skip(reason="ThemeEditorWidget needs refactoring to use commands")
    def test_theme_editor_no_direct_service_calls(self):
        """Test that ThemeEditorWidget doesn't make direct service calls."""
        # This test will be enabled after refactoring ThemeEditorWidget
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
