#!/usr/bin/env python3
"""
VSCode Dark+ Theme Colors
Accurate color values from the official VSCode Dark+ theme.
"""

# =============================================================================
# CORE COLORS
# =============================================================================

# Editor colors
EDITOR_BACKGROUND = "#1e1e1e"  # Main editor background
EDITOR_FOREGROUND = "#d4d4d4"  # Main editor text
EDITOR_LINE_HIGHLIGHT = "#2a2d2e"  # Current line highlight
EDITOR_SELECTION = "#264f78"  # Selection background
EDITOR_CURSOR = "#aeafad"  # Cursor color

# Activity Bar (left icon bar)
ACTIVITY_BAR_BACKGROUND = "#333333"
ACTIVITY_BAR_FOREGROUND = "#ffffff"
ACTIVITY_BAR_INACTIVE = "#ffffff66"  # 40% opacity
ACTIVITY_BAR_BORDER = "#333333"
ACTIVITY_BAR_ACTIVE_BORDER = "#ffffff"
ACTIVITY_BAR_ACTIVE_BACKGROUND = "#1e1e1e"

# Side Bar (file explorer, search, etc.)
SIDEBAR_BACKGROUND = "#252526"
SIDEBAR_FOREGROUND = "#cccccc"
SIDEBAR_BORDER = "#1e1e1e"
SIDEBAR_SECTION_HEADER = "#37373d"

# Tab colors - Fixed for better visibility
TAB_ACTIVE_BACKGROUND = "#1e1e1e"
TAB_ACTIVE_FOREGROUND = "#ffffff"
TAB_ACTIVE_BORDER = "#1e1e1e"
TAB_ACTIVE_BORDER_TOP = "#007acc"  # Blue accent on active tab
TAB_INACTIVE_BACKGROUND = "#2d2d30"
TAB_INACTIVE_FOREGROUND = "#969696"  # Better visibility
TAB_BORDER = "#252526"
TAB_CONTAINER_BACKGROUND = "#252526"  # Container background different from tabs

# Status Bar
STATUS_BAR_BACKGROUND = "#16825d"  # Darker blue-green like VSCode
STATUS_BAR_FOREGROUND = "#ffffff"
STATUS_BAR_NO_FOLDER_BACKGROUND = "#68217a"  # Purple when no folder
STATUS_BAR_DEBUG_BACKGROUND = "#cc6633"  # Orange in debug mode
STATUS_BAR_BORDER = "#007acc"

# Title Bar
TITLE_BAR_ACTIVE_BACKGROUND = "#3c3c3c"
TITLE_BAR_ACTIVE_FOREGROUND = "#cccccc"
TITLE_BAR_INACTIVE_BACKGROUND = "#3c3c3c"
TITLE_BAR_INACTIVE_FOREGROUND = "#cccccc99"  # 60% opacity
TITLE_BAR_BORDER = "#3c3c3c"

# Panel (terminal, output, etc.)
PANEL_BACKGROUND = "#1e1e1e"
PANEL_BORDER = "#3c3c3c"
PANEL_TITLE_ACTIVE_BORDER = "#007acc"
PANEL_TITLE_ACTIVE_FOREGROUND = "#e7e7e7"
PANEL_TITLE_INACTIVE_FOREGROUND = "#e7e7e799"  # 60% opacity
PANEL_FOREGROUND = "#d4d4d4"  # Panel text color

# Input controls
INPUT_BACKGROUND = "#3c3c3c"
INPUT_FOREGROUND = "#cccccc"
INPUT_BORDER = "#3c3c3c"
INPUT_PLACEHOLDER = "#a6a6a6"
FOCUS_BORDER = "#007acc"  # Border color when focused

# Button colors
BUTTON_BACKGROUND = "#0e639c"
BUTTON_FOREGROUND = "#ffffff"
BUTTON_HOVER_BACKGROUND = "#1177bb"
BUTTON_SECONDARY_BACKGROUND = "#3a3d41"
BUTTON_SECONDARY_FOREGROUND = "#cccccc"
BUTTON_BORDER = "#0e639c"  # Button border color

# Dropdown colors
DROPDOWN_BACKGROUND = "#3c3c3c"
DROPDOWN_FOREGROUND = "#f0f0f0"
DROPDOWN_BORDER = "#3c3c3c"

# Lists and trees
LIST_ACTIVE_SELECTION_BACKGROUND = "#094771"
LIST_ACTIVE_SELECTION_FOREGROUND = "#ffffff"
LIST_INACTIVE_SELECTION_BACKGROUND = "#37373d"
LIST_INACTIVE_SELECTION_FOREGROUND = "#cccccc"
LIST_HOVER_BACKGROUND = "#2a2d2e"
LIST_HOVER_FOREGROUND = "#cccccc"

# Scrollbar
SCROLLBAR_SLIDER_BACKGROUND = "#79797966"  # 40% opacity
SCROLLBAR_SLIDER_HOVER_BACKGROUND = "#646464b3"  # 70% opacity
SCROLLBAR_SLIDER_ACTIVE_BACKGROUND = "#bfbfbf66"  # 40% opacity

# Menu colors
MENU_BACKGROUND = "#252526"
MENU_FOREGROUND = "#cccccc"
MENU_SELECTION_BACKGROUND = "#094771"
MENU_SELECTION_FOREGROUND = "#ffffff"
MENU_SELECTION_BORDER = "#007acc"
MENU_SEPARATOR = "#606060"

# Splitter
SPLITTER_BACKGROUND = "#3c3c3c"
SPLITTER_HOVER = "#007acc"

# Terminal colors
TERMINAL_BACKGROUND = "#1e1e1e"
TERMINAL_FOREGROUND = "#d4d4d4"
TERMINAL_ANSI_BLACK = "#000000"
TERMINAL_ANSI_RED = "#cd3131"
TERMINAL_ANSI_GREEN = "#0dbc79"
TERMINAL_ANSI_YELLOW = "#e5e510"
TERMINAL_ANSI_BLUE = "#2472c8"
TERMINAL_ANSI_MAGENTA = "#bc3fbc"
TERMINAL_ANSI_CYAN = "#11a8cd"
TERMINAL_ANSI_WHITE = "#e5e5e5"
TERMINAL_ANSI_BRIGHT_BLACK = "#666666"
TERMINAL_ANSI_BRIGHT_RED = "#f14c4c"
TERMINAL_ANSI_BRIGHT_GREEN = "#23d18b"
TERMINAL_ANSI_BRIGHT_YELLOW = "#f5f543"
TERMINAL_ANSI_BRIGHT_BLUE = "#3b8eea"
TERMINAL_ANSI_BRIGHT_MAGENTA = "#d670d6"
TERMINAL_ANSI_BRIGHT_CYAN = "#29b8db"
TERMINAL_ANSI_BRIGHT_WHITE = "#e5e5e5"

# Accent colors
ACCENT_COLOR = "#007acc"  # Primary blue accent
ACCENT_COLOR_HOVER = "#1ba1e2"  # Lighter blue on hover
ERROR_COLOR = "#f48771"  # Error red
WARNING_COLOR = "#cca700"  # Warning yellow
INFO_COLOR = "#75beff"  # Info blue
SUCCESS_COLOR = "#4ec9b0"  # Success green

# Pane Header Bar (custom for our implementation)
PANE_HEADER_BACKGROUND = "#2d2d30"  # Slightly lighter than editor for contrast
PANE_HEADER_ACTIVE_BACKGROUND = "#2d2d30"  # Consistent header color
PANE_HEADER_FOREGROUND = "#969696"  # Muted text for inactive
PANE_HEADER_ACTIVE_FOREGROUND = "#e7e7e7"  # Brighter text for active
PANE_HEADER_BORDER = "#464647"  # Subtle border
PANE_HEADER_BUTTON_HOVER = "#505050"
PANE_HEADER_CLOSE_HOVER = "#e81123"

# =============================================================================
# STYLESHEET GENERATOR FUNCTIONS
# =============================================================================

def get_editor_stylesheet():
    """Get stylesheet for editor widgets."""
    return f"""
        QPlainTextEdit, QTextEdit {{
            background-color: {EDITOR_BACKGROUND};
            color: {EDITOR_FOREGROUND};
            border: none;
            font-family: 'Consolas', 'Cascadia Code', 'Monaco', monospace;
            font-size: 13px;
            selection-background-color: {EDITOR_SELECTION};
            selection-color: {EDITOR_FOREGROUND};
        }}
    """

def get_terminal_stylesheet():
    """Get stylesheet for terminal widgets."""
    return f"""
        QTextEdit {{
            background-color: {TERMINAL_BACKGROUND};
            color: {TERMINAL_FOREGROUND};
            border: none;
            font-family: 'Consolas', 'Cascadia Code', 'Monaco', monospace;
            font-size: 13px;
            selection-background-color: {EDITOR_SELECTION};
        }}
    """

def get_sidebar_stylesheet():
    """Get stylesheet for sidebar."""
    return f"""
        QWidget#sidebar {{
            background-color: {SIDEBAR_BACKGROUND};
            border-right: 1px solid {SIDEBAR_BORDER};
        }}
        QTreeWidget {{
            background-color: {SIDEBAR_BACKGROUND};
            color: {SIDEBAR_FOREGROUND};
            border: none;
            outline: none;
        }}
        QTreeWidget::item {{
            padding: 4px;
        }}
        QTreeWidget::item:hover {{
            background-color: {LIST_HOVER_BACKGROUND};
        }}
        QTreeWidget::item:selected {{
            background-color: {LIST_ACTIVE_SELECTION_BACKGROUND};
            color: {LIST_ACTIVE_SELECTION_FOREGROUND};
        }}
    """

def get_tab_widget_stylesheet():
    """Get stylesheet for tab widgets."""
    return f"""
        QTabWidget::pane {{
            background-color: {EDITOR_BACKGROUND};
            border: none;
            border-top: 1px solid {TAB_BORDER};
        }}
        QTabWidget::tab-bar {{
            background-color: {TAB_CONTAINER_BACKGROUND};
        }}
        QTabBar {{
            background-color: {TAB_CONTAINER_BACKGROUND};
        }}
        QTabBar::tab {{
            background-color: {TAB_INACTIVE_BACKGROUND};
            color: {TAB_INACTIVE_FOREGROUND};
            padding: 6px 14px;
            border: none;
            border-right: 1px solid {TAB_BORDER};
            min-width: 100px;
            margin-top: 2px;
        }}
        QTabBar::tab:selected {{
            background-color: {TAB_ACTIVE_BACKGROUND};
            color: {TAB_ACTIVE_FOREGROUND};
            border-top: 1px solid {TAB_ACTIVE_BORDER_TOP};
            margin-top: 0;
            padding-top: 7px;
        }}
        QTabBar::tab:hover:!selected {{
            background-color: #2a2a2a;
            color: #cccccc;
        }}
        QTabBar::close-button {{
            width: 16px;
            height: 16px;
            background-color: transparent;
            border: none;
            border-radius: 3px;
            margin: 2px;
        }}
        QTabBar::close-button:hover {{
            background-color: rgba(90, 93, 94, 0.8);
        }}
        QTabBar::close-button:pressed {{
            background-color: rgba(90, 93, 94, 1.0);
        }}
    """

def get_menu_stylesheet():
    """Get stylesheet for menus."""
    return f"""
        QMenu {{
            background-color: {MENU_BACKGROUND};
            color: {MENU_FOREGROUND};
            border: 1px solid {SPLITTER_BACKGROUND};
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 20px;
            border-radius: 3px;
        }}
        QMenu::item:selected {{
            background-color: {MENU_SELECTION_BACKGROUND};
            color: {MENU_SELECTION_FOREGROUND};
        }}
        QMenu::separator {{
            height: 1px;
            background-color: {MENU_SEPARATOR};
            margin: 4px 0;
        }}
    """

def get_splitter_stylesheet():
    """Get stylesheet for splitters."""
    return f"""
        QSplitter {{
            background-color: {EDITOR_BACKGROUND};
        }}
        QSplitter::handle {{
            background-color: {SPLITTER_BACKGROUND};
        }}
        QSplitter::handle:horizontal {{
            width: 1px;
        }}
        QSplitter::handle:vertical {{
            height: 1px;
        }}
        QSplitter::handle:hover {{
            background-color: {SPLITTER_HOVER};
        }}
    """

def get_status_bar_stylesheet():
    """Get stylesheet for status bar."""
    return f"""
        QStatusBar {{
            background-color: {STATUS_BAR_BACKGROUND};
            color: {STATUS_BAR_FOREGROUND};
            border: none;
            padding: 2px 10px;
            font-size: 12px;
        }}
        QStatusBar::item {{
            border: none;
        }}
    """

def get_main_window_stylesheet():
    """Get complete stylesheet for main window."""
    return f"""
        QMainWindow {{
            background-color: {EDITOR_BACKGROUND};
        }}
        QToolBar {{
            background-color: {TITLE_BAR_ACTIVE_BACKGROUND};
            border: none;
            spacing: 5px;
            padding: 5px;
        }}
        QToolBar QToolButton {{
            background-color: transparent;
            color: {TITLE_BAR_ACTIVE_FOREGROUND};
            border: none;
            padding: 5px;
            margin: 2px;
        }}
        QToolBar QToolButton:hover {{
            background-color: {BUTTON_SECONDARY_BACKGROUND};
        }}
        QToolBar QToolButton:pressed {{
            background-color: {BUTTON_BACKGROUND};
        }}
        QMenuBar {{
            background-color: {TITLE_BAR_ACTIVE_BACKGROUND};
            color: {TITLE_BAR_ACTIVE_FOREGROUND};
            border: none;
        }}
        QMenuBar::item {{
            padding: 5px 10px;
            background-color: transparent;
        }}
        QMenuBar::item:selected {{
            background-color: {BUTTON_SECONDARY_BACKGROUND};
        }}
        QMenuBar::item:pressed {{
            background-color: {MENU_BACKGROUND};
        }}
    """

def get_settings_widget_stylesheet():
    """Get stylesheet for settings/configuration widgets."""
    return f"""
        /* Main container */
        QWidget {{
            background-color: {EDITOR_BACKGROUND};
            color: {EDITOR_FOREGROUND};
        }}

        /* Tree/Table widgets for displaying settings */
        QTreeWidget, QTableWidget {{
            background-color: {EDITOR_BACKGROUND};
            color: {EDITOR_FOREGROUND};
            border: 1px solid {PANEL_BORDER};
            outline: none;
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
            font-size: 13px;
            alternate-background-color: {EDITOR_BACKGROUND};  /* Disable alternating colors */
        }}

        QTreeWidget::item, QTableWidget::item {{
            padding: 6px;
            border: none;
            background-color: transparent;
        }}

        QTreeWidget::item:alternate {{
            background-color: {EDITOR_BACKGROUND};  /* Ensure no alternating colors */
        }}

        QTreeWidget::item:hover, QTableWidget::item:hover {{
            background-color: {LIST_HOVER_BACKGROUND};
        }}

        QTreeWidget::item:selected, QTableWidget::item:selected {{
            background-color: {LIST_ACTIVE_SELECTION_BACKGROUND};
            color: {LIST_ACTIVE_SELECTION_FOREGROUND};
        }}

        /* Headers */
        QHeaderView::section {{
            background-color: {PANEL_BACKGROUND};
            color: {PANEL_FOREGROUND};
            border: none;
            border-bottom: 1px solid {PANEL_BORDER};
            padding: 8px;
            font-weight: 600;
        }}

        /* Line edits for input */
        QLineEdit {{
            background-color: {INPUT_BACKGROUND};
            color: {INPUT_FOREGROUND};
            border: 1px solid {INPUT_BORDER};
            border-radius: 2px;
            padding: 4px 8px;
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
            font-size: 13px;
        }}

        QLineEdit:focus {{
            border-color: {FOCUS_BORDER};
            outline: none;
        }}

        QLineEdit:disabled {{
            background-color: {SIDEBAR_BACKGROUND};
            color: {TAB_INACTIVE_FOREGROUND};
        }}

        /* Buttons */
        QPushButton {{
            background-color: {BUTTON_BACKGROUND};
            color: {BUTTON_FOREGROUND};
            border: 1px solid {BUTTON_BORDER};
            border-radius: 2px;
            padding: 6px 14px;
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
            font-size: 13px;
            font-weight: 600;
        }}

        QPushButton:hover {{
            background-color: {BUTTON_HOVER_BACKGROUND};
        }}

        QPushButton:pressed {{
            background-color: {BUTTON_SECONDARY_BACKGROUND};
        }}

        QPushButton:disabled {{
            background-color: {SIDEBAR_BACKGROUND};
            color: {TAB_INACTIVE_FOREGROUND};
            border-color: {PANEL_BORDER};
        }}

        /* Labels */
        QLabel {{
            color: {EDITOR_FOREGROUND};
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
            font-size: 13px;
        }}

        /* ComboBox */
        QComboBox {{
            background-color: {INPUT_BACKGROUND};
            color: {INPUT_FOREGROUND};
            border: 1px solid {INPUT_BORDER};
            border-radius: 2px;
            padding: 4px 8px;
            font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
            font-size: 13px;
        }}

        QComboBox:focus {{
            border-color: {FOCUS_BORDER};
        }}

        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}

        QComboBox::down-arrow {{
            image: none;
            border-style: solid;
            border-width: 4px;
            border-color: transparent;
            border-top-color: {INPUT_FOREGROUND};
            margin-top: 4px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {DROPDOWN_BACKGROUND};
            color: {DROPDOWN_FOREGROUND};
            border: 1px solid {INPUT_BORDER};
            selection-background-color: {LIST_ACTIVE_SELECTION_BACKGROUND};
            selection-color: {LIST_ACTIVE_SELECTION_FOREGROUND};
        }}

        /* Scroll bars */
        QScrollBar:vertical {{
            background-color: {EDITOR_BACKGROUND};
            width: 14px;
            border: none;
        }}

        QScrollBar::handle:vertical {{
            background-color: {SCROLLBAR_SLIDER_BACKGROUND};
            border-radius: 7px;
            min-height: 20px;
        }}

        QScrollBar::handle:vertical:hover {{
            background-color: {SCROLLBAR_SLIDER_HOVER_BACKGROUND};
        }}

        QScrollBar::handle:vertical:pressed {{
            background-color: {SCROLLBAR_SLIDER_ACTIVE_BACKGROUND};
        }}

        QScrollBar:horizontal {{
            background-color: {EDITOR_BACKGROUND};
            height: 14px;
            border: none;
        }}

        QScrollBar::handle:horizontal {{
            background-color: {SCROLLBAR_SLIDER_BACKGROUND};
            border-radius: 7px;
            min-width: 20px;
        }}

        QScrollBar::handle:horizontal:hover {{
            background-color: {SCROLLBAR_SLIDER_HOVER_BACKGROUND};
        }}

        QScrollBar::handle:horizontal:pressed {{
            background-color: {SCROLLBAR_SLIDER_ACTIVE_BACKGROUND};
        }}

        QScrollBar::add-line, QScrollBar::sub-line {{
            border: none;
            background: none;
        }}
    """

def get_pane_header_stylesheet():
    """Get stylesheet for pane header bars."""
    return f"""
        PaneHeaderBar {{
            background-color: {PANE_HEADER_BACKGROUND};
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }}
        PaneHeaderBar[active="true"] {{
            background-color: {PANE_HEADER_ACTIVE_BACKGROUND};
            border-bottom: 2px solid rgba(255, 255, 255, 0.15);
        }}
        PaneHeaderBar QLabel {{
            color: {PANE_HEADER_FOREGROUND};
            font-size: 12px;
            padding: 0 4px;
        }}
        PaneHeaderBar[active="true"] QLabel {{
            color: {PANE_HEADER_ACTIVE_FOREGROUND};
            font-weight: bold;
        }}
        PaneHeaderBar QToolButton {{
            background-color: transparent;
            color: {PANE_HEADER_FOREGROUND};
            border: none;
            padding: 2px;
            font-size: 14px;
        }}
        PaneHeaderBar QToolButton:hover {{
            background-color: {PANE_HEADER_BUTTON_HOVER};
            border-radius: 2px;
        }}
        PaneHeaderBar QToolButton#closeButton:hover {{
            background-color: {PANE_HEADER_CLOSE_HOVER};
            color: white;
        }}
    """