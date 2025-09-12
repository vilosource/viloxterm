#!/usr/bin/env python3
"""
Tab management commands.

This module contains commands for managing tabs including
duplicating, closing, and renaming tabs.
"""

import logging
from typing import Optional

from core.commands.base import CommandContext, CommandResult
from core.commands.decorators import command
from core.services.service_locator import get_service

logger = logging.getLogger(__name__)


@command(
    id="workbench.action.duplicateTab",
    title="Duplicate Tab",
    category="Tabs",
    description="Duplicate the current or specified tab"
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
        workspace_service = get_service('WorkspaceService')
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        # Get tab index from context
        tab_index = context.args.get('tab_index')
        
        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")
        
        # If no index provided, use current tab
        if tab_index is None:
            tab_index = workspace.tab_widget.currentIndex()
        
        # Duplicate the tab
        if hasattr(workspace, 'duplicate_tab'):
            workspace.duplicate_tab(tab_index)
            return CommandResult(success=True, value={"duplicated_tab": tab_index})
        else:
            # Fallback: create a new tab with same name
            if tab_index in workspace.tabs:
                tab_data = workspace.tabs[tab_index]
                new_name = f"{tab_data.name} (Copy)"
                workspace.add_editor_tab(new_name)
                return CommandResult(success=True, value={"new_tab_name": new_name})
            
        return CommandResult(success=False, error="Could not duplicate tab")
        
    except Exception as e:
        logger.error(f"Error duplicating tab: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.closeTabsToRight",
    title="Close Tabs to the Right",
    category="Tabs",
    description="Close all tabs to the right of the current or specified tab"
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
        workspace_service = get_service('WorkspaceService')
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        # Get tab index from context
        tab_index = context.args.get('tab_index')
        
        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")
        
        # If no index provided, use current tab
        if tab_index is None:
            tab_index = workspace.tab_widget.currentIndex()
        
        # Close tabs to the right
        if hasattr(workspace, 'close_tabs_to_right'):
            workspace.close_tabs_to_right(tab_index)
            return CommandResult(success=True, value={"closed_from_index": tab_index + 1})
        
        return CommandResult(success=False, error="Could not close tabs")
        
    except Exception as e:
        logger.error(f"Error closing tabs to right: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.renameTab",
    title="Rename Tab",
    category="Tabs",
    description="Rename the current or specified tab"
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
        workspace_service = get_service('WorkspaceService')
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        # Get tab index from context
        tab_index = context.args.get('tab_index')
        new_name = context.args.get('new_name')
        
        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")
        
        # If no index provided, use current tab
        if tab_index is None:
            tab_index = workspace.tab_widget.currentIndex()
        
        # If new name provided, rename directly
        if new_name:
            workspace.tab_widget.setTabText(tab_index, new_name)
            if tab_index in workspace.tabs:
                workspace.tabs[tab_index].name = new_name
            return CommandResult(success=True, value={"tab_index": tab_index, "new_name": new_name})
        
        # Otherwise, start interactive rename
        if hasattr(workspace, 'start_tab_rename'):
            current_text = workspace.tab_widget.tabText(tab_index)
            workspace.start_tab_rename(tab_index, current_text)
            return CommandResult(success=True, value={"tab_index": tab_index, "mode": "interactive"})
        
        return CommandResult(success=False, error="Could not rename tab")
        
    except Exception as e:
        logger.error(f"Error renaming tab: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.closeOtherTabs",
    title="Close Other Tabs",
    category="Tabs",
    description="Close all tabs except the current or specified one"
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
        workspace_service = get_service('WorkspaceService')
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        # Get tab index from context
        tab_index = context.args.get('tab_index')
        
        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")
        
        # If no index provided, use current tab
        if tab_index is None:
            tab_index = workspace.tab_widget.currentIndex()
        
        # Close other tabs
        if hasattr(workspace, 'close_other_tabs'):
            workspace.close_other_tabs(tab_index)
            return CommandResult(success=True, value={"kept_tab": tab_index})
        
        return CommandResult(success=False, error="Could not close other tabs")
        
    except Exception as e:
        logger.error(f"Error closing other tabs: {e}", exc_info=True)
        return CommandResult(success=False, error=str(e))