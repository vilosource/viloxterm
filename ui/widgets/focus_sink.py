#!/usr/bin/env python3
"""
FocusSink Widget for Command Mode

This invisible widget captures keyboard input during command mode,
ensuring that digit keys and escape are handled by Qt rather than
by any focused widget (especially WebEngine terminals).
"""

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class FocusSinkWidget(QWidget):
    """
    Invisible widget that captures keyboard input during command mode.

    When pane numbers are shown and the user presses Alt+P, focus is
    transferred to this widget. It then captures digit keys (1-9) for
    pane selection and Escape for cancellation.
    """

    # Signals
    digitPressed = Signal(int)  # Emits pane number (1-9)
    cancelled = Signal()  # Emits when Escape is pressed
    commandModeExited = Signal()  # Emits when command mode should exit

    def __init__(self, parent=None):
        """Initialize the focus sink widget."""
        super().__init__(parent)

        # Make the widget invisible and minimal
        self.setFixedSize(0, 0)
        self.setVisible(False)  # Hidden by default

        # Strong focus policy to ensure it gets keyboard events
        self.setFocusPolicy(Qt.StrongFocus)

        # Track command mode state
        self._in_command_mode = False
        self._original_focus_widget = None

        logger.debug("FocusSinkWidget initialized")

    def enter_command_mode(self, original_focus_widget=None):
        """
        Enter command mode and capture focus.

        Args:
            original_focus_widget: Widget that had focus before command mode
        """
        self._in_command_mode = True
        self._original_focus_widget = original_focus_widget

        # Make visible (though still 0x0 size) and grab focus
        self.setVisible(True)
        self.setFocus()
        self.grabKeyboard()  # Ensure we get all keyboard events

        logger.info("Entered command mode, FocusSink has focus")

    def exit_command_mode(self, restore_focus=True):
        """
        Exit command mode and optionally restore focus.

        Args:
            restore_focus: Whether to restore focus to original widget
        """
        self._in_command_mode = False

        # Release keyboard and hide
        self.releaseKeyboard()
        self.setVisible(False)

        # Restore focus if requested
        if restore_focus and self._original_focus_widget:
            self._original_focus_widget.setFocus()
            logger.debug(
                f"Restored focus to {self._original_focus_widget.__class__.__name__}"
            )

        self._original_focus_widget = None
        self.commandModeExited.emit()

        logger.info("Exited command mode")

    def keyPressEvent(self, event: QKeyEvent):
        """
        Handle key press events during command mode.

        Captures:
        - Digits 1-9: Select pane by number
        - Escape: Cancel command mode
        - Any other key: Exit command mode
        """
        if not self._in_command_mode:
            super().keyPressEvent(event)
            return

        key = event.key()

        # Handle digit keys (1-9)
        if Qt.Key_1 <= key <= Qt.Key_9:
            digit = key - Qt.Key_0
            logger.info(f"FocusSink: Digit {digit} pressed")
            self.digitPressed.emit(digit)
            # Exit command mode immediately WITHOUT restoring focus
            # The pane switch will handle focus properly
            self.exit_command_mode(restore_focus=False)
            event.accept()

        # Handle Escape - cancel command mode
        elif key == Qt.Key_Escape:
            logger.info("FocusSink: Escape pressed, cancelling command mode")
            self.cancelled.emit()
            self.exit_command_mode(restore_focus=True)
            event.accept()

        # Any other key exits command mode
        else:
            logger.info(
                f"FocusSink: Non-command key pressed ({key}), exiting command mode"
            )
            self.exit_command_mode(restore_focus=True)
            # Don't accept the event - let it propagate
            event.ignore()

    def focusOutEvent(self, event):
        """
        Handle focus lost event.

        If we lose focus while in command mode, exit command mode.
        """
        if self._in_command_mode:
            logger.warning("FocusSink lost focus during command mode")
            self.exit_command_mode(restore_focus=False)
        super().focusOutEvent(event)
