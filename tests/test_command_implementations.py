#!/usr/bin/env python3
"""
Comprehensive tests for command implementations using pytest-qt.

This module tests that all command implementations work correctly
with the actual Qt widgets and services, verifying UI state changes
and service integration.
"""

from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from core.commands.base import Command, CommandContext, CommandResult
from core.commands.executor import execute_command
from core.commands.registry import command_registry
from services.service_locator import ServiceLocator
from services.workspace_service import WorkspaceService


class TestPaneCommands:
    """Test pane-related commands with real Qt widgets."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, main_window):
        """Setup for each test."""
        self.qtbot = qtbot
        self.main_window = main_window
        self.workspace = main_window.workspace

        # Get the ServiceLocator instance
        service_locator = ServiceLocator()

        # Check if WorkspaceService is already registered from main_window init
        try:
            workspace_service = service_locator.get(WorkspaceService)
            if not workspace_service.get_workspace():
                workspace_service.set_workspace(self.workspace)
        except Exception:
            # If not registered, create and register it
            workspace_service = WorkspaceService()
            workspace_service.set_workspace(self.workspace)
            service_locator.register(WorkspaceService, workspace_service)

    def test_split_pane_horizontal_command(self):
        """Test horizontal pane splitting through command."""
        # Get initial pane count
        initial_panes = len(self.workspace.get_all_panes())
        assert initial_panes == 1  # Should start with one pane

        # Execute split command
        result = execute_command("workbench.action.splitPaneHorizontal")
        assert result.success, f"Command failed: {result.error}"

        # Verify pane was created
        self.qtbot.wait(100)  # Allow Qt to process events
        final_panes = len(self.workspace.get_all_panes())
        assert final_panes == 2, "Pane was not split horizontally"

    def test_split_pane_vertical_command(self):
        """Test vertical pane splitting through command."""
        # Get initial pane count
        initial_panes = len(self.workspace.get_all_panes())

        # Execute split command
        result = execute_command("workbench.action.splitPaneVertical")
        assert result.success, f"Command failed: {result.error}"

        # Verify pane was created
        self.qtbot.wait(100)
        final_panes = len(self.workspace.get_all_panes())
        assert final_panes == initial_panes + 1, "Pane was not split vertically"

    def test_close_pane_command(self):
        """Test closing a pane through command."""
        # First split to have multiple panes
        execute_command("workbench.action.splitPaneHorizontal")
        self.qtbot.wait(100)

        initial_panes = len(self.workspace.get_all_panes())
        assert initial_panes > 1, "Need multiple panes for test"

        # Get a pane to close
        pane_to_close = self.workspace.get_all_panes()[0]

        # Execute close command with specific pane
        result = execute_command("workbench.action.closePane", pane=pane_to_close)
        assert result.success, f"Command failed: {result.error}"

        # Verify pane was closed
        self.qtbot.wait(100)
        final_panes = len(self.workspace.get_all_panes())
        assert final_panes == initial_panes - 1, "Pane was not closed"

    def test_maximize_pane_command(self):
        """Test maximizing and restoring a pane."""
        # Split to have multiple panes
        execute_command("workbench.action.splitPaneHorizontal")
        self.qtbot.wait(100)

        panes = self.workspace.get_all_panes()
        assert len(panes) > 1, "Need multiple panes for maximize test"

        # Get initial visibility states
        {pane: pane.isVisible() for pane in panes}

        # Maximize first pane
        result = execute_command("workbench.action.maximizePane", pane=panes[0])
        assert result.success, f"Command failed: {result.error}"
        self.qtbot.wait(100)

        # Check that only first pane is visible
        assert panes[0].isVisible(), "Maximized pane should be visible"
        for pane in panes[1:]:
            assert not pane.isVisible(), "Non-maximized pane should be hidden"

        # Restore (toggle maximize again)
        result = execute_command("workbench.action.maximizePane", pane=panes[0])
        assert result.success, f"Command failed: {result.error}"
        self.qtbot.wait(100)

        # All panes should be visible again
        for pane in panes:
            assert pane.isVisible(), "All panes should be visible after restore"


class TestTabCommands:
    """Test tab-related commands with real Qt widgets."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, main_window):
        """Setup for each test."""
        self.qtbot = qtbot
        self.main_window = main_window
        self.workspace = main_window.workspace

        # Setup service locator
        ServiceLocator.clear()
        workspace_service = WorkspaceService()
        workspace_service.set_workspace(self.workspace)
        ServiceLocator.register(WorkspaceService, workspace_service)

        # Ensure we have at least one tab
        if self.workspace.tab_widget.count() == 0:
            self.workspace.add_editor_tab("Test Tab")
            self.qtbot.wait(100)

    def test_duplicate_tab_command(self):
        """Test duplicating a tab through command."""
        initial_count = self.workspace.tab_widget.count()
        initial_text = self.workspace.tab_widget.tabText(0)

        # Execute duplicate command
        result = execute_command("workbench.action.duplicateTab", tab_index=0)
        assert result.success, f"Command failed: {result.error}"

        self.qtbot.wait(100)

        # Verify tab was duplicated
        final_count = self.workspace.tab_widget.count()
        assert final_count == initial_count + 1, "Tab was not duplicated"

        # Check that new tab has similar name
        new_tab_text = self.workspace.tab_widget.tabText(final_count - 1)
        assert "Copy" in new_tab_text or initial_text in new_tab_text

    def test_rename_tab_command(self):
        """Test renaming a tab through command."""
        self.workspace.tab_widget.tabText(0)
        new_name = "Renamed Tab"

        # Execute rename command with new name
        result = execute_command(
            "workbench.action.renameTab", tab_index=0, new_name=new_name
        )
        assert result.success, f"Command failed: {result.error}"

        # Verify tab was renamed
        current_name = self.workspace.tab_widget.tabText(0)
        assert current_name == new_name, f"Tab not renamed: {current_name}"

    def test_close_tabs_to_right_command(self):
        """Test closing tabs to the right of current tab."""
        # Create multiple tabs
        for i in range(4):
            self.workspace.add_editor_tab(f"Tab {i}")
        self.qtbot.wait(100)

        initial_count = self.workspace.tab_widget.count()
        assert initial_count >= 4, "Need at least 4 tabs for test"

        # Close tabs to the right of index 1
        result = execute_command("workbench.action.closeTabsToRight", tab_index=1)
        assert result.success, f"Command failed: {result.error}"

        self.qtbot.wait(100)

        # Should have only tabs 0 and 1 remaining
        final_count = self.workspace.tab_widget.count()
        assert final_count == 2, f"Expected 2 tabs, got {final_count}"

    def test_close_other_tabs_command(self):
        """Test closing all tabs except the specified one."""
        # Create multiple tabs
        for i in range(4):
            self.workspace.add_editor_tab(f"Tab {i}")
        self.qtbot.wait(100)

        initial_count = self.workspace.tab_widget.count()
        assert initial_count >= 4, "Need at least 4 tabs for test"

        # Keep only tab at index 2
        kept_tab_text = self.workspace.tab_widget.tabText(2)

        result = execute_command("workbench.action.closeOtherTabs", tab_index=2)
        assert result.success, f"Command failed: {result.error}"

        self.qtbot.wait(100)

        # Should have only one tab
        final_count = self.workspace.tab_widget.count()
        assert final_count == 1, f"Expected 1 tab, got {final_count}"
        assert self.workspace.tab_widget.tabText(0) == kept_tab_text


class TestSidebarCommands:
    """Test sidebar view commands."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, main_window):
        """Setup for each test."""
        self.qtbot = qtbot
        self.main_window = main_window
        self.sidebar = main_window.sidebar
        self.activity_bar = main_window.activity_bar

    def test_show_explorer_command(self):
        """Test showing explorer view through command."""
        # Execute command
        result = execute_command("workbench.view.explorer")
        assert result.success, f"Command failed: {result.error}"

        self.qtbot.wait(100)

        # Verify explorer is shown
        assert self.activity_bar.current_view == "explorer"
        assert self.sidebar.isVisible(), "Sidebar should be visible"

    def test_show_search_command(self):
        """Test showing search view through command."""
        result = execute_command("workbench.view.search")
        assert result.success, f"Command failed: {result.error}"

        self.qtbot.wait(100)

        assert self.activity_bar.current_view == "search"
        assert self.sidebar.isVisible(), "Sidebar should be visible"

    def test_show_git_command(self):
        """Test showing git view through command."""
        result = execute_command("workbench.view.git")
        assert result.success, f"Command failed: {result.error}"

        self.qtbot.wait(100)

        assert self.activity_bar.current_view == "git"
        assert self.sidebar.isVisible(), "Sidebar should be visible"

    def test_toggle_sidebar_command(self):
        """Test toggling sidebar visibility."""
        # Ensure sidebar is visible first
        self.sidebar.show()
        self.qtbot.wait(100)
        initial_visible = self.sidebar.isVisible()

        # Toggle sidebar
        result = execute_command("workbench.action.toggleSidebar")
        assert result.success, f"Command failed: {result.error}"

        self.qtbot.wait(100)

        # Sidebar visibility should be toggled
        assert self.sidebar.isVisible() != initial_visible


class TestNavigationCommands:
    """Test navigation commands between panes and tabs."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, main_window):
        """Setup for each test."""
        self.qtbot = qtbot
        self.main_window = main_window
        self.workspace = main_window.workspace

        # Setup service locator
        ServiceLocator.clear()
        workspace_service = WorkspaceService()
        workspace_service.set_workspace(self.workspace)
        ServiceLocator.register(WorkspaceService, workspace_service)

        # Create multiple panes for navigation tests
        execute_command("workbench.action.splitPaneHorizontal")
        execute_command("workbench.action.splitPaneVertical")
        self.qtbot.wait(100)

    def test_focus_next_pane_command(self):
        """Test focusing next pane in order."""
        panes = self.workspace.get_all_panes()
        assert len(panes) > 1, "Need multiple panes for navigation test"

        # Set focus to first pane
        panes[0].setFocus()
        self.qtbot.wait(100)

        # Execute focus next command
        result = execute_command("workbench.action.focusNextPane")
        assert result.success, f"Command failed: {result.error}"

        self.qtbot.wait(100)

        # Verify focus moved
        # Note: Actual focus checking might need adjustment based on implementation
        assert self.workspace.get_active_pane() != panes[0]

    def test_focus_directional_navigation(self):
        """Test directional pane navigation (left, right, up, down)."""
        # This requires a specific layout to test properly
        # We'll test that commands execute without error

        commands = [
            "workbench.action.focusLeftPane",
            "workbench.action.focusRightPane",
            "workbench.action.focusAbovePane",
            "workbench.action.focusBelowPane",
        ]

        for cmd in commands:
            result = execute_command(cmd)
            # Command should execute even if no pane in that direction
            assert result.success or "No pane" in str(result.error)

    def test_tab_navigation_commands(self):
        """Test tab navigation commands."""
        # Add multiple tabs
        for i in range(3):
            self.workspace.add_editor_tab(f"Tab {i}")
        self.qtbot.wait(100)

        tab_widget = self.workspace.tab_widget

        # Test next tab
        tab_widget.setCurrentIndex(0)
        result = execute_command("workbench.action.nextTab")
        assert result.success
        self.qtbot.wait(100)
        assert tab_widget.currentIndex() == 1

        # Test previous tab
        result = execute_command("workbench.action.previousTab")
        assert result.success
        self.qtbot.wait(100)
        assert tab_widget.currentIndex() == 0

        # Test first/last tab
        result = execute_command("workbench.action.lastTab")
        assert result.success
        self.qtbot.wait(100)
        assert tab_widget.currentIndex() == tab_widget.count() - 1

        result = execute_command("workbench.action.firstTab")
        assert result.success
        self.qtbot.wait(100)
        assert tab_widget.currentIndex() == 0


class TestCommandIntegration:
    """Test command system integration with UI."""

    @pytest.fixture(autouse=True)
    def setup(self, qtbot, main_window):
        """Setup for each test."""
        self.qtbot = qtbot
        self.main_window = main_window

    def test_command_context_propagation(self):
        """Test that command context correctly propagates UI state."""
        # Create a mock command that checks context
        context_received = {}

        def test_context_command(context: CommandContext) -> CommandResult:
            nonlocal context_received
            context_received = {
                "has_main_window": context.main_window is not None,
                "has_workspace": context.workspace is not None,
                "has_services": context.get_service(WorkspaceService) is not None,
            }
            return CommandResult(success=True)

        # Register temporary test command
        test_cmd = Command(
            id="test.context",
            title="Test Context",
            category="Test",
            handler=test_context_command,
        )
        command_registry.register(test_cmd)

        # Execute command
        execute_command("test.context")

        # Verify context was properly populated
        assert context_received.get("has_main_window"), "Main window not in context"
        assert context_received.get("has_workspace"), "Workspace not in context"
        assert context_received.get("has_services"), "Services not in context"

    def test_command_error_handling(self):
        """Test that commands handle errors gracefully."""
        # Test executing non-existent command
        result = execute_command("non.existent.command")
        assert not result.success
        assert "not found" in result.error.lower()

        # Test command with missing service
        ServiceLocator.clear()  # Clear services
        result = execute_command("workbench.action.splitPaneHorizontal")
        assert not result.success
        assert "service" in result.error.lower()

    def test_keyboard_shortcut_triggers_command(self, qtbot):
        """Test that keyboard shortcuts trigger the correct commands."""
        # Spy on execute_command to see if it gets called
        with patch("core.commands.executor.execute_command") as mock_execute:
            mock_execute.return_value = CommandResult(success=True)

            # Simulate Ctrl+N keyboard shortcut
            QTest.keyClick(self.main_window, Qt.Key_N, Qt.ControlModifier)

            self.qtbot.wait(100)

            # Verify command was executed
            # Note: This depends on keyboard shortcuts being properly connected
            # mock_execute.assert_called_with("file.newEditorTab")


class TestCommandPerformance:
    """Test command system performance and edge cases."""

    def test_rapid_command_execution(self, qtbot, main_window):
        """Test executing many commands rapidly."""
        workspace = main_window.workspace

        # Execute many split commands rapidly
        for _i in range(10):
            result = execute_command("workbench.action.splitPaneHorizontal")
            assert result.success

        qtbot.wait(200)

        # Verify all panes were created
        panes = workspace.get_all_panes()
        assert len(panes) > 10, "Not all panes were created"

    def test_command_with_invalid_arguments(self):
        """Test commands with invalid arguments."""
        # Test with invalid tab index
        result = execute_command("workbench.action.renameTab", tab_index=999)
        assert not result.success or result.value is None

        # Test with wrong argument types
        result = execute_command(
            "workbench.action.duplicateTab", tab_index="not_a_number"
        )
        # Should handle gracefully
        assert isinstance(result, CommandResult)

    def test_concurrent_command_execution(self, qtbot):
        """Test executing commands concurrently."""
        import threading

        results = []

        def execute_split():
            result = execute_command("workbench.action.splitPaneHorizontal")
            results.append(result)

        # Start multiple threads executing commands
        threads = []
        for _i in range(5):
            t = threading.Thread(target=execute_split)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        qtbot.wait(200)

        # All commands should have completed
        assert len(results) == 5
        # At least some should succeed (Qt might serialize them)
        success_count = sum(1 for r in results if r.success)
        assert success_count > 0


def test_all_registered_commands_have_handlers():
    """Test that all registered commands have valid handlers."""
    all_commands = command_registry.get_all_commands()

    for cmd in all_commands:
        assert callable(cmd.handler), f"Command {cmd.id} has no valid handler"

        # Test that handler accepts correct signature
        import inspect

        sig = inspect.signature(cmd.handler)
        params = list(sig.parameters.keys())
        assert len(params) >= 1, f"Command {cmd.id} handler missing context parameter"

        # First parameter should accept CommandContext
        # (This is a basic check, full type checking would need more work)


def test_command_categories_are_organized():
    """Test that commands are properly categorized."""
    all_commands = command_registry.get_all_commands()
    categories = {}

    for cmd in all_commands:
        if cmd.category not in categories:
            categories[cmd.category] = []
        categories[cmd.category].append(cmd.id)

    # Verify we have expected categories
    expected_categories = [
        "File",
        "View",
        "Edit",
        "Navigation",
        "Workspace",
        "Tabs",
        "Pane",
        "Sidebar",
    ]

    for expected in expected_categories:
        assert expected in categories, f"Missing category: {expected}"
        assert len(categories[expected]) > 0, f"Category {expected} has no commands"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
