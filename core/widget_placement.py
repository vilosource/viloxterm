#!/usr/bin/env python3
"""
Widget placement intent system.

This module defines how widgets should be placed (new tab vs replace pane)
based on context and user intent.
"""

from enum import Enum
from typing import Optional


class WidgetPlacement(Enum):
    """
    Defines where a widget should be placed when opened.
    """

    NEW_TAB = "new_tab"  # Always create new tab
    REPLACE_CURRENT = "replace"  # Always replace current pane
    SMART = "smart"  # Context-aware decision


class CommandSource(Enum):
    """
    Identifies where a command was invoked from.

    This helps determine the appropriate widget placement behavior.
    """

    MENU_BAR = "menu_bar"  # Main application menu
    PANE_HEADER = "pane_header"  # Pane header menu
    COMMAND_PALETTE = "command_palette"  # Command palette
    KEYBOARD_SHORTCUT = "keyboard"  # Direct keyboard shortcut
    CONTEXT_MENU = "context_menu"  # Right-click context menu
    API = "api"  # Programmatic API call
    UNKNOWN = "unknown"  # Unknown source


def determine_placement(
    metadata: "AppWidgetMetadata",
    source: CommandSource = CommandSource.UNKNOWN,
    preferred: Optional[WidgetPlacement] = None,
) -> WidgetPlacement:
    """
    Determine where to place a widget based on context and metadata.

    Args:
        metadata: Widget metadata containing placement preferences
        source: Where the command was invoked from
        preferred: Optional override for placement

    Returns:
        The determined widget placement strategy
    """
    # If explicit preference provided, use it
    if preferred is not None:
        return preferred

    # Context-specific rules
    if source == CommandSource.PANE_HEADER:
        # Pane header actions should affect the current pane
        if metadata.supports_replacement:
            return WidgetPlacement.REPLACE_CURRENT
        else:
            # Some widgets may not support replacement
            return WidgetPlacement.NEW_TAB

    elif source == CommandSource.MENU_BAR:
        # Menu bar typically creates new tabs
        if metadata.supports_new_tab:
            return WidgetPlacement.NEW_TAB
        else:
            return WidgetPlacement.REPLACE_CURRENT

    elif source == CommandSource.COMMAND_PALETTE:
        # Command palette uses smart defaults
        return metadata.default_placement

    elif source == CommandSource.KEYBOARD_SHORTCUT:
        # Keyboard shortcuts use smart defaults
        return metadata.default_placement

    else:
        # Unknown context - use widget's default
        return metadata.default_placement


def should_ask_user(metadata: "AppWidgetMetadata", source: CommandSource) -> bool:
    """
    Determine if we should ask the user for placement preference.

    Args:
        metadata: Widget metadata
        source: Command source

    Returns:
        True if user should be prompted for placement preference
    """
    # In the future, this could check user preferences
    # For now, we use automatic determination
    return False
