#!/usr/bin/env python3
"""
Terminal Bridge for QWebChannel Communication
Provides a clean interface between Qt and JavaScript without exposing unnecessary properties.
"""

import logging
from typing import Any

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class TerminalBridge(QObject):
    """
    Bridge object for QWebChannel communication with terminal JavaScript.
    Only exposes necessary methods and signals for terminal functionality.
    """

    # Signals
    themeChanged = Signal(dict)
    terminalClicked = Signal()
    terminalFocused = Signal()
    shortcutPressed = Signal(str)  # Emits shortcut string like "Alt+P"

    def __init__(self, parent=None):
        """Initialize the terminal bridge."""
        super().__init__(parent)
        self._current_theme = {}

    def set_theme(self, theme_data: dict[str, Any]):
        """Set the current theme and emit change signal."""
        self._current_theme = theme_data
        self.themeChanged.emit(theme_data)

    @Slot(result=dict)
    def getCurrentTheme(self):
        """
        Provide current theme to JavaScript.
        Called when terminal initializes.
        """
        logger.debug("JavaScript requested current theme")
        return self._current_theme

    @Slot()
    def js_terminal_clicked(self):
        """Called from JavaScript when terminal is clicked."""
        self.terminalClicked.emit()

    @Slot()
    def js_terminal_focused(self):
        """Called from JavaScript when terminal gains focus."""
        self.terminalFocused.emit()

    @Slot(str)
    def js_log(self, message: str):
        """Log message from JavaScript for debugging."""
        logger.info(f"JS Log: {message}")

    @Slot(str)
    def js_error(self, message: str):
        """Log error from JavaScript."""
        logger.error(f"JS Error: {message}")

    @Slot(str)
    def js_shortcut_pressed(self, shortcut: str):
        """
        Called from JavaScript when a reserved shortcut is pressed.
        This allows JS to notify Qt about shortcuts that should be handled
        at the application level, not by the terminal.
        """
        logger.debug(f"Shortcut pressed in terminal (from JavaScript): {shortcut}")
        self.shortcutPressed.emit(shortcut)

    def focus_terminal_element(self, web_view):
        """
        Focus the terminal element inside the web page.
        This is called after Qt sets focus to the QWebEngineView.
        """
        if web_view and web_view.page():
            web_view.page().runJavaScript("if (window.focusTerminal) window.focusTerminal();")
            logger.debug("Requested terminal element focus via JavaScript")
