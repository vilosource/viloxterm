#!/usr/bin/env python3
"""
File-related commands using the service layer.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="file.newEditorTab",
    title="New Editor Tab",
    category="File",
    description="Create a new editor tab",
    shortcut="ctrl+shift+n",
    icon="file-plus",
)
def new_editor_tab_command(context: CommandContext) -> CommandResult:
    """Create a new editor tab using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "create_tab"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        name = context.parameters.get("name") if context.parameters else None
        if not name:
            # Count existing editor tabs for naming
            editor_count = sum(1 for tab in context.model.state.tabs if "Editor" in tab.name)
            name = f"Editor {editor_count + 1}"

        # Create tab with editor widget type
        from viloapp.models.workspace_model import WidgetType

        tab_id = context.model.create_tab(name, WidgetType.EDITOR)
        index = len(context.model.state.tabs) - 1

        return CommandResult(
            status=CommandStatus.SUCCESS, data={"index": index, "name": name, "tab_id": tab_id}
        )
    except Exception as e:
        logger.error(f"Failed to create editor tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="file.newTerminalTab",
    title="New Terminal Tab",
    category="File",
    description="Create a new terminal tab",
    shortcut="ctrl+n",
    icon="terminal",
)
def new_terminal_tab_command(context: CommandContext) -> CommandResult:
    """Create a new terminal tab using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "create_tab"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Terminal service is external, so we keep it for server management
        # But we get it from ServiceLocator instead of context
        try:
            from viloapp.services.service_locator import ServiceLocator
            from viloapp.services.terminal_service import TerminalService

            terminal_service = ServiceLocator.get_instance().get(TerminalService)

            # Ensure terminal server is running
            if terminal_service and not terminal_service.is_server_running():
                terminal_service.start_server()
        except Exception:
            # Terminal service is optional
            pass

        name = context.parameters.get("name") if context.parameters else None
        if not name:
            # Count existing terminal tabs for naming
            terminal_count = sum(1 for tab in context.model.state.tabs if "Terminal" in tab.name)
            name = f"Terminal {terminal_count + 1}"

        # Create tab with terminal widget type
        from viloapp.models.workspace_model import WidgetType

        tab_id = context.model.create_tab(name, WidgetType.TERMINAL)
        index = len(context.model.state.tabs) - 1

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"index": index, "name": name, "tab_id": tab_id},
        )
    except Exception as e:
        logger.error(f"Failed to create terminal tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="terminal.newTerminal",
    title="New Terminal",
    category="Terminal",
    description="Create a new terminal tab",
    shortcut="ctrl+`",
    icon="terminal",
)
def new_terminal_command(context: CommandContext) -> CommandResult:
    """Alias for new_terminal_tab_command with backtick shortcut."""
    return new_terminal_tab_command(context)


@command(
    id="file.closeTab",
    title="Close Tab",
    category="File",
    description="Close the current tab",
    shortcut="ctrl+w",
    when="workbench.tabs.count > 0",
)
def close_tab_command(context: CommandContext) -> CommandResult:
    """Close the current tab using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "close_tab"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        index = context.parameters.get("index") if context.parameters else None

        # If index provided, get tab by index
        if index is not None:
            tabs = context.model.state.tabs
            if 0 <= index < len(tabs):
                tab_id = tabs[index].id
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE, message=f"Invalid tab index: {index}"
                )
        else:
            # Use active tab
            active_tab = context.model.state.get_active_tab()
            if not active_tab:
                return CommandResult(status=CommandStatus.FAILURE, message="No active tab")
            tab_id = active_tab.id

        # Don't close last tab
        if len(context.model.state.tabs) == 1:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Cannot close last tab"
            )

        success = context.model.close_tab(tab_id)

        if success:
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to close tab")

    except Exception as e:
        logger.error(f"Failed to close tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="file.saveState",
    title="Save Application State",
    category="File",
    description="Save the current application state",
    shortcut="ctrl+s",
)
def save_state_command(context: CommandContext) -> CommandResult:
    """Save application state using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "save_state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        state_dict = context.model.save_state()

        # Save to persistent storage (QSettings)
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()
            import json

            settings.setValue("Workspace/state", json.dumps(state_dict))
            settings.sync()
        except Exception as e:
            logger.warning(f"Failed to persist state: {e}")

        # Show status message
        if context.parameters and context.parameters.get("main_window"):
            main_window = context.parameters.get("main_window")
            if hasattr(main_window, "status_bar"):
                main_window.status_bar.set_message("State saved", 2000)

        return CommandResult(status=CommandStatus.SUCCESS)

    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="file.restoreState",
    title="Restore Application State",
    category="File",
    description="Restore the saved application state",
)
def restore_state_command(context: CommandContext) -> CommandResult:
    """Restore application state using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "load_state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Load from persistent storage (QSettings)
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()
            import json

            state_json = settings.value("Workspace/state")
            if state_json:
                state_dict = json.loads(state_json)
                context.model.load_state(state_dict)

                # Show status message
                if context.parameters and context.parameters.get("main_window"):
                    main_window = context.parameters.get("main_window")
                    if hasattr(main_window, "status_bar"):
                        main_window.status_bar.set_message("State restored", 2000)

                return CommandResult(status=CommandStatus.SUCCESS)
            else:
                return CommandResult(status=CommandStatus.FAILURE, message="No saved state found")
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE, message=f"Failed to load state: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Failed to restore state: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="file.replaceWithTerminal",
    title="Replace Pane with Terminal",
    category="File",
    description="Replace current pane content with terminal",
)
def replace_with_terminal_command(context: CommandContext) -> CommandResult:
    """Replace current pane with terminal."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "change_pane_widget_type"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get the pane and pane_id from context
        pane = context.parameters.get("pane") if context.parameters else None
        pane_id = context.parameters.get("pane_id") if context.parameters else None

        # Try to get pane_id if not provided
        if not pane_id:
            if pane and hasattr(pane, "leaf_node") and hasattr(pane.leaf_node, "id"):
                pane_id = pane.leaf_node.id
            else:
                # Use active pane
                active_tab = context.model.state.get_active_tab()
                if active_tab and active_tab.active_pane_id:
                    pane_id = active_tab.active_pane_id

        if pane_id:
            # Change the pane type through model
            from viloapp.models.workspace_model import WidgetType

            success = context.model.change_pane_widget_type(pane_id, WidgetType.TERMINAL)
            if success:
                logger.info(f"Replaced pane {pane_id} with terminal")
                return CommandResult(status=CommandStatus.SUCCESS)
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE, message="Failed to change pane type"
                )

        return CommandResult(
            status=CommandStatus.FAILURE, message="Could not identify pane for replacement"
        )

    except Exception as e:
        logger.error(f"Failed to replace pane with terminal: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="file.replaceWithEditor",
    title="Replace Pane with Editor",
    category="File",
    description="Replace current pane content with text editor",
)
def replace_with_editor_command(context: CommandContext) -> CommandResult:
    """Replace current pane with text editor."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "change_pane_widget_type"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get the pane and pane_id from context
        pane = context.parameters.get("pane") if context.parameters else None
        pane_id = context.parameters.get("pane_id") if context.parameters else None

        # Try to get pane_id if not provided
        if not pane_id:
            if pane and hasattr(pane, "leaf_node") and hasattr(pane.leaf_node, "id"):
                pane_id = pane.leaf_node.id
            else:
                # Use active pane
                active_tab = context.model.state.get_active_tab()
                if active_tab and active_tab.active_pane_id:
                    pane_id = active_tab.active_pane_id

        if pane_id:
            # Change the pane type through model
            from viloapp.models.workspace_model import WidgetType

            success = context.model.change_pane_widget_type(pane_id, WidgetType.EDITOR)
            if success:
                logger.info(f"Replaced pane {pane_id} with text editor")
                return CommandResult(status=CommandStatus.SUCCESS)
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE, message="Failed to change pane type"
                )

        return CommandResult(
            status=CommandStatus.FAILURE, message="Could not identify pane for replacement"
        )

    except Exception as e:
        logger.error(f"Failed to replace pane with editor: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_file_commands():
    """Register all file commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("File commands registered")
