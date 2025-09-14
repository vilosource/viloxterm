#!/usr/bin/env python3
"""
Built-in widget registration.

This module registers all built-in widgets with the AppWidgetManager
at application startup. It serves as the central location for defining
metadata for all built-in widgets.
"""

import logging
from typing import Optional
from core.app_widget_manager import AppWidgetManager
from core.app_widget_metadata import AppWidgetMetadata, WidgetCategory
from ui.widgets.widget_registry import WidgetType

logger = logging.getLogger(__name__)


def register_builtin_widgets():
    """
    Register all built-in widgets with the AppWidgetManager.

    This function should be called once at application startup
    to register all built-in widgets with their metadata.
    """
    manager = AppWidgetManager.get_instance()

    # Register Terminal Widget
    try:
        from ui.terminal.terminal_app_widget import TerminalAppWidget

        manager.register_widget(AppWidgetMetadata(
            widget_id="com.viloapp.terminal",
            widget_type=WidgetType.TERMINAL,
            display_name="Terminal",
            description="Integrated terminal emulator with shell access",
            icon="terminal",
            category=WidgetCategory.TERMINAL,
            widget_class=TerminalAppWidget,
            # Note: No factory needed - TerminalAppWidget can be instantiated directly
            open_command="file.newTerminalTab",
            provides_capabilities=["shell_execution", "ansi_colors", "terminal_emulation"],
            requires_services=["terminal_service"],
            preserve_context_menu=True,
            min_width=300,
            min_height=200
        ))
        logger.debug("Registered Terminal widget")
    except ImportError as e:
        logger.warning(f"Could not register Terminal widget: {e}")

    # Register Text Editor Widget
    try:
        from ui.widgets.editor_app_widget import EditorAppWidget

        manager.register_widget(AppWidgetMetadata(
            widget_id="com.viloapp.editor",
            widget_type=WidgetType.TEXT_EDITOR,
            display_name="Text Editor",
            description="Simple text editor for code and documents",
            icon="file-text",
            category=WidgetCategory.EDITOR,
            widget_class=EditorAppWidget,
            open_command="file.newEditorTab",
            provides_capabilities=["text_editing", "syntax_highlighting"],
            supported_file_types=["txt", "py", "js", "json", "md", "yml", "yaml"],
            preserve_context_menu=True,
            min_width=400,
            min_height=300
        ))
        logger.debug("Registered Text Editor widget")
    except ImportError as e:
        logger.warning(f"Could not register Text Editor widget: {e}")

    # Register Theme Editor Widget
    try:
        from ui.widgets.theme_editor_widget import ThemeEditorAppWidget

        def create_theme_editor_widget(widget_id: str) -> 'ThemeEditorAppWidget':
            return ThemeEditorAppWidget(widget_id)

        from core.widget_placement import WidgetPlacement

        metadata = AppWidgetMetadata(
            widget_id="com.viloapp.theme_editor",
            widget_type=WidgetType.SETTINGS,  # Using SETTINGS for now, should be THEME_EDITOR
            display_name="Theme Editor",
            description="Visual theme customization tool with live preview",
            icon="palette",
            category=WidgetCategory.TOOLS,
            widget_class=ThemeEditorAppWidget,
            factory=create_theme_editor_widget,
            open_command="theme.openEditor",
            singleton=True,  # Only one theme editor needed
            provides_capabilities=["theme_editing", "live_preview", "color_customization"],
            requires_services=["theme_service"],
            min_width=800,
            min_height=600,
            show_header=True,

            # New intent fields
            default_placement=WidgetPlacement.SMART,
            supports_replacement=True,
            supports_new_tab=True
        )

        # Add context-specific commands
        metadata.commands = {
            "open_new_tab": "theme.openEditor",
            "replace_pane": "theme.replaceInPane"
        }

        manager.register_widget(metadata)
        logger.debug("Registered Theme Editor widget")
    except ImportError as e:
        logger.warning(f"Could not register Theme Editor widget: {e}")

    # Register Keyboard Shortcuts Widget
    try:
        from ui.widgets.shortcut_config_app_widget import ShortcutConfigAppWidget

        def create_shortcut_config_widget(widget_id: str) -> 'ShortcutConfigAppWidget':
            return ShortcutConfigAppWidget(widget_id)

        manager.register_widget(AppWidgetMetadata(
            widget_id="com.viloapp.shortcuts",
            widget_type=WidgetType.SETTINGS,  # Note: multiple widgets can share a type
            display_name="Keyboard Shortcuts",
            description="Configure and customize keyboard shortcuts",
            icon="keyboard",
            category=WidgetCategory.TOOLS,
            widget_class=ShortcutConfigAppWidget,
            factory=create_shortcut_config_widget,
            open_command="settings.openKeyboardShortcuts",
            singleton=True,  # Only one shortcuts editor needed
            provides_capabilities=["shortcut_configuration", "keybinding_editor"],
            requires_services=["keyboard_service", "command_service"],
            min_width=600,
            min_height=400
        ))
        logger.debug("Registered Keyboard Shortcuts widget")
    except ImportError as e:
        logger.warning(f"Could not register Keyboard Shortcuts widget: {e}")

    # Register Placeholder Widget
    try:
        from ui.widgets.placeholder_app_widget import PlaceholderAppWidget

        manager.register_widget(AppWidgetMetadata(
            widget_id="com.viloapp.placeholder",
            widget_type=WidgetType.PLACEHOLDER,
            display_name="Empty Pane",
            description="Empty pane - right-click to change type",
            icon="layout",
            category=WidgetCategory.SYSTEM,
            widget_class=PlaceholderAppWidget,
            show_in_menu=True,  # Allow users to explicitly create empty panes
            show_in_palette=False,  # Don't show in command palette
            min_width=100,
            min_height=100
        ))
        logger.debug("Registered Placeholder widget")
    except ImportError as e:
        logger.warning(f"Could not register Placeholder widget: {e}")

    # Register Output Widget (for future use)
    try:
        from ui.widgets.placeholder_app_widget import PlaceholderAppWidget  # Temporary

        manager.register_widget(AppWidgetMetadata(
            widget_id="com.viloapp.output",
            widget_type=WidgetType.OUTPUT,
            display_name="Output Panel",
            description="Output and console messages",
            icon="message-square",
            category=WidgetCategory.TOOLS,
            widget_class=PlaceholderAppWidget,  # Using placeholder for now
            provides_capabilities=["output_display", "console_messages"],
            preserve_context_menu=True,
            min_width=300,
            min_height=150
        ))
        logger.debug("Registered Output widget")
    except ImportError as e:
        logger.warning(f"Could not register Output widget: {e}")

    # Register File Explorer Widget (for future use)
    try:
        from ui.widgets.placeholder_app_widget import PlaceholderAppWidget  # Temporary

        manager.register_widget(AppWidgetMetadata(
            widget_id="com.viloapp.explorer",
            widget_type=WidgetType.EXPLORER,
            display_name="File Explorer",
            description="Browse and manage files",
            icon="folder",
            category=WidgetCategory.VIEWER,
            widget_class=PlaceholderAppWidget,  # Using placeholder for now
            provides_capabilities=["file_browsing", "file_management"],
            requires_services=["file_service"],
            preserve_context_menu=True,
            min_width=200,
            min_height=300,
            show_in_menu=False  # Hide until implemented
        ))
        logger.debug("Registered File Explorer widget")
    except ImportError as e:
        logger.warning(f"Could not register File Explorer widget: {e}")

    logger.info(f"Registered {len(manager)} built-in widgets")


def get_widget_for_command(command_id: str) -> Optional[AppWidgetMetadata]:
    """
    Get the widget associated with a command.

    Args:
        command_id: Command identifier

    Returns:
        Widget metadata if found, None otherwise
    """
    manager = AppWidgetManager.get_instance()
    for widget in manager.get_all_widgets():
        if widget.open_command == command_id:
            return widget
        if command_id in widget.associated_commands:
            return widget
    return None


def get_default_widget_for_file(file_path: str) -> Optional[AppWidgetMetadata]:
    """
    Get the default widget for opening a file.

    Args:
        file_path: Path to the file

    Returns:
        Best matching widget metadata or None
    """
    import os
    _, ext = os.path.splitext(file_path)
    ext = ext.lstrip('.')

    if not ext:
        return None

    manager = AppWidgetManager.get_instance()
    widgets = manager.get_widgets_for_file_type(ext)

    # Prefer editors over viewers
    for widget in widgets:
        if widget.category == WidgetCategory.EDITOR:
            return widget

    # Return first available widget
    return widgets[0] if widgets else None