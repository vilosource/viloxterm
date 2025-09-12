#!/usr/bin/env python3
"""
UI-related commands for toggling Chrome mode and other UI features.
"""

from core.commands.base import CommandResult, CommandContext
from core.commands.decorators import command
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox
import logging

logger = logging.getLogger(__name__)


@command(
    id="ui.toggleChromeMode",
    title="Toggle Chrome Mode",
    category="UI",
    description="Toggle between Chrome-style tabs and traditional UI"
)
def toggle_chrome_mode(context: CommandContext, **kwargs) -> CommandResult:
    """Toggle Chrome mode and prompt for restart."""
    try:
        # Get current setting
        settings = QSettings("ViloApp", "ViloApp")
        current_mode = settings.value("UI/ChromeMode", False, type=bool)
        
        # Toggle the mode
        new_mode = not current_mode
        settings.setValue("UI/ChromeMode", new_mode)
        settings.sync()
        
        # Show message to user
        mode_name = "Chrome-style" if new_mode else "Traditional"
        
        reply = QMessageBox.information(
            context.main_window,
            "UI Mode Changed",
            f"UI mode changed to {mode_name}.\n\n"
            "Please restart the application for the change to take effect.\n\n"
            "Would you like to restart now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Restart the application
            import sys
            import os
            from PySide6.QtCore import QCoreApplication
            
            # Save state before restart
            if hasattr(context.main_window, 'save_state'):
                context.main_window.save_state()
            
            # Get the executable and arguments
            executable = sys.executable
            args = sys.argv
            
            # Quit the current instance
            QCoreApplication.quit()
            
            # Start new instance
            os.execl(executable, executable, *args)
        
        return CommandResult(
            success=True,
            value=f"Chrome mode {'enabled' if new_mode else 'disabled'}. Restart required."
        )
        
    except Exception as e:
        logger.error(f"Failed to toggle Chrome mode: {e}")
        return CommandResult(
            success=False,
            error=str(e)
        )


@command(
    id="ui.enableChromeMode", 
    title="Enable Chrome Mode",
    category="UI",
    description="Enable Chrome-style tabs in title bar"
)
def enable_chrome_mode(context: CommandContext, **kwargs) -> CommandResult:
    """Enable Chrome-style UI mode."""
    try:
        settings = QSettings("ViloApp", "ViloApp")
        current_mode = settings.value("UI/ChromeMode", False, type=bool)
        
        if current_mode:
            return CommandResult(
                success=True,
                value="Chrome mode is already enabled"
            )
        
        settings.setValue("UI/ChromeMode", True)
        settings.sync()
        
        QMessageBox.information(
            context.main_window,
            "Chrome Mode Enabled",
            "Chrome-style UI has been enabled.\n\n"
            "Please restart the application for the change to take effect."
        )
        
        return CommandResult(
            success=True,
            value="Chrome mode enabled. Restart required."
        )
        
    except Exception as e:
        logger.error(f"Failed to enable Chrome mode: {e}")
        return CommandResult(
            success=False,
            error=str(e)
        )


@command(
    id="ui.disableChromeMode",
    title="Disable Chrome Mode", 
    category="UI",
    description="Disable Chrome-style tabs, use traditional UI"
)
def disable_chrome_mode(context: CommandContext, **kwargs) -> CommandResult:
    """Disable Chrome-style UI mode."""
    try:
        settings = QSettings("ViloApp", "ViloApp")
        current_mode = settings.value("UI/ChromeMode", False, type=bool)
        
        if not current_mode:
            return CommandResult(
                success=True,
                value="Chrome mode is already disabled"
            )
        
        settings.setValue("UI/ChromeMode", False)
        settings.sync()
        
        QMessageBox.information(
            context.main_window,
            "Chrome Mode Disabled",
            "Traditional UI has been restored.\n\n"
            "Please restart the application for the change to take effect."
        )
        
        return CommandResult(
            success=True,
            value="Chrome mode disabled. Restart required."
        )
        
    except Exception as e:
        logger.error(f"Failed to disable Chrome mode: {e}")
        return CommandResult(
            success=False,
            error=str(e)
        )