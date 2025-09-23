#!/usr/bin/env python3
"""
Debug-related commands using the service layer.
"""

import logging

from PySide6.QtWidgets import QMessageBox

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

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
                return CommandResult(
                    status=CommandStatus.NOT_APPLICABLE, message="User cancelled reset"
                )

        # Reset saved state directly via QSettings
        from PySide6.QtCore import QSettings

        settings = QSettings("ViloxTerm", "ViloxTerm")
        settings.clear()
        settings.sync()

        # Reset model state if available
        if context.model:
            # Reset to default state - get default terminal widget
            from viloapp.core.app_widget_manager import app_widget_manager
            from viloapp.core.app_widget_metadata import WidgetCategory

            terminal_widget_id = app_widget_manager.get_default_widget_for_category(WidgetCategory.TERMINAL)
            if not terminal_widget_id:
                # Fallback to any available widget
                terminal_widget_id = app_widget_manager.get_default_widget_id()

            context.model.state.tabs.clear()
            if terminal_widget_id:
                context.model.create_tab("Terminal 1", terminal_widget_id)

        # Show confirmation message
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message("Application state reset to defaults", 3000)

        return CommandResult(status=CommandStatus.SUCCESS)

    except Exception as e:
        logger.error(f"Failed to reset app state: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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

        return CommandResult(status=CommandStatus.SUCCESS, data=info)

    except Exception as e:
        logger.error(f"Failed to get service info: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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

        return CommandResult(status=CommandStatus.SUCCESS, data=info)

    except Exception as e:
        logger.error(f"Failed to get command info: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        # Get workspace info directly from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        info = {
            "available": True,
            "tab_count": len(context.model.state.tabs),
            "active_tab_id": context.model.state.active_tab_id,
            "pane_count": sum(
                len(tab.tree.root.get_all_panes()) for tab in context.model.state.tabs
            ),
            "tabs": [
                {"name": tab.name, "id": tab.id, "pane_count": len(tab.tree.root.get_all_panes())}
                for tab in context.model.state.tabs
            ],
        }

        # Show summary in status bar
        if context.main_window and hasattr(context.main_window, "status_bar"):
            if info["available"]:
                msg = f"Workspace: {info['tab_count']} tabs, {info['pane_count']} panes"
            else:
                msg = "Workspace: not available"
            context.main_window.status_bar.set_message(msg, 3000)

        return CommandResult(status=CommandStatus.SUCCESS, data=info)

    except Exception as e:
        logger.error(f"Failed to get workspace info: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        test_message = (
            context.parameters.get("message", "Test command executed successfully!")
            if context.parameters
            else "Test command executed successfully!"
        )

        # Show in status bar
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message(test_message, 2000)

        logger.info(f"Test command executed: {test_message}")

        return CommandResult(status=CommandStatus.SUCCESS, data={"message": test_message})

    except Exception as e:
        logger.error(f"Test command failed: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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

        return CommandResult(status=CommandStatus.SUCCESS)

    except Exception as e:
        logger.error(f"Failed to reload window: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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

        # Toggle development features directly via QSettings
        from PySide6.QtCore import QSettings

        settings = QSettings("ViloxTerm", "ViloxTerm")

        current_dev_mode = settings.value("dev_mode", False, type=bool)
        new_dev_mode = not current_dev_mode
        settings.setValue("dev_mode", new_dev_mode)
        settings.sync()

        # Show status
        if context.main_window and hasattr(context.main_window, "status_bar"):
            status = "enabled" if new_dev_mode else "disabled"
            context.main_window.status_bar.set_message(f"Developer mode {status}", 2000)

        logger.info(f"Developer mode {'enabled' if new_dev_mode else 'disabled'}")

        return CommandResult(status=CommandStatus.SUCCESS, data={"dev_mode": new_dev_mode})

    except Exception as e:
        logger.error(f"Failed to toggle dev mode: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_debug_commands():
    """Register all debug commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Debug commands registered")
