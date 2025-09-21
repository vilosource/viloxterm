"""Autocomplete functionality for the code editor."""

import logging
from typing import List, Dict, Any, Set
from abc import ABC, abstractmethod
import re

from PySide6.QtWidgets import (
    QListWidget, QListWidgetItem, QFrame, QVBoxLayout
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QTextCursor, QKeySequence, QShortcut, QFont

logger = logging.getLogger(__name__)


class CompletionProvider(ABC):
    """Abstract base class for completion providers."""

    @abstractmethod
    def get_completions(self, text: str, cursor_position: int, context: Dict[str, Any]) -> List[str]:
        """Get completions for the given text and cursor position."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the name of this provider."""
        pass


class KeywordCompletionProvider(CompletionProvider):
    """Provides completion for language keywords."""

    def __init__(self, language: str = "python"):
        self.language = language
        self.keywords = self._get_keywords(language)

    def _get_keywords(self, language: str) -> Set[str]:
        """Get keywords for the specified language."""
        keywords_dict = {
            "python": {
                "False", "None", "True", "__peg_parser__", "and", "as", "assert", "async", "await",
                "break", "class", "continue", "def", "del", "elif", "else", "except", "finally",
                "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal", "not",
                "or", "pass", "raise", "return", "try", "while", "with", "yield"
            },
            "javascript": {
                "abstract", "arguments", "await", "boolean", "break", "byte", "case", "catch",
                "char", "class", "const", "continue", "debugger", "default", "delete", "do",
                "double", "else", "enum", "eval", "export", "extends", "false", "final",
                "finally", "float", "for", "function", "goto", "if", "implements", "import",
                "in", "instanceof", "int", "interface", "let", "long", "native", "new", "null",
                "package", "private", "protected", "public", "return", "short", "static", "super",
                "switch", "synchronized", "this", "throw", "throws", "transient", "true", "try",
                "typeof", "var", "void", "volatile", "while", "with", "yield"
            },
            "json": {
                "true", "false", "null"
            }
        }
        return keywords_dict.get(language, set())

    def get_completions(self, text: str, cursor_position: int, context: Dict[str, Any]) -> List[str]:
        """Get keyword completions."""
        # Extract the current word being typed
        lines = text[:cursor_position].split('\n')
        current_line = lines[-1] if lines else ""

        # Find the word at cursor
        word_match = re.search(r'\b\w*$', current_line)
        if not word_match:
            return []

        current_word = word_match.group()
        if len(current_word) < 2:  # Only suggest after 2 characters
            return []

        # Filter keywords that start with the current word
        completions = [
            keyword for keyword in self.keywords
            if keyword.startswith(current_word) and keyword != current_word
        ]

        return sorted(completions)

    def get_provider_name(self) -> str:
        return f"Keywords ({self.language})"


class SnippetCompletionProvider(CompletionProvider):
    """Provides completion for code snippets."""

    def __init__(self, language: str = "python"):
        self.language = language
        self.snippets = self._get_snippets(language)

    def _get_snippets(self, language: str) -> Dict[str, str]:
        """Get snippets for the specified language."""
        snippets_dict = {
            "python": {
                "def": "def ${1:function_name}(${2:args}):\n    ${3:pass}",
                "class": "class ${1:ClassName}:\n    def __init__(self${2:, args}):\n        ${3:pass}",
                "if": "if ${1:condition}:\n    ${2:pass}",
                "for": "for ${1:item} in ${2:iterable}:\n    ${3:pass}",
                "while": "while ${1:condition}:\n    ${2:pass}",
                "try": "try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:pass}",
                "main": "if __name__ == '__main__':\n    ${1:pass}",
                "init": "def __init__(self${1:, args}):\n    ${2:pass}"
            },
            "javascript": {
                "function": "function ${1:name}(${2:params}) {\n    ${3:// body}\n}",
                "arrow": "(${1:params}) => {\n    ${2:// body}\n}",
                "if": "if (${1:condition}) {\n    ${2:// body}\n}",
                "for": "for (${1:let i = 0}; ${2:i < length}; ${3:i++}) {\n    ${4:// body}\n}",
                "class": "class ${1:ClassName} {\n    constructor(${2:args}) {\n        ${3:// constructor}\n    }\n}",
                "try": "try {\n    ${1:// try}\n} catch (${2:error}) {\n    ${3:// catch}\n}"
            }
        }
        return snippets_dict.get(language, {})

    def get_completions(self, text: str, cursor_position: int, context: Dict[str, Any]) -> List[str]:
        """Get snippet completions."""
        # Extract the current word being typed
        lines = text[:cursor_position].split('\n')
        current_line = lines[-1] if lines else ""

        # Find the word at cursor
        word_match = re.search(r'\b\w*$', current_line)
        if not word_match:
            return []

        current_word = word_match.group()
        if len(current_word) < 2:  # Only suggest after 2 characters
            return []

        # Filter snippets that start with the current word
        completions = [
            f"{trigger} (snippet)" for trigger in self.snippets.keys()
            if trigger.startswith(current_word) and trigger != current_word
        ]

        return sorted(completions)

    def get_provider_name(self) -> str:
        return f"Snippets ({self.language})"


class VariableCompletionProvider(CompletionProvider):
    """Provides completion for variables found in the current document."""

    def __init__(self):
        self.variable_cache = {}
        self.last_text = ""

    def _extract_variables(self, text: str, language: str = "python") -> Set[str]:
        """Extract variable names from the text."""
        variables = set()

        if language == "python":
            # Match Python variable assignments and function definitions
            patterns = [
                r'\b([a-zA-Z_]\w*)\s*=',  # Variable assignments
                r'def\s+([a-zA-Z_]\w*)',  # Function definitions
                r'class\s+([a-zA-Z_]\w*)',  # Class definitions
                r'for\s+([a-zA-Z_]\w*)\s+in',  # For loop variables
                r'import\s+([a-zA-Z_]\w*)',  # Import statements
                r'from\s+\w+\s+import\s+([a-zA-Z_]\w*)',  # From import statements
            ]
        elif language == "javascript":
            patterns = [
                r'\b(?:var|let|const)\s+([a-zA-Z_$]\w*)',  # Variable declarations
                r'function\s+([a-zA-Z_$]\w*)',  # Function declarations
                r'class\s+([a-zA-Z_$]\w*)',  # Class declarations
                r'([a-zA-Z_$]\w*)\s*=',  # Assignments
            ]
        else:
            # Generic patterns
            patterns = [
                r'\b([a-zA-Z_]\w*)\s*=',  # Variable assignments
                r'function\s+([a-zA-Z_]\w*)',  # Function definitions
                r'def\s+([a-zA-Z_]\w*)',  # Function definitions
            ]

        for pattern in patterns:
            matches = re.finditer(pattern, text, re.MULTILINE)
            for match in matches:
                variables.add(match.group(1))

        # Filter out common keywords and very short names
        filtered = {
            var for var in variables
            if len(var) > 2 and var not in {'def', 'class', 'for', 'if', 'else', 'try', 'except'}
        }

        return filtered

    def get_completions(self, text: str, cursor_position: int, context: Dict[str, Any]) -> List[str]:
        """Get variable completions."""
        # Update cache if text has changed significantly
        if self.last_text != text:
            language = context.get('language', 'python')
            self.variable_cache = self._extract_variables(text, language)
            self.last_text = text

        # Extract the current word being typed
        lines = text[:cursor_position].split('\n')
        current_line = lines[-1] if lines else ""

        # Find the word at cursor
        word_match = re.search(r'\b\w*$', current_line)
        if not word_match:
            return []

        current_word = word_match.group()
        if len(current_word) < 2:  # Only suggest after 2 characters
            return []

        # Filter variables that start with the current word
        completions = [
            var for var in self.variable_cache
            if var.startswith(current_word) and var != current_word
        ]

        return sorted(completions)

    def get_provider_name(self) -> str:
        return "Variables"


class AutoComplete:
    """Main autocomplete manager."""

    def __init__(self, editor=None):
        self.editor = editor
        self.providers: List[CompletionProvider] = []
        self.completion_popup = None
        self.completion_cache = {}
        self.cache_timeout = 5000  # 5 seconds
        self.min_chars = 2
        self.enabled = True

        # Setup providers
        self.setup_default_providers()

        # Setup completion timer
        self.completion_timer = QTimer()
        self.completion_timer.setSingleShot(True)
        self.completion_timer.timeout.connect(self._trigger_completion)

    def setup_default_providers(self):
        """Setup default completion providers."""
        self.add_provider(KeywordCompletionProvider("python"))
        self.add_provider(SnippetCompletionProvider("python"))
        self.add_provider(VariableCompletionProvider())

    def add_provider(self, provider: CompletionProvider):
        """Add a completion provider."""
        self.providers.append(provider)

    def remove_provider(self, provider: CompletionProvider):
        """Remove a completion provider."""
        if provider in self.providers:
            self.providers.remove(provider)

    def set_editor(self, editor):
        """Set the editor instance."""
        self.editor = editor
        if editor:
            self.setup_editor_integration()

    def setup_editor_integration(self):
        """Setup integration with the editor."""
        if not self.editor:
            return

        # Connect to text changes
        self.editor.textChanged.connect(self.on_text_changed)

        # Setup shortcuts
        tab_shortcut = QShortcut(QKeySequence("Tab"), self.editor)
        tab_shortcut.activated.connect(self.handle_tab_completion)

        escape_shortcut = QShortcut(QKeySequence("Escape"), self.editor)
        escape_shortcut.activated.connect(self.hide_popup)

    def on_text_changed(self):
        """Handle text change in editor."""
        if not self.enabled or not self.editor:
            return

        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        cursor_position = cursor.position()

        # Check if we should trigger completion
        if self.should_trigger_completion(text, cursor_position):
            self.completion_timer.stop()
            self.completion_timer.start(300)  # 300ms delay
        else:
            self.hide_popup()

    def should_trigger_completion(self, text: str, cursor_position: int) -> bool:
        """Check if completion should be triggered."""
        if cursor_position < self.min_chars:
            return False

        # Get text before cursor
        text_before = text[:cursor_position]
        lines = text_before.split('\n')
        current_line = lines[-1] if lines else ""

        # Check if we're in the middle of a word
        word_match = re.search(r'\b\w*$', current_line)
        if not word_match:
            return False

        current_word = word_match.group()
        return len(current_word) >= self.min_chars

    def _trigger_completion(self):
        """Trigger completion display."""
        if not self.editor:
            return

        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        cursor_position = cursor.position()

        completions = self.get_completions(text, cursor_position)
        if completions:
            self.show_completion_popup(completions)
        else:
            self.hide_popup()

    def get_completions(self, text: str, cursor_position: int) -> List[str]:
        """Get all completions from providers."""
        all_completions = []
        context = {
            'language': 'python',  # Could be detected from file extension
            'cursor_position': cursor_position
        }

        for provider in self.providers:
            try:
                completions = provider.get_completions(text, cursor_position, context)
                all_completions.extend(completions)
            except Exception as e:
                logger.warning(f"Provider {provider.get_provider_name()} failed: {e}")

        # Remove duplicates and sort
        unique_completions = list(set(all_completions))
        return sorted(unique_completions)

    def show_completion_popup(self, completions: List[str]):
        """Show the completion popup."""
        if not self.editor or not completions:
            return

        if self.completion_popup is None:
            self.completion_popup = CompletionPopup(self.editor)
            self.completion_popup.completion_selected.connect(self.insert_completion)

        self.completion_popup.set_completions(completions)
        self.completion_popup.show_at_cursor()

    def hide_popup(self):
        """Hide the completion popup."""
        if self.completion_popup:
            self.completion_popup.hide()

    def handle_tab_completion(self):
        """Handle tab key for completion."""
        if self.completion_popup and self.completion_popup.isVisible():
            self.completion_popup.accept_current()
        else:
            # Insert regular tab
            if self.editor:
                cursor = self.editor.textCursor()
                cursor.insertText("    ")  # 4 spaces

    def insert_completion(self, completion: str):
        """Insert the selected completion."""
        if not self.editor:
            return

        cursor = self.editor.textCursor()
        text = self.editor.toPlainText()
        cursor_position = cursor.position()

        # Find the word to replace
        text_before = text[:cursor_position]
        lines = text_before.split('\n')
        current_line = lines[-1] if lines else ""

        word_match = re.search(r'\b\w*$', current_line)
        if word_match:
            word_start = cursor_position - len(word_match.group())
            cursor.setPosition(word_start)
            cursor.setPosition(cursor_position, QTextCursor.KeepAnchor)

            # Handle snippets
            if completion.endswith(" (snippet)"):
                snippet_name = completion.replace(" (snippet)", "")
                for provider in self.providers:
                    if isinstance(provider, SnippetCompletionProvider):
                        snippet_text = provider.snippets.get(snippet_name, snippet_name)
                        # Simple snippet expansion (without placeholders for now)
                        expanded = snippet_text.replace("${1:pass}", "pass").replace("${2:}", "").replace("${3:}", "")
                        expanded = re.sub(r'\$\{\d+:[^}]*\}', '', expanded)
                        cursor.insertText(expanded)
                        break
            else:
                cursor.insertText(completion)

        self.hide_popup()


class CompletionPopup(QFrame):
    """Popup widget for showing completions."""

    completion_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(200)
        self.list_widget.setFont(QFont("monospace", 10))
        layout.addWidget(self.list_widget)

        # Connect signals
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        self.list_widget.itemActivated.connect(self.on_item_activated)

        self.setStyleSheet("""
            CompletionPopup {
                background-color: #2d2d30;
                border: 1px solid #3e3e42;
                color: #cccccc;
            }
            QListWidget {
                background-color: #2d2d30;
                border: none;
                color: #cccccc;
                selection-background-color: #094771;
            }
            QListWidget::item {
                padding: 2px 4px;
                border-bottom: 1px solid #3e3e42;
            }
            QListWidget::item:hover {
                background-color: #3e3e42;
            }
        """)

    def set_completions(self, completions: List[str]):
        """Set the completions to display."""
        self.list_widget.clear()
        for completion in completions:
            item = QListWidgetItem(completion)
            self.list_widget.addItem(item)

        if completions:
            self.list_widget.setCurrentRow(0)

    def show_at_cursor(self):
        """Show the popup at the cursor position."""
        if not self.parent():
            return

        editor = self.parent()
        cursor = editor.textCursor()
        cursor_rect = editor.cursorRect(cursor)

        # Position popup below cursor
        global_pos = editor.mapToGlobal(cursor_rect.bottomLeft())
        self.move(global_pos)
        self.show()

    def accept_current(self):
        """Accept the currently selected completion."""
        current_item = self.list_widget.currentItem()
        if current_item:
            self.completion_selected.emit(current_item.text())

    def on_item_clicked(self, item):
        """Handle item click."""
        self.completion_selected.emit(item.text())

    def on_item_activated(self, item):
        """Handle item activation (double-click or enter)."""
        self.completion_selected.emit(item.text())

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.accept_current()
        elif event.key() == Qt.Key_Tab:
            self.accept_current()
        else:
            super().keyPressEvent(event)