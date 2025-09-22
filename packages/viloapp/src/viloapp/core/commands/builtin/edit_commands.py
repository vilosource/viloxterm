#!/usr/bin/env python3
"""
Edit-related commands using the service layer.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="editor.action.cut",
    title="Cut",
    category="Edit",
    description="Cut selected text to clipboard",
    shortcut="ctrl+x",
    icon="scissors",
    when="editorFocus && editorHasSelection",
)
def cut_command(context: CommandContext) -> CommandResult:
    """Cut selected text from active editor."""
    try:
        # Get active editor widget from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane or not active_pane.widget:
            return CommandResult(status=CommandStatus.FAILURE, message="No active widget")

        # Check if it's an editor widget and has cut method
        widget = active_pane.widget
        if hasattr(widget, "cut"):
            widget.cut()
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Active widget is not an editor"
            )

    except Exception as e:
        logger.error(f"Failed to cut: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="editor.action.copy",
    title="Copy",
    category="Edit",
    description="Copy selected text to clipboard",
    shortcut="ctrl+c",
    icon="copy",
    when="editorFocus && editorHasSelection",
)
def copy_command(context: CommandContext) -> CommandResult:
    """Copy selected text from active editor."""
    try:
        # Get active editor widget from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane or not active_pane.widget:
            return CommandResult(status=CommandStatus.FAILURE, message="No active widget")

        # Check if it's an editor widget and has copy method
        widget = active_pane.widget
        if hasattr(widget, "copy"):
            widget.copy()
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Active widget is not an editor"
            )

    except Exception as e:
        logger.error(f"Failed to copy: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="editor.action.paste",
    title="Paste",
    category="Edit",
    description="Paste text from clipboard",
    shortcut="ctrl+v",
    icon="clipboard",
    when="editorFocus",
)
def paste_command(context: CommandContext) -> CommandResult:
    """Paste text to active editor."""
    try:
        # Get active editor widget from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane or not active_pane.widget:
            return CommandResult(status=CommandStatus.FAILURE, message="No active widget")

        # Check if it's an editor widget and has paste method
        widget = active_pane.widget
        if hasattr(widget, "paste"):
            widget.paste()
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Active widget is not an editor"
            )

    except Exception as e:
        logger.error(f"Failed to paste: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="editor.action.selectAll",
    title="Select All",
    category="Edit",
    description="Select all text in the editor",
    shortcut="ctrl+a",
    icon="select-all",
    when="editorFocus",
)
def select_all_command(context: CommandContext) -> CommandResult:
    """Select all text in active editor."""
    try:
        # Get active editor widget from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane or not active_pane.widget:
            return CommandResult(status=CommandStatus.FAILURE, message="No active widget")

        # Check if it's an editor widget and has selectAll method
        widget = active_pane.widget
        if hasattr(widget, "selectAll"):
            widget.selectAll()
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Active widget is not an editor"
            )

    except Exception as e:
        logger.error(f"Failed to select all: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="editor.action.undo",
    title="Undo",
    category="Edit",
    description="Undo last edit operation",
    shortcut="ctrl+z",
    icon="undo",
    when="editorFocus",
)
def undo_command(context: CommandContext) -> CommandResult:
    """Undo last operation in active editor."""
    try:
        # Get active editor widget from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane or not active_pane.widget:
            return CommandResult(status=CommandStatus.FAILURE, message="No active widget")

        # Check if it's an editor widget and has undo method
        widget = active_pane.widget
        if hasattr(widget, "undo"):
            widget.undo()
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Active widget is not an editor"
            )

    except Exception as e:
        logger.error(f"Failed to undo: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="editor.action.redo",
    title="Redo",
    category="Edit",
    description="Redo last undone operation",
    shortcut="ctrl+shift+z",
    icon="redo",
    when="editorFocus",
)
def redo_command(context: CommandContext) -> CommandResult:
    """Redo last undone operation in active editor."""
    try:
        # Get active editor widget from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane or not active_pane.widget:
            return CommandResult(status=CommandStatus.FAILURE, message="No active widget")

        # Check if it's an editor widget and has redo method
        widget = active_pane.widget
        if hasattr(widget, "redo"):
            widget.redo()
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Active widget is not an editor"
            )

    except Exception as e:
        logger.error(f"Failed to redo: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="editor.action.find",
    title="Find",
    category="Edit",
    description="Find text in the editor",
    shortcut="ctrl+f",
    icon="search",
    when="editorFocus",
)
def find_command(context: CommandContext) -> CommandResult:
    """Find text in active editor."""
    try:
        # Get active editor widget from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane or not active_pane.widget:
            return CommandResult(status=CommandStatus.FAILURE, message="No active widget")

        widget = active_pane.widget

        search_term = context.parameters.get("search_term", "") if context.parameters else ""
        # TODO: Add support for case_sensitive and whole_word search options

        if not search_term and hasattr(widget, "textCursor"):
            # Get selected text as default search term
            search_term = widget.textCursor().selectedText() or ""

        if search_term and hasattr(widget, "find"):
            # Simple find - most editors support this
            found = widget.find(search_term)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                data={
                    "search_term": search_term,
                    "found": found,
                },
            )
        else:
            return CommandResult(
                status=CommandStatus.FAILURE, message="No search term or find not supported"
            )

    except Exception as e:
        logger.error(f"Failed to find text: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="editor.action.replace",
    title="Replace",
    category="Edit",
    description="Replace text in the editor",
    shortcut="ctrl+h",
    icon="replace",
    when="editorFocus",
)
def replace_command(context: CommandContext) -> CommandResult:
    """Replace text in active editor."""
    try:
        # Get active editor widget from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane or not active_pane.widget:
            return CommandResult(status=CommandStatus.FAILURE, message="No active widget")

        widget = active_pane.widget

        search_term = context.parameters.get("search_term", "") if context.parameters else ""
        replace_term = context.parameters.get("replace_term", "") if context.parameters else ""
        all_occurrences = context.parameters.get("all", False) if context.parameters else False

        if search_term and hasattr(widget, "toPlainText"):
            # Simple replace implementation
            text = widget.toPlainText()
            if all_occurrences:
                new_text = text.replace(search_term, replace_term)
                count = text.count(search_term)
            else:
                # Replace first occurrence
                new_text = text.replace(search_term, replace_term, 1)
                count = 1 if search_term in text else 0

            if count > 0:
                widget.setPlainText(new_text)

            # Show status message
            if context.main_window and hasattr(context.main_window, "status_bar"):
                if count > 0:
                    msg = f"Replaced {count} occurrence{'s' if count > 1 else ''}"
                else:
                    msg = "No occurrences found"
                context.main_window.status_bar.set_message(msg, 2000)

            return CommandResult(
                status=CommandStatus.SUCCESS,
                data={
                    "search_term": search_term,
                    "replace_term": replace_term,
                    "count": count,
                },
            )
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="No search term provided")

    except Exception as e:
        logger.error(f"Failed to replace text: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_edit_commands():
    """Register all edit commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Edit commands registered")
