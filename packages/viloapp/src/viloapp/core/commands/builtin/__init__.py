#!/usr/bin/env python3
"""
Built-in commands for ViloApp.

This module contains all the built-in commands that come with the application,
organized by category.
"""

import viloapp.core.commands.builtin.help_commands
import viloapp.core.commands.builtin.registry_commands
import viloapp.core.commands.builtin.theme_management_commands

# Import UI, window, and theme commands to trigger their decorators
import viloapp.core.commands.builtin.ui_commands
import viloapp.core.commands.builtin.window_commands
from viloapp.core.commands.builtin.debug_commands import register_debug_commands
from viloapp.core.commands.builtin.edit_commands import register_edit_commands
from viloapp.core.commands.builtin.file_commands import register_file_commands
from viloapp.core.commands.builtin.navigation_commands import register_navigation_commands
from viloapp.core.commands.builtin.palette_commands import register_palette_commands
from viloapp.core.commands.builtin.pane_commands import register_pane_commands
from viloapp.core.commands.builtin.settings_commands import register_settings_commands
from viloapp.core.commands.builtin.sidebar_commands import register_sidebar_commands
from viloapp.core.commands.builtin.tab_commands import register_tab_commands
from viloapp.core.commands.builtin.terminal_commands import register_terminal_commands
from viloapp.core.commands.builtin.theme_commands import register_theme_commands
from viloapp.core.commands.builtin.view_commands import register_view_commands
from viloapp.core.commands.builtin.workspace_commands import register_workspace_commands


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
    register_theme_commands()


__all__ = [
    "register_all_builtin_commands",
    "register_file_commands",
    "register_view_commands",
    "register_workspace_commands",
    "register_edit_commands",
    "register_navigation_commands",
    "register_debug_commands",
    "register_settings_commands",
    "register_palette_commands",
    "register_terminal_commands",
    "register_tab_commands",
    "register_pane_commands",
    "register_sidebar_commands",
    "register_theme_commands",
]
