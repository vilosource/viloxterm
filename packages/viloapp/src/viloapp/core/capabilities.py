#!/usr/bin/env python3
"""
Widget capability definitions for ViloxTerm.

This module defines the capabilities that widgets can declare and implement.
The platform uses these capabilities to interact with widgets without knowing
their specific types or implementations.

ARCHITECTURE COMPLIANCE:
- Capabilities are abstract concepts, not tied to specific widgets
- Platform discovers capabilities at runtime
- No hardcoded widget knowledge
"""

from enum import Enum


class WidgetCapability(Enum):
    """
    Core widget capabilities that the platform can interact with.

    These capabilities define WHAT widgets can do, not HOW they do it.
    Widgets declare which capabilities they support and implement the
    corresponding actions.
    """

    # === Text Operations ===
    TEXT_EDITING = "text_editing"  # Can modify text content
    TEXT_VIEWING = "text_viewing"  # Can display text (read-only)
    TEXT_INPUT = "text_input"  # Can accept text input
    TEXT_SELECTION = "text_selection"  # Can select text ranges
    TEXT_SEARCH = "text_search"  # Can search within text

    # === Display Operations ===
    CLEAR_DISPLAY = "clear_display"  # Can clear its display/content
    SCROLL_CONTENT = "scroll_content"  # Can scroll its content
    ZOOM_CONTENT = "zoom_content"  # Can zoom in/out
    SYNTAX_HIGHLIGHTING = "syntax_highlighting"  # Can highlight syntax

    # === File Operations ===
    FILE_VIEWING = "file_viewing"  # Can display file contents
    FILE_EDITING = "file_editing"  # Can modify file contents
    FILE_SAVING = "file_saving"  # Can save to files
    FILE_OPENING = "file_opening"  # Can open files

    # === Clipboard Operations ===
    CLIPBOARD_COPY = "clipboard_copy"  # Can copy to clipboard
    CLIPBOARD_PASTE = "clipboard_paste"  # Can paste from clipboard
    CLIPBOARD_CUT = "clipboard_cut"  # Can cut to clipboard

    # === Shell Operations ===
    SHELL_EXECUTION = "shell_execution"  # Can execute shell commands
    COMMAND_RUNNING = "command_running"  # Can run commands
    PROCESS_MANAGEMENT = "process_management"  # Can manage processes

    # === Navigation Operations ===
    FIND_AND_REPLACE = "find_and_replace"  # Can find and replace text
    GOTO_LINE = "goto_line"  # Can navigate to specific lines
    NAVIGATE_HISTORY = "navigate_history"  # Can navigate through history

    # === UI Operations ===
    SPLIT_VIEW = "split_view"  # Can be split into multiple views
    FOCUS_MANAGEMENT = "focus_management"  # Can manage focus states
    CONTEXT_MENU = "context_menu"  # Can show context menus

    # === Development Operations ===
    CODE_COMPLETION = "code_completion"  # Can provide code completions
    DEBUGGING = "debugging"  # Can debug code
    VERSION_CONTROL = "version_control"  # Can interact with VCS

    # === Configuration Operations ===
    SETTINGS_MANAGEMENT = "settings_management"  # Can manage settings
    CONFIGURATION_EDITING = "configuration_editing"  # Can edit configurations
    PREFERENCES_HANDLING = "preferences_handling"  # Can handle preferences

    # === Widget-Specific Operations ===
    CUSTOM_RENDERING = "custom_rendering"  # Has custom rendering logic
    STATE_PERSISTENCE = "state_persistence"  # Can persist/restore state
    PLUGIN_HOSTING = "plugin_hosting"  # Can host other plugins

    def __str__(self) -> str:
        """String representation of the capability."""
        return self.value


class CapabilityCategory(Enum):
    """
    Categories for grouping related capabilities.

    Used for organizing capabilities in UI and documentation.
    """

    TEXT = "text"  # Text-related capabilities
    DISPLAY = "display"  # Display and rendering capabilities
    FILE = "file"  # File operation capabilities
    CLIPBOARD = "clipboard"  # Clipboard operation capabilities
    SHELL = "shell"  # Shell and command capabilities
    NAVIGATION = "navigation"  # Navigation capabilities
    UI = "ui"  # UI-related capabilities
    DEVELOPMENT = "development"  # Development tool capabilities
    CONFIGURATION = "configuration"  # Configuration capabilities
    SPECIAL = "special"  # Special/unique capabilities


def get_capability_category(capability: WidgetCapability) -> CapabilityCategory:
    """
    Get the category for a given capability.

    Args:
        capability: The widget capability

    Returns:
        The category this capability belongs to
    """
    # Map capabilities to categories based on their prefix
    capability_name = capability.name

    if capability_name.startswith("TEXT_"):
        return CapabilityCategory.TEXT
    elif capability_name.startswith("FILE_"):
        return CapabilityCategory.FILE
    elif capability_name.startswith("CLIPBOARD_"):
        return CapabilityCategory.CLIPBOARD
    elif (
        capability_name.startswith("SHELL_")
        or capability_name.startswith("COMMAND_")
        or capability_name.startswith("PROCESS_")
    ):
        return CapabilityCategory.SHELL
    elif capability_name in [
        "CLEAR_DISPLAY",
        "SCROLL_CONTENT",
        "ZOOM_CONTENT",
        "SYNTAX_HIGHLIGHTING",
    ]:
        return CapabilityCategory.DISPLAY
    elif capability_name in ["FIND_AND_REPLACE", "GOTO_LINE", "NAVIGATE_HISTORY"]:
        return CapabilityCategory.NAVIGATION
    elif capability_name in ["SPLIT_VIEW", "FOCUS_MANAGEMENT", "CONTEXT_MENU"]:
        return CapabilityCategory.UI
    elif capability_name in ["CODE_COMPLETION", "DEBUGGING", "VERSION_CONTROL"]:
        return CapabilityCategory.DEVELOPMENT
    elif capability_name in [
        "SETTINGS_MANAGEMENT",
        "CONFIGURATION_EDITING",
        "PREFERENCES_HANDLING",
    ]:
        return CapabilityCategory.CONFIGURATION
    else:
        return CapabilityCategory.SPECIAL


def is_compatible_capability(required: WidgetCapability, provided: WidgetCapability) -> bool:
    """
    Check if a provided capability satisfies a required capability.

    Some capabilities may be compatible even if not exactly the same.
    For example, TEXT_EDITING implies TEXT_VIEWING.

    Args:
        required: The required capability
        provided: The provided capability

    Returns:
        True if the provided capability satisfies the requirement
    """
    # Exact match
    if required == provided:
        return True

    # TEXT_EDITING implies TEXT_VIEWING and TEXT_INPUT
    if required in [WidgetCapability.TEXT_VIEWING, WidgetCapability.TEXT_INPUT]:
        if provided == WidgetCapability.TEXT_EDITING:
            return True

    # FILE_EDITING implies FILE_VIEWING
    if required == WidgetCapability.FILE_VIEWING:
        if provided == WidgetCapability.FILE_EDITING:
            return True

    # CLIPBOARD_CUT implies CLIPBOARD_COPY
    if required == WidgetCapability.CLIPBOARD_COPY:
        if provided == WidgetCapability.CLIPBOARD_CUT:
            return True

    return False
