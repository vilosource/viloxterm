#!/usr/bin/env python3
"""
Tab management commands.

This module contains commands for managing tabs including
duplicating, closing, and renaming tabs.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.core.commands.decorators import command
from viloapp.services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)


@command(
    id="workbench.action.duplicateTab",
    title="Duplicate Tab",
    category="Tabs",
    description="Duplicate the current or specified tab",
)
def duplicate_tab_command(context: CommandContext) -> CommandResult:
    """
    Duplicate a tab.

    Args:
        context: Command context with optional tab_index

    Returns:
        CommandResult indicating success or failure
    """
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get tab index from context
        tab_index = context.args.get("tab_index")

        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")

        # If no index provided, use current tab
        if tab_index is None:
            tab_index = workspace_service.get_current_tab_index()

        # Duplicate the tab using WorkspaceService
        new_index = workspace_service.duplicate_tab(tab_index)
        return CommandResult(
            success=True, value={"duplicated_tab": tab_index, "new_index": new_index}
        )

    except Exception as e:
        logger.error(f"Error duplicating tab: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.closeTabsToRight",
    title="Close Tabs to the Right",
    category="Tabs",
    description="Close all tabs to the right of the current or specified tab",
)
def close_tabs_to_right_command(context: CommandContext) -> CommandResult:
    """
    Close all tabs to the right of a tab.

    Args:
        context: Command context with optional tab_index

    Returns:
        CommandResult indicating success or failure
    """
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get tab index from context
        tab_index = context.args.get("tab_index")

        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")

        # If no index provided, use current tab
        if tab_index is None:
            tab_index = workspace_service.get_current_tab_index()

        # Close tabs to the right using WorkspaceService
        closed_count = workspace_service.close_tabs_to_right(tab_index)
        return CommandResult(
            success=True, value={"closed_from_index": tab_index + 1, "closed_count": closed_count}
        )

    except Exception as e:
        logger.error(f"Error closing tabs to right: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.renameTab",
    title="Rename Tab",
    category="Tabs",
    description="Rename the current or specified tab",
)
def rename_tab_command(context: CommandContext) -> CommandResult:
    """
    Start renaming a tab.

    Args:
        context: Command context with optional tab_index and new_name

    Returns:
        CommandResult indicating success or failure
    """
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get tab index from context
        tab_index = context.args.get("tab_index")
        new_name = context.args.get("new_name")

        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")

        # If no index provided, use current tab
        if tab_index is None:
            tab_index = workspace_service.get_current_tab_index()

        # If new name provided, rename directly using WorkspaceService
        if new_name:
            success = workspace_service.rename_tab(tab_index, new_name)
            if success:
                return CommandResult(
                    success=True, value={"tab_index": tab_index, "new_name": new_name}
                )
            else:
                return CommandResult(success=False, error="Failed to rename tab")

        # Otherwise, start interactive rename using service
        success = workspace_service.start_interactive_tab_rename(tab_index)
        if success:
            return CommandResult(
                success=True, value={"tab_index": tab_index, "mode": "interactive"}
            )

        return CommandResult(success=False, error="Could not rename tab")

    except Exception as e:
        logger.error(f"Error renaming tab: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.closeOtherTabs",
    title="Close Other Tabs",
    category="Tabs",
    description="Close all tabs except the current or specified one",
)
def close_other_tabs_command(context: CommandContext) -> CommandResult:
    """
    Close all tabs except one.

    Args:
        context: Command context with optional tab_index

    Returns:
        CommandResult indicating success or failure
    """
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get tab index from context
        tab_index = context.args.get("tab_index")

        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")

        # If no index provided, use current tab
        if tab_index is None:
            tab_index = workspace_service.get_current_tab_index()

        # Close other tabs using WorkspaceService
        closed_count = workspace_service.close_other_tabs(tab_index)
        return CommandResult(
            success=True, value={"kept_tab": tab_index, "closed_count": closed_count}
        )

    except Exception as e:
        logger.error(f"Error closing other tabs: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


def register_tab_commands():
    """Register all tab commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Tab commands registered")
