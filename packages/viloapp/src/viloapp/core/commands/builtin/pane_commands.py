#!/usr/bin/env python3
"""
Pane management commands.

This module contains commands for managing panes including
splitting, closing, and widget type changes.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.core.commands.decorators import command
from viloapp.services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)


@command(
    id="workbench.action.splitPaneHorizontal",
    title="Split Pane Horizontal",
    category="Panes",
    description="Split the current pane horizontally",
)
def split_pane_horizontal_command(context: CommandContext) -> CommandResult:
    """
    Split a pane horizontally.

    Args:
        context: Command context with optional pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Call service method ONLY - no UI access
        result_pane_id = workspace_service.split_active_pane("horizontal")

        if result_pane_id:
            return CommandResult(success=True, value={"action": "split_horizontal", "pane_id": result_pane_id})
        else:
            return CommandResult(success=False, error="Could not split pane")

    except Exception as e:
        logger.error(f"Error splitting pane horizontally: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.splitPaneVertical",
    title="Split Pane Vertical",
    category="Panes",
    description="Split the current pane vertically",
)
def split_pane_vertical_command(context: CommandContext) -> CommandResult:
    """
    Split a pane vertically.

    Args:
        context: Command context with optional pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Call service method ONLY - no UI access
        result_pane_id = workspace_service.split_active_pane("vertical")

        if result_pane_id:
            return CommandResult(success=True, value={"action": "split_vertical", "pane_id": result_pane_id})
        else:
            return CommandResult(success=False, error="Could not split pane")

    except Exception as e:
        logger.error(f"Error splitting pane vertically: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.closePane",
    title="Close Pane",
    category="Panes",
    description="Close the current pane",
    shortcut="ctrl+shift+w",
)
def close_pane_command(context: CommandContext) -> CommandResult:
    """
    Close a pane.

    Args:
        context: Command context with optional pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get the pane from context if provided
        pane = context.args.get("pane")
        pane_id = None

        # Extract pane_id from the pane object if it has a leaf_node
        if pane and hasattr(pane, "leaf_node") and hasattr(pane.leaf_node, "id"):
            pane_id = pane.leaf_node.id
            logger.debug(f"Closing specific pane with ID: {pane_id}")

        # If we have a specific pane ID, close that pane
        if pane_id:
            result = workspace_service.close_pane(pane_id)
        else:
            # Fall back to closing active pane if no specific pane provided
            result = workspace_service.close_active_pane()

        if result:
            return CommandResult(success=True, value={"action": "close_pane"})
        else:
            return CommandResult(success=False, error="Cannot close the last pane")

    except Exception as e:
        logger.error(f"Error closing pane: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.maximizePane",
    title="Maximize Pane",
    category="Panes",
    description="Maximize or restore the current pane",
)
def maximize_pane_command(context: CommandContext) -> CommandResult:
    """
    Maximize or restore a pane.

    Args:
        context: Command context with optional pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")

        # Get current pane from context or focused pane
        pane = context.args.get("pane")
        if not pane:
            # Get currently focused pane
            if hasattr(workspace, "get_focused_pane"):
                pane = workspace.get_focused_pane()

        if pane and hasattr(pane, "toggle_maximize"):
            pane.toggle_maximize()
            return CommandResult(success=True, value={"action": "toggle_maximize"})

        return CommandResult(success=False, error="Could not maximize pane")

    except Exception as e:
        logger.error(f"Error maximizing pane: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.replaceWidgetInPane",
    title="Replace Widget in Pane",
    category="Panes",
    description="Replace current pane content with specified widget",
)
def replace_widget_in_pane_command(context: CommandContext) -> CommandResult:
    """
    Replace the current pane's widget with a new one from AppWidgetManager.

    Args:
        context: Command context with widget_id and pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        from viloapp.core.app_widget_manager import AppWidgetManager

        widget_id = context.args.get("widget_id")
        pane = context.args.get("pane")
        pane_id = context.args.get("pane_id")  # Can be passed directly

        if not widget_id:
            return CommandResult(success=False, error="No widget_id specified")

        # Get workspace service
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Try to get pane_id from different sources
        if not pane_id:
            # Try from PaneContent wrapper
            if pane and hasattr(pane, "leaf_node") and hasattr(pane.leaf_node, "id"):
                pane_id = pane.leaf_node.id
            elif pane and hasattr(pane, "pane_id"):
                pane_id = pane.pane_id

        if pane_id:
            # Get widget metadata
            manager = AppWidgetManager.get_instance()
            metadata = manager.get_widget_metadata(widget_id)

            if metadata:
                # Call service method ONLY - no direct model access
                if hasattr(metadata, "widget_type"):
                    success = workspace_service.change_pane_widget_type(pane_id, metadata.widget_type)
                    if success:
                        logger.info(f"Replaced pane {pane_id} with widget {widget_id}")
                        return CommandResult(success=True, value={"widget_id": widget_id})

            return CommandResult(success=False, error=f"Could not find widget {widget_id}")

        return CommandResult(success=False, error="Could not identify pane")

    except Exception as e:
        logger.error(f"Error replacing widget in pane: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.changePaneType",
    title="Change Pane Type",
    category="Panes",
    description="Change the widget type of a pane",
)
def change_pane_type_command(context: CommandContext) -> CommandResult:
    """
    Change the widget type of a pane.

    Args:
        context: Command context with pane reference and widget_type

    Returns:
        CommandResult indicating success or failure
    """
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")

        # Get widget type from context
        widget_type = context.args.get("widget_type")
        if not widget_type:
            return CommandResult(success=False, error="No widget type specified")

        # Get current pane from context or focused pane
        pane = context.args.get("pane")
        if not pane:
            # Get currently focused pane
            if hasattr(workspace, "get_focused_pane"):
                pane = workspace.get_focused_pane()

        if pane and hasattr(pane, "set_widget_type"):
            pane.set_widget_type(widget_type)
            return CommandResult(success=True, value={"widget_type": widget_type})

        return CommandResult(success=False, error="Could not change pane type")

    except Exception as e:
        logger.error(f"Error changing pane type: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


def register_pane_commands():
    """Register all pane commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Pane commands registered")
