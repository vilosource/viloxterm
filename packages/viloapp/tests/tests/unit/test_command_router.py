#!/usr/bin/env python3
"""
Tests for the Command Router.

These tests verify that the Command Router correctly routes operations
through the command system and enforces the Command Pattern.
"""

from unittest.mock import Mock, patch

import pytest

from viloapp.core.commands.base import CommandResult
from viloapp.core.commands.router import CommandRouter


class TestCommandRouter:
    """Test the Command Router functionality."""

    @patch("viloapp.core.commands.router.execute_command")
    def test_split_pane_horizontal(self, mock_execute):
        """Test that split_pane routes to correct command."""
        # Configure mock
        mock_execute.return_value = CommandResult(success=True, value={"pane_id": "new_pane"})

        # Execute operation
        result = CommandRouter.split_pane("horizontal")

        # Verify correct command was called
        mock_execute.assert_called_once_with(
            "workbench.action.splitPaneHorizontal", orientation="horizontal"
        )
        assert result.success

    @patch("viloapp.core.commands.router.execute_command")
    def test_split_pane_vertical(self, mock_execute):
        """Test that split_pane routes to correct command."""
        # Configure mock
        mock_execute.return_value = CommandResult(success=True, value={"pane_id": "new_pane"})

        # Execute operation
        result = CommandRouter.split_pane("vertical", pane_id="existing_pane")

        # Verify correct command was called
        mock_execute.assert_called_once_with(
            "workbench.action.splitPaneVertical", orientation="vertical", pane_id="existing_pane"
        )
        assert result.success

    @patch("viloapp.core.commands.router.execute_command")
    def test_close_pane(self, mock_execute):
        """Test that close_pane routes to correct command."""
        # Configure mock
        mock_execute.return_value = CommandResult(success=True)

        # Execute operation
        result = CommandRouter.close_pane("pane_123")

        # Verify correct command was called
        mock_execute.assert_called_once_with("workbench.action.closePane", pane_id="pane_123")
        assert result.success

    @patch("viloapp.core.commands.router.execute_command")
    def test_add_terminal_tab(self, mock_execute):
        """Test that add_tab routes to correct command for terminal."""
        # Configure mock
        mock_execute.return_value = CommandResult(success=True, value={"tab_index": 1})

        # Execute operation
        result = CommandRouter.add_tab("terminal", "My Terminal")

        # Verify correct command was called
        mock_execute.assert_called_once_with("file.newTerminal", name="My Terminal")
        assert result.success

    @patch("viloapp.core.commands.router.execute_command")
    def test_add_editor_tab(self, mock_execute):
        """Test that add_tab routes to correct command for editor."""
        # Configure mock
        mock_execute.return_value = CommandResult(success=True, value={"tab_index": 1})

        # Execute operation
        result = CommandRouter.add_tab("editor")

        # Verify correct command was called
        mock_execute.assert_called_once_with("file.newEditor", name=None)
        assert result.success

    @patch("viloapp.core.commands.router.execute_command")
    def test_rename_tab(self, mock_execute):
        """Test that rename_tab routes to correct command."""
        # Configure mock
        mock_execute.return_value = CommandResult(success=True)

        # Execute operation
        result = CommandRouter.rename_tab(2, "New Name")

        # Verify correct command was called
        mock_execute.assert_called_once_with(
            "workbench.action.renameTab", tab_index=2, new_name="New Name"
        )
        assert result.success

    @patch("viloapp.core.commands.router.execute_command")
    def test_execute_workspace_operation(self, mock_execute):
        """Test the general operation executor."""
        # Configure mock
        mock_execute.return_value = CommandResult(success=True)

        # Execute operation
        result = CommandRouter.execute_workspace_operation("split_horizontal", pane_id="test")

        # Verify correct command was called
        mock_execute.assert_called_once_with("workbench.action.splitPaneHorizontal", pane_id="test")
        assert result.success

    def test_execute_workspace_operation_unknown(self):
        """Test that unknown operations return error."""
        result = CommandRouter.execute_workspace_operation("unknown_operation")

        assert not result.success
        assert "Unknown operation: unknown_operation" in result.error

    @patch("viloapp.core.commands.router.execute_command")
    def test_convenience_functions(self, mock_execute):
        """Test convenience functions work correctly."""
        from viloapp.core.commands.router import (
            close_current_tab,
            close_pane,
            duplicate_current_tab,
            new_editor_tab,
            new_terminal_tab,
            split_horizontal,
            split_vertical,
        )

        # Configure mock
        mock_execute.return_value = CommandResult(success=True)

        # Test convenience functions
        split_horizontal("pane1")
        mock_execute.assert_called_with(
            "workbench.action.splitPaneHorizontal", orientation="horizontal", pane_id="pane1"
        )

        split_vertical()
        mock_execute.assert_called_with(
            "workbench.action.splitPaneVertical", orientation="vertical"
        )

        close_pane("pane2")
        mock_execute.assert_called_with("workbench.action.closePane", pane_id="pane2")

        new_terminal_tab("Terminal")
        mock_execute.assert_called_with("file.newTerminal", name="Terminal")

        new_editor_tab()
        mock_execute.assert_called_with("file.newEditor", name=None)

        close_current_tab()
        mock_execute.assert_called_with("file.closeTab")

        duplicate_current_tab()
        mock_execute.assert_called_with("workbench.action.duplicateTab")

        # Verify all functions were called
        assert mock_execute.call_count == 7


class TestCommandRouterIntegration:
    """Integration tests to verify the router works with the command system."""

    def test_router_enforces_single_entry_point(self):
        """Test that the router enforces single entry point for operations."""
        # This test documents the architectural benefit

        # Before: Multiple ways to split a pane
        # 1. workspace.split_active_pane_horizontal()  # Direct UI call
        # 2. split_widget.model.split_pane()           # Direct model call
        # 3. execute_command("splitPane")              # Command call

        # After: Single way through router
        # CommandRouter.split_pane("horizontal")       # Only correct way

        # The router ensures all operations go through commands
        assert hasattr(CommandRouter, "split_pane")
        assert hasattr(CommandRouter, "close_pane")
        assert hasattr(CommandRouter, "add_tab")
        assert hasattr(CommandRouter, "rename_tab")

    def test_router_provides_consistent_interface(self):
        """Test that router provides consistent interface for all operations."""
        # All router methods should return CommandResult

        # Check method signatures exist
        router_methods = [
            "split_pane",
            "close_pane",
            "maximize_pane",
            "change_pane_type",
            "add_tab",
            "close_tab",
            "rename_tab",
            "duplicate_tab",
        ]

        for method_name in router_methods:
            assert hasattr(CommandRouter, method_name), f"Router missing method: {method_name}"
            method = getattr(CommandRouter, method_name)
            assert callable(method), f"Router method not callable: {method_name}"
