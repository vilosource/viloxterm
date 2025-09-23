#!/usr/bin/env python3
"""
Context key definitions for the application.

Context keys represent the current state of the application and are used
to evaluate when clauses for commands and keyboard shortcuts.
"""


class ContextKey:
    """
    Standard context keys for the application.

    These keys represent various states and focus areas in the application
    and are used to determine when commands and shortcuts are available.
    """

    # Focus contexts - which part of the UI has focus
    # Editor and Terminal focus removed - provided by plugins
    SIDEBAR_FOCUS = "sidebarFocus"
    ACTIVITY_BAR_FOCUS = "activityBarFocus"
    COMMAND_PALETTE_FOCUS = "commandPaletteFocus"
    MENU_FOCUS = "menuFocus"
    DIALOG_FOCUS = "dialogFocus"

    # Visibility contexts - what is visible
    SIDEBAR_VISIBLE = "sidebarVisible"
    TERMINAL_VISIBLE = "terminalVisible"
    MENU_BAR_VISIBLE = "menuBarVisible"
    STATUS_BAR_VISIBLE = "statusBarVisible"
    COMMAND_PALETTE_VISIBLE = "commandPaletteVisible"

    # Editor state contexts - removed, provided by editor plugins
    # Plugins can register their own context keys
    HAS_SELECTION = "hasSelection"  # Generic, can be used by any widget
    HAS_MULTIPLE_SELECTIONS = "hasMultipleSelections"
    IS_READ_ONLY = "isReadOnly"
    IS_DIRTY = "isDirty"

    # Tab and pane contexts
    HAS_MULTIPLE_TABS = "hasMultipleTabs"
    CAN_SPLIT = "canSplit"
    HAS_MULTIPLE_PANES = "hasMultiplePanes"
    PANE_COUNT = "paneCount"
    TAB_COUNT = "tabCount"

    # Content type contexts
    ACTIVE_TAB_TYPE = "activeTabType"  # Values determined by registered widgets
    ACTIVE_PANE_TYPE = "activePaneType"  # Values: "editor", "terminal", "output"
    RESOURCE_EXTENSION = "resourceExtension"  # File extension
    RESOURCE_SCHEME = "resourceScheme"  # "file", "untitled", etc.
    IS_UNTITLED = "isUntitled"

    # Application state contexts
    IS_FULL_SCREEN = "isFullScreen"
    IS_DEVELOPMENT = "isDevelopment"
    IS_DEBUG_MODE = "isDebugMode"
    PLATFORM = "platform"  # "windows", "linux", "darwin"

    # Mode contexts (future features)
    VIM_MODE = "vimMode"
    VIM_INSERT_MODE = "vimInsertMode"
    VIM_NORMAL_MODE = "vimNormalMode"
    VIM_VISUAL_MODE = "vimVisualMode"
    SEARCH_MODE = "searchMode"
    REPLACE_MODE = "replaceMode"

    # Input contexts
    INPUT_FOCUS = "inputFocus"  # Any input field has focus
    SEARCH_INPUT_FOCUS = "searchInputFocus"
    QUICK_OPEN_FOCUS = "quickOpenFocus"

    # Terminal specific contexts
    TERMINAL_PROCESS_RUNNING = "terminalProcessRunning"
    TERMINAL_SELECTION = "terminalSelection"
    TERMINAL_COUNT = "terminalCount"

    # Navigation contexts
    CAN_GO_BACK = "canGoBack"
    CAN_GO_FORWARD = "canGoForward"
    CAN_NAVIGATE = "canNavigate"

    # Feature flags
    FEATURE_COMMAND_PALETTE = "feature.commandPalette"
    FEATURE_VIM_MODE = "feature.vimMode"
    FEATURE_MULTI_CURSOR = "feature.multiCursor"

    @classmethod
    def get_all_keys(cls) -> set[str]:
        """
        Get all defined context keys.

        Returns:
            Set of all context key names
        """
        keys = set()
        for name, value in cls.__dict__.items():
            if not name.startswith("_") and isinstance(value, str):
                keys.add(value)
        return keys

    @classmethod
    def is_valid_key(cls, key: str) -> bool:
        """
        Check if a key is a valid context key.

        Args:
            key: Key to check

        Returns:
            True if the key is defined
        """
        return key in cls.get_all_keys()


class ContextValue:
    """Common context values."""

    # Tab types
    TAB_TYPE_EDITOR = "editor"
    TAB_TYPE_TERMINAL = "terminal"
    TAB_TYPE_OUTPUT = "output"
    TAB_TYPE_WELCOME = "welcome"

    # Pane types
    PANE_TYPE_EDITOR = "editor"
    PANE_TYPE_TERMINAL = "terminal"
    PANE_TYPE_OUTPUT = "output"
    PANE_TYPE_PLACEHOLDER = "placeholder"

    # Platforms
    PLATFORM_WINDOWS = "windows"
    PLATFORM_LINUX = "linux"
    PLATFORM_MACOS = "darwin"

    # File schemes
    SCHEME_FILE = "file"
    SCHEME_UNTITLED = "untitled"
    SCHEME_TERMINAL = "terminal"

    # Common extensions
    EXT_PYTHON = ".py"
    EXT_JAVASCRIPT = ".js"
    EXT_TYPESCRIPT = ".ts"
    EXT_MARKDOWN = ".md"
    EXT_JSON = ".json"
    EXT_YAML = ".yaml"
    EXT_HTML = ".html"
    EXT_CSS = ".css"
