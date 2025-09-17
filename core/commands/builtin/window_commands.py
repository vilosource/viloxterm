#!/usr/bin/env python3
"""
Window-related commands for managing window state and frameless mode.
"""

import logging

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QMessageBox

from core.app_config import should_show_confirmations
from core.commands.base import CommandContext, CommandResult
from core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="window.toggleFrameless",
    title="Toggle Frameless Mode",
    category="Window",
    description="Toggle between normal and frameless window mode"
)
def toggle_frameless_mode(context: CommandContext) -> CommandResult:
    """Toggle frameless window mode."""
    try:
        # Use UIService to toggle frameless mode for consistency
        from services.ui_service import UIService
        ui_service = context.get_service(UIService)

        if ui_service:
            new_mode = ui_service.toggle_frameless_mode()
        else:
            # Fallback to direct settings if service not available
            settings = QSettings("ViloxTerm", "ViloxTerm")
            current_mode = settings.value("UI/FramelessMode", False, type=bool)
            new_mode = not current_mode
            settings.setValue("UI/FramelessMode", new_mode)
            settings.sync()

        # Show message to user (unless in test mode)
        mode_name = "Frameless" if new_mode else "Normal"

        if should_show_confirmations():
            reply = QMessageBox.information(
                context.main_window,
                "Window Mode Changed",
                f"Window mode changed to {mode_name}.\n\n"
                "Please restart the application for the change to take effect.\n\n"
                "Would you like to restart now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                # Restart the application
                import os
                import sys

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
        else:
            # In test mode, just log the change
            logger.info(f"Window mode changed to {mode_name} (test mode - no restart)")

        return CommandResult(
            success=True,
            value=f"Frameless mode {'enabled' if new_mode else 'disabled'}. Restart required."
        )

    except Exception as e:
        logger.error(f"Failed to toggle frameless mode: {e}")
        return CommandResult(
            success=False,
            error=str(e)
        )


@command(
    id="window.minimize",
    title="Minimize Window",
    category="Window",
    description="Minimize the application window"
)
def minimize_window(context: CommandContext) -> CommandResult:
    """Minimize the window."""
    try:
        if context.main_window:
            context.main_window.showMinimized()
            return CommandResult(success=True)
        return CommandResult(success=False, error="No window available")
    except Exception as e:
        logger.error(f"Failed to minimize window: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="window.maximize",
    title="Maximize Window",
    category="Window",
    description="Maximize the application window"
)
def maximize_window(context: CommandContext) -> CommandResult:
    """Maximize the window."""
    try:
        if context.main_window:
            if context.main_window.isMaximized():
                context.main_window.showNormal()
                return CommandResult(success=True, value="restored")
            else:
                context.main_window.showMaximized()
                return CommandResult(success=True, value="maximized")
        return CommandResult(success=False, error="No window available")
    except Exception as e:
        logger.error(f"Failed to maximize window: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="window.restore",
    title="Restore Window",
    category="Window",
    description="Restore the application window to normal size"
)
def restore_window(context: CommandContext) -> CommandResult:
    """Restore the window to normal size."""
    try:
        if context.main_window:
            context.main_window.showNormal()
            return CommandResult(success=True)
        return CommandResult(success=False, error="No window available")
    except Exception as e:
        logger.error(f"Failed to restore window: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="window.close",
    title="Close Window",
    category="Window",
    description="Close the application window",
    shortcut="alt+f4"
)
def close_window(context: CommandContext) -> CommandResult:
    """Close the window."""
    try:
        if context.main_window:
            context.main_window.close()
            return CommandResult(success=True)
        return CommandResult(success=False, error="No window available")
    except Exception as e:
        logger.error(f"Failed to close window: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="window.toggleFullScreen",
    title="Toggle Full Screen",
    category="Window",
    description="Toggle full screen mode",
    shortcut="f11"
)
def toggle_fullscreen(context: CommandContext) -> CommandResult:
    """Toggle full screen mode."""
    try:
        if context.main_window:
            if context.main_window.isFullScreen():
                context.main_window.showNormal()
                return CommandResult(success=True, value="normal")
            else:
                context.main_window.showFullScreen()
                return CommandResult(success=True, value="fullscreen")
        return CommandResult(success=False, error="No window available")
    except Exception as e:
        logger.error(f"Failed to toggle fullscreen: {e}")
        return CommandResult(success=False, error=str(e))
