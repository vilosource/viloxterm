#!/usr/bin/env python3
"""
Terminal Theme Management
Converts application themes to xterm.js format.
"""

from typing import Any


def get_dark_theme() -> dict[str, Any]:
    """Get dark theme for xterm.js."""
    return {
        "background": "#1e1e1e",
        "foreground": "#d4d4d4",
        "cursor": "#ffffff",
        "cursorAccent": "#000000",
        "selection": "#264f78",
        "black": "#000000",
        "red": "#cd3131",
        "green": "#0dbc79",
        "yellow": "#e5e510",
        "blue": "#2472c8",
        "magenta": "#bc3fbc",
        "cyan": "#11a8cd",
        "white": "#e5e5e5",
        "brightBlack": "#666666",
        "brightRed": "#f14c4c",
        "brightGreen": "#23d18b",
        "brightYellow": "#f5f543",
        "brightBlue": "#3b8eea",
        "brightMagenta": "#d670d6",
        "brightCyan": "#29b8db",
        "brightWhite": "#e5e5e5",
    }


def get_light_theme() -> dict[str, Any]:
    """Get light theme for xterm.js."""
    return {
        "background": "#ffffff",
        "foreground": "#333333",
        "cursor": "#333333",
        "cursorAccent": "#ffffff",
        "selection": "#add6ff",
        "black": "#000000",
        "red": "#cd3131",
        "green": "#00bc00",
        "yellow": "#949800",
        "blue": "#0451a5",
        "magenta": "#bc05bc",
        "cyan": "#0598bc",
        "white": "#555555",
        "brightBlack": "#666666",
        "brightRed": "#cd3131",
        "brightGreen": "#14ce14",
        "brightYellow": "#b5ba00",
        "brightBlue": "#0451a5",
        "brightMagenta": "#bc05bc",
        "brightCyan": "#0598bc",
        "brightWhite": "#a5a5a5",
    }


def get_terminal_theme_from_app_theme() -> dict[str, Any]:
    """Get terminal theme based on current application theme."""
    from viloapp.core.commands.executor import execute_command

    # Get current theme using command pattern
    result = execute_command("theme.getCurrentTheme")

    if result.success and result.value and "theme" in result.value:
        theme = result.value["theme"]
        # Get colors from theme object
        colors = theme.colors if hasattr(theme, "colors") else {}

        # Build terminal theme from application theme colors
        return {
            "background": colors.get("terminal.background", "#1e1e1e"),
            "foreground": colors.get("terminal.foreground", "#d4d4d4"),
            "cursor": colors.get("terminalCursor.foreground", "#ffffff"),
            "cursorAccent": colors.get("terminalCursor.background", "#000000"),
            "selection": colors.get("editor.selectionBackground", "#264f78"),
            "black": colors.get("terminal.ansiBlack", "#000000"),
            "red": colors.get("terminal.ansiRed", "#cd3131"),
            "green": colors.get("terminal.ansiGreen", "#0dbc79"),
            "yellow": colors.get("terminal.ansiYellow", "#e5e510"),
            "blue": colors.get("terminal.ansiBlue", "#2472c8"),
            "magenta": colors.get("terminal.ansiMagenta", "#bc3fbc"),
            "cyan": colors.get("terminal.ansiCyan", "#11a8cd"),
            "white": colors.get("terminal.ansiWhite", "#e5e5e5"),
            "brightBlack": colors.get("terminal.ansiBrightBlack", "#666666"),
            "brightRed": colors.get("terminal.ansiBrightRed", "#f14c4c"),
            "brightGreen": colors.get("terminal.ansiBrightGreen", "#23d18b"),
            "brightYellow": colors.get("terminal.ansiBrightYellow", "#f5f543"),
            "brightBlue": colors.get("terminal.ansiBrightBlue", "#3b8eea"),
            "brightMagenta": colors.get("terminal.ansiBrightMagenta", "#d670d6"),
            "brightCyan": colors.get("terminal.ansiBrightCyan", "#29b8db"),
            "brightWhite": colors.get("terminal.ansiBrightWhite", "#e5e5e5"),
        }

    # Fallback to dark theme if service not available
    return get_dark_theme()


def get_terminal_theme(theme_name: str = None) -> dict[str, Any]:
    """
    Get terminal theme by name or current app theme.

    Args:
        theme_name: 'dark', 'light', or None for current app theme

    Returns:
        Terminal theme dictionary for xterm.js
    """
    if theme_name == "dark":
        return get_dark_theme()
    elif theme_name == "light":
        return get_light_theme()
    else:
        return get_terminal_theme_from_app_theme()
