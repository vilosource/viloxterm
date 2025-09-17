#!/usr/bin/env python3
"""
Centralized list of shortcuts that should be reserved for application handling
in QtWebEngine widgets (terminals, browsers, etc.).

These shortcuts will be intercepted before web content can consume them,
ensuring they trigger the appropriate commands in our application.
"""

# List of shortcuts that should always be handled by the application,
# not by web content (xterm.js, web pages, etc.)
WEBENGINE_RESERVED_SHORTCUTS = [
    # View commands
    "Alt+P",  # Toggle pane numbers
    "Ctrl+B",  # Toggle sidebar
    "Ctrl+T",  # Toggle theme
    "Ctrl+Shift+M",  # Toggle menu bar
    "F11",  # Toggle fullscreen
    # Directional pane navigation
    "Alt+Left",  # Navigate to pane on the left
    "Alt+Right",  # Navigate to pane on the right
    "Alt+Up",  # Navigate to pane above
    "Alt+Down",  # Navigate to pane below
    # Workspace/pane commands
    "Ctrl+\\",  # Split horizontal
    "Ctrl+Shift+\\",  # Split vertical
    "Ctrl+W",  # Close tab/pane
    "Ctrl+K",  # Chord sequence starter
    "F2",  # Rename pane
    # Command palette
    "Ctrl+Shift+P",  # Show command palette
    # File operations
    "Ctrl+N",  # New terminal tab (default)
    "Ctrl+Shift+N",  # New editor tab
    "Ctrl+`",  # New terminal tab (alternative)
    "Ctrl+S",  # Save
    # Navigation
    "Ctrl+Tab",  # Next tab
    "Ctrl+Shift+Tab",  # Previous tab
    "Ctrl+PageDown",  # Next tab (alternative)
    "Ctrl+PageUp",  # Previous tab (alternative)
    "Ctrl+1",  # Go to tab 1 (future: go to pane 1)
    "Ctrl+2",  # Go to tab 2 (future: go to pane 2)
    "Ctrl+3",  # Go to tab 3 (future: go to pane 3)
    "Ctrl+4",  # Go to tab 4 (future: go to pane 4)
    "Ctrl+5",  # Go to tab 5 (future: go to pane 5)
    "Ctrl+6",  # Go to tab 6 (future: go to pane 6)
    "Ctrl+7",  # Go to tab 7 (future: go to pane 7)
    "Ctrl+8",  # Go to tab 8 (future: go to pane 8)
    "Ctrl+9",  # Go to tab 9 (future: go to pane 9)
    # Debug/development
    "Ctrl+R",  # Reload window
    "Ctrl+Shift+R",  # Reset app state
]


def get_reserved_shortcuts():
    """
    Get the list of reserved shortcuts.

    Returns:
        List of shortcut strings that should be reserved for application handling
    """
    return WEBENGINE_RESERVED_SHORTCUTS.copy()


def add_reserved_shortcut(shortcut: str):
    """
    Add a shortcut to the reserved list.

    Args:
        shortcut: String representation of the shortcut (e.g., "Alt+P")
    """
    if shortcut not in WEBENGINE_RESERVED_SHORTCUTS:
        WEBENGINE_RESERVED_SHORTCUTS.append(shortcut)


def remove_reserved_shortcut(shortcut: str):
    """
    Remove a shortcut from the reserved list.

    Args:
        shortcut: String representation of the shortcut
    """
    if shortcut in WEBENGINE_RESERVED_SHORTCUTS:
        WEBENGINE_RESERVED_SHORTCUTS.remove(shortcut)
