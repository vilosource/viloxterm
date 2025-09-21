"""Code editor widget implementation."""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtWidgets import QPlainTextEdit, QWidget
from PySide6.QtCore import Signal, Qt, QRect, QSize
from PySide6.QtGui import QTextOption, QPainter, QColor, QTextFormat, QFont, QKeySequence, QShortcut

try:
    from pygments import highlight
    from pygments.lexers import get_lexer_for_filename, TextLexer
    from pygments.formatters import HtmlFormatter
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class LineNumberArea(QWidget):
    """Line number area for editor."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):
    """Code editor widget with syntax highlighting."""

    # Signals
    file_loaded = Signal(str)  # file_path
    file_saved = Signal(str)  # file_path
    modified_changed = Signal(bool)  # is_modified
    cursor_position_changed = Signal(int, int)  # line, column
    find_requested = Signal()  # find dialog requested
    replace_requested = Signal()  # replace dialog requested

    def __init__(self, parent=None):
        super().__init__(parent)

        self.file_path: Optional[Path] = None
        self.lexer = None
        self.line_number_area = LineNumberArea(self)
        self.find_replace_widget = None

        self.setup_editor()
        self.setup_shortcuts()
        self.update_line_number_area_width(0)

        # Connect signals
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.textChanged.connect(self._on_text_changed)

    def setup_editor(self):
        """Setup editor configuration."""
        # Font
        font = QFont("monospace")
        font.setPointSize(12)
        self.setFont(font)

        # Tab settings
        self.setTabStopDistance(4 * self.fontMetrics().horizontalAdvance(' '))

        # Word wrap
        self.setWordWrapMode(QTextOption.NoWrap)

        # Style
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
        """)

        # Initial highlight
        self.highlight_current_line()

    def setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        # Find and replace shortcuts
        find_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        find_shortcut.activated.connect(self.show_find_dialog)

        replace_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        replace_shortcut.activated.connect(self.show_replace_dialog)

        # Find next/previous shortcuts (F3/Shift+F3) will be handled by the find widget

    def line_number_area_width(self):
        """Calculate line number area width."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num /= 10
            digits += 1

        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Update line number area width."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Update line number area on scroll."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(),
                                        self.line_number_area.width(),
                                        rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Handle resize event."""
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(),
                                                self.line_number_area_width(),
                                                cr.height()))

    def line_number_area_paint_event(self, event):
        """Paint line numbers."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#2d2d30"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#858585"))
                painter.drawText(0, int(top), self.line_number_area.width(),
                               self.fontMetrics().height(),
                               Qt.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        """Highlight the current line."""
        from PySide6.QtWidgets import QTextEdit

        extra_selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            line_color = QColor("#2f2f30")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            extra_selections.append(selection)

        self.setExtraSelections(extra_selections)

        # Emit cursor position
        cursor = self.textCursor()
        line = cursor.blockNumber() + 1
        column = cursor.columnNumber() + 1
        self.cursor_position_changed.emit(line, column)

    def load_file(self, file_path: str):
        """Load a file into the editor."""
        try:
            self.file_path = Path(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.setPlainText(content)
            self.document().setModified(False)

            # Set lexer based on file extension
            if PYGMENTS_AVAILABLE:
                try:
                    self.lexer = get_lexer_for_filename(file_path)
                except:
                    self.lexer = TextLexer()

            self.file_loaded.emit(file_path)

        except Exception as e:
            logger.error(f"Failed to load file {file_path}: {e}")

    def save_file(self, file_path: str = None):
        """Save the editor content to file."""
        if file_path:
            self.file_path = Path(file_path)

        if not self.file_path:
            return False

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.toPlainText())

            self.document().setModified(False)
            self.file_saved.emit(str(self.file_path))
            return True

        except Exception as e:
            logger.error(f"Failed to save file {self.file_path}: {e}")
            return False

    def _on_text_changed(self):
        """Handle text change."""
        is_modified = self.document().isModified()
        self.modified_changed.emit(is_modified)

    def update_theme(self, theme_data: Dict[str, Any]):
        """Update editor theme."""
        bg_color = theme_data.get("editor.background", "#1e1e1e")
        fg_color = theme_data.get("editor.foreground", "#d4d4d4")
        selection_bg = theme_data.get("editor.selectionBackground", "#264f78")

        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {bg_color};
                color: {fg_color};
                border: none;
                selection-background-color: {selection_bg};
                selection-color: #ffffff;
            }}
        """)

        # Update line number area
        self.line_number_area.update()

    def show_find_dialog(self):
        """Show find dialog."""
        self.find_requested.emit()

    def show_replace_dialog(self):
        """Show find/replace dialog."""
        self.replace_requested.emit()

    def get_find_replace_widget(self):
        """Get or create the find/replace widget."""
        if self.find_replace_widget is None:
            # Import here to avoid circular imports
            from .features.find_replace import FindReplace
            self.find_replace_widget = FindReplace(self.parent())
            self.find_replace_widget.set_editor(self)
        return self.find_replace_widget

    def set_find_replace_widget(self, widget):
        """Set an external find/replace widget."""
        self.find_replace_widget = widget
        if widget:
            widget.set_editor(self)