#!/usr/bin/env python3
"""
Default settings values for the application.

This module defines all default configuration values used throughout the application.
Settings are organized by category for easy maintenance.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ============= Command Palette Settings =============
COMMAND_PALETTE_SETTINGS = {
    "max_results": 50,
    "show_recent_commands": True,
    "recent_commands_count": 10,
    "search_debounce_ms": 150,
    "auto_select_first": True,
    "show_shortcuts": True,
    "show_categories": True,
    "fuzzy_search_threshold": 0.3,
    "remember_window_size": True,
    "window_width": 600,
    "window_height": 400
}

# ============= Keyboard Shortcut Settings =============
DEFAULT_KEYBOARD_SHORTCUTS = {
    # Command Palette
    "commandPalette.show": "ctrl+shift+p",
    "commandPalette.showInCurrentCategory": "ctrl+p",

    # File Operations (Legacy - to be removed)
    # "file.newTerminalTab": "ctrl+n",  # Replaced by workspace.newTab
    # "file.newEditorTab": "ctrl+shift+n",  # Replaced by workspace.newTab
    "file.openFile": "ctrl+o",
    "file.save": "ctrl+s",
    "file.saveAs": "ctrl+shift+s",
    "file.saveAll": "ctrl+k s",
    "file.closeFile": "ctrl+w",
    "file.closeAll": "ctrl+shift+w",
    "file.reopenClosedFile": "ctrl+shift+t",

    # View Operations
    "view.toggleSidebar": "ctrl+b",
    "view.toggleActivityBar": "ctrl+shift+a",
    "view.toggleStatusBar": "ctrl+shift+b",
    "view.toggleMenuBar": "ctrl+shift+m",
    "view.zoomIn": "ctrl+=",
    "view.zoomOut": "ctrl+-",
    "view.resetZoom": "ctrl+0",
    "view.toggleFullScreen": "f11",

    # Workspace Operations
    "workspace.splitVertical": "ctrl+\\",
    "workspace.splitHorizontal": "ctrl+shift+\\",
    "workspace.closePane": "ctrl+shift+w",
    "workspace.newTab": "ctrl+t",  # Uses default widget type from settings
    "workspace.newTabWithType": "ctrl+shift+t",  # Choose widget type
    "workspace.closeTab": "ctrl+w",
    "workspace.nextTab": "ctrl+tab",
    "workspace.previousTab": "ctrl+shift+tab",
    "workspace.switchToTab1": "ctrl+1",
    "workspace.switchToTab2": "ctrl+2",
    "workspace.switchToTab3": "ctrl+3",
    "workspace.switchToTab4": "ctrl+4",
    "workspace.switchToTab5": "ctrl+5",
    "workspace.switchToTab6": "ctrl+6",
    "workspace.switchToTab7": "ctrl+7",
    "workspace.switchToTab8": "ctrl+8",
    "workspace.switchToTab9": "ctrl+9",

    # Edit Operations
    "edit.undo": "ctrl+z",
    "edit.redo": "ctrl+y",
    "edit.cut": "ctrl+x",
    "edit.copy": "ctrl+c",
    "edit.paste": "ctrl+v",
    "edit.selectAll": "ctrl+a",
    "edit.find": "ctrl+f",
    "edit.findAndReplace": "ctrl+h",

    # Navigation
    "navigation.goToLine": "ctrl+g",
    "navigation.goToSymbol": "ctrl+shift+o",
    "navigation.goToFile": "ctrl+shift+e",

    # Debug Operations
    "debug.resetAppState": "ctrl+shift+r",
    "debug.reloadWindow": "ctrl+r",
    "debug.testCommand": "",  # No default shortcut
    "debug.toggleDevMode": "",  # No default shortcut
}

# ============= Theme Settings =============
THEME_SETTINGS = {
    "theme": "dark",  # "light", "dark", "auto"
    "accent_color": "#007ACC",
    "font_family": "Consolas, Monaco, monospace",
    "font_size": 12,
    "line_height": 1.5,
    "editor_theme": "vscode_dark",
    "icon_theme": "vscode",
    "auto_detect_theme": False  # Follow OS theme
}

# ============= UI Settings =============
UI_SETTINGS = {
    "show_activity_bar": True,
    "show_sidebar": True,
    "show_status_bar": True,
    "show_menu_bar": True,
    "sidebar_width": 300,
    "activity_bar_width": 48,
    "status_bar_height": 22,
    "tab_size": 4,
    "word_wrap": False,
    "line_numbers": True,
    "minimap_enabled": False,
    "breadcrumbs_enabled": True,
    "frameless_mode": False  # Enable frameless window mode for more screen space
}

# ============= Workspace Settings =============
WORKSPACE_SETTINGS = {
    "auto_save": True,
    "auto_save_delay": 1000,  # ms
    "restore_workspace": True,
    "restore_files": True,
    "max_recent_workspaces": 10,
    "default_workspace_layout": "explorer_editor_terminal",
    "enable_workspace_trust": False,
    "exclude_patterns": [
        "*.pyc",
        "__pycache__/",
        ".git/",
        ".vscode/",
        "node_modules/",
        ".env"
    ]
}

# ============= Editor Settings =============
EDITOR_SETTINGS = {
    "auto_indent": True,
    "smart_indent": True,
    "trim_whitespace": True,
    "insert_final_newline": True,
    "detect_indentation": True,
    "tab_completion": True,
    "bracket_matching": True,
    "code_folding": True,
    "highlight_current_line": True,
    "show_whitespace": False,
    "rulers": [80, 120],
    "selection_highlight": True
}

# ============= Terminal Settings =============
TERMINAL_SETTINGS = {
    "shell": "auto",  # "auto", "bash", "zsh", "fish", "cmd", "powershell"
    "font_family": "Consolas, Monaco, monospace",
    "font_size": 12,
    "cursor_style": "block",  # "block", "line", "underline"
    "cursor_blink": True,
    "scrollback_lines": 10000,
    "bell": False,
    "copy_on_select": False,
    "paste_on_right_click": True,
    "confirm_on_exit": True
}

# ============= Performance Settings =============
PERFORMANCE_SETTINGS = {
    "max_file_size_mb": 50,
    "max_search_results": 1000,
    "indexing_enabled": True,
    "file_watcher_enabled": True,
    "git_integration": True,
    "language_server_timeout": 30000,  # ms
    "ui_animation_duration": 200,  # ms
    "debounce_typing": 300,  # ms
}

# ============= Privacy Settings =============
PRIVACY_SETTINGS = {
    "telemetry_enabled": False,
    "crash_reporting": True,
    "usage_analytics": False,
    "error_reporting": True,
    "improvement_program": False
}

# ============= Complete Default Settings =============
DEFAULT_SETTINGS = {
    "command_palette": COMMAND_PALETTE_SETTINGS,
    "keyboard_shortcuts": DEFAULT_KEYBOARD_SHORTCUTS,
    "theme": THEME_SETTINGS,
    "ui": UI_SETTINGS,
    "workspace": WORKSPACE_SETTINGS,
    "editor": EDITOR_SETTINGS,
    "terminal": TERMINAL_SETTINGS,
    "performance": PERFORMANCE_SETTINGS,
    "privacy": PRIVACY_SETTINGS,

    # Meta settings
    "settings_version": "1.0.0",
    "last_migration": None
}


def get_default_keyboard_shortcuts() -> dict[str, str]:
    """
    Get default keyboard shortcuts.

    Returns:
        Dictionary of command_id -> shortcut mappings
    """
    return DEFAULT_KEYBOARD_SHORTCUTS.copy()


def get_settings_category(category: str) -> dict[str, Any]:
    """
    Get default settings for a specific category.

    Args:
        category: Settings category name

    Returns:
        Default settings for the category
    """
    return DEFAULT_SETTINGS.get(category, {})


def get_all_categories() -> list[str]:
    """
    Get list of all settings categories.

    Returns:
        List of category names
    """
    return [key for key in DEFAULT_SETTINGS.keys() if not key.startswith('settings_')]


def validate_category(category: str) -> bool:
    """
    Check if a settings category is valid.

    Args:
        category: Category name to validate

    Returns:
        True if category exists
    """
    return category in DEFAULT_SETTINGS


def get_setting_description(category: str, key: str) -> str:
    """
    Get description for a specific setting.

    Args:
        category: Settings category
        key: Setting key

    Returns:
        Human-readable description
    """
    descriptions = {
        # Command Palette
        ("command_palette", "max_results"): "Maximum number of search results to show",
        ("command_palette", "show_recent_commands"): "Show recently used commands at top",
        ("command_palette", "recent_commands_count"): "Number of recent commands to remember",
        ("command_palette", "search_debounce_ms"): "Delay before searching while typing (ms)",
        ("command_palette", "auto_select_first"): "Automatically select first search result",
        ("command_palette", "show_shortcuts"): "Display keyboard shortcuts in results",
        ("command_palette", "show_categories"): "Group results by command category",
        ("command_palette", "fuzzy_search_threshold"): "Minimum match score for fuzzy search",

        # Theme
        ("theme", "theme"): "Color theme (light, dark, auto)",
        ("theme", "accent_color"): "Accent color for UI elements",
        ("theme", "font_family"): "Default font family",
        ("theme", "font_size"): "Default font size",
        ("theme", "auto_detect_theme"): "Automatically follow OS theme",

        # UI
        ("ui", "show_activity_bar"): "Show activity bar on left side",
        ("ui", "show_sidebar"): "Show sidebar by default",
        ("ui", "show_status_bar"): "Show status bar at bottom",
        ("ui", "show_menu_bar"): "Show menu bar at top",
        ("ui", "sidebar_width"): "Default sidebar width (pixels)",

        # Workspace
        ("workspace", "auto_save"): "Automatically save files",
        ("workspace", "auto_save_delay"): "Delay before auto-saving (ms)",
        ("workspace", "restore_workspace"): "Restore workspace on startup",
        ("workspace", "restore_files"): "Restore open files on startup",
    }

    return descriptions.get((category, key), f"{category}.{key}")


if __name__ == "__main__":
    # Print summary for debugging
    print("Default settings loaded:")
    for category, settings in DEFAULT_SETTINGS.items():
        if isinstance(settings, dict):
            print(f"  {category}: {len(settings)} settings")
        else:
            print(f"  {category}: {settings}")

    print(f"\nTotal categories: {len(get_all_categories())}")
    print(f"Keyboard shortcuts: {len(DEFAULT_KEYBOARD_SHORTCUTS)}")
