#!/usr/bin/env python3
"""
File-related commands using the service layer.
"""

from core.commands.base import Command, CommandResult, CommandContext
from core.commands.registry import CommandRegistry
from core.commands.decorators import command
from services.workspace_service import WorkspaceService
from services.terminal_service import TerminalService
from services.state_service import StateService
import logging

logger = logging.getLogger(__name__)


@command(
    id="file.newEditorTab",
    title="New Editor Tab",
    category="File",
    description="Create a new editor tab",
    shortcut="ctrl+n",
    icon="file-plus"
)
def new_editor_tab_command(context: CommandContext) -> CommandResult:
    """Create a new editor tab using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        name = context.args.get('name')
        index = workspace_service.add_editor_tab(name)
        
        return CommandResult(
            success=True,
            value={'index': index, 'name': name or f"Editor {index + 1}"}
        )
    except Exception as e:
        logger.error(f"Failed to create editor tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="file.newTerminalTab",
    title="New Terminal Tab",
    category="File",
    description="Create a new terminal tab",
    shortcut="ctrl+`",
    icon="terminal"
)
def new_terminal_tab_command(context: CommandContext) -> CommandResult:
    """Create a new terminal tab using WorkspaceService and TerminalService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        terminal_service = context.get_service(TerminalService)
        
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        # Ensure terminal server is running
        if terminal_service and not terminal_service.is_server_running():
            terminal_service.start_server()
        
        name = context.args.get('name')
        index = workspace_service.add_terminal_tab(name)
        
        # Create a terminal session for this tab
        if terminal_service:
            session_id = terminal_service.create_session()
            logger.debug(f"Created terminal session {session_id} for tab {index}")
        
        return CommandResult(
            success=True,
            value={'index': index, 'name': name or f"Terminal {index + 1}"}
        )
    except Exception as e:
        logger.error(f"Failed to create terminal tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="file.closeTab",
    title="Close Tab",
    category="File",
    description="Close the current tab",
    shortcut="ctrl+w",
    when="workbench.tabs.count > 0"
)
def close_tab_command(context: CommandContext) -> CommandResult:
    """Close the current tab using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")
        
        index = context.args.get('index')  # Optional specific tab index
        success = workspace_service.close_tab(index)
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to close tab")
            
    except Exception as e:
        logger.error(f"Failed to close tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="file.saveState",
    title="Save Application State",
    category="File",
    description="Save the current application state",
    shortcut="ctrl+s"
)
def save_state_command(context: CommandContext) -> CommandResult:
    """Save application state using StateService."""
    try:
        state_service = context.get_service(StateService)
        if not state_service:
            return CommandResult(success=False, error="StateService not available")
        
        state_service.save_all_state()
        
        # Show status message
        if context.main_window and hasattr(context.main_window, 'status_bar'):
            context.main_window.status_bar.set_message("State saved", 2000)
        
        return CommandResult(success=True)
        
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="file.restoreState", 
    title="Restore Application State",
    category="File",
    description="Restore the saved application state"
)
def restore_state_command(context: CommandContext) -> CommandResult:
    """Restore application state using StateService."""
    try:
        state_service = context.get_service(StateService)
        if not state_service:
            return CommandResult(success=False, error="StateService not available")
        
        success = state_service.restore_all_state()
        
        if success:
            # Show status message
            if context.main_window and hasattr(context.main_window, 'status_bar'):
                context.main_window.status_bar.set_message("State restored", 2000)
            
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="No saved state found")
            
    except Exception as e:
        logger.error(f"Failed to restore state: {e}")
        return CommandResult(success=False, error=str(e))


def register_file_commands():
    """Register all file commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("File commands registered")