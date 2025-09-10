#!/usr/bin/env python3
"""
Terminal Bridge for QWebChannel Communication
Provides a clean interface between Qt and JavaScript without exposing unnecessary properties.
"""

from PySide6.QtCore import QObject, Slot, Signal
from typing import Dict, Any
import logging

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
    
    def __init__(self, parent=None):
        """Initialize the terminal bridge."""
        super().__init__(parent)
        self._current_theme = {}
        
    def set_theme(self, theme_data: Dict[str, Any]):
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
        logger.debug("Terminal clicked (from JavaScript)")
        self.terminalClicked.emit()
    
    @Slot()
    def js_terminal_focused(self):
        """Called from JavaScript when terminal gains focus."""
        logger.debug("Terminal focused (from JavaScript)")
        self.terminalFocused.emit()
    
    @Slot(str)
    def js_log(self, message: str):
        """Log message from JavaScript for debugging."""
        logger.info(f"JS Log: {message}")
    
    @Slot(str)
    def js_error(self, message: str):
        """Log error from JavaScript."""
        logger.error(f"JS Error: {message}")