#!/usr/bin/env python3
"""
Settings-related commands for managing application configuration.
"""

from core.commands.base import Command, CommandResult, CommandContext
from core.commands.decorators import command
from core.settings.service import SettingsService
from PySide6.QtWidgets import QMessageBox, QInputDialog
import logging

logger = logging.getLogger(__name__)

# Register the shortcut configuration widget factory at module load time
def _register_shortcut_config_widget():
    """Register the shortcut configuration widget factory."""
    try:
        from ui.widgets.shortcut_config_app_widget import ShortcutConfigAppWidget
        from ui.widgets.widget_registry import widget_registry, WidgetType

        def create_shortcut_config_widget(widget_id: str) -> ShortcutConfigAppWidget:
            return ShortcutConfigAppWidget(widget_id)

        # NOTE: Widget registration now handled by AppWidgetManager in core/app_widget_registry.py
        # This legacy registration is kept for backward compatibility but is deprecated
        widget_registry.register_factory(WidgetType.SETTINGS, create_shortcut_config_widget)
        logger.debug("Registered shortcut configuration widget factory (deprecated - now handled by AppWidgetManager)")
    except ImportError as e:
        logger.error(f"Failed to register shortcut config widget: {e}")

# Register the factory when this module is imported
_register_shortcut_config_widget()


@command(
    id="settings.openSettings", 
    title="Open Settings",
    category="Settings",
    description="Open application settings dialog",
    shortcut="ctrl+,",
    icon="settings"
)
def open_settings_command(context: CommandContext) -> CommandResult:
    """Open the settings dialog."""
    try:
        # For now, show a message that settings UI is coming soon
        if context.main_window:
            QMessageBox.information(
                context.main_window,
                "Settings",
                "Settings UI is coming soon!\n\n"
                "Currently available settings commands:\n"
                "• Reset Settings\n"
                "• Show Settings Information\n"
                "• Toggle Theme\n"
                "• Change Font Size"
            )
        
        return CommandResult(success=True, message="Settings dialog shown")
        
    except Exception as e:
        logger.error(f"Failed to open settings: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="settings.resetSettings",
    title="Reset All Settings",
    category="Settings",
    description="Reset all settings to default values",
    icon="refresh"
)
def reset_settings_command(context: CommandContext) -> CommandResult:
    """Reset all settings to defaults."""
    try:
        settings_service = context.get_service(SettingsService)
        if not settings_service:
            return CommandResult(success=False, error="SettingsService not available")
        
        # Show confirmation dialog
        if context.main_window:
            reply = QMessageBox.question(
                context.main_window,
                "Reset Settings",
                "This will reset all settings to their default values.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return CommandResult(success=False, error="User cancelled reset")
        
        # Reset settings
        success = settings_service.reset()
        
        if success:
            message = "All settings reset to defaults"
            if context.main_window and hasattr(context.main_window, 'status_bar'):
                context.main_window.status_bar.set_message(message, 3000)
            
            return CommandResult(success=True, message=message)
        else:
            return CommandResult(success=False, error="Failed to reset settings")
        
    except Exception as e:
        logger.error(f"Failed to reset settings: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="settings.showSettingsInfo",
    title="Show Settings Information",
    category="Settings",
    description="Display current settings information",
    icon="info"
)
def show_settings_info_command(context: CommandContext) -> CommandResult:
    """Show information about current settings."""
    try:
        settings_service = context.get_service(SettingsService)
        if not settings_service:
            return CommandResult(success=False, error="SettingsService not available")
        
        # Get settings info
        service_info = settings_service.get_service_info()
        all_settings = settings_service.get_all()
        
        info = {
            'service_info': service_info,
            'categories': list(all_settings.keys()),
            'current_theme': settings_service.get_theme(),
            'current_font_size': settings_service.get_font_size(),
        }
        
        # Show in status bar
        if context.main_window and hasattr(context.main_window, 'status_bar'):
            categories = len(service_info.get('categories', []))
            total_settings = service_info.get('total_settings', 0)
            context.main_window.status_bar.set_message(
                f"Settings: {categories} categories, {total_settings} total settings", 3000
            )
        
        return CommandResult(success=True, value=info)
        
    except Exception as e:
        logger.error(f"Failed to get settings info: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="settings.toggleTheme",
    title="Toggle Theme",
    category="Settings",
    description="Toggle between light and dark themes",
    # Removed ctrl+t to avoid conflict with view.toggleTheme
    icon="sun"
)
def toggle_theme_command(context: CommandContext) -> CommandResult:
    """Toggle between light and dark themes."""
    try:
        settings_service = context.get_service(SettingsService)
        if not settings_service:
            return CommandResult(success=False, error="SettingsService not available")
        
        # Get current theme and toggle
        current_theme = settings_service.get_theme()
        new_theme = "light" if current_theme == "dark" else "dark"
        
        # Update theme
        success = settings_service.set_theme(new_theme)
        
        if success:
            message = f"Theme changed to {new_theme}"
            
            # Show in status bar
            if context.main_window and hasattr(context.main_window, 'status_bar'):
                context.main_window.status_bar.set_message(message, 2000)
            
            return CommandResult(success=True, message=message, value={'theme': new_theme})
        else:
            return CommandResult(success=False, error="Failed to toggle theme")
        
    except Exception as e:
        logger.error(f"Failed to toggle theme: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="settings.changeFontSize",
    title="Change Font Size",
    category="Settings",
    description="Change the application font size",
    icon="type"
)
def change_font_size_command(context: CommandContext) -> CommandResult:
    """Change the application font size."""
    try:
        settings_service = context.get_service(SettingsService)
        if not settings_service:
            return CommandResult(success=False, error="SettingsService not available")
        
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
                72  # maximum
            )
            
            if not ok:
                return CommandResult(success=False, error="User cancelled")
        else:
            # If no main window, use provided size or increment
            new_size = context.args.get('size', current_size + 1)
        
        # Update font size
        success = settings_service.set("theme", "font_size", new_size)
        
        if success:
            message = f"Font size changed to {new_size}px"
            
            # Show in status bar
            if context.main_window and hasattr(context.main_window, 'status_bar'):
                context.main_window.status_bar.set_message(message, 2000)
            
            return CommandResult(success=True, message=message, value={'font_size': new_size})
        else:
            return CommandResult(success=False, error="Failed to change font size")
        
    except Exception as e:
        logger.error(f"Failed to change font size: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="settings.resetKeyboardShortcuts",
    title="Reset Keyboard Shortcuts",
    category="Settings", 
    description="Reset all keyboard shortcuts to defaults",
    icon="keyboard"
)
def reset_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    """Reset keyboard shortcuts to defaults."""
    try:
        settings_service = context.get_service(SettingsService)
        if not settings_service:
            return CommandResult(success=False, error="SettingsService not available")
        
        # Show confirmation dialog
        if context.main_window:
            reply = QMessageBox.question(
                context.main_window,
                "Reset Keyboard Shortcuts",
                "This will reset all keyboard shortcuts to their default values.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return CommandResult(success=False, error="User cancelled reset")
        
        # Reset shortcuts
        success = settings_service.reset_keyboard_shortcuts()
        
        if success:
            message = "Keyboard shortcuts reset to defaults"
            
            # Show in status bar
            if context.main_window and hasattr(context.main_window, 'status_bar'):
                context.main_window.status_bar.set_message(message, 3000)
            
            return CommandResult(success=True, message=message)
        else:
            return CommandResult(success=False, error="Failed to reset keyboard shortcuts")
        
    except Exception as e:
        logger.error(f"Failed to reset keyboard shortcuts: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="settings.openKeyboardShortcuts",
    title="Keyboard Shortcuts...",
    category="Settings",
    description="Open keyboard shortcuts configuration",
    shortcut="ctrl+k ctrl+s",  # This is a chord, not conflicting with ctrl+s
    icon="keyboard"
)
def open_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    """Open keyboard shortcuts configuration widget."""
    try:
        from services.workspace_service import WorkspaceService
        from ui.widgets.widget_registry import WidgetType
        import uuid

        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Create and add shortcut configuration widget in a new tab
        # The factory is already registered at module load time
        widget_id = f"shortcuts_config_{uuid.uuid4().hex[:8]}"
        success = workspace_service.add_app_widget(WidgetType.SETTINGS, widget_id, "Keyboard Shortcuts")

        if success:
            return CommandResult(
                success=True,
                value={'widget_id': widget_id, 'message': 'Opened keyboard shortcuts configuration'}
            )
        else:
            return CommandResult(success=False, error="Failed to create shortcuts configuration tab")

    except Exception as e:
        logger.error(f"Failed to open keyboard shortcuts configuration: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="settings.replaceWithKeyboardShortcuts",
    title="Replace Pane with Keyboard Shortcuts",
    category="Settings",
    description="Replace current pane content with keyboard shortcuts editor"
)
def replace_with_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    """Replace current pane with keyboard shortcuts editor."""
    try:
        from ui.widgets.widget_registry import WidgetType
        from services.workspace_service import WorkspaceService

        # Get the pane and pane_id from context
        pane = context.args.get('pane')
        pane_id = context.args.get('pane_id')

        # Get workspace service
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get workspace
        workspace = workspace_service.get_workspace()
        if not workspace:
            return CommandResult(success=False, error="No workspace available")

        # Get current tab's split widget
        current_tab = workspace.tab_widget.currentWidget()
        if not current_tab or not hasattr(current_tab, 'model'):
            return CommandResult(success=False, error="No split widget available")

        split_widget = current_tab

        # Try to get pane_id if not provided
        if not pane_id:
            if pane and hasattr(pane, 'leaf_node') and hasattr(pane.leaf_node, 'id'):
                pane_id = pane.leaf_node.id

        if pane_id:
            # Change the pane type directly to SETTINGS (which triggers the shortcuts widget factory)
            success = split_widget.model.change_pane_type(pane_id, WidgetType.SETTINGS)
            if success:
                split_widget.refresh_view()
                logger.info(f"Replaced pane {pane_id} with keyboard shortcuts editor")
                return CommandResult(success=True)

        return CommandResult(
            success=False,
            error="Could not identify pane for replacement"
        )

    except Exception as e:
        logger.error(f"Failed to replace pane with keyboard shortcuts editor: {e}")
        return CommandResult(
            success=False,
            error=str(e)
        )


@command(
    id="settings.showKeyboardShortcuts",
    title="Show Keyboard Shortcuts",
    category="Settings",
    description="Display all keyboard shortcuts",
    icon="keyboard"
)
def show_keyboard_shortcuts_command(context: CommandContext) -> CommandResult:
    """Show all keyboard shortcuts."""
    try:
        settings_service = context.get_service(SettingsService)
        if not settings_service:
            return CommandResult(success=False, error="SettingsService not available")

        # Get keyboard shortcuts
        shortcuts = settings_service.get_keyboard_shortcuts()

        # Filter out empty shortcuts and sort
        active_shortcuts = {cmd: shortcut for cmd, shortcut in shortcuts.items() if shortcut.strip()}

        # Show in status bar
        if context.main_window and hasattr(context.main_window, 'status_bar'):
            total_shortcuts = len(shortcuts)
            active_count = len(active_shortcuts)
            context.main_window.status_bar.set_message(
                f"Shortcuts: {active_count} active of {total_shortcuts} total", 3000
            )

        return CommandResult(
            success=True,
            value={
                'shortcuts': shortcuts,
                'active_shortcuts': active_shortcuts,
                'total': len(shortcuts),
                'active': len(active_shortcuts)
            }
        )

    except Exception as e:
        logger.error(f"Failed to show keyboard shortcuts: {e}")
        return CommandResult(success=False, error=str(e))


def register_settings_commands():
    """Register all settings commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Settings commands registered")