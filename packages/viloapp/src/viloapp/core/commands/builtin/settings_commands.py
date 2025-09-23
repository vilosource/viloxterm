#!/usr/bin/env python3
"""
Settings-related commands for managing application configuration.
"""

import logging

from PySide6.QtWidgets import QInputDialog, QMessageBox

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)

# Legacy widget registry registration removed
# All widget registration is now handled by AppWidgetManager in core/app_widget_registry.py


@command(
    id="settings.openSettings",
    title="Open Settings",
    category="Settings",
    description="Open application settings dialog",
    shortcut="ctrl+,",
    icon="settings",
)
def open_settings_command(context: CommandContext) -> CommandResult:
    """Open the settings dialog."""
    try:
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # 🚨 SINGLETON PATTERN: Use consistent widget_id for Settings
        # This ensures only one Settings instance exists at a time
        # Get the settings widget ID from registry
        from viloapp.core.app_widget_manager import app_widget_manager
        settings_widgets = [w for w in app_widget_manager.get_available_widget_ids()
                          if app_widget_manager.get_widget_metadata(w) and
                          "settings" in app_widget_manager.get_widget_metadata(w).categories]
        widget_id = settings_widgets[0] if settings_widgets else "com.viloapp.placeholder"

        # Check if settings tab already exists
        for tab in context.model.state.tabs:
            if tab.name == "Settings" or (hasattr(tab, "widget_id") and tab.widget_id == widget_id):
                # Focus existing settings tab
                context.model.state.active_tab_index = context.model.state.tabs.index(tab)
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    data={"widget_id": widget_id, "action": "focused_existing"},
                )

        # Create new settings tab
        from viloapp.core.widget_ids import SETTINGS

        tab_id = context.model.create_tab("Settings", SETTINGS)

        if tab_id:
            return CommandResult(
                status=CommandStatus.SUCCESS, data={"widget_id": widget_id, "action": "created_new"}
            )
        else:
            return CommandResult(
                status=CommandStatus.FAILURE, message="Failed to add Settings to workspace"
            )

    except Exception as e:
        logger.error(f"Failed to open settings: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.resetSettings",
    title="Reset All Settings",
    category="Settings",
    description="Reset all settings to default values",
    icon="refresh",
)
def reset_settings_command(context: CommandContext) -> CommandResult:
    """Reset all settings to defaults."""
    try:
        # SettingsService is an external service, get from ServiceLocator
        from viloapp.core.settings.service import SettingsService
        from viloapp.services.service_locator import ServiceLocator

        settings_service = ServiceLocator.get_instance().get(SettingsService)
        if not settings_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="SettingsService not available"
            )

        # Show confirmation dialog
        if context.main_window:
            reply = QMessageBox.question(
                context.main_window,
                "Reset Settings",
                "This will reset all settings to their default values.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return CommandResult(
                    status=CommandStatus.NOT_APPLICABLE, message="User cancelled reset"
                )

        # Reset settings
        success = settings_service.reset()

        if success:
            message = "All settings reset to defaults"
            if context.main_window and hasattr(context.main_window, "status_bar"):
                context.main_window.status_bar.set_message(message, 3000)

            return CommandResult(status=CommandStatus.SUCCESS, message=message)
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to reset settings")

    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.showSettingsInfo",
    title="Show Settings Information",
    category="Settings",
    description="Display current settings information",
    icon="info",
)
def show_settings_info_command(context: CommandContext) -> CommandResult:
    """Show information about current settings."""
    try:
        # SettingsService is an external service, get from ServiceLocator
        from viloapp.core.settings.service import SettingsService
        from viloapp.services.service_locator import ServiceLocator

        settings_service = ServiceLocator.get_instance().get(SettingsService)
        if not settings_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="SettingsService not available"
            )

        # Get settings info
        service_info = settings_service.get_service_info()
        all_settings = settings_service.get_all()

        info = {
            "service_info": service_info,
            "categories": list(all_settings.keys()),
            "current_theme": settings_service.get_theme(),
            "current_font_size": settings_service.get_font_size(),
        }

        # Show in status bar
        if context.main_window and hasattr(context.main_window, "status_bar"):
            categories = len(service_info.get("categories", []))
            total_settings = service_info.get("total_settings", 0)
            context.main_window.status_bar.set_message(
                f"Settings: {categories} categories, {total_settings} total settings",
                3000,
            )

        return CommandResult(status=CommandStatus.SUCCESS, data=info)

    except Exception as e:
        logger.error(f"Failed to get settings info: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.toggleTheme",
    title="Toggle Theme",
    category="Settings",
    description="Toggle between light and dark themes",
    # Removed ctrl+t to avoid conflict with view.toggleTheme
    icon="sun",
)
def toggle_theme_command(context: CommandContext) -> CommandResult:
    """Toggle between light and dark themes."""
    try:
        # SettingsService is an external service, get from ServiceLocator
        from viloapp.core.settings.service import SettingsService
        from viloapp.services.service_locator import ServiceLocator

        settings_service = ServiceLocator.get_instance().get(SettingsService)
        if not settings_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="SettingsService not available"
            )

        # Get current theme and toggle
        current_theme = settings_service.get_theme()
        new_theme = "light" if current_theme == "dark" else "dark"

        # Update theme
        success = settings_service.set_theme(new_theme)

        if success:
            message = f"Theme changed to {new_theme}"

            # Show in status bar
            if context.main_window and hasattr(context.main_window, "status_bar"):
                context.main_window.status_bar.set_message(message, 2000)

            return CommandResult(status=CommandStatus.SUCCESS, message=message, data={"theme": new_theme})
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to toggle theme")

    except Exception as e:
        logger.error(f"Failed to toggle theme: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.changeFontSize",
    title="Change Font Size",
    category="Settings",
    description="Change the application font size",
    icon="type",
)
def change_font_size_command(context: CommandContext) -> CommandResult:
    """Change the application font size."""
    try:
        # SettingsService is an external service, get from ServiceLocator
        from viloapp.core.settings.service import SettingsService
        from viloapp.services.service_locator import ServiceLocator

        settings_service = ServiceLocator.get_instance().get(SettingsService)
        if not settings_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="SettingsService not available"
            )

        # Get current font size
        current_size = settings_service.get_font_size()

        # Show input dialog
        if context.main_window:
            new_size, ok = QInputDialog.getInt(
                context.main_window,
                "Change Font Size",
                "Enter new font size:",
                current_size,
                8,  # minimum
                72,  # maximum
            )

            if not ok:
                return CommandResult(status=CommandStatus.NOT_APPLICABLE, message="User cancelled")
        else:
            # If no main window, use provided size or increment
            new_size = context.args.get("size", current_size + 1)

        # Update font size
        success = settings_service.set("theme", "font_size", new_size)

        if success:
            message = f"Font size changed to {new_size}px"

            # Show in status bar
            if context.main_window and hasattr(context.main_window, "status_bar"):
                context.main_window.status_bar.set_message(message, 2000)

            return CommandResult(status=CommandStatus.SUCCESS, message=message, data={"font_size": new_size})
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to change font size")

    except Exception as e:
        logger.error(f"Failed to change font size: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.resetKeyboardShortcuts",
    title="Reset Keyboard Shortcuts",
    category="Settings",
    description="Reset all keyboard shortcuts to defaults",
    icon="keyboard",
)
def reset_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    """Reset keyboard shortcuts to defaults."""
    try:
        # SettingsService is an external service, get from ServiceLocator
        from viloapp.core.settings.service import SettingsService
        from viloapp.services.service_locator import ServiceLocator

        settings_service = ServiceLocator.get_instance().get(SettingsService)
        if not settings_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="SettingsService not available"
            )

        # Show confirmation dialog
        if context.main_window:
            reply = QMessageBox.question(
                context.main_window,
                "Reset Keyboard Shortcuts",
                "This will reset all keyboard shortcuts to their default values.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )

            if reply != QMessageBox.Yes:
                return CommandResult(
                    status=CommandStatus.NOT_APPLICABLE, message="User cancelled reset"
                )

        # Reset shortcuts
        success = settings_service.reset_keyboard_shortcuts()

        if success:
            message = "Keyboard shortcuts reset to defaults"

            # Show in status bar
            if context.main_window and hasattr(context.main_window, "status_bar"):
                context.main_window.status_bar.set_message(message, 3000)

            return CommandResult(status=CommandStatus.SUCCESS, message=message)
        else:
            return CommandResult(
                status=CommandStatus.FAILURE, message="Failed to reset keyboard shortcuts"
            )

    except Exception as e:
        logger.error(f"Failed to reset keyboard shortcuts: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.openKeyboardShortcuts",
    title="Keyboard Shortcuts...",
    category="Settings",
    description="Open keyboard shortcuts configuration",
    shortcut="ctrl+k ctrl+s",  # This is a chord, not conflicting with ctrl+s
    icon="keyboard",
)
def open_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    """Open keyboard shortcuts configuration widget."""
    try:
        from viloapp.core.widget_ids import SETTINGS
        from viloapp.services.workspace_service import WorkspaceService

        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="WorkspaceService not available"
            )

        # 🚨 SINGLETON PATTERN: Use consistent widget_id for Shortcuts
        # This ensures only one Shortcuts configuration instance exists at a time
        # Get the shortcuts widget ID from registry
        from viloapp.core.app_widget_manager import app_widget_manager
        shortcut_widgets = [w for w in app_widget_manager.get_available_widget_ids()
                          if app_widget_manager.get_widget_metadata(w) and
                          "shortcuts" in app_widget_manager.get_widget_metadata(w).categories]
        widget_id = shortcut_widgets[0] if shortcut_widgets else "com.viloapp.placeholder"

        # Check for existing Shortcuts instance
        if workspace_service.has_widget(widget_id):
            workspace_service.focus_widget(widget_id)
            return CommandResult(status=CommandStatus.SUCCESS,
                value={
                    "widget_id": widget_id,
                    "message": "Focused existing keyboard shortcuts configuration",
                    "action": "focused_existing",
                },
            )

        # Create and add shortcut configuration widget in a new tab
        # The factory is already registered at module load time
        success = workspace_service.add_app_widget(
            SETTINGS, widget_id, "Keyboard Shortcuts"
        )

        if success:
            return CommandResult(status=CommandStatus.SUCCESS,
                value={
                    "widget_id": widget_id,
                    "message": "Opened keyboard shortcuts configuration",
                    "action": "created_new",
                },
            )
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to create shortcuts configuration tab"
            )

    except Exception as e:
        logger.error(f"Failed to open keyboard shortcuts configuration: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.replaceWithKeyboardShortcuts",
    title="Replace Pane with Keyboard Shortcuts",
    category="Settings",
    description="Replace current pane content with keyboard shortcuts editor",
)
def replace_with_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    """Replace current pane with keyboard shortcuts editor."""
    try:
        from viloapp.services.workspace_service import WorkspaceService

        # Get the pane and pane_id from context
        pane = context.args.get("pane")
        pane_id = context.args.get("pane_id")

        # Get workspace service
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="WorkspaceService not available"
            )

        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(status=CommandStatus.FAILURE, message="No workspace available")

        # Get current tab's split widget
        current_tab = workspace.tab_widget.currentWidget()
        if not current_tab or not hasattr(current_tab, "model"):
            return CommandResult(status=CommandStatus.FAILURE, message="No split widget available")

        # Try to get pane_id if not provided
        if not pane_id:
            if pane and hasattr(pane, "leaf_node") and hasattr(pane.leaf_node, "id"):
                pane_id = pane.leaf_node.id

        if pane_id:
            # Change the pane type through service
            success = workspace_service.change_pane_widget_type(pane_id, "settings")
            if success:
                logger.info(f"Replaced pane {pane_id} with keyboard shortcuts editor")
                return CommandResult(status=CommandStatus.SUCCESS)

        return CommandResult(status=CommandStatus.FAILURE, message="Could not identify pane for replacement")

    except Exception as e:
        logger.error(f"Failed to replace pane with keyboard shortcuts editor: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.showKeyboardShortcuts",
    title="Show Keyboard Shortcuts",
    category="Settings",
    description="Display all keyboard shortcuts",
    icon="keyboard",
)
def show_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    """Show all keyboard shortcuts."""
    try:
        # SettingsService is an external service, get from ServiceLocator
        from viloapp.core.settings.service import SettingsService
        from viloapp.services.service_locator import ServiceLocator

        settings_service = ServiceLocator.get_instance().get(SettingsService)
        if not settings_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="SettingsService not available"
            )

        # Get keyboard shortcuts
        shortcuts = settings_service.get_keyboard_shortcuts()

        # Filter out empty shortcuts and sort
        active_shortcuts = {
            cmd: shortcut for cmd, shortcut in shortcuts.items() if shortcut.strip()
        }

        # Show in status bar
        if context.main_window and hasattr(context.main_window, "status_bar"):
            total_shortcuts = len(shortcuts)
            active_count = len(active_shortcuts)
            context.main_window.status_bar.set_message(
                f"Shortcuts: {active_count} active of {total_shortcuts} total", 3000
            )

        return CommandResult(status=CommandStatus.SUCCESS,
            value={
                "shortcuts": shortcuts,
                "active_shortcuts": active_shortcuts,
                "total": len(shortcuts),
                "active": len(active_shortcuts),
            },
        )

    except Exception as e:
        logger.error(f"Failed to show keyboard shortcuts: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.setKeyboardShortcut",
    title="Set Keyboard Shortcut",
    category="Settings",
    description="Set keyboard shortcut for a specific command",
)
def set_keyboard_shortcut_command(context: CommandContext) -> CommandResult:
    """Set keyboard shortcut for a command."""
    try:
        command_id = context.args.get("command_id")
        shortcut = context.args.get("shortcut")

        if not command_id:
            return CommandResult(status=CommandStatus.FAILURE, message="command_id is required")

        # SettingsService is an external service, get from ServiceLocator
        from viloapp.core.settings.service import SettingsService
        from viloapp.services.service_locator import ServiceLocator

        settings_service = ServiceLocator.get_instance().get(SettingsService)
        if not settings_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="SettingsService not available"
            )

        # Set the shortcut
        settings_service.set_keyboard_shortcut(command_id, shortcut or "")

        return CommandResult(
            status=CommandStatus.SUCCESS, data={"command_id": command_id, "shortcut": shortcut}
        )

    except Exception as e:
        logger.error(f"Failed to set keyboard shortcut: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="settings.registerKeyboardShortcut",
    title="Register Keyboard Shortcut",
    category="Settings",
    description="Register a keyboard shortcut with the keyboard service",
)
def register_keyboard_shortcut_command(context: CommandContext) -> CommandResult:
    """Register a keyboard shortcut with the keyboard service."""
    try:
        from viloapp.core.commands.registry import command_registry
        from viloapp.core.keyboard.service import KeyboardService

        command_id = context.args.get("command_id")
        shortcut = context.args.get("shortcut")

        if not command_id:
            return CommandResult(status=CommandStatus.FAILURE, message="command_id is required")

        keyboard_service = context.get_service(KeyboardService)
        if not keyboard_service:
            return CommandResult(
                status=CommandStatus.FAILURE, message="KeyboardService not available"
            )

        # Unregister old shortcut first
        keyboard_service.unregister_shortcut(f"command.{command_id}")

        # Register new shortcut if provided
        if shortcut:
            command = command_registry.get_command(command_id)
            if command:
                keyboard_service.register_shortcut_from_string(
                    shortcut_id=f"command.{command_id}",
                    sequence_str=shortcut,
                    command_id=command_id,
                    description=command.description or command.title,
                    source="user",
                    priority=100,  # User shortcuts have higher priority
                )

        return CommandResult(
            status=CommandStatus.SUCCESS, data={"command_id": command_id, "shortcut": shortcut}
        )

    except Exception as e:
        logger.error(f"Failed to register keyboard shortcut: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_settings_commands():
    """Register all settings commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Settings commands registered")
