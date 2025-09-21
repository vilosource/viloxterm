#!/usr/bin/env python3
"""
Debug-related commands using the service layer.
"""

import logging

from PySide6.QtWidgets import QMessageBox

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.core.commands.decorators import command
from viloapp.services.state_service import StateService
from viloapp.services.ui_service import UIService
from viloapp.services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)


@command(
    id="debug.resetAppState",
    title="Reset Application State",
    category="Debug",
    description="Reset application to default state, clearing all saved settings",
    shortcut="ctrl+shift+r",
    icon="refresh-cw",
)
def reset_app_state_command(context: CommandContext) -> CommandResult:
    """Reset application state using StateService."""
    try:
        # Show confirmation dialog first
        if context.main_window:
            reply = QMessageBox.question(
                context.main_window,
                "Reset Application State",
                "This will reset the application to default state and clear all saved settings.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return CommandResult(success=False, error="User cancelled reset")

        state_service = context.get_service(StateService)
        if not state_service:
            return CommandResult(success=False, error="StateService not available")

        # Reset all saved state
        state_service.reset_all_state()

        # Reset UI to defaults
        ui_service = context.get_service(UIService)
        if ui_service:
            ui_service.reset_layout()

        # Show confirmation message
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message("Application state reset to defaults", 3000)

        return CommandResult(success=True)

    except Exception as e:
        logger.error(f"Failed to reset app state: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="debug.showServiceInfo",
    title="Show Service Information",
    category="Debug",
    description="Display information about all registered services",
    icon="info",
)
def show_service_info_command(context: CommandContext) -> CommandResult:
    """Show information about all services."""
    try:
        from viloapp.services.service_locator import ServiceLocator

        locator = ServiceLocator.get_instance()
        services = locator.get_all()

        info = {"service_count": len(services), "services": []}

        for service in services:
            service_info = {
                "name": service.name,
                "type": type(service).__name__,
                "initialized": service.is_initialized,
            }

            # Get service-specific info if available
            if hasattr(service, "get_service_info"):
                try:
                    service_info.update(service.get_service_info())
                except (AttributeError, RuntimeError, ValueError) as e:
                    import logging

                    logger = logging.getLogger(__name__)
                    logger.debug(f"Failed to get service info from {service.name}: {e}")
                    # Service info not available, continue without it

            info["services"].append(service_info)

        # Show in status bar
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message(
                f"Services: {len(services)} registered", 3000
            )

        return CommandResult(success=True, value=info)

    except Exception as e:
        logger.error(f"Failed to get service info: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="debug.showCommandInfo",
    title="Show Command Information",
    category="Debug",
    description="Display information about all registered commands",
    icon="command",
)
def show_command_info_command(context: CommandContext) -> CommandResult:
    """Show information about all commands."""
    try:
        from viloapp.core.commands.registry import CommandRegistry

        registry = CommandRegistry()
        commands = registry.get_all_commands()

        info = {"command_count": len(commands), "categories": {}, "shortcuts": {}}

        # Group by category
        for command in commands:
            category = command.category
            if category not in info["categories"]:
                info["categories"][category] = []

            cmd_info = {
                "id": command.id,
                "title": command.title,
                "shortcut": command.shortcut,
                "when": command.when,
            }
            info["categories"][category].append(cmd_info)

            # Track shortcuts
            if command.shortcut:
                info["shortcuts"][command.shortcut] = command.id

        # Show in status bar
        if context.main_window and hasattr(context.main_window, "status_bar"):
            categories = len(info["categories"])
            shortcuts = len(info["shortcuts"])
            context.main_window.status_bar.set_message(
                f"Commands: {len(commands)} total, {categories} categories, {shortcuts} shortcuts",
                3000,
            )

        return CommandResult(success=True, value=info)

    except Exception as e:
        logger.error(f"Failed to get command info: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="debug.showWorkspaceInfo",
    title="Show Workspace Information",
    category="Debug",
    description="Display current workspace state information",
    icon="layout",
)
def show_workspace_info_command(context: CommandContext) -> CommandResult:
    """Show workspace information."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        info = workspace_service.get_workspace_info()

        # Show summary in status bar
        if context.main_window and hasattr(context.main_window, "status_bar"):
            if info["available"]:
                msg = f"Workspace: {info['tab_count']} tabs, {info['pane_count']} panes"
            else:
                msg = "Workspace: not available"
            context.main_window.status_bar.set_message(msg, 3000)

        return CommandResult(success=True, value=info)

    except Exception as e:
        logger.error(f"Failed to get workspace info: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="debug.testCommand",
    title="Test Command",
    category="Debug",
    description="Test command for debugging the command system",
    icon="test-tube",
)
def test_command(context: CommandContext) -> CommandResult:
    """Simple test command for debugging."""
    try:
        test_message = context.args.get("message", "Test command executed successfully!")

        # Show in status bar
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message(test_message, 2000)

        logger.info(f"Test command executed: {test_message}")

        return CommandResult(success=True, value={"message": test_message})

    except Exception as e:
        logger.error(f"Test command failed: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="debug.reloadWindow",
    title="Reload Window",
    category="Debug",
    description="Reload the main window (development only)",
    shortcut="ctrl+r",
    icon="refresh",
)
def reload_window_command(context: CommandContext) -> CommandResult:
    """Reload window - placeholder for development."""
    try:
        # This is a placeholder - in a real implementation,
        # this might trigger a window refresh or restart

        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message(
                "Window reload triggered (development feature)", 2000
            )

        logger.info("Window reload command executed")

        return CommandResult(success=True)

    except Exception as e:
        logger.error(f"Failed to reload window: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="debug.toggleDevMode",
    title="Toggle Developer Mode",
    category="Debug",
    description="Enable/disable developer mode features",
    icon="code",
)
def toggle_dev_mode_command(context: CommandContext) -> CommandResult:
    """Toggle developer mode."""
    try:
        # This would toggle development features like extra logging,
        # debug panels, etc. For now, just a placeholder

        state_service = context.get_service(StateService)
        current_dev_mode = False

        if state_service:
            current_dev_mode = state_service.get_preference("dev_mode", False)
            new_dev_mode = not current_dev_mode
            state_service.save_preference("dev_mode", new_dev_mode)
        else:
            new_dev_mode = not current_dev_mode

        # Show status
        if context.main_window and hasattr(context.main_window, "status_bar"):
            status = "enabled" if new_dev_mode else "disabled"
            context.main_window.status_bar.set_message(f"Developer mode {status}", 2000)

        logger.info(f"Developer mode {'enabled' if new_dev_mode else 'disabled'}")

        return CommandResult(success=True, value={"dev_mode": new_dev_mode})

    except Exception as e:
        logger.error(f"Failed to toggle dev mode: {e}")
        return CommandResult(success=False, error=str(e))


def register_debug_commands():
    """Register all debug commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Debug commands registered")
