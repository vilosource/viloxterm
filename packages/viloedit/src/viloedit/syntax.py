"""Syntax highlighting for editor."""

import logging
from typing import Dict, Any

from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont

try:
    from pygments import lex
    from pygments.token import Token
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class SyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter using Pygments."""

    def __init__(self, document, lexer=None):
        super().__init__(document)
        self.lexer = lexer
        self.setup_formats()

    def setup_formats(self):
        """Setup text formats for highlighting."""
        self.formats = {}

        # Keyword format
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569cd6"))
        keyword_format.setFontWeight(QFont.Bold)
        self.formats['keyword'] = keyword_format

        # String format
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#ce9178"))
        self.formats['string'] = string_format

        # Comment format
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6a9955"))
        comment_format.setFontItalic(True)
        self.formats['comment'] = comment_format

        # Function format
        function_format = QTextCharFormat()
        function_format.setForeground(QColor("#dcdcaa"))
        self.formats['function'] = function_format

        # Number format
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#b5cea8"))
        self.formats['number'] = number_format

        # Class format
        class_format = QTextCharFormat()
        class_format.setForeground(QColor("#4ec9b0"))
        self.formats['class'] = class_format

        # Variable format
        variable_format = QTextCharFormat()
        variable_format.setForeground(QColor("#9cdcfe"))
        self.formats['variable'] = variable_format

    def highlightBlock(self, text):
        """Highlight a block of text."""
        if not self.lexer or not PYGMENTS_AVAILABLE:
            return

        try:
            # Use Pygments to tokenize
            tokens = list(lex(text, self.lexer))

            index = 0
            for token_type, token_text in tokens:
                length = len(token_text)

                # Map token type to format
                format = self.get_format_for_token(token_type)
                if format:
                    self.setFormat(index, length, format)

                index += length
        except Exception as e:
            logger.debug(f"Syntax highlighting error: {e}")

    def get_format_for_token(self, token_type):
        """Get format for a token type."""
        if not PYGMENTS_AVAILABLE:
            return None

        if token_type in Token.Keyword:
            return self.formats['keyword']
        elif token_type in Token.String:
            return self.formats['string']
        elif token_type in Token.Comment:
            return self.formats['comment']
        elif token_type in Token.Name.Function:
            return self.formats['function']
        elif token_type in Token.Name.Class:
            return self.formats['class']
        elif token_type in Token.Name.Variable:
            return self.formats['variable']
        elif token_type in Token.Number:
            return self.formats['number']

        return None

    def update_theme(self, theme_data: Dict[str, Any]):
        """Update highlighter colors based on theme."""
        # Update format colors
        if 'keyword' in theme_data:
            self.formats['keyword'].setForeground(QColor(theme_data['keyword']))
        if 'string' in theme_data:
            self.formats['string'].setForeground(QColor(theme_data['string']))
        if 'comment' in theme_data:
            self.formats['comment'].setForeground(QColor(theme_data['comment']))

        # Re-highlight document
        self.rehighlight()