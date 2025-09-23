#!/usr/bin/env python3
"""
Command Router - Single Entry Point for All Operations

This module provides a centralized routing mechanism to ensure all UI operations
go through commands, enforcing the Command Pattern and maintaining single responsibility.
"""

import logging
from typing import Optional

from viloapp.core.commands.base import CommandResult, CommandStatus
from viloapp.core.commands.executor import execute_command

logger = logging.getLogger(__name__)


class CommandRouter:
    """
    Ensures all UI operations go through commands.

    This router provides a single point of entry for all workspace operations,
    ensuring consistent command execution and preventing direct UI access.
    """

    @staticmethod
    def split_pane(orientation: str, pane_id: Optional[str] = None) -> CommandResult:
        """
        Split a pane in the specified orientation.

        Args:
            orientation: "horizontal" or "vertical"
            pane_id: Optional specific pane ID to split

        Returns:
            CommandResult with operation outcome
        """
        command_id = f"workbench.action.splitPane{orientation.title()}"
        args = {"orientation": orientation}
        if pane_id:
            args["pane_id"] = pane_id

        return execute_command(command_id, **args)

    @staticmethod
    def close_pane(pane_id: Optional[str] = None) -> CommandResult:
        """
        Close a pane.

        Args:
            pane_id: Optional specific pane ID to close

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if pane_id:
            args["pane_id"] = pane_id

        return execute_command("workbench.action.closePane", **args)

    @staticmethod
    def maximize_pane(pane_id: Optional[str] = None) -> CommandResult:
        """
        Maximize or restore a pane.

        Args:
            pane_id: Optional specific pane ID to maximize

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if pane_id:
            args["pane_id"] = pane_id

        return execute_command("workbench.action.maximizePane", **args)

    @staticmethod
    def change_pane_type(pane_id: str, widget_id: str) -> CommandResult:
        """
        Change the widget type of a pane.

        Args:
            pane_id: ID of the pane to change
            widget_id: New widget type

        Returns:
            CommandResult with operation outcome
        """
        return execute_command(
            "workbench.action.changePaneType", pane_id=pane_id, widget_id=widget_id
        )

    @staticmethod
    def replace_widget_in_pane(pane_id: str, widget_id: str) -> CommandResult:
        """
        Replace the widget in a pane.

        Args:
            pane_id: ID of the pane
            widget_id: ID of the new widget

        Returns:
            CommandResult with operation outcome
        """
        return execute_command(
            "workbench.action.replaceWidgetInPane", pane_id=pane_id, widget_id=widget_id
        )

    @staticmethod
    def add_tab(tab_type: str = "terminal", name: Optional[str] = None) -> CommandResult:
        """
        Add a new tab.

        Args:
            tab_type: Type of tab to create
            name: Optional name for the tab

        Returns:
            CommandResult with operation outcome
        """
        # Map legacy tab types to capabilities and find appropriate widgets
        from viloapp.core.commands.capability_commands import (
            get_widget_for_file_operation,
            get_widget_for_shell_operation,
        )

        widget_id = None
        if tab_type == "terminal":
            widget_id = get_widget_for_shell_operation()
        elif tab_type == "editor":
            widget_id = get_widget_for_file_operation()

        if widget_id:
            return execute_command("workspace.newTab", name=name, widget_id=widget_id)
        else:
            # Use default widget if no specific capability match
            return execute_command("workspace.newTab", name=name)

    @staticmethod
    def close_tab(tab_index: Optional[int] = None) -> CommandResult:
        """
        Close a tab.

        Args:
            tab_index: Optional index of tab to close

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if tab_index is not None:
            args["tab_index"] = tab_index

        return execute_command("file.closeTab", **args)

    @staticmethod
    def duplicate_tab(tab_index: Optional[int] = None) -> CommandResult:
        """
        Duplicate a tab.

        Args:
            tab_index: Optional index of tab to duplicate

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if tab_index is not None:
            args["tab_index"] = tab_index

        return execute_command("workbench.action.duplicateTab", **args)

    @staticmethod
    def rename_tab(tab_index: int, new_name: str) -> CommandResult:
        """
        Rename a tab.

        Args:
            tab_index: Index of tab to rename
            new_name: New name for the tab

        Returns:
            CommandResult with operation outcome
        """
        return execute_command("workbench.action.renameTab", tab_index=tab_index, new_name=new_name)

    @staticmethod
    def start_interactive_tab_rename(tab_index: Optional[int] = None) -> CommandResult:
        """
        Start interactive tab renaming.

        Args:
            tab_index: Optional index of tab to rename

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if tab_index is not None:
            args["tab_index"] = tab_index

        return execute_command("workbench.action.renameTab", **args)

    @staticmethod
    def close_other_tabs(tab_index: Optional[int] = None) -> CommandResult:
        """
        Close all tabs except one.

        Args:
            tab_index: Optional index of tab to keep

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if tab_index is not None:
            args["tab_index"] = tab_index

        return execute_command("workbench.action.closeOtherTabs", **args)

    @staticmethod
    def close_tabs_to_right(tab_index: Optional[int] = None) -> CommandResult:
        """
        Close all tabs to the right of a tab.

        Args:
            tab_index: Optional index of reference tab

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if tab_index is not None:
            args["tab_index"] = tab_index

        return execute_command("workbench.action.closeTabsToRight", **args)

    @staticmethod
    def open_terminal_in_pane(pane_id: Optional[str] = None) -> CommandResult:
        """
        Open a terminal in a specific pane.

        Args:
            pane_id: Optional pane ID to replace

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if pane_id:
            args["pane_id"] = pane_id

        return execute_command("file.replaceWithTerminal", **args)

    @staticmethod
    def open_editor_in_pane(pane_id: Optional[str] = None) -> CommandResult:
        """
        Open an editor in a specific pane.

        Args:
            pane_id: Optional pane ID to replace

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if pane_id:
            args["pane_id"] = pane_id

        return execute_command("file.replaceWithEditor", **args)

    @staticmethod
    def open_settings_in_pane(pane_id: Optional[str] = None) -> CommandResult:
        """
        Open settings in a specific pane.

        Args:
            pane_id: Optional pane ID to replace

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if pane_id:
            args["pane_id"] = pane_id

        return execute_command("settings.replaceWithShortcutsEditor", **args)

    @staticmethod
    def open_theme_editor_in_pane(pane_id: Optional[str] = None) -> CommandResult:
        """
        Open theme editor in a specific pane.

        Args:
            pane_id: Optional pane ID to replace

        Returns:
            CommandResult with operation outcome
        """
        args = {}
        if pane_id:
            args["pane_id"] = pane_id

        return execute_command("theme.replaceWithEditor", **args)

    @staticmethod
    def execute_workspace_operation(operation: str, **kwargs) -> CommandResult:
        """
        Execute any workspace operation through commands.

        This is a general-purpose method for operations not covered by specific methods.

        Args:
            operation: The operation to execute
            **kwargs: Arguments for the operation

        Returns:
            CommandResult with operation outcome
        """
        # Map operation names to command IDs
        operation_map = {
            "split_horizontal": "workbench.action.splitPaneHorizontal",
            "split_vertical": "workbench.action.splitPaneVertical",
            "close_pane": "workbench.action.closePane",
            "maximize_pane": "workbench.action.maximizePane",
            "new_terminal": "file.newTerminal",
            "new_editor": "file.newEditor",
            "close_tab": "file.closeTab",
            "duplicate_tab": "workbench.action.duplicateTab",
            "rename_tab": "workbench.action.renameTab",
        }

        command_id = operation_map.get(operation)
        if not command_id:
            return CommandResult(status=CommandStatus.FAILURE, message=f"Unknown operation: {operation}")

        return execute_command(command_id, **kwargs)


# Convenience functions for common operations
def split_horizontal(pane_id: Optional[str] = None) -> CommandResult:
    """Split a pane horizontally."""
    return CommandRouter.split_pane("horizontal", pane_id)


def split_vertical(pane_id: Optional[str] = None) -> CommandResult:
    """Split a pane vertically."""
    return CommandRouter.split_pane("vertical", pane_id)


def close_pane(pane_id: Optional[str] = None) -> CommandResult:
    """Close a pane."""
    return CommandRouter.close_pane(pane_id)


def new_terminal_tab(name: Optional[str] = None) -> CommandResult:
    """Create a new terminal tab."""
    return CommandRouter.add_tab("terminal", name)


def new_editor_tab(name: Optional[str] = None) -> CommandResult:
    """Create a new editor tab."""
    return CommandRouter.add_tab("editor", name)


def close_current_tab() -> CommandResult:
    """Close the current tab."""
    return CommandRouter.close_tab()


def duplicate_current_tab() -> CommandResult:
    """Duplicate the current tab."""
    return CommandRouter.duplicate_tab()


# Export the main router class and convenience functions
__all__ = [
    "CommandRouter",
    "split_horizontal",
    "split_vertical",
    "close_pane",
    "new_terminal_tab",
    "new_editor_tab",
    "close_current_tab",
    "duplicate_current_tab",
]
