#!/usr/bin/env python3
"""
Text editor implementation as an AppWidget.
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import QVBoxLayout, QPlainTextEdit
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextOption

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType


class EditorAppWidget(AppWidget):
    """
    Text editor widget that extends AppWidget.
    
    Provides a simple text editing interface with basic features.
    """
    
    def __init__(self, widget_id: str, parent=None):
        """Initialize the editor widget."""
        super().__init__(widget_id, WidgetType.TEXT_EDITOR, parent)
        self.editor = None
        self.file_path = None
        self.is_modified = False
        self.setup_editor()
        
    def setup_editor(self):
        """Set up the editor UI."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create editor
        self.editor = QPlainTextEdit()
        self.setup_editor_style()
        
        # Connect signals
        self.editor.textChanged.connect(self.on_text_changed)
        
        # Add to layout
        layout.addWidget(self.editor)
        
        # Add initial content
        self.editor.setPlainText(f"# Editor {self.widget_id}\n\nStart typing...")
        self.is_modified = False  # Reset after initial text
        
    def mousePressEvent(self, event):
        """Handle mouse press to focus this editor."""
        # Request focus when user clicks anywhere on the editor widget
        self.request_focus()
        super().mousePressEvent(event)
        
    def focus_widget(self):
        """Set keyboard focus on the text editor."""
        if self.editor:
            self.editor.setFocus()
        
    def setup_editor_style(self):
        """Configure editor appearance."""
        # Set font
        font = QFont("Consolas, Monaco, 'Courier New', monospace")
        font.setPointSize(11)
        self.editor.setFont(font)
        
        # Set colors (VSCode dark theme style)
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: none;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
        """)
        
        # Set tab width
        self.editor.setTabStopDistance(40)  # Approximately 4 spaces
        
        # Enable word wrap
        self.editor.setWordWrapMode(QTextOption.NoWrap)
        
    def on_text_changed(self):
        """Handle text changes."""
        self.is_modified = True
        self.notify_state_change({"modified": True})
        
    def cleanup(self):
        """Clean up resources."""
        # Could prompt to save if modified
        pass
        
    def get_state(self) -> Dict[str, Any]:
        """Get editor state for persistence."""
        state = super().get_state()
        
        # Add editor-specific state
        state["content"] = self.editor.toPlainText()
        state["file_path"] = self.file_path
        state["is_modified"] = self.is_modified
        
        # Cursor position
        cursor = self.editor.textCursor()
        state["cursor_position"] = cursor.position()
        
        # Scroll position
        state["scroll_position"] = {
            "horizontal": self.editor.horizontalScrollBar().value(),
            "vertical": self.editor.verticalScrollBar().value()
        }
        
        return state
        
    def set_state(self, state: Dict[str, Any]):
        """Restore editor state."""
        super().set_state(state)
        
        # Restore content
        if "content" in state:
            self.editor.setPlainText(state["content"])
            
        # Restore file path
        if "file_path" in state:
            self.file_path = state["file_path"]
            
        # Restore modified state
        if "is_modified" in state:
            self.is_modified = state["is_modified"]
            
        # Restore cursor position
        if "cursor_position" in state:
            cursor = self.editor.textCursor()
            cursor.setPosition(state["cursor_position"])
            self.editor.setTextCursor(cursor)
            
        # Restore scroll position
        if "scroll_position" in state:
            self.editor.horizontalScrollBar().setValue(state["scroll_position"].get("horizontal", 0))
            self.editor.verticalScrollBar().setValue(state["scroll_position"].get("vertical", 0))
            
    def get_title(self) -> str:
        """Get editor title."""
        if self.file_path:
            import os
            name = os.path.basename(self.file_path)
            return f"{name}{'*' if self.is_modified else ''}"
        return f"Untitled{'*' if self.is_modified else ''}"
        
    def can_close(self) -> bool:
        """Check if editor can be closed."""
        # For now, always allow close
        # Could prompt to save if modified
        return True
        
    def load_file(self, file_path: str):
        """Load a file into the editor."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
            self.file_path = file_path
            self.is_modified = False
            self.notify_state_change({"file_loaded": file_path})
        except Exception as e:
            # Could show error dialog
            print(f"Error loading file: {e}")
            
    def save_file(self, file_path: Optional[str] = None):
        """Save editor content to file."""
        if file_path:
            self.file_path = file_path
            
        if not self.file_path:
            return False
            
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.is_modified = False
            self.notify_state_change({"file_saved": self.file_path})
            return True
        except Exception as e:
            # Could show error dialog
            print(f"Error saving file: {e}")
            return False
            
    def get_selected_text(self) -> str:
        """Get currently selected text."""
        cursor = self.editor.textCursor()
        return cursor.selectedText()
        
    def insert_text(self, text: str):
        """Insert text at current cursor position."""
        self.editor.insertPlainText(text)