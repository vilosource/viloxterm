#!/usr/bin/env python3
"""
Event filter for WebEngine and text widgets to properly handle application shortcuts.

This filter ensures that application-level shortcuts work even when WebEngine
or text editor widgets have focus, by intercepting ShortcutOverride events
and telling Qt to route them through the shortcut system instead of letting
them become widget input.
"""

import logging

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QKeySequence

logger = logging.getLogger(__name__)


class WebShortcutGuard(QObject):
    """
    Event filter that guards application shortcuts from being consumed by widgets.

    This is particularly important for QWebEngineView where Chromium/xterm.js
    would otherwise consume all keyboard input, preventing application shortcuts
    from working.
    """

    def __init__(self, parent=None):
        """
        Initialize the shortcut guard.

        Args:
            parent: Parent QObject (optional)
        """
        super().__init__(parent)
        self._reserved_shortcuts = []
        logger.debug("WebShortcutGuard initialized")

    def set_reserved_shortcuts(self, shortcuts):
        """
        Set shortcuts that should be reserved for application handling.

        Args:
            shortcuts: List of QKeySequence objects or strings like ["Alt+P", "Ctrl+B"]
                      These shortcuts will be intercepted and routed to Qt's shortcut system.
        """
        self._reserved_shortcuts = [
            s if isinstance(s, QKeySequence) else QKeySequence(s)
            for s in shortcuts
        ]
        logger.info(f"WebShortcutGuard reserved {len(self._reserved_shortcuts)} shortcuts")
        for shortcut in self._reserved_shortcuts:
            logger.debug(f"  Reserved: {shortcut.toString()}")

    def add_reserved_shortcut(self, shortcut):
        """
        Add a single shortcut to the reserved list.

        Args:
            shortcut: QKeySequence or string representation of the shortcut
        """
        if isinstance(shortcut, str):
            shortcut = QKeySequence(shortcut)
        if shortcut not in self._reserved_shortcuts:
            self._reserved_shortcuts.append(shortcut)
            logger.debug(f"Added reserved shortcut: {shortcut.toString()}")

    def remove_reserved_shortcut(self, shortcut):
        """
        Remove a shortcut from the reserved list.

        Args:
            shortcut: QKeySequence or string representation of the shortcut
        """
        if isinstance(shortcut, str):
            shortcut = QKeySequence(shortcut)
        if shortcut in self._reserved_shortcuts:
            self._reserved_shortcuts.remove(shortcut)
            logger.debug(f"Removed reserved shortcut: {shortcut.toString()}")

    def eventFilter(self, obj, event):
        """
        Filter events to intercept shortcuts before widgets process them.

        We handle TWO types of events:
        1. ShortcutOverride: Tells Qt to treat this as a shortcut (not text input)
        2. KeyPress: Actually blocks the key from reaching the widget

        The ShortcutOverride event is sent before a key press is delivered
        to the widget. By accepting this event and returning True for our
        reserved shortcuts, we tell Qt to treat them as shortcuts rather
        than regular key input, ensuring they flow through the normal Qt
        shortcut handling system.

        We ALSO need to filter the actual KeyPress event to prevent it from
        reaching WebEngine content, which would otherwise send it to the
        terminal via JavaScript/WebSocket.

        Args:
            obj: The object that the event was sent to
            event: The event to filter

        Returns:
            True if the event was handled (prevents widget from seeing it)
            False to let the event continue to the widget
        """
        # Handle both ShortcutOverride AND KeyPress events
        if event.type() in (QEvent.Type.ShortcutOverride, QEvent.Type.KeyPress):
            ke = event  # QKeyEvent
            key = ke.key()

            if key != Qt.Key_unknown:
                # Build a QKeySequence from the current key event
                # Combine modifiers with the key to create the full sequence
                ks = QKeySequence(int(ke.modifiers().value) | int(key))

                # Check if this matches any of our reserved shortcuts
                for reserved in self._reserved_shortcuts:
                    if ks.matches(reserved) == QKeySequence.ExactMatch:
                        if event.type() == QEvent.Type.ShortcutOverride:
                            logger.info(f"WebShortcutGuard intercepted ShortcutOverride: {reserved.toString()}")
                            event.accept()   # Tell Qt this is a shortcut
                            # IMPORTANT: Return False to let Qt process the shortcut
                            return False
                        else:  # KeyPress
                            logger.info(f"WebShortcutGuard blocked KeyPress: {reserved.toString()}")
                            return True      # Block the event from reaching the widget

        # Not a reserved shortcut - let widget handle it normally
        return False
