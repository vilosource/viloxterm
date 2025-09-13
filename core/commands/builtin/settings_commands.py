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
    id="settings.showKeyboardShortcuts",
    title="Show Keyboard Shortcuts",
    category="Settings",
    description="Display all keyboard shortcuts",
    shortcut="ctrl+k ctrl+s",  # This is a chord, not conflicting with ctrl+s
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