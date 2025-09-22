#!/usr/bin/env python3
"""
Help-related commands for ViloxTerm.

Provides commands for help, about, and documentation access.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="help.about",
    title="About ViloxTerm",
    category="Help",
    description="Show information about ViloxTerm",
)
def show_about_command(context: CommandContext) -> CommandResult:
    """Show the About dialog."""
    try:
        from viloapp.ui.dialogs.about_dialog import AboutDialog

        # Get main window from context parameters
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Create and show the About dialog
        dialog = AboutDialog(main_window)
        dialog.exec()

        return CommandResult(status=CommandStatus.SUCCESS, data={"action": "about_shown"})

    except Exception as e:
        logger.error(f"Failed to show About dialog: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="help.documentation",
    title="Open Documentation",
    category="Help",
    description="Open ViloxTerm documentation in browser",
)
def open_documentation_command(context: CommandContext) -> CommandResult:
    """Open the documentation in the default browser."""
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        from viloapp.core.version import APP_URL

        # For now, open the GitHub repository
        # In the future, this could point to dedicated docs
        docs_url = f"{APP_URL}/wiki"
        QDesktopServices.openUrl(QUrl(docs_url))

        return CommandResult(status=CommandStatus.SUCCESS, data={"url": docs_url})

    except Exception as e:
        logger.error(f"Failed to open documentation: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="help.reportIssue",
    title="Report Issue",
    category="Help",
    description="Report an issue on GitHub",
)
def report_issue_command(context: CommandContext) -> CommandResult:
    """Open the issue tracker in the default browser."""
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        from viloapp.core.version import APP_URL

        issues_url = f"{APP_URL}/issues"
        QDesktopServices.openUrl(QUrl(issues_url))

        return CommandResult(status=CommandStatus.SUCCESS, data={"url": issues_url})

    except Exception as e:
        logger.error(f"Failed to open issue tracker: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="help.checkForUpdates",
    title="Check for Updates",
    category="Help",
    description="Check for ViloxTerm updates",
)
def check_for_updates_command(context: CommandContext) -> CommandResult:
    """Check for application updates."""
    try:
        from PySide6.QtWidgets import QMessageBox

        from viloapp.core.version import APP_NAME, __version__

        # Get main window from context parameters
        main_window = context.parameters.get("main_window") if context.parameters else None

        # For now, just show current version
        # In the future, this could check GitHub releases API
        QMessageBox.information(
            main_window,
            "Check for Updates",
            f"{APP_NAME} v{__version__}\n\n"
            "Automatic update checking is not yet implemented.\n"
            "Please check the GitHub repository for the latest releases.",
        )

        return CommandResult(status=CommandStatus.SUCCESS, data={"current_version": __version__})

    except Exception as e:
        logger.error(f"Failed to check for updates: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))
