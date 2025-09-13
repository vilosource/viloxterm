#!/usr/bin/env python3
"""
Editor service for managing text editor operations.

This service handles editor-specific functionality like
text manipulation, search/replace, and editor state management.
"""

from typing import Optional, Dict, Any, List, Tuple
import logging

from services.base import Service

logger = logging.getLogger(__name__)


class EditorService(Service):
    """
    Service for managing editor operations.
    
    Handles text editing, search/replace, cursor management,
    and editor-specific functionality.
    """
    
    def __init__(self):
        """Initialize the editor service."""
        super().__init__("EditorService")
        self._active_editor = None
        self._editors: Dict[str, Any] = {}  # widget_id -> editor info
        self._clipboard_content = ""
        self._search_history: List[str] = []
        self._replace_history: List[str] = []
        
    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize the service with application context."""
        super().initialize(context)
        
        # Load search/replace history
        self._load_history()
        
        logger.info("EditorService initialized")
    
    def cleanup(self) -> None:
        """Cleanup service resources."""
        # Save history
        self._save_history()
        
        self._active_editor = None
        self._editors.clear()
        super().cleanup()
    
    # ============= Editor Management =============
    
    def register_editor(self, widget_id: str, editor_widget: Any) -> None:
        """
        Register an editor widget.
        
        Args:
            widget_id: Unique widget identifier
            editor_widget: The editor widget instance
        """
        self._editors[widget_id] = {
            'id': widget_id,
            'widget': editor_widget,
            'file_path': None,
            'modified': False,
            'language': 'plaintext'
        }
        
        # Set as active if it's the only one
        if len(self._editors) == 1:
            self._active_editor = widget_id
        
        # Notify observers
        self.notify('editor_registered', {'widget_id': widget_id})
        
        logger.debug(f"Editor registered: {widget_id}")
    
    def unregister_editor(self, widget_id: str) -> None:
        """
        Unregister an editor widget.
        
        Args:
            widget_id: Widget identifier to unregister
        """
        if widget_id in self._editors:
            del self._editors[widget_id]
            
            # Update active editor
            if self._active_editor == widget_id:
                self._active_editor = next(iter(self._editors), None)
            
            # Notify observers
            self.notify('editor_unregistered', {'widget_id': widget_id})
            
            logger.debug(f"Editor unregistered: {widget_id}")
    
    def set_active_editor(self, widget_id: str) -> bool:
        """
        Set the active editor.
        
        Args:
            widget_id: Widget identifier to make active
            
        Returns:
            True if editor was set as active
        """
        if widget_id not in self._editors:
            logger.warning(f"Editor not found: {widget_id}")
            return False
        
        self._active_editor = widget_id
        
        # Notify observers
        self.notify('editor_activated', {'widget_id': widget_id})
        
        return True
    
    def get_active_editor(self) -> Optional[Any]:
        """
        Get the active editor widget.
        
        Returns:
            Active editor widget or None
        """
        if self._active_editor and self._active_editor in self._editors:
            return self._editors[self._active_editor]['widget']
        return None
    
    # ============= Text Operations =============
    
    def get_text(self, widget_id: Optional[str] = None) -> Optional[str]:
        """
        Get text from an editor.
        
        Args:
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            Editor text or None
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return None
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'toPlainText'):
            return editor.toPlainText()
        elif hasattr(editor, 'text'):
            return editor.text()
        
        return None
    
    def set_text(self, text: str, widget_id: Optional[str] = None) -> bool:
        """
        Set text in an editor.
        
        Args:
            text: Text to set
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            True if text was set
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return False
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'setPlainText'):
            editor.setPlainText(text)
        elif hasattr(editor, 'setText'):
            editor.setText(text)
        else:
            return False
        
        # Mark as modified
        self._editors[widget_id]['modified'] = True
        
        # Notify observers
        self.notify('text_changed', {'widget_id': widget_id})
        
        return True
    
    def insert_text(self, text: str, widget_id: Optional[str] = None) -> bool:
        """
        Insert text at cursor position.
        
        Args:
            text: Text to insert
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            True if text was inserted
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return False
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'insertPlainText'):
            editor.insertPlainText(text)
            
            # Mark as modified
            self._editors[widget_id]['modified'] = True
            
            # Notify observers
            self.notify('text_inserted', {
                'widget_id': widget_id,
                'text': text
            })
            
            return True
        
        return False
    
    # ============= Clipboard Operations =============
    
    def cut(self, widget_id: Optional[str] = None) -> bool:
        """
        Cut selected text to clipboard.
        
        Args:
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            True if text was cut
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return False
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'cut'):
            editor.cut()
            
            # Mark as modified
            self._editors[widget_id]['modified'] = True
            
            # Notify observers
            self.notify('text_cut', {'widget_id': widget_id})
            
            return True
        
        return False
    
    def copy(self, widget_id: Optional[str] = None) -> bool:
        """
        Copy selected text to clipboard.
        
        Args:
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            True if text was copied
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return False
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'copy'):
            editor.copy()
            
            # Notify observers
            self.notify('text_copied', {'widget_id': widget_id})
            
            return True
        
        return False
    
    def paste(self, widget_id: Optional[str] = None) -> bool:
        """
        Paste text from clipboard.
        
        Args:
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            True if text was pasted
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return False
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'paste'):
            editor.paste()
            
            # Mark as modified
            self._editors[widget_id]['modified'] = True
            
            # Notify observers
            self.notify('text_pasted', {'widget_id': widget_id})
            
            return True
        
        return False
    
    # ============= Selection Operations =============
    
    def select_all(self, widget_id: Optional[str] = None) -> bool:
        """
        Select all text in editor.
        
        Args:
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            True if text was selected
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return False
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'selectAll'):
            editor.selectAll()
            
            # Notify observers
            self.notify('text_selected', {'widget_id': widget_id})
            
            return True
        
        return False
    
    def get_selected_text(self, widget_id: Optional[str] = None) -> Optional[str]:
        """
        Get selected text from editor.
        
        Args:
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            Selected text or None
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return None
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'textCursor'):
            cursor = editor.textCursor()
            return cursor.selectedText() if cursor.hasSelection() else None
        
        return None
    
    # ============= Undo/Redo Operations =============
    
    def undo(self, widget_id: Optional[str] = None) -> bool:
        """
        Undo last operation.
        
        Args:
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            True if undo was performed
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return False
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'undo'):
            editor.undo()
            
            # Notify observers
            self.notify('undo_performed', {'widget_id': widget_id})
            
            return True
        
        return False
    
    def redo(self, widget_id: Optional[str] = None) -> bool:
        """
        Redo last undone operation.
        
        Args:
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            True if redo was performed
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return False
        
        editor = self._editors[widget_id]['widget']
        if hasattr(editor, 'redo'):
            editor.redo()
            
            # Notify observers
            self.notify('redo_performed', {'widget_id': widget_id})
            
            return True
        
        return False
    
    # ============= Search Operations =============
    
    def find_text(self, 
                  search_term: str, 
                  case_sensitive: bool = False,
                  whole_word: bool = False,
                  widget_id: Optional[str] = None) -> List[Tuple[int, int]]:
        """
        Find text in editor.
        
        Args:
            search_term: Text to search for
            case_sensitive: Whether search is case sensitive
            whole_word: Whether to match whole words only
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            List of (start, end) positions
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return []
        
        text = self.get_text(widget_id)
        if not text:
            return []
        
        # Add to search history
        if search_term and search_term not in self._search_history:
            self._search_history.insert(0, search_term)
            self._search_history = self._search_history[:20]  # Keep last 20
        
        # Simple search implementation (can be enhanced)
        matches = []
        search_text = text if case_sensitive else text.lower()
        search_pattern = search_term if case_sensitive else search_term.lower()
        
        start = 0
        while True:
            pos = search_text.find(search_pattern, start)
            if pos == -1:
                break
            
            # Check whole word if required
            if whole_word:
                # Check boundaries
                if pos > 0 and search_text[pos-1].isalnum():
                    start = pos + 1
                    continue
                if pos + len(search_pattern) < len(search_text) and \
                   search_text[pos + len(search_pattern)].isalnum():
                    start = pos + 1
                    continue
            
            matches.append((pos, pos + len(search_pattern)))
            start = pos + 1
        
        # Notify observers
        self.notify('text_found', {
            'widget_id': widget_id,
            'search_term': search_term,
            'matches': len(matches)
        })
        
        return matches
    
    def replace_text(self,
                    search_term: str,
                    replace_term: str,
                    all_occurrences: bool = False,
                    widget_id: Optional[str] = None) -> int:
        """
        Replace text in editor.
        
        Args:
            search_term: Text to search for
            replace_term: Text to replace with
            all_occurrences: Whether to replace all occurrences
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            Number of replacements made
        """
        widget_id = widget_id or self._active_editor
        if not widget_id or widget_id not in self._editors:
            return 0
        
        text = self.get_text(widget_id)
        if not text:
            return 0
        
        # Add to history
        if replace_term and replace_term not in self._replace_history:
            self._replace_history.insert(0, replace_term)
            self._replace_history = self._replace_history[:20]
        
        # Perform replacement
        if all_occurrences:
            new_text = text.replace(search_term, replace_term)
            count = text.count(search_term)
        else:
            new_text = text.replace(search_term, replace_term, 1)
            count = 1 if search_term in text else 0
        
        if count > 0:
            self.set_text(new_text, widget_id)
            
            # Notify observers
            self.notify('text_replaced', {
                'widget_id': widget_id,
                'search_term': search_term,
                'replace_term': replace_term,
                'count': count
            })
        
        return count
    
    # ============= Utility Methods =============
    
    def _load_history(self) -> None:
        """Load search/replace history from settings."""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("ViloxTerm", "Editor")
            
            search_history = settings.value("search_history", [])
            if isinstance(search_history, list):
                self._search_history = search_history[:20]
            
            replace_history = settings.value("replace_history", [])
            if isinstance(replace_history, list):
                self._replace_history = replace_history[:20]
                
        except Exception as e:
            logger.error(f"Failed to load editor history: {e}")
    
    def _save_history(self) -> None:
        """Save search/replace history to settings."""
        try:
            from PySide6.QtCore import QSettings
            settings = QSettings("ViloxTerm", "Editor")
            
            settings.setValue("search_history", self._search_history)
            settings.setValue("replace_history", self._replace_history)
            settings.sync()
            
        except Exception as e:
            logger.error(f"Failed to save editor history: {e}")
    
    def get_editor_count(self) -> int:
        """Get the number of registered editors."""
        return len(self._editors)
    
    def get_all_editor_ids(self) -> List[str]:
        """Get all registered editor widget IDs."""
        return list(self._editors.keys())
    
    def is_modified(self, widget_id: Optional[str] = None) -> bool:
        """
        Check if editor has unsaved changes.
        
        Args:
            widget_id: Editor widget ID, or None for active editor
            
        Returns:
            True if editor is modified
        """
        widget_id = widget_id or self._active_editor
        if widget_id and widget_id in self._editors:
            return self._editors[widget_id]['modified']
        return False
    
    def set_modified(self, modified: bool, widget_id: Optional[str] = None) -> None:
        """
        Set editor modified state.
        
        Args:
            modified: Whether editor is modified
            widget_id: Editor widget ID, or None for active editor
        """
        widget_id = widget_id or self._active_editor
        if widget_id and widget_id in self._editors:
            self._editors[widget_id]['modified'] = modified