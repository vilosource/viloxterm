#!/usr/bin/env python3
"""
Base keymap definitions shared across all keymap schemes.

This module provides the common shortcuts that are consistent across
all keymap providers, avoiding duplication and ensuring consistency.
"""

from typing import Any

from viloapp.core.commands.constants import CommandID


class BaseKeymapShortcuts:
    """Base shortcuts shared across all keymap schemes."""

    @staticmethod
    def get_common_shortcuts() -> list[dict[str, Any]]:
        """
        Get shortcuts that are common across all keymap schemes.

        These are the core shortcuts that should be consistent
        regardless of which keymap (Default, VSCode, Vim) is active.
        """
        return [
            # ========== File Operations ==========
            # Terminal and Editor shortcuts removed - provided by plugins
            {
                "id": "file.open",
                "sequence": "ctrl+o",
                "command_id": CommandID.File.OPEN,
            },
            {
                "id": "file.save",
                "sequence": "ctrl+s",
                "command_id": CommandID.File.SAVE,
            },
            {
                "id": "file.save_as",
                "sequence": "ctrl+shift+s",
                "command_id": CommandID.File.SAVE_AS,
            },
            {"id": "file.close", "sequence": "ctrl+w", "command_id": "file.closeTab"},
            # ========== Edit Operations ==========
            # Editor-specific shortcuts removed - provided by editor plugins
            # ========== View Operations ==========
            {
                "id": "view.sidebar",
                "sequence": "ctrl+b",
                "command_id": CommandID.View.TOGGLE_SIDEBAR,
            },
            {
                "id": "view.terminal",
                "sequence": "ctrl+`",
                "command_id": CommandID.View.TOGGLE_TERMINAL,
            },
            {
                "id": "view.fullscreen",
                "sequence": "f11",
                "command_id": CommandID.View.TOGGLE_FULLSCREEN,
            },
            {
                "id": "view.theme",
                "sequence": "ctrl+t",
                "command_id": CommandID.View.TOGGLE_THEME,
            },
            {
                "id": "view.command_palette",
                "sequence": "ctrl+shift+p",
                "command_id": CommandID.CommandPalette.SHOW,
            },
            # ========== Workspace Operations ==========
            {
                "id": "workspace.split_horizontal",
                "sequence": "ctrl+\\",
                "command_id": "workbench.action.splitRight",
            },
            {
                "id": "workspace.split_vertical",
                "sequence": "ctrl+shift+\\",
                "command_id": "workbench.action.splitDown",
            },
            # Terminal shortcuts removed - provided by terminal plugins
            # ========== Navigation ==========
            {
                "id": "nav.next_tab",
                "sequence": "ctrl+tab",
                "command_id": "workbench.action.nextTab",
            },
            {
                "id": "nav.prev_tab",
                "sequence": "ctrl+shift+tab",
                "command_id": "workbench.action.previousTab",
            },
            # ========== Focus Navigation ==========
            {
                "id": "focus.next_group",
                "sequence": "f6",
                "command_id": "workbench.action.focusNextGroup",
            },
            {
                "id": "focus.prev_group",
                "sequence": "shift+f6",
                "command_id": "workbench.action.focusPreviousGroup",
            },
            # ========== Help ==========
            {"id": "help.about", "sequence": "f1", "command_id": "help.about"},
            {
                "id": "help.shortcuts",
                "sequence": "ctrl+k ctrl+s",
                "command_id": "help.keyboardShortcuts",
            },
        ]

    @staticmethod
    def get_default_extensions() -> list[dict[str, Any]]:
        """Get default-specific extensions to the base shortcuts."""
        return [
            # Default ViloApp specific shortcuts
            {"id": "edit.redo", "sequence": "ctrl+y", "command_id": "editor.redo"},
            {
                "id": "workspace.next_pane",
                "sequence": "ctrl+k ctrl+right",
                "command_id": "workbench.action.focusNextPane",
            },
            {
                "id": "workspace.prev_pane",
                "sequence": "ctrl+k ctrl+left",
                "command_id": "workbench.action.focusPreviousPane",
            },
        ]

    @staticmethod
    def get_vscode_extensions() -> list[dict[str, Any]]:
        """Get VSCode-specific extensions to the base shortcuts."""
        return [
            # VSCode specific overrides and additions
            {
                "id": "edit.redo",
                "sequence": "ctrl+shift+z",
                "command_id": "editor.redo",
            },
            {
                "id": "file.close_all",
                "sequence": "ctrl+k ctrl+w",
                "command_id": "file.closeAllTabs",
            },
            {
                "id": "file.reopen",
                "sequence": "ctrl+shift+t",
                "command_id": "file.reopenClosedTab",
            },
            {
                "id": "workspace.close_group",
                "sequence": "ctrl+k w",
                "command_id": "workbench.action.closeActivePane",
            },
            {
                "id": "workspace.focus_left",
                "sequence": "ctrl+k ctrl+left",
                "command_id": "workbench.action.focusPreviousPane",
            },
            {
                "id": "workspace.focus_right",
                "sequence": "ctrl+k ctrl+right",
                "command_id": "workbench.action.focusNextPane",
            },
            {
                "id": "nav.quick_open",
                "sequence": "ctrl+p",
                "command_id": "quickOpen.show",
            },
            {
                "id": "nav.go_to_line",
                "sequence": "ctrl+g",
                "command_id": "editor.goToLine",
            },
            {
                "id": "settings.open",
                "sequence": "ctrl+,",
                "command_id": "settings.open",
            },
            # Tab navigation by number
            {
                "id": "nav.tab_1",
                "sequence": "ctrl+1",
                "command_id": "workbench.action.openEditorAtIndex1",
            },
            {
                "id": "nav.tab_2",
                "sequence": "ctrl+2",
                "command_id": "workbench.action.openEditorAtIndex2",
            },
            {
                "id": "nav.tab_3",
                "sequence": "ctrl+3",
                "command_id": "workbench.action.openEditorAtIndex3",
            },
            {
                "id": "nav.tab_4",
                "sequence": "ctrl+4",
                "command_id": "workbench.action.openEditorAtIndex4",
            },
            {
                "id": "nav.tab_5",
                "sequence": "ctrl+5",
                "command_id": "workbench.action.openEditorAtIndex5",
            },
            {
                "id": "nav.tab_6",
                "sequence": "ctrl+6",
                "command_id": "workbench.action.openEditorAtIndex6",
            },
            {
                "id": "nav.tab_7",
                "sequence": "ctrl+7",
                "command_id": "workbench.action.openEditorAtIndex7",
            },
            {
                "id": "nav.tab_8",
                "sequence": "ctrl+8",
                "command_id": "workbench.action.openEditorAtIndex8",
            },
            {
                "id": "nav.tab_9",
                "sequence": "ctrl+9",
                "command_id": "workbench.action.openEditorAtIndex9",
            },
            # Focus navigation
            {
                "id": "focus.next_group",
                "sequence": "f6",
                "command_id": "workbench.action.focusNextGroup",
            },
            {
                "id": "focus.prev_group",
                "sequence": "shift+f6",
                "command_id": "workbench.action.focusPreviousGroup",
            },
        ]

    @staticmethod
    def get_vim_conditional_shortcuts() -> list[dict[str, Any]]:
        """
        Get Vim-specific shortcuts that are conditional on vim mode.

        These shortcuts use 'when' clauses to only activate in vim mode.
        """
        return [
            # Vim mode specific (with when clauses)
            {
                "id": "file.save_vim",
                "sequence": "space w",
                "command_id": "file.save",
                "when": "vimMode",
            },
            {
                "id": "file.quit",
                "sequence": "space q",
                "command_id": "file.closeActiveTab",
                "when": "vimMode",
            },
            {
                "id": "edit.undo_vim",
                "sequence": "u",
                "command_id": "editor.undo",
                "when": "vimMode && vimNormalMode",
            },
            {
                "id": "edit.redo_vim",
                "sequence": "ctrl+r",
                "command_id": "editor.redo",
                "when": "vimMode && vimNormalMode",
            },
            {
                "id": "view.sidebar_vim",
                "sequence": "space e",
                "command_id": "view.toggleSidebar",
                "when": "vimMode",
            },
            {
                "id": "view.terminal_vim",
                "sequence": "space t",
                "command_id": "view.toggleTerminal",
                "when": "vimMode",
            },
            {
                "id": "workspace.split_h_vim",
                "sequence": "space s",
                "command_id": "workbench.action.splitRight",
                "when": "vimMode",
            },
            {
                "id": "workspace.split_v_vim",
                "sequence": "space v",
                "command_id": "workbench.action.splitDown",
                "when": "vimMode",
            },
            {
                "id": "workspace.focus_left_vim",
                "sequence": "space h",
                "command_id": "workbench.action.focusPreviousPane",
                "when": "vimMode",
            },
            {
                "id": "workspace.focus_right_vim",
                "sequence": "space l",
                "command_id": "workbench.action.focusNextPane",
                "when": "vimMode",
            },
            {
                "id": "nav.next_buffer",
                "sequence": "space b n",
                "command_id": "workbench.action.nextTab",
                "when": "vimMode",
            },
            {
                "id": "nav.prev_buffer",
                "sequence": "space b p",
                "command_id": "workbench.action.previousTab",
                "when": "vimMode",
            },
        ]
