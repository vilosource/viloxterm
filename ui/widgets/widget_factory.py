"""Factory for creating different widget types for panes."""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget, QTextEdit, QListWidget, QTreeWidget, QPlainTextEdit, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class WidgetFactory:
    """Factory class for creating different types of widgets for panes."""
    
    @staticmethod
    def create_widget(widget_type: str, widget_state: Optional[Dict[str, Any]] = None, 
                     parent: Optional[QWidget] = None) -> QWidget:
        """
        Create a widget of the specified type.
        
        Args:
            widget_type: Type of widget to create
            widget_state: Optional state to restore
            parent: Parent widget
            
        Returns:
            Created widget instance
        """
        creators = {
            'editor': WidgetFactory._create_editor,
            'terminal': WidgetFactory._create_terminal,
            'explorer': WidgetFactory._create_explorer,
            'output': WidgetFactory._create_output,
            'variables': WidgetFactory._create_variables,
            'callstack': WidgetFactory._create_callstack,
            'search': WidgetFactory._create_search,
            'markdown': WidgetFactory._create_markdown,
            'placeholder': WidgetFactory._create_placeholder,
        }
        
        creator = creators.get(widget_type, WidgetFactory._create_placeholder)
        widget = creator(parent)
        
        # Restore state if provided
        if widget_state:
            WidgetFactory._restore_widget_state(widget, widget_type, widget_state)
            
        return widget
    
    @staticmethod
    def _create_editor(parent: Optional[QWidget] = None) -> QWidget:
        """Create an editor widget."""
        editor = QTextEdit(parent)
        editor.setPlainText("# Editor Widget\n\n# This is a code editor placeholder\n")
        editor.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 14px;
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
            }
        """)
        return editor
    
    @staticmethod
    def _create_terminal(parent: Optional[QWidget] = None) -> QWidget:
        """Create a terminal widget."""
        terminal = QPlainTextEdit(parent)
        terminal.setPlainText("$ Terminal Widget\n$ This is a terminal placeholder\n$ ")
        terminal.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                background-color: #0c0c0c;
                color: #cccccc;
                border: none;
            }
        """)
        terminal.setReadOnly(False)
        return terminal
    
    @staticmethod
    def _create_explorer(parent: Optional[QWidget] = None) -> QWidget:
        """Create a file explorer widget."""
        explorer = QTreeWidget(parent)
        explorer.setHeaderLabel("Explorer")
        
        # Add sample items
        from PySide6.QtWidgets import QTreeWidgetItem
        root = QTreeWidgetItem(explorer, ["Project"])
        src = QTreeWidgetItem(root, ["src"])
        QTreeWidgetItem(src, ["main.py"])
        QTreeWidgetItem(src, ["utils.py"])
        tests = QTreeWidgetItem(root, ["tests"])
        QTreeWidgetItem(tests, ["test_main.py"])
        
        explorer.expandAll()
        explorer.setStyleSheet("""
            QTreeWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
        """)
        return explorer
    
    @staticmethod
    def _create_output(parent: Optional[QWidget] = None) -> QWidget:
        """Create an output console widget."""
        output = QPlainTextEdit(parent)
        output.setPlainText("Output Console\n" + "="*40 + "\n")
        output.setReadOnly(True)
        output.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                background-color: #1e1e1e;
                color: #cccccc;
                border: none;
            }
        """)
        return output
    
    @staticmethod
    def _create_variables(parent: Optional[QWidget] = None) -> QWidget:
        """Create a variables viewer widget."""
        variables = QListWidget(parent)
        variables.addItems([
            "x = 42",
            "name = 'John'",
            "data = [1, 2, 3, 4, 5]",
            "config = {'debug': True}"
        ])
        variables.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)
        return variables
    
    @staticmethod
    def _create_callstack(parent: Optional[QWidget] = None) -> QWidget:
        """Create a call stack widget."""
        callstack = QListWidget(parent)
        callstack.addItems([
            "main() - line 45",
            "process_data() - line 123", 
            "validate_input() - line 67",
            "parse_config() - line 89"
        ])
        callstack.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)
        return callstack
    
    @staticmethod
    def _create_search(parent: Optional[QWidget] = None) -> QWidget:
        """Create a search results widget."""
        search = QListWidget(parent)
        search.addItems([
            "main.py:12 - def process_data():",
            "utils.py:45 - data = process_data(input)",
            "test_main.py:78 - assert process_data([])"
        ])
        search.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #cccccc;
                border: none;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QListWidget::item:selected {
                background-color: #094771;
            }
        """)
        return search
    
    @staticmethod
    def _create_markdown(parent: Optional[QWidget] = None) -> QWidget:
        """Create a markdown preview widget."""
        markdown = QTextEdit(parent)
        markdown.setHtml("""
            <h1>Markdown Preview</h1>
            <p>This is a <strong>markdown</strong> preview widget.</p>
            <ul>
                <li>Feature 1</li>
                <li>Feature 2</li>
                <li>Feature 3</li>
            </ul>
        """)
        markdown.setReadOnly(True)
        markdown.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                color: #333333;
                border: none;
                padding: 10px;
            }
        """)
        return markdown
    
    @staticmethod
    def _create_placeholder(parent: Optional[QWidget] = None) -> QWidget:
        """Create a placeholder widget."""
        label = QLabel("Empty Pane\n\nRight-click for options", parent)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                color: #969696;
                font-size: 14px;
                padding: 20px;
            }
        """)
        return label
    
    @staticmethod
    def _restore_widget_state(widget: QWidget, widget_type: str, state: Dict[str, Any]):
        """Restore widget state from saved data."""
        if widget_type == 'editor' and isinstance(widget, QTextEdit):
            if 'content' in state:
                widget.setPlainText(state['content'])
            if 'cursor_position' in state:
                cursor = widget.textCursor()
                cursor.setPosition(state['cursor_position'])
                widget.setTextCursor(cursor)
                
        elif widget_type == 'terminal' and isinstance(widget, QPlainTextEdit):
            if 'content' in state:
                widget.setPlainText(state['content'])
                
        # Add more state restoration as needed
    
    @staticmethod
    def get_widget_state(widget: QWidget, widget_type: str) -> Dict[str, Any]:
        """Get the current state of a widget."""
        state = {}
        
        if widget_type == 'editor' and isinstance(widget, QTextEdit):
            state['content'] = widget.toPlainText()
            state['cursor_position'] = widget.textCursor().position()
            
        elif widget_type == 'terminal' and isinstance(widget, QPlainTextEdit):
            state['content'] = widget.toPlainText()
            
        # Add more state extraction as needed
        
        return state
    
    @staticmethod
    def get_available_widget_types() -> list[str]:
        """Get list of available widget types."""
        return [
            'editor',
            'terminal',
            'explorer',
            'output',
            'variables',
            'callstack',
            'search',
            'markdown',
            'placeholder'
        ]
    
    @staticmethod
    def get_widget_display_name(widget_type: str) -> str:
        """Get display name for a widget type."""
        names = {
            'editor': 'Editor',
            'terminal': 'Terminal',
            'explorer': 'File Explorer',
            'output': 'Output Console',
            'variables': 'Variables',
            'callstack': 'Call Stack',
            'search': 'Search Results',
            'markdown': 'Markdown Preview',
            'placeholder': 'Empty'
        }
        return names.get(widget_type, widget_type.title())