#!/usr/bin/env python3
"""
Terminal Theme Management
Converts application themes to xterm.js format.
"""

from typing import Dict, Any
import ui.vscode_theme as vt


def get_dark_theme() -> Dict[str, Any]:
    """Get dark theme for xterm.js."""
    return {
        'background': vt.TERMINAL_BACKGROUND,
        'foreground': vt.TERMINAL_FOREGROUND,
        'cursor': '#ffffff',
        'cursorAccent': '#000000',
        'selection': vt.EDITOR_SELECTION,
        'black': vt.TERMINAL_ANSI_BLACK,
        'red': vt.TERMINAL_ANSI_RED,
        'green': vt.TERMINAL_ANSI_GREEN,
        'yellow': vt.TERMINAL_ANSI_YELLOW,
        'blue': vt.TERMINAL_ANSI_BLUE,
        'magenta': vt.TERMINAL_ANSI_MAGENTA,
        'cyan': vt.TERMINAL_ANSI_CYAN,
        'white': vt.TERMINAL_ANSI_WHITE,
        'brightBlack': vt.TERMINAL_ANSI_BRIGHT_BLACK,
        'brightRed': vt.TERMINAL_ANSI_BRIGHT_RED,
        'brightGreen': vt.TERMINAL_ANSI_BRIGHT_GREEN,
        'brightYellow': vt.TERMINAL_ANSI_BRIGHT_YELLOW,
        'brightBlue': vt.TERMINAL_ANSI_BRIGHT_BLUE,
        'brightMagenta': vt.TERMINAL_ANSI_BRIGHT_MAGENTA,
        'brightCyan': vt.TERMINAL_ANSI_BRIGHT_CYAN,
        'brightWhite': vt.TERMINAL_ANSI_BRIGHT_WHITE,
    }


def get_light_theme() -> Dict[str, Any]:
    """Get light theme for xterm.js."""
    # Light theme colors (VSCode Light+ inspired)
    return {
        'background': '#ffffff',
        'foreground': '#333333',
        'cursor': '#333333',
        'cursorAccent': '#ffffff',
        'selection': '#add6ff',
        'black': '#000000',
        'red': '#cd3131',
        'green': '#00bc00',
        'yellow': '#949800',
        'blue': '#0451a5',
        'magenta': '#bc05bc',
        'cyan': '#0598bc',
        'white': '#555555',
        'brightBlack': '#666666',
        'brightRed': '#cd3131',
        'brightGreen': '#14ce14',
        'brightYellow': '#b5ba00',
        'brightBlue': '#0451a5',
        'brightMagenta': '#bc05bc',
        'brightCyan': '#0598bc',
        'brightWhite': '#a5a5a5',
    }


def get_terminal_theme(theme_name: str) -> Dict[str, Any]:
    """
    Get terminal theme by name.
    
    Args:
        theme_name: Name of the theme ('dark' or 'light')
        
    Returns:
        Dictionary with xterm.js theme configuration
    """
    if theme_name == 'light':
        return get_light_theme()
    else:
        return get_dark_theme()


def get_terminal_config(font_size: int = 14, 
                        font_family: str = 'Consolas, "Courier New", monospace',
                        line_height: float = 1.2) -> Dict[str, Any]:
    """
    Get terminal configuration options.
    
    Args:
        font_size: Font size in pixels
        font_family: Font family string
        line_height: Line height multiplier
        
    Returns:
        Dictionary with terminal configuration
    """
    return {
        'cursorBlink': True,
        'macOptionIsMeta': True,
        'scrollback': 1000,
        'fontFamily': font_family,
        'fontSize': font_size,
        'lineHeight': line_height,
        'bellStyle': 'visual',
        'allowTransparency': False,
        'rightClickSelectsWord': True,
        'wordSeparator': ' ()[]{}\'"',
    }