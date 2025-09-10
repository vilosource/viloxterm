#!/usr/bin/env python3
"""
Edit-related commands using the service layer.
"""

from core.commands.base import Command, CommandResult, CommandContext
from core.commands.decorators import command
from services.editor_service import EditorService
import logging

logger = logging.getLogger(__name__)


@command(
    id="editor.action.cut",
    title="Cut",
    category="Edit",
    description="Cut selected text to clipboard",
    shortcut="ctrl+x",
    icon="scissors",
    when="editorFocus && editorHasSelection"
)
def cut_command(context: CommandContext) -> CommandResult:
    """Cut selected text using EditorService."""
    try:
        editor_service = context.get_service(EditorService)
        if not editor_service:
            return CommandResult(success=False, error="EditorService not available")
        
        success = editor_service.cut()
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to cut text")
            
    except Exception as e:
        logger.error(f"Failed to cut: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="editor.action.copy",
    title="Copy",
    category="Edit",
    description="Copy selected text to clipboard",
    shortcut="ctrl+c",
    icon="copy",
    when="editorFocus && editorHasSelection"
)
def copy_command(context: CommandContext) -> CommandResult:
    """Copy selected text using EditorService."""
    try:
        editor_service = context.get_service(EditorService)
        if not editor_service:
            return CommandResult(success=False, error="EditorService not available")
        
        success = editor_service.copy()
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to copy text")
            
    except Exception as e:
        logger.error(f"Failed to copy: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="editor.action.paste",
    title="Paste",
    category="Edit",
    description="Paste text from clipboard",
    shortcut="ctrl+v",
    icon="clipboard",
    when="editorFocus"
)
def paste_command(context: CommandContext) -> CommandResult:
    """Paste text using EditorService."""
    try:
        editor_service = context.get_service(EditorService)
        if not editor_service:
            return CommandResult(success=False, error="EditorService not available")
        
        success = editor_service.paste()
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to paste text")
            
    except Exception as e:
        logger.error(f"Failed to paste: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="editor.action.selectAll",
    title="Select All",
    category="Edit",
    description="Select all text in the editor",
    shortcut="ctrl+a",
    icon="select-all",
    when="editorFocus"
)
def select_all_command(context: CommandContext) -> CommandResult:
    """Select all text using EditorService."""
    try:
        editor_service = context.get_service(EditorService)
        if not editor_service:
            return CommandResult(success=False, error="EditorService not available")
        
        success = editor_service.select_all()
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to select all")
            
    except Exception as e:
        logger.error(f"Failed to select all: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="editor.action.undo",
    title="Undo",
    category="Edit",
    description="Undo last edit operation",
    shortcut="ctrl+z",
    icon="undo",
    when="editorFocus"
)
def undo_command(context: CommandContext) -> CommandResult:
    """Undo last operation using EditorService."""
    try:
        editor_service = context.get_service(EditorService)
        if not editor_service:
            return CommandResult(success=False, error="EditorService not available")
        
        success = editor_service.undo()
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to undo")
            
    except Exception as e:
        logger.error(f"Failed to undo: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="editor.action.redo",
    title="Redo",
    category="Edit",
    description="Redo last undone operation",
    shortcut="ctrl+shift+z",
    icon="redo",
    when="editorFocus"
)
def redo_command(context: CommandContext) -> CommandResult:
    """Redo last undone operation using EditorService."""
    try:
        editor_service = context.get_service(EditorService)
        if not editor_service:
            return CommandResult(success=False, error="EditorService not available")
        
        success = editor_service.redo()
        
        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to redo")
            
    except Exception as e:
        logger.error(f"Failed to redo: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="editor.action.find",
    title="Find",
    category="Edit",
    description="Find text in the editor",
    shortcut="ctrl+f",
    icon="search",
    when="editorFocus"
)
def find_command(context: CommandContext) -> CommandResult:
    """Find text in editor using EditorService."""
    try:
        editor_service = context.get_service(EditorService)
        if not editor_service:
            return CommandResult(success=False, error="EditorService not available")
        
        search_term = context.args.get('search_term', '')
        case_sensitive = context.args.get('case_sensitive', False)
        whole_word = context.args.get('whole_word', False)
        
        if not search_term:
            # Get selected text as default search term
            search_term = editor_service.get_selected_text() or ''
        
        if search_term:
            matches = editor_service.find_text(
                search_term,
                case_sensitive=case_sensitive,
                whole_word=whole_word
            )
            
            return CommandResult(
                success=True,
                value={
                    'search_term': search_term,
                    'matches': matches,
                    'count': len(matches)
                }
            )
        else:
            return CommandResult(success=False, error="No search term provided")
            
    except Exception as e:
        logger.error(f"Failed to find text: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="editor.action.replace",
    title="Replace",
    category="Edit",
    description="Replace text in the editor",
    shortcut="ctrl+h",
    icon="replace",
    when="editorFocus"
)
def replace_command(context: CommandContext) -> CommandResult:
    """Replace text in editor using EditorService."""
    try:
        editor_service = context.get_service(EditorService)
        if not editor_service:
            return CommandResult(success=False, error="EditorService not available")
        
        search_term = context.args.get('search_term', '')
        replace_term = context.args.get('replace_term', '')
        all_occurrences = context.args.get('all', False)
        
        if search_term:
            count = editor_service.replace_text(
                search_term,
                replace_term,
                all_occurrences=all_occurrences
            )
            
            # Show status message
            if context.main_window and hasattr(context.main_window, 'status_bar'):
                if count > 0:
                    msg = f"Replaced {count} occurrence{'s' if count > 1 else ''}"
                else:
                    msg = "No occurrences found"
                context.main_window.status_bar.set_message(msg, 2000)
            
            return CommandResult(
                success=True,
                value={
                    'search_term': search_term,
                    'replace_term': replace_term,
                    'count': count
                }
            )
        else:
            return CommandResult(success=False, error="No search term provided")
            
    except Exception as e:
        logger.error(f"Failed to replace text: {e}")
        return CommandResult(success=False, error=str(e))


def register_edit_commands():
    """Register all edit commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Edit commands registered")