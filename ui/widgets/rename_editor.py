"""
Inline rename editor widget for tabs and panes.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLineEdit


class RenameEditor(QLineEdit):
    """Inline editor for renaming tabs and panes."""

    rename_completed = Signal(str)  # New name
    rename_cancelled = Signal()

    def __init__(self, initial_text: str = "", parent=None):
        super().__init__(parent)
        self.setText(initial_text)
        self.selectAll()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.rename_completed.emit(self.text())
        elif event.key() == Qt.Key_Escape:
            self.rename_cancelled.emit()
        else:
            super().keyPressEvent(event)
