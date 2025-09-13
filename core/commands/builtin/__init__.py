#!/usr/bin/env python3
"""
Built-in commands for ViloApp.

This module contains all the built-in commands that come with the application,
organized by category.
"""

from core.commands.builtin.file_commands import register_file_commands
from core.commands.builtin.view_commands import register_view_commands
from core.commands.builtin.workspace_commands import register_workspace_commands
from core.commands.builtin.edit_commands import register_edit_commands
from core.commands.builtin.navigation_commands import register_navigation_commands
from core.commands.builtin.debug_commands import register_debug_commands
from core.commands.builtin.settings_commands import register_settings_commands
from core.commands.builtin.palette_commands import register_palette_commands
from core.commands.builtin.terminal_commands import register_terminal_commands
from core.commands.builtin.tab_commands import register_tab_commands
from core.commands.builtin.pane_commands import register_pane_commands
from core.commands.builtin.sidebar_commands import register_sidebar_commands
# Import UI and window commands to trigger their decorators
import core.commands.builtin.ui_commands
import core.commands.builtin.window_commands
import core.commands.builtin.help_commands

def register_all_builtin_commands():
    """Register all built-in commands with the command registry."""
    register_file_commands()
    register_view_commands()
    register_workspace_commands()
    register_edit_commands()
    register_navigation_commands()
    register_debug_commands()
    register_settings_commands()
    register_palette_commands()
    register_terminal_commands()
    register_tab_commands()
    register_pane_commands()
    register_sidebar_commands()

__all__ = [
    'register_all_builtin_commands',
    'register_file_commands',
    'register_view_commands', 
    'register_workspace_commands',
    'register_edit_commands',
    'register_navigation_commands',
    'register_debug_commands',
    'register_settings_commands',
    'register_palette_commands',
    'register_terminal_commands',
    'register_tab_commands',
    'register_pane_commands',
    'register_sidebar_commands',
]