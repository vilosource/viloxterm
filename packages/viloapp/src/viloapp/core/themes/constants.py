#!/usr/bin/env python3
"""
Theme color key constants.

This module defines all the color keys that can be used in themes.
Based on VSCode's theme color reference.
"""


class ThemeColors:
    """Constants for theme color keys."""

    # Editor Colors
    EDITOR_BACKGROUND = "editor.background"
    EDITOR_FOREGROUND = "editor.foreground"
    EDITOR_LINE_HIGHLIGHT = "editor.lineHighlightBackground"
    EDITOR_SELECTION = "editor.selectionBackground"
    EDITOR_CURSOR = "editorCursor.foreground"
    EDITOR_WHITESPACE = "editorWhitespace.foreground"
    EDITOR_INDENT_GUIDE = "editorIndentGuide.background"
    EDITOR_INDENT_GUIDE_ACTIVE = "editorIndentGuide.activeBackground"

    # Activity Bar
    ACTIVITY_BAR_BACKGROUND = "activityBar.background"
    ACTIVITY_BAR_FOREGROUND = "activityBar.foreground"
    ACTIVITY_BAR_INACTIVE_FOREGROUND = "activityBar.inactiveForeground"
    ACTIVITY_BAR_BORDER = "activityBar.border"
    ACTIVITY_BAR_ACTIVE_BORDER = "activityBar.activeBorder"
    ACTIVITY_BAR_ACTIVE_BACKGROUND = "activityBar.activeBackground"

    # Side Bar
    SIDEBAR_BACKGROUND = "sideBar.background"
    SIDEBAR_FOREGROUND = "sideBar.foreground"
    SIDEBAR_BORDER = "sideBar.border"
    SIDEBAR_SECTION_HEADER_BACKGROUND = "sideBarSectionHeader.background"
    SIDEBAR_SECTION_HEADER_FOREGROUND = "sideBarSectionHeader.foreground"

    # Status Bar
    STATUS_BAR_BACKGROUND = "statusBar.background"
    STATUS_BAR_FOREGROUND = "statusBar.foreground"
    STATUS_BAR_BORDER = "statusBar.border"
    STATUS_BAR_NO_FOLDER_BACKGROUND = "statusBar.noFolderBackground"
    STATUS_BAR_DEBUG_BACKGROUND = "statusBar.debuggingBackground"
    STATUS_BAR_DEBUG_FOREGROUND = "statusBar.debuggingForeground"

    # Title Bar
    TITLE_BAR_ACTIVE_BACKGROUND = "titleBar.activeBackground"
    TITLE_BAR_ACTIVE_FOREGROUND = "titleBar.activeForeground"
    TITLE_BAR_INACTIVE_BACKGROUND = "titleBar.inactiveBackground"
    TITLE_BAR_INACTIVE_FOREGROUND = "titleBar.inactiveForeground"
    TITLE_BAR_BORDER = "titleBar.border"

    # Tabs
    TAB_ACTIVE_BACKGROUND = "tab.activeBackground"
    TAB_ACTIVE_FOREGROUND = "tab.activeForeground"
    TAB_ACTIVE_BORDER = "tab.activeBorder"
    TAB_ACTIVE_BORDER_TOP = "tab.activeBorderTop"
    TAB_INACTIVE_BACKGROUND = "tab.inactiveBackground"
    TAB_INACTIVE_FOREGROUND = "tab.inactiveForeground"
    TAB_BORDER = "tab.border"

    # Panel (Terminal, Output, etc.)
    PANEL_BACKGROUND = "panel.background"
    PANEL_BORDER = "panel.border"
    PANEL_TITLE_ACTIVE_BORDER = "panelTitle.activeBorder"
    PANEL_TITLE_ACTIVE_FOREGROUND = "panelTitle.activeForeground"
    PANEL_TITLE_INACTIVE_FOREGROUND = "panelTitle.inactiveForeground"

    # Input Controls
    INPUT_BACKGROUND = "input.background"
    INPUT_FOREGROUND = "input.foreground"
    INPUT_BORDER = "input.border"
    INPUT_PLACEHOLDER_FOREGROUND = "input.placeholderForeground"
    FOCUS_BORDER = "focusBorder"

    # Buttons
    BUTTON_BACKGROUND = "button.background"
    BUTTON_FOREGROUND = "button.foreground"
    BUTTON_HOVER_BACKGROUND = "button.hoverBackground"
    BUTTON_SECONDARY_BACKGROUND = "button.secondaryBackground"
    BUTTON_SECONDARY_FOREGROUND = "button.secondaryForeground"
    BUTTON_BORDER = "button.border"

    # Dropdown
    DROPDOWN_BACKGROUND = "dropdown.background"
    DROPDOWN_FOREGROUND = "dropdown.foreground"
    DROPDOWN_BORDER = "dropdown.border"

    # Lists and Trees
    LIST_ACTIVE_SELECTION_BACKGROUND = "list.activeSelectionBackground"
    LIST_ACTIVE_SELECTION_FOREGROUND = "list.activeSelectionForeground"
    LIST_INACTIVE_SELECTION_BACKGROUND = "list.inactiveSelectionBackground"
    LIST_INACTIVE_SELECTION_FOREGROUND = "list.inactiveSelectionForeground"
    LIST_HOVER_BACKGROUND = "list.hoverBackground"
    LIST_HOVER_FOREGROUND = "list.hoverForeground"

    # Scrollbar
    SCROLLBAR_SLIDER_BACKGROUND = "scrollbarSlider.background"
    SCROLLBAR_SLIDER_HOVER_BACKGROUND = "scrollbarSlider.hoverBackground"
    SCROLLBAR_SLIDER_ACTIVE_BACKGROUND = "scrollbarSlider.activeBackground"

    # Menu
    MENU_BACKGROUND = "menu.background"
    MENU_FOREGROUND = "menu.foreground"
    MENU_SELECTION_BACKGROUND = "menu.selectionBackground"
    MENU_SELECTION_FOREGROUND = "menu.selectionForeground"
    MENU_SELECTION_BORDER = "menu.selectionBorder"
    MENU_SEPARATOR_BACKGROUND = "menu.separatorBackground"

    # Terminal Colors
    TERMINAL_BACKGROUND = "terminal.background"
    TERMINAL_FOREGROUND = "terminal.foreground"
    TERMINAL_CURSOR_BACKGROUND = "terminalCursor.background"
    TERMINAL_CURSOR_FOREGROUND = "terminalCursor.foreground"
    TERMINAL_SELECTION_BACKGROUND = "terminal.selectionBackground"

    # Terminal ANSI Colors
    TERMINAL_ANSI_BLACK = "terminal.ansiBlack"
    TERMINAL_ANSI_RED = "terminal.ansiRed"
    TERMINAL_ANSI_GREEN = "terminal.ansiGreen"
    TERMINAL_ANSI_YELLOW = "terminal.ansiYellow"
    TERMINAL_ANSI_BLUE = "terminal.ansiBlue"
    TERMINAL_ANSI_MAGENTA = "terminal.ansiMagenta"
    TERMINAL_ANSI_CYAN = "terminal.ansiCyan"
    TERMINAL_ANSI_WHITE = "terminal.ansiWhite"
    TERMINAL_ANSI_BRIGHT_BLACK = "terminal.ansiBrightBlack"
    TERMINAL_ANSI_BRIGHT_RED = "terminal.ansiBrightRed"
    TERMINAL_ANSI_BRIGHT_GREEN = "terminal.ansiBrightGreen"
    TERMINAL_ANSI_BRIGHT_YELLOW = "terminal.ansiBrightYellow"
    TERMINAL_ANSI_BRIGHT_BLUE = "terminal.ansiBrightBlue"
    TERMINAL_ANSI_BRIGHT_MAGENTA = "terminal.ansiBrightMagenta"
    TERMINAL_ANSI_BRIGHT_CYAN = "terminal.ansiBrightCyan"
    TERMINAL_ANSI_BRIGHT_WHITE = "terminal.ansiBrightWhite"

    # Accent Colors
    ACCENT_COLOR = "accent.color"
    ERROR_FOREGROUND = "errorForeground"
    WARNING_FOREGROUND = "warningForeground"
    INFO_FOREGROUND = "infoForeground"
    SUCCESS_FOREGROUND = "successForeground"

    # Custom Pane Header Colors (ViloxTerm specific)
    PANE_HEADER_BACKGROUND = "paneHeader.background"
    PANE_HEADER_ACTIVE_BACKGROUND = "paneHeader.activeBackground"
    PANE_HEADER_FOREGROUND = "paneHeader.foreground"
    PANE_HEADER_ACTIVE_FOREGROUND = "paneHeader.activeForeground"
    PANE_HEADER_BORDER = "paneHeader.border"
    PANE_HEADER_BUTTON_HOVER = "paneHeader.buttonHoverBackground"
    PANE_HEADER_CLOSE_HOVER = "paneHeader.closeButtonHoverBackground"

    # Splitter
    SPLITTER_BACKGROUND = "splitter.background"
    SPLITTER_HOVER = "splitter.hoverBackground"

    # Icon Colors
    ICON_FOREGROUND = "icon.foreground"
    ICON_ACTIVE_FOREGROUND = "icon.activeForeground"


# Default fallback colors (used when a color is not defined in theme)
DEFAULT_COLORS = {
    ThemeColors.EDITOR_BACKGROUND: "#1e1e1e",
    ThemeColors.EDITOR_FOREGROUND: "#d4d4d4",
    ThemeColors.ACTIVITY_BAR_BACKGROUND: "#333333",
    ThemeColors.ACTIVITY_BAR_FOREGROUND: "#ffffff",
    ThemeColors.SIDEBAR_BACKGROUND: "#252526",
    ThemeColors.SIDEBAR_FOREGROUND: "#cccccc",
    ThemeColors.STATUS_BAR_BACKGROUND: "#007acc",
    ThemeColors.STATUS_BAR_FOREGROUND: "#ffffff",
}
