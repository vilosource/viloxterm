#!/usr/bin/env python3
"""
Pane management commands.

This module contains commands for managing panes including
splitting, closing, and widget type changes.
"""

import logging
from typing import Optional

from core.commands.base import CommandContext, CommandResult
from core.commands.decorators import command
from services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)


@command(
    id="workbench.action.splitPaneHorizontal",
    title="Split Pane Horizontal",
    category="Panes",
    description="Split the current pane horizontally"
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
        
        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")
        
        # Get current pane from context or focused pane
        pane = context.args.get('pane')
        if not pane:
            # Get currently focused pane
            if hasattr(workspace, 'get_focused_pane'):
                pane = workspace.get_focused_pane()
        
        if pane and hasattr(pane, 'split_horizontal'):
            pane.split_horizontal()
            return CommandResult(success=True, value={"action": "split_horizontal"})
        
        return CommandResult(success=False, error="Could not split pane")
        
    except Exception as e:
        logger.error(f"Error splitting pane horizontally: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.splitPaneVertical",
    title="Split Pane Vertical",
    category="Panes",
    description="Split the current pane vertically"
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
        
        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")
        
        # Get current pane from context or focused pane
        pane = context.args.get('pane')
        if not pane:
            # Get currently focused pane
            if hasattr(workspace, 'get_focused_pane'):
                pane = workspace.get_focused_pane()
        
        if pane and hasattr(pane, 'split_vertical'):
            pane.split_vertical()
            return CommandResult(success=True, value={"action": "split_vertical"})
        
        return CommandResult(success=False, error="Could not split pane")
        
    except Exception as e:
        logger.error(f"Error splitting pane vertically: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.closePane",
    title="Close Pane",
    category="Panes",
    description="Close the current pane"
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
        
        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")
        
        # Get current pane from context or focused pane
        pane = context.args.get('pane')
        if not pane:
            # Get currently focused pane
            if hasattr(workspace, 'get_focused_pane'):
                pane = workspace.get_focused_pane()
        
        if pane and hasattr(pane, 'close'):
            pane.close()
            return CommandResult(success=True, value={"action": "close_pane"})
        
        return CommandResult(success=False, error="Could not close pane")
        
    except Exception as e:
        logger.error(f"Error closing pane: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.maximizePane",
    title="Maximize Pane",
    category="Panes",
    description="Maximize or restore the current pane"
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
        pane = context.args.get('pane')
        if not pane:
            # Get currently focused pane
            if hasattr(workspace, 'get_focused_pane'):
                pane = workspace.get_focused_pane()
        
        if pane and hasattr(pane, 'toggle_maximize'):
            pane.toggle_maximize()
            return CommandResult(success=True, value={"action": "toggle_maximize"})
        
        return CommandResult(success=False, error="Could not maximize pane")
        
    except Exception as e:
        logger.error(f"Error maximizing pane: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.changePaneType",
    title="Change Pane Type",
    category="Panes",
    description="Change the widget type of a pane"
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
        widget_type = context.args.get('widget_type')
        if not widget_type:
            return CommandResult(success=False, error="No widget type specified")
        
        # Get current pane from context or focused pane
        pane = context.args.get('pane')
        if not pane:
            # Get currently focused pane
            if hasattr(workspace, 'get_focused_pane'):
                pane = workspace.get_focused_pane()
        
        if pane and hasattr(pane, 'set_widget_type'):
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