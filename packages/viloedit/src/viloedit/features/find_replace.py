"""Find and replace functionality for the code editor."""

import re
import logging
from typing import List, Tuple, Dict, Any
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QCheckBox, QLabel, QComboBox, QTextEdit
)
from PySide6.QtCore import Signal, QTimer, QRegularExpression
from PySide6.QtGui import QTextCursor, QTextDocument, QKeySequence, QShortcut

logger = logging.getLogger(__name__)


class SearchDirection(Enum):
    """Search direction enum."""
    FORWARD = "forward"
    BACKWARD = "backward"


class SearchMode(Enum):
    """Search mode enum."""
    NORMAL = "normal"
    REGEX = "regex"
    WHOLE_WORD = "whole_word"
    CASE_SENSITIVE = "case_sensitive"


class FindReplaceResult:
    """Result of a find/replace operation."""

    def __init__(self, found: bool = False, position: int = -1, matches: int = 0, replaced: int = 0):
        self.found = found
        self.position = position
        self.matches = matches
        self.replaced = replaced


class FindReplace(QWidget):
    """Find and replace widget for code editor."""

    # Signals
    find_requested = Signal(str, dict)  # pattern, options
    replace_requested = Signal(str, str, dict)  # find_text, replace_text, options
    replace_all_requested = Signal(str, str, dict)  # find_text, replace_text, options
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.editor = None
        self.last_search_position = 0
        self.search_history = []
        self.replace_history = []
        self.setup_ui()
        self.setup_shortcuts()

    def setup_ui(self):
        """Setup the find/replace UI."""
        self.setWindowTitle("Find and Replace")
        self.setFixedHeight(120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Find section
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))

        self.find_input = QComboBox()
        self.find_input.setEditable(True)
        self.find_input.setMinimumWidth(300)
        find_layout.addWidget(self.find_input)

        self.find_prev_btn = QPushButton("◀ Previous")
        self.find_next_btn = QPushButton("Next ▶")
        self.find_all_btn = QPushButton("Find All")

        find_layout.addWidget(self.find_prev_btn)
        find_layout.addWidget(self.find_next_btn)
        find_layout.addWidget(self.find_all_btn)

        layout.addLayout(find_layout)

        # Replace section
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))

        self.replace_input = QComboBox()
        self.replace_input.setEditable(True)
        self.replace_input.setMinimumWidth(300)
        replace_layout.addWidget(self.replace_input)

        self.replace_btn = QPushButton("Replace")
        self.replace_all_btn = QPushButton("Replace All")

        replace_layout.addWidget(self.replace_btn)
        replace_layout.addWidget(self.replace_all_btn)

        layout.addLayout(replace_layout)

        # Options section
        options_layout = QHBoxLayout()

        self.case_sensitive_cb = QCheckBox("Case sensitive")
        self.whole_word_cb = QCheckBox("Whole word")
        self.regex_cb = QCheckBox("Regular expression")
        self.wrap_search_cb = QCheckBox("Wrap around")
        self.wrap_search_cb.setChecked(True)  # Default to true

        options_layout.addWidget(self.case_sensitive_cb)
        options_layout.addWidget(self.whole_word_cb)
        options_layout.addWidget(self.regex_cb)
        options_layout.addWidget(self.wrap_search_cb)
        options_layout.addStretch()

        self.close_btn = QPushButton("✕ Close")
        options_layout.addWidget(self.close_btn)

        layout.addLayout(options_layout)

        # Connect signals
        self.find_next_btn.clicked.connect(self.find_next)
        self.find_prev_btn.clicked.connect(self.find_previous)
        self.find_all_btn.clicked.connect(self.find_all)
        self.replace_btn.clicked.connect(self.replace_current)
        self.replace_all_btn.clicked.connect(self.replace_all)
        self.close_btn.clicked.connect(self.close_widget)

        # Auto-search on text change with delay
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.auto_search)

        self.find_input.currentTextChanged.connect(self.on_text_changed)

    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Find next/previous
        find_next_shortcut = QShortcut(QKeySequence("F3"), self)
        find_next_shortcut.activated.connect(self.find_next)

        find_prev_shortcut = QShortcut(QKeySequence("Shift+F3"), self)
        find_prev_shortcut.activated.connect(self.find_previous)

        # Enter key in find field
        find_enter_shortcut = QShortcut(QKeySequence("Return"), self.find_input)
        find_enter_shortcut.activated.connect(self.find_next)

        # Escape to close
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self.close_widget)

    def set_editor(self, editor):
        """Set the editor instance to work with."""
        self.editor = editor
        if editor and hasattr(editor, 'textCursor'):
            # Initialize with selected text if any
            cursor = editor.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText()
                if selected_text:
                    self.find_input.setCurrentText(selected_text)

    def get_search_options(self) -> Dict[str, Any]:
        """Get current search options."""
        return {
            'case_sensitive': self.case_sensitive_cb.isChecked(),
            'whole_word': self.whole_word_cb.isChecked(),
            'regex': self.regex_cb.isChecked(),
            'wrap_around': self.wrap_search_cb.isChecked()
        }

    def on_text_changed(self):
        """Handle text change in find field."""
        self.search_timer.stop()
        if self.find_input.currentText():
            self.search_timer.start(300)  # 300ms delay

    def auto_search(self):
        """Perform automatic search after text change."""
        text = self.find_input.currentText()
        if text and self.editor:
            self.find_text(text, SearchDirection.FORWARD, from_current=True)

    def find_next(self):
        """Find next occurrence."""
        text = self.find_input.currentText()
        if text:
            self.add_to_history(text, self.search_history)
            self.find_text(text, SearchDirection.FORWARD)

    def find_previous(self):
        """Find previous occurrence."""
        text = self.find_input.currentText()
        if text:
            self.add_to_history(text, self.search_history)
            self.find_text(text, SearchDirection.BACKWARD)

    def find_all(self):
        """Find all occurrences and highlight them."""
        text = self.find_input.currentText()
        if text and self.editor:
            self.add_to_history(text, self.search_history)
            matches = self.find_all_matches(text)
            logger.info(f"Found {len(matches)} matches for '{text}'")

    def find_text(self, text: str, direction: SearchDirection, from_current: bool = False) -> FindReplaceResult:
        """Find text in the editor."""
        if not self.editor or not text:
            return FindReplaceResult()

        options = self.get_search_options()
        cursor = self.editor.textCursor()

        # Set search flags
        search_flags = QTextDocument.FindFlags()
        if options['case_sensitive']:
            search_flags |= QTextDocument.FindCaseSensitively
        if options['whole_word']:
            search_flags |= QTextDocument.FindWholeWords
        if direction == SearchDirection.BACKWARD:
            search_flags |= QTextDocument.FindBackward

        # Prepare search pattern
        if options['regex']:
            pattern = QRegularExpression(text)
            if not options['case_sensitive']:
                pattern.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
        else:
            pattern = text

        # Perform search
        if not from_current and direction == SearchDirection.FORWARD:
            cursor.movePosition(QTextCursor.Start)
        elif not from_current and direction == SearchDirection.BACKWARD:
            cursor.movePosition(QTextCursor.End)

        if options['regex']:
            found_cursor = self.editor.document().find(pattern, cursor, search_flags)
        else:
            found_cursor = self.editor.document().find(text, cursor, search_flags)

        # Handle wrap around
        if found_cursor.isNull() and options['wrap_around']:
            if direction == SearchDirection.FORWARD:
                cursor.movePosition(QTextCursor.Start)
            else:
                cursor.movePosition(QTextCursor.End)

            if options['regex']:
                found_cursor = self.editor.document().find(pattern, cursor, search_flags)
            else:
                found_cursor = self.editor.document().find(text, cursor, search_flags)

        if not found_cursor.isNull():
            self.editor.setTextCursor(found_cursor)
            self.editor.ensureCursorVisible()
            return FindReplaceResult(found=True, position=found_cursor.position())

        return FindReplaceResult()

    def find_all_matches(self, text: str) -> List[Tuple[int, int]]:
        """Find all matches and return their positions."""
        if not self.editor or not text:
            return []

        options = self.get_search_options()
        matches = []

        # Reset cursor to start
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.Start)

        # Set search flags
        search_flags = QTextDocument.FindFlags()
        if options['case_sensitive']:
            search_flags |= QTextDocument.FindCaseSensitively
        if options['whole_word']:
            search_flags |= QTextDocument.FindWholeWords

        # Prepare search pattern
        if options['regex']:
            pattern = QRegularExpression(text)
            if not options['case_sensitive']:
                pattern.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
        else:
            pattern = text

        # Find all matches
        while True:
            if options['regex']:
                found_cursor = self.editor.document().find(pattern, cursor, search_flags)
            else:
                found_cursor = self.editor.document().find(text, cursor, search_flags)

            if found_cursor.isNull():
                break

            start = found_cursor.selectionStart()
            end = found_cursor.selectionEnd()
            matches.append((start, end))

            # Move cursor past this match
            cursor = found_cursor
            cursor.clearSelection()

        # Highlight all matches (basic implementation)
        if matches:
            self.highlight_matches(matches)

        return matches

    def highlight_matches(self, matches: List[Tuple[int, int]]):
        """Highlight all matches in the editor."""
        if not self.editor:
            return

        # This is a basic implementation
        # In a full implementation, you'd use QTextEdit.ExtraSelection
        from PySide6.QtGui import QColor

        extra_selections = []

        for start, end in matches:
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor(255, 255, 0, 100))  # Yellow highlight
            selection.cursor = self.editor.textCursor()
            selection.cursor.setPosition(start)
            selection.cursor.setPosition(end, QTextCursor.KeepAnchor)
            extra_selections.append(selection)

        self.editor.setExtraSelections(extra_selections)

    def replace_current(self):
        """Replace current selection."""
        find_text = self.find_input.currentText()
        replace_text = self.replace_input.currentText()

        if not find_text or not self.editor:
            return

        self.add_to_history(replace_text, self.replace_history)

        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            # Check if selection matches our search
            selected = cursor.selectedText()
            options = self.get_search_options()

            if self.text_matches(selected, find_text, options):
                cursor.insertText(replace_text)
                # Find next occurrence
                self.find_next()

    def replace_all(self):
        """Replace all occurrences."""
        find_text = self.find_input.currentText()
        replace_text = self.replace_input.currentText()

        if not find_text or not self.editor:
            return

        self.add_to_history(replace_text, self.replace_history)

        matches = self.find_all_matches(find_text)
        if not matches:
            return

        # Perform replacements from end to start to maintain positions
        cursor = self.editor.textCursor()
        cursor.beginEditBlock()

        replaced_count = 0
        for start, end in reversed(matches):
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.KeepAnchor)
            cursor.insertText(replace_text)
            replaced_count += 1

        cursor.endEditBlock()
        logger.info(f"Replaced {replaced_count} occurrences")

    def text_matches(self, text: str, pattern: str, options: Dict[str, Any]) -> bool:
        """Check if text matches the pattern with given options."""
        if options['regex']:
            flags = 0 if options['case_sensitive'] else re.IGNORECASE
            return bool(re.fullmatch(pattern, text, flags))
        else:
            if not options['case_sensitive']:
                text = text.lower()
                pattern = pattern.lower()

            if options['whole_word']:
                # Simple whole word check
                return text == pattern
            else:
                return pattern in text

    def add_to_history(self, text: str, history: List[str]):
        """Add text to history."""
        if text and text not in history:
            history.insert(0, text)
            if len(history) > 20:  # Keep last 20 items
                history.pop()

    def show_find_widget(self):
        """Show the find widget and focus on find input."""
        self.show()
        self.find_input.setFocus()
        if self.find_input.lineEdit():
            self.find_input.lineEdit().selectAll()

    def show_replace_widget(self):
        """Show the find/replace widget and focus on find input."""
        self.show()
        self.find_input.setFocus()
        if self.find_input.lineEdit():
            self.find_input.lineEdit().selectAll()

    def close_widget(self):
        """Close the find/replace widget."""
        self.hide()
        if self.editor:
            # Clear highlights
            self.editor.setExtraSelections([])
            # Return focus to editor
            self.editor.setFocus()
        self.closed.emit()


class FindReplaceDialog(QDialog):
    """Standalone find/replace dialog."""

    def __init__(self, editor=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find and Replace")
        self.setModal(False)

        layout = QVBoxLayout(self)

        self.find_replace_widget = FindReplace()
        self.find_replace_widget.set_editor(editor)
        layout.addWidget(self.find_replace_widget)

        # Connect close signal
        self.find_replace_widget.closed.connect(self.close)

    def show_find(self):
        """Show dialog in find mode."""
        self.find_replace_widget.show_find_widget()
        self.show()

    def show_replace(self):
        """Show dialog in replace mode."""
        self.find_replace_widget.show_replace_widget()
        self.show()