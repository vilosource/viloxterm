#!/usr/bin/env python3
"""
Command ID constants to prevent typos and enable refactoring.

This module provides centralized constants for all command IDs used
throughout the application, ensuring consistency and type safety.
"""


class CommandID:
    """Command ID constants organized by category."""

    # ========== File Commands ==========
    class File:
        NEW_FILE = "file.new"
        # Editor and Terminal commands removed - provided by plugins
        OPEN = "file.open"
        SAVE = "file.save"
        SAVE_AS = "file.saveAs"
        SAVE_ALL = "file.saveAll"
        CLOSE_ACTIVE_TAB = "file.closeActiveTab"
        CLOSE_ALL_TABS = "file.closeAllTabs"
        REOPEN_CLOSED_TAB = "file.reopenClosedTab"
        EXIT = "file.exit"

    # ========== Edit Commands ==========
    class Edit:
        # Editor-specific commands removed - provided by editor plugins
        # Generic edit commands can be added here if needed
        pass

    # ========== View Commands ==========
    class View:
        TOGGLE_SIDEBAR = "view.toggleSidebar"
        TOGGLE_TERMINAL = "view.toggleTerminal"
        TOGGLE_FULLSCREEN = "view.toggleFullscreen"
        TOGGLE_THEME = "view.toggleTheme"
        TOGGLE_MENU_BAR = "view.toggleMenuBar"
        ZOOM_IN = "view.zoomIn"
        ZOOM_OUT = "view.zoomOut"
        ZOOM_RESET = "view.zoomReset"
        SHOW_EXPLORER = "view.showExplorer"
        SHOW_SEARCH = "view.showSearch"
        SHOW_GIT = "view.showGit"
        SHOW_EXTENSIONS = "view.showExtensions"

    # ========== Workspace Commands ==========
    class Workspace:
        SPLIT_RIGHT = "workbench.action.splitRight"
        SPLIT_DOWN = "workbench.action.splitDown"
        CLOSE_ACTIVE_PANE = "workbench.action.closeActivePane"
        FOCUS_NEXT_PANE = "workbench.action.focusNextPane"
        FOCUS_PREVIOUS_PANE = "workbench.action.focusPreviousPane"
        FOCUS_LEFT_PANE = "workbench.action.focusLeftPane"
        FOCUS_RIGHT_PANE = "workbench.action.focusRightPane"
        FOCUS_ABOVE_PANE = "workbench.action.focusAbovePane"
        FOCUS_BELOW_PANE = "workbench.action.focusBelowPane"
        MAXIMIZE_PANE = "workbench.action.maximizePane"
        RESTORE_PANE = "workbench.action.restorePane"

    # ========== Navigation Commands ==========
    class Navigation:
        NEXT_TAB = "workbench.action.nextTab"
        PREVIOUS_TAB = "workbench.action.previousTab"
        OPEN_EDITOR_AT_INDEX_1 = "workbench.action.openEditorAtIndex1"
        OPEN_EDITOR_AT_INDEX_2 = "workbench.action.openEditorAtIndex2"
        OPEN_EDITOR_AT_INDEX_3 = "workbench.action.openEditorAtIndex3"
        OPEN_EDITOR_AT_INDEX_4 = "workbench.action.openEditorAtIndex4"
        OPEN_EDITOR_AT_INDEX_5 = "workbench.action.openEditorAtIndex5"
        OPEN_EDITOR_AT_INDEX_6 = "workbench.action.openEditorAtIndex6"
        OPEN_EDITOR_AT_INDEX_7 = "workbench.action.openEditorAtIndex7"
        OPEN_EDITOR_AT_INDEX_8 = "workbench.action.openEditorAtIndex8"
        OPEN_EDITOR_AT_INDEX_9 = "workbench.action.openEditorAtIndex9"
        FOCUS_NEXT_GROUP = "workbench.action.focusNextGroup"
        FOCUS_PREVIOUS_GROUP = "workbench.action.focusPreviousGroup"

    # Terminal commands removed - provided by terminal plugins

    # ========== Command Palette ==========
    class CommandPalette:
        SHOW = "commandPalette.show"
        SHOW_RECENT = "commandPalette.showRecent"
        CLEAR_RECENT = "commandPalette.clearRecent"

    # ========== Quick Open ==========
    class QuickOpen:
        SHOW = "quickOpen.show"
        SHOW_FILES = "quickOpen.showFiles"
        SHOW_SYMBOLS = "quickOpen.showSymbols"

    # ========== Settings ==========
    class Settings:
        OPEN = "settings.open"
        OPEN_JSON = "settings.openJson"
        OPEN_KEYBOARD_SHORTCUTS = "settings.openKeyboardShortcuts"
        RESET_TO_DEFAULT = "settings.resetToDefault"
        TOGGLE_AUTO_SAVE = "settings.toggleAutoSave"
        SET_THEME = "settings.setTheme"
        SET_KEYMAP = "settings.setKeymap"

    # ========== Debug Commands ==========
    class Debug:
        SHOW_CONTEXT = "debug.showContext"
        SHOW_SHORTCUTS = "debug.showShortcuts"
        SHOW_COMMANDS = "debug.showCommands"
        TEST_COMMAND = "debug.testCommand"
        RELOAD_WINDOW = "debug.reloadWindow"
        TOGGLE_DEV_TOOLS = "debug.toggleDevTools"
        SHOW_LOGS = "debug.showLogs"

    # ========== Help Commands ==========
    class Help:
        ABOUT = "help.about"
        DOCUMENTATION = "help.documentation"
        KEYBOARD_SHORTCUTS = "help.keyboardShortcuts"
        RELEASE_NOTES = "help.releaseNotes"
        REPORT_ISSUE = "help.reportIssue"
        TOGGLE_DEV_TOOLS = "help.toggleDevTools"


# Convenience mappings for backward compatibility
FILE_NEW = CommandID.File.NEW_FILE
FILE_OPEN = CommandID.File.OPEN
FILE_SAVE = CommandID.File.SAVE
FILE_SAVE_AS = CommandID.File.SAVE_AS
FILE_CLOSE = CommandID.File.CLOSE_ACTIVE_TAB

# Editor commands removed - provided by editor plugins

VIEW_TOGGLE_SIDEBAR = CommandID.View.TOGGLE_SIDEBAR
VIEW_TOGGLE_TERMINAL = CommandID.View.TOGGLE_TERMINAL
VIEW_TOGGLE_THEME = CommandID.View.TOGGLE_THEME

COMMAND_PALETTE_SHOW = CommandID.CommandPalette.SHOW


def validate_command_id(command_id: str) -> bool:
    """
    Validate that a command ID follows the naming convention.

    Args:
        command_id: Command ID to validate

    Returns:
        True if valid, False otherwise
    """
    if not command_id:
        return False

    # Command IDs should be in format: category.action or category.subcategory.action
    parts = command_id.split(".")
    if len(parts) < 2 or len(parts) > 4:
        return False

    # Each part should be non-empty and contain only alphanumeric characters
    for part in parts:
        if not part or not part.replace("_", "").replace("-", "").isalnum():
            return False

    return True


def get_command_category(command_id: str) -> str:
    """
    Extract the category from a command ID.

    Args:
        command_id: Command ID

    Returns:
        Category name or empty string if invalid
    """
    if not validate_command_id(command_id):
        return ""

    return command_id.split(".")[0]
