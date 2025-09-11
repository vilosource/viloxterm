#!/usr/bin/env python3
"""
Workspace-related commands using the service layer.
"""

from core.commands.base import Command, CommandResult, CommandContext
from core.commands.decorators import command
from services.workspace_service import WorkspaceService
import logging

logger = logging.getLogger(__name__)


@command(
    id="workbench.action.splitRight",
    title="Split Pane Right",
    category="Workspace",
    description="Split the active pane horizontally",
    shortcut="ctrl+\\",
    icon="split-horizontal",
    when="workbench.pane.canSplit"
)
def split_pane_right_command(context: CommandContext) -> CommandResult:
    """Split active pane horizontally using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        new_pane_id = workspace_service.split_active_pane("horizontal")
        
        if new_pane_id:
            return CommandResult(
                success=True,
                value={'new_pane_id': new_pane_id}
            )
        else:
            return CommandResult(success=False, error="Failed to split pane")
            
    except Exception as e:
        logger.error(f"Failed to split pane right: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.splitDown",
    title="Split Pane Down",
    category="Workspace",
    description="Split the active pane vertically",
    shortcut="ctrl+shift+\\",
    icon="split-vertical",
    when="workbench.pane.canSplit"
)
def split_pane_down_command(context: CommandContext) -> CommandResult:
    """Split active pane vertically using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        new_pane_id = workspace_service.split_active_pane("vertical")
        
        if new_pane_id:
            return CommandResult(
                success=True,
                value={'new_pane_id': new_pane_id}
            )
        else:
            return CommandResult(success=False, error="Failed to split pane")
            
    except Exception as e:
        logger.error(f"Failed to split pane down: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.closeActivePane",
    title="Close Active Pane",
    category="Workspace",
    description="Close the active pane",
    shortcut="ctrl+k w",
    icon="x",
    when="workbench.pane.count > 1"
)
def close_active_pane_command(context: CommandContext) -> CommandResult:
    """Close active pane using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        success = workspace_service.close_active_pane()
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Cannot close the last pane")
            
    except Exception as e:
        logger.error(f"Failed to close active pane: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.focusNextPane",
    title="Focus Next Pane",
    category="Workspace",
    description="Focus the next pane",
    shortcut="tab",
    when="workbench.pane.count > 1"
)
def focus_next_pane_command(context: CommandContext) -> CommandResult:
    """Focus next pane using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        success = workspace_service.navigate_to_next_pane()
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to navigate to next pane")
            
    except Exception as e:
        logger.error(f"Failed to focus next pane: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.focusPreviousPane",
    title="Focus Previous Pane",
    category="Workspace",
    description="Focus the previous pane",
    shortcut="shift+tab",
    when="workbench.pane.count > 1"
)
def focus_previous_pane_command(context: CommandContext) -> CommandResult:
    """Focus previous pane using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        success = workspace_service.navigate_to_previous_pane()
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to navigate to previous pane")
            
    except Exception as e:
        logger.error(f"Failed to focus previous pane: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.nextTab",
    title="Next Tab",
    category="Workspace",
    description="Switch to the next tab",
    shortcut="ctrl+pagedown",
    when="workbench.tabs.count > 1"
)
def next_tab_command(context: CommandContext) -> CommandResult:
    """Switch to next tab using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        current = workspace_service.get_current_tab_index()
        count = workspace_service.get_tab_count()
        
        if count > 1:
            next_index = (current + 1) % count
            success = workspace_service.switch_to_tab(next_index)
            
            if success:
                return CommandResult(success=True, value={'tab_index': next_index})
        
        return CommandResult(success=False, error="No other tabs to switch to")
        
    except Exception as e:
        logger.error(f"Failed to switch to next tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.previousTab",
    title="Previous Tab",
    category="Workspace",
    description="Switch to the previous tab",
    shortcut="ctrl+pageup",
    when="workbench.tabs.count > 1"
)
def previous_tab_command(context: CommandContext) -> CommandResult:
    """Switch to previous tab using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        current = workspace_service.get_current_tab_index()
        count = workspace_service.get_tab_count()
        
        if count > 1:
            prev_index = (current - 1) % count
            success = workspace_service.switch_to_tab(prev_index)
            
            if success:
                return CommandResult(success=True, value={'tab_index': prev_index})
        
        return CommandResult(success=False, error="No other tabs to switch to")
        
    except Exception as e:
        logger.error(f"Failed to switch to previous tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.saveLayout",
    title="Save Workspace Layout",
    category="Workspace",
    description="Save the current workspace layout",
    icon="save"
)
def save_layout_command(context: CommandContext) -> CommandResult:
    """Save workspace layout using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        layout = workspace_service.save_layout()
        
        # Show status message
        if context.main_window and hasattr(context.main_window, 'status_bar'):
            context.main_window.status_bar.set_message("Layout saved", 2000)
        
        return CommandResult(success=True, value={'layout': layout})
        
    except Exception as e:
        logger.error(f"Failed to save layout: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.restoreLayout",
    title="Restore Workspace Layout",
    category="Workspace",
    description="Restore the saved workspace layout",
    icon="refresh"
)
def restore_layout_command(context: CommandContext) -> CommandResult:
    """Restore workspace layout using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        # Get layout from context args or use saved one
        layout = context.args.get('layout')
        if layout:
            success = workspace_service.restore_layout(layout)
            
            if success:
                # Show status message
                if context.main_window and hasattr(context.main_window, 'status_bar'):
                    context.main_window.status_bar.set_message("Layout restored", 2000)
                
                return CommandResult(success=True)
        
        return CommandResult(success=False, error="No layout to restore")
        
    except Exception as e:
        logger.error(f"Failed to restore layout: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.renamePane",
    title="Rename Pane",
    category="Workspace",
    description="Rename the active pane",
    shortcut="f2",
    when="workbench.pane.focused"
)
def rename_pane_command(context: CommandContext) -> CommandResult:
    """Rename the active pane."""
    # Will be implemented with UI integration
    return CommandResult(success=True)


def register_workspace_commands():
    """Register all workspace commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Workspace commands registered")