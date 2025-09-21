"""Multi-cursor functionality for the code editor."""

import logging
from typing import List, Optional
from dataclasses import dataclass

from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtGui import QTextCursor, QKeySequence, QShortcut, QTextFormat, QColor

logger = logging.getLogger(__name__)


@dataclass
class CursorInfo:
    """Information about a cursor position."""

    position: int
    anchor: int = None  # For selections

    def __post_init__(self):
        if self.anchor is None:
            self.anchor = self.position

    @property
    def has_selection(self) -> bool:
        """Check if this cursor has a selection."""
        return self.position != self.anchor

    @property
    def selection_start(self) -> int:
        """Get the start of the selection."""
        return min(self.position, self.anchor)

    @property
    def selection_end(self) -> int:
        """Get the end of the selection."""
        return max(self.position, self.anchor)

    def selection_text(self, document_text: str) -> str:
        """Get the selected text."""
        if not self.has_selection:
            return ""
        return document_text[self.selection_start : self.selection_end]


class MultiCursor(QObject):
    """Multi-cursor manager for code editor."""

    # Signals
    cursors_changed = Signal()
    selection_changed = Signal()

    def __init__(self, editor=None):
        super().__init__()
        self.editor = editor
        self.cursors: List[CursorInfo] = []
        self.primary_cursor_index = 0
        self.enabled = True
        self._updating = False

        if editor:
            self.setup_editor_integration()

    def setup_editor_integration(self):
        """Setup integration with the editor."""
        if not self.editor:
            return

        # Setup shortcuts
        add_cursor_down = QShortcut(QKeySequence("Ctrl+Alt+Down"), self.editor)
        add_cursor_down.activated.connect(self.add_cursor_down)

        add_cursor_up = QShortcut(QKeySequence("Ctrl+Alt+Up"), self.editor)
        add_cursor_up.activated.connect(self.add_cursor_up)

        select_all_occurrences = QShortcut(QKeySequence("Ctrl+Shift+L"), self.editor)
        select_all_occurrences.activated.connect(self.select_all_occurrences)

        add_next_occurrence = QShortcut(QKeySequence("Ctrl+D"), self.editor)
        add_next_occurrence.activated.connect(self.add_next_occurrence)

        escape_multi_cursor = QShortcut(QKeySequence("Escape"), self.editor)
        escape_multi_cursor.activated.connect(self.clear_cursors)

        # Connect to editor events
        self.editor.cursorPositionChanged.connect(self.on_cursor_position_changed)

    def set_editor(self, editor):
        """Set the editor instance."""
        self.editor = editor
        if editor:
            self.setup_editor_integration()

    def is_active(self) -> bool:
        """Check if multi-cursor mode is active."""
        return self.enabled and len(self.cursors) > 1

    def add_cursor_at_position(self, position: int, anchor: int = None) -> bool:
        """Add a cursor at the specified position."""
        if not self.enabled:
            return False

        cursor_info = CursorInfo(position, anchor)

        # Check if cursor already exists at this position
        for existing in self.cursors:
            if existing.position == position and existing.anchor == cursor_info.anchor:
                return False

        self.cursors.append(cursor_info)
        self.cursors.sort(key=lambda c: c.position)
        self.update_visual_indicators()
        self.cursors_changed.emit()
        return True

    def add_cursor_down(self):
        """Add a cursor on the line below the primary cursor."""
        if not self.editor:
            return

        primary_cursor = self.get_primary_cursor()
        if not primary_cursor:
            # Start multi-cursor mode with current cursor
            editor_cursor = self.editor.textCursor()
            self.cursors = [CursorInfo(editor_cursor.position(), editor_cursor.anchor())]
            primary_cursor = self.cursors[0]

        # Calculate position on next line
        document = self.editor.document()
        block = document.findBlock(primary_cursor.position)
        next_block = block.next()

        if next_block.isValid():
            # Try to maintain column position
            cursor_in_block = primary_cursor.position - block.position()
            next_line_pos = next_block.position() + min(cursor_in_block, next_block.length() - 1)
            self.add_cursor_at_position(next_line_pos)

    def add_cursor_up(self):
        """Add a cursor on the line above the primary cursor."""
        if not self.editor:
            return

        primary_cursor = self.get_primary_cursor()
        if not primary_cursor:
            # Start multi-cursor mode with current cursor
            editor_cursor = self.editor.textCursor()
            self.cursors = [CursorInfo(editor_cursor.position(), editor_cursor.anchor())]
            primary_cursor = self.cursors[0]

        # Calculate position on previous line
        document = self.editor.document()
        block = document.findBlock(primary_cursor.position)
        prev_block = block.previous()

        if prev_block.isValid():
            # Try to maintain column position
            cursor_in_block = primary_cursor.position - block.position()
            prev_line_pos = prev_block.position() + min(cursor_in_block, prev_block.length() - 1)
            self.add_cursor_at_position(prev_line_pos)

    def add_next_occurrence(self):
        """Add a cursor at the next occurrence of the selected text."""
        if not self.editor:
            return

        editor_cursor = self.editor.textCursor()
        if not editor_cursor.hasSelection():
            # Select word under cursor
            editor_cursor.select(QTextCursor.WordUnderCursor)
            self.editor.setTextCursor(editor_cursor)

        selected_text = editor_cursor.selectedText()
        if not selected_text:
            return

        # Start multi-cursor mode if not active
        if not self.is_active():
            self.cursors = [CursorInfo(editor_cursor.position(), editor_cursor.anchor())]

        # Find next occurrence
        document = self.editor.document()
        start_position = max(cursor.position for cursor in self.cursors) + 1

        found_cursor = document.find(selected_text, start_position)
        if not found_cursor.isNull():
            self.add_cursor_at_position(found_cursor.position(), found_cursor.anchor())
        else:
            # Wrap around to beginning
            found_cursor = document.find(selected_text, 0)
            if not found_cursor.isNull():
                self.add_cursor_at_position(found_cursor.position(), found_cursor.anchor())

    def select_all_occurrences(self):
        """Select all occurrences of the selected text."""
        if not self.editor:
            return

        editor_cursor = self.editor.textCursor()
        if not editor_cursor.hasSelection():
            editor_cursor.select(QTextCursor.WordUnderCursor)
            self.editor.setTextCursor(editor_cursor)

        selected_text = editor_cursor.selectedText()
        if not selected_text:
            return

        # Find all occurrences
        document = self.editor.document()
        self.cursors = []
        position = 0

        while True:
            found_cursor = document.find(selected_text, position)
            if found_cursor.isNull():
                break

            self.cursors.append(CursorInfo(found_cursor.position(), found_cursor.anchor()))
            position = found_cursor.position() + len(selected_text)

        if self.cursors:
            self.update_visual_indicators()
            self.cursors_changed.emit()

    def get_primary_cursor(self) -> Optional[CursorInfo]:
        """Get the primary cursor (usually the first one)."""
        if not self.cursors:
            return None
        if self.primary_cursor_index < len(self.cursors):
            return self.cursors[self.primary_cursor_index]
        return self.cursors[0]

    def clear_cursors(self):
        """Clear all cursors and return to single cursor mode."""
        if not self.cursors:
            return

        # Set editor cursor to primary cursor position
        primary = self.get_primary_cursor()
        if primary and self.editor:
            cursor = self.editor.textCursor()
            cursor.setPosition(primary.position)
            self.editor.setTextCursor(cursor)

        self.cursors.clear()
        self.clear_visual_indicators()
        self.cursors_changed.emit()

    def on_cursor_position_changed(self):
        """Handle cursor position change in editor."""
        if self._updating or not self.is_active():
            return

        # Update primary cursor position
        if self.editor:
            editor_cursor = self.editor.textCursor()
            if self.cursors and self.primary_cursor_index < len(self.cursors):
                self.cursors[self.primary_cursor_index].position = editor_cursor.position()
                self.cursors[self.primary_cursor_index].anchor = editor_cursor.anchor()
                self.update_visual_indicators()

    def insert_text(self, text: str):
        """Insert text at all cursor positions."""
        if not self.is_active() or not self.editor:
            return

        document = self.editor.document()
        cursor = QTextCursor(document)

        # Sort cursors by position (descending) to maintain positions during insertion
        sorted_cursors = sorted(self.cursors, key=lambda c: c.position, reverse=True)

        cursor.beginEditBlock()
        for cursor_info in sorted_cursors:
            cursor.setPosition(cursor_info.position)
            if cursor_info.has_selection:
                cursor.setPosition(cursor_info.anchor, QTextCursor.KeepAnchor)
            cursor.insertText(text)

            # Update cursor positions after insertion
            text_length = len(text)
            for other_cursor in self.cursors:
                if other_cursor.position > cursor_info.position:
                    other_cursor.position += text_length
                    other_cursor.anchor += text_length
                elif other_cursor.position == cursor_info.position:
                    other_cursor.position += text_length
                    if not cursor_info.has_selection:
                        other_cursor.anchor = other_cursor.position

        cursor.endEditBlock()
        self.update_visual_indicators()

    def delete_selected_text(self):
        """Delete selected text at all cursor positions."""
        if not self.is_active() or not self.editor:
            return

        document = self.editor.document()
        cursor = QTextCursor(document)

        # Sort cursors by position (descending) to maintain positions during deletion
        sorted_cursors = sorted(
            [c for c in self.cursors if c.has_selection],
            key=lambda c: c.selection_start,
            reverse=True,
        )

        if not sorted_cursors:
            return

        cursor.beginEditBlock()
        for cursor_info in sorted_cursors:
            cursor.setPosition(cursor_info.selection_start)
            cursor.setPosition(cursor_info.selection_end, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()

            # Update cursor positions after deletion
            deleted_length = cursor_info.selection_end - cursor_info.selection_start
            for other_cursor in self.cursors:
                if other_cursor.position > cursor_info.selection_end:
                    other_cursor.position -= deleted_length
                    other_cursor.anchor -= deleted_length
                elif other_cursor.position > cursor_info.selection_start:
                    other_cursor.position = cursor_info.selection_start
                    other_cursor.anchor = cursor_info.selection_start

        cursor.endEditBlock()
        self.update_visual_indicators()

    def update_visual_indicators(self):
        """Update visual indicators for multiple cursors."""
        if not self.editor or not self.is_active():
            self.clear_visual_indicators()
            return

        try:
            extra_selections = []

            for i, cursor_info in enumerate(self.cursors):
                selection = QTextEdit.ExtraSelection()

                if cursor_info.has_selection:
                    # Highlight selection
                    selection.format.setBackground(QColor(100, 100, 255, 100))  # Light blue
                    selection.cursor = self.editor.textCursor()
                    selection.cursor.setPosition(cursor_info.anchor)
                    selection.cursor.setPosition(cursor_info.position, QTextCursor.KeepAnchor)
                else:
                    # Show cursor position
                    selection.format.setBackground(QColor(255, 255, 255, 200))  # White
                    selection.format.setProperty(QTextFormat.FullWidthSelection, False)
                    selection.cursor = self.editor.textCursor()
                    selection.cursor.setPosition(cursor_info.position)

                extra_selections.append(selection)

            self.editor.setExtraSelections(extra_selections)
        except Exception as e:
            # Gracefully handle errors in test environment
            logger.debug(f"Error updating visual indicators: {e}")

    def clear_visual_indicators(self):
        """Clear visual indicators."""
        if self.editor:
            self.editor.setExtraSelections([])

    def handle_key_press(self, event) -> bool:
        """Handle key press events for multi-cursor mode."""
        if not self.is_active():
            return False

        key = event.key()
        modifiers = event.modifiers()

        # Handle text input
        if event.text() and event.text().isprintable():
            if modifiers == Qt.NoModifier or modifiers == Qt.ShiftModifier:
                self.insert_text(event.text())
                return True

        # Handle special keys
        if key == Qt.Key_Backspace:
            if any(c.has_selection for c in self.cursors):
                self.delete_selected_text()
            else:
                # Delete character before each cursor
                self.delete_before_cursors()
            return True

        elif key == Qt.Key_Delete:
            if any(c.has_selection for c in self.cursors):
                self.delete_selected_text()
            else:
                # Delete character after each cursor
                self.delete_after_cursors()
            return True

        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self.insert_text("\n")
            return True

        elif key == Qt.Key_Tab:
            if modifiers == Qt.NoModifier:
                self.insert_text("    ")  # 4 spaces
                return True

        return False

    def delete_before_cursors(self):
        """Delete one character before each cursor."""
        if not self.is_active() or not self.editor:
            return

        document = self.editor.document()
        cursor = QTextCursor(document)

        # Sort cursors by position (descending)
        sorted_cursors = sorted(self.cursors, key=lambda c: c.position, reverse=True)

        cursor.beginEditBlock()
        for cursor_info in sorted_cursors:
            if cursor_info.position > 0:
                cursor.setPosition(cursor_info.position - 1)
                cursor.setPosition(cursor_info.position, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()

                # Update cursor positions
                for other_cursor in self.cursors:
                    if other_cursor.position > cursor_info.position:
                        other_cursor.position -= 1
                        other_cursor.anchor -= 1
                    elif other_cursor.position == cursor_info.position:
                        other_cursor.position -= 1
                        other_cursor.anchor = other_cursor.position

        cursor.endEditBlock()
        self.update_visual_indicators()

    def delete_after_cursors(self):
        """Delete one character after each cursor."""
        if not self.is_active() or not self.editor:
            return

        document = self.editor.document()
        cursor = QTextCursor(document)
        text = document.toPlainText()

        # Sort cursors by position (descending)
        sorted_cursors = sorted(self.cursors, key=lambda c: c.position, reverse=True)

        cursor.beginEditBlock()
        for cursor_info in sorted_cursors:
            if cursor_info.position < len(text):
                cursor.setPosition(cursor_info.position)
                cursor.setPosition(cursor_info.position + 1, QTextCursor.KeepAnchor)
                cursor.removeSelectedText()

                # Update cursor positions
                for other_cursor in self.cursors:
                    if other_cursor.position > cursor_info.position:
                        other_cursor.position -= 1
                        other_cursor.anchor -= 1

        cursor.endEditBlock()
        self.update_visual_indicators()

    def get_cursor_count(self) -> int:
        """Get the number of active cursors."""
        return len(self.cursors)

    def get_cursor_positions(self) -> List[int]:
        """Get list of cursor positions."""
        return [cursor.position for cursor in self.cursors]

    def set_enabled(self, enabled: bool):
        """Enable or disable multi-cursor mode."""
        if not enabled and self.is_active():
            self.clear_cursors()
        self.enabled = enabled
